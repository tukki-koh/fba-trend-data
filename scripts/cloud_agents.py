"""
クラウド常駐AI社員（GitHub Actions から実行）

このアプリ（Claude Code）の起動状態に依存せず、24時間365日クラウドで動く。

モード:
  ads    … Google広告最適化担当（隔週）  marketing/google_ads_assets.md を刷新
  seo    … 月次SEO/GEO担当             public/llms.txt 刷新 ＋ metadata を微修正
  growth … 成長・ベンチマーク担当        世界最高水準の企業を手本にLPを1点改善

安全設計:
  - コードを触るモードは「完全一致の find / replace」でのみ編集する（自由な書き換えは禁止）
  - 適用後に GitHub Actions 側で `npm run build` を実行し、失敗したら変更を破棄する
  - find が見つからない場合は何もせず正常終了（壊れた状態でコミットしない）

必要な環境変数: ANTHROPIC_API_KEY
"""

import os
import re
import sys
import json
import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
TODAY = datetime.date.today()

if not KEY:
    print("[SKIP] ANTHROPIC_API_KEY 未設定のため終了")
    sys.exit(0)

try:
    import anthropic
except ImportError:
    sys.exit("anthropic 未インストール")

client = anthropic.Anthropic(api_key=KEY, max_retries=4, timeout=300.0)

SERVICE = """
サービス名: FBAトレンドレーダー（https://fba-trend-data.vercel.app）
内容: Amazon JPの売れ筋ランキングTOP10を5カテゴリ（ペット用品・アウトドア・キッチン・ビューティー・ベビー）、
      毎週月曜AM7:00にPDFでメール配信。
料金: スタンダード月額1,480円 / プロ月額2,480円。14日間全額返金保証。無料サンプルあり（カード登録不要）。
対象: 副業でAmazon FBA物販・せどりをする初心者〜中級者、30〜40代。
方針: 実在しない実績・顧客の声は絶対に書かない（景品表示法の優良誤認・ステマ規制を厳守）。
"""


def ask(prompt: str, model: str, max_tokens: int = 4000) -> str:
    """モデルを順に試して最初に成功したものを返す"""
    for m in [model, "claude-sonnet-5", "claude-haiku-4-5-20251001"]:
        try:
            r = client.messages.create(
                model=m, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"  [model] {m}")
            return r.content[0].text.strip()
        except Exception as e:
            print(f"  [warn] {m} 失敗: {type(e).__name__}: {e}")
    return ""


def parse_json(text: str) -> dict:
    """```json フェンス付きでも素のJSONでも読めるようにする"""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", t, re.S)
    if m:
        t = m.group(1).strip()
    else:
        i, j = t.find("{"), t.rfind("}")
        if i != -1 and j > i:
            t = t[i:j + 1]
    try:
        return json.loads(t)
    except Exception as e:
        print(f"[ERROR] JSON解析に失敗: {e}")
        return {}


def apply_edits(edits: list) -> int:
    """find/replace を完全一致で適用。見つからなければスキップ（壊さない）"""
    applied = 0
    for ed in edits:
        rel = (ed.get("file") or "").lstrip("/")
        find = ed.get("find") or ""
        repl = ed.get("replace")
        if not rel or not find or repl is None:
            continue
        path = BASE / rel
        if not path.exists():
            print(f"  [skip] ファイルなし: {rel}")
            continue
        src = path.read_text(encoding="utf-8")
        if find not in src:
            print(f"  [skip] 一致なし: {rel} / {find[:40]!r}")
            continue
        if src.count(find) > 1:
            print(f"  [skip] 複数一致のため危険: {rel} / {find[:40]!r}")
            continue
        path.write_text(src.replace(find, repl, 1), encoding="utf-8")
        print(f"  [edit] {rel}: {find[:36]!r} → {repl[:36]!r}")
        applied += 1
    return applied


# ── ① Google広告最適化担当（隔週） ─────────────────────────
def run_ads() -> None:
    # 隔週運用: 偶数週はスキップ
    wk = int(TODAY.strftime("%V"))
    if wk % 2 == 0:
        print(f"[SKIP] 隔週運用のため今週（第{wk}週・偶数）はスキップ")
        return

    f = BASE / "marketing" / "google_ads_assets.md"
    cur = f.read_text(encoding="utf-8") if f.exists() else ""
    prompt = f"""あなたはGoogle広告の運用専門家です。以下のアセット集を「今週版」に更新してください。

{SERVICE}

## 現在のファイル
{cur}

## 更新方針
- RSA見出し（全角15字以内）を2〜3本、より訴求の強い表現に入れ替える
- キーワード・除外キーワードを季節性（現在{TODAY.year}年{TODAY.month}月）に合わせて見直す
- 文字数制限を厳守: 見出し全角15字 / 説明文全角45字 / パス全角7字
- 「最終更新」を {TODAY} に更新する
- 実在しない実績は書かない

## 出力
更新後のMarkdown全文のみを出力してください。前置き・後書き・コードフェンスは不要です。"""

    out = ask(prompt, "claude-haiku-4-5-20251001", 6000)
    if len(out) < 800 or "RSA" not in out:
        print("[SKIP] 出力が不十分のため更新しません")
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out.rstrip() + "\n", encoding="utf-8")
    print(f"[OK] {f.relative_to(BASE)} を更新（{len(out)}字）")


# ── ② 月次SEO/GEO担当 ────────────────────────────────────
def run_seo() -> None:
    llms = BASE / "public" / "llms.txt"
    layout = BASE / "src" / "app" / "layout.tsx"
    cur_llms = llms.read_text(encoding="utf-8") if llms.exists() else ""
    cur_layout = layout.read_text(encoding="utf-8") if layout.exists() else ""

    prompt = f"""あなたはSEO/GEO（生成エンジン最適化）の専門家です。

{SERVICE}

## 現在の public/llms.txt
{cur_llms}

## 現在の src/app/layout.tsx（抜粋・metadata部分）
{cur_layout[:3000]}

## タスク
1. llms.txt を、ChatGPT・Perplexity・Geminiが引用しやすい形に刷新する
   （## このサービスは何か / 誰向けか / 料金 / 何が届くか / よくある質問(Q&A 5問以上)）
2. layout.tsx の description を、検索クリック率が高まる文言に1箇所だけ改善する（130字以内）

## 出力（このJSONのみ。前置き不要）
{{
  "summary": "何をどう変えたかを1文で",
  "llms_txt": "llms.txtの全文",
  "edits": [
    {{"file": "src/app/layout.tsx", "find": "変更前の文字列（ファイル内に1度だけ現れる短い完全一致文字列）", "replace": "変更後の文字列"}}
  ]
}}

重要: find はファイル内の文字列と1文字も違わない完全一致にすること。自信がなければ edits は空配列にすること。"""

    data = parse_json(ask(prompt, "claude-sonnet-5", 6000))
    if not data:
        print("[SKIP] 応答を解析できませんでした")
        return

    body = data.get("llms_txt", "")
    if len(body) > 400 and "1,480" in body.replace("，", ","):
        llms.parent.mkdir(parents=True, exist_ok=True)
        llms.write_text(body.rstrip() + f"\n\n<!-- 最終更新: {TODAY} / 月次SEO/GEO担当(cloud) -->\n",
                        encoding="utf-8")
        print(f"[OK] public/llms.txt を更新（{len(body)}字）")
    else:
        print("[SKIP] llms.txt の出力が不十分")

    n = apply_edits(data.get("edits") or [])
    print(f"[OK] コード編集 {n} 件 ／ 要約: {data.get('summary', '-')}")


# ── ③ 成長・ベンチマーク担当（週次） ─────────────────────
def run_growth() -> None:
    page = BASE / "src" / "app" / "page.tsx"
    cur = page.read_text(encoding="utf-8")

    prompt = f"""あなたは「成長・ベンチマーク担当」です。世界で最も成功している企業のやり方を手本に、
このランディングページを今週1点だけ改善してください。

{SERVICE}

## 手本にする企業の例
Apple / Stripe / Notion / Superhuman / Linear（明快さ・余白・信頼設計）
Netflix / Spotify / Amazon / Duolingo（無料お試し・継続の設計）

## 現在の src/app/page.tsx
{cur}

## 制約（厳守）
- 変更は1箇所のみ。文言の改善が中心で、レイアウトの大改造は禁止
- 既存のデザイン（amber/stoneの配色・落ち着いたトーン）を壊さない
- 実在しない実績・顧客の声・数値は絶対に追加しない
- JSXとして必ず正しい構文にする（壊れるとサイトが落ちる）
- find は page.tsx 内に1度だけ現れる完全一致の文字列にすること

## 出力（このJSONのみ。前置き不要）
{{
  "benchmark": "手本にした企業名",
  "summary": "何をどう変え、狙いは何かを1文で",
  "edits": [
    {{"file": "src/app/page.tsx", "find": "変更前の文字列", "replace": "変更後の文字列"}}
  ]
}}

自信が持てない場合は edits を空配列にしてください（無理に変更しないこと）。"""

    data = parse_json(ask(prompt, "claude-sonnet-5", 6000))
    if not data:
        print("[SKIP] 応答を解析できませんでした")
        return
    n = apply_edits(data.get("edits") or [])
    print(f"[OK] 手本: {data.get('benchmark', '-')} ／ 変更 {n} 件 ／ {data.get('summary', '-')}")


MODES = {"ads": run_ads, "seo": run_seo, "growth": run_growth}

if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if mode not in MODES:
        sys.exit(f"使い方: python scripts/cloud_agents.py [{'|'.join(MODES)}]")
    print(f"=== クラウドAI社員: {mode} ／ {TODAY} ===")
    MODES[mode]()
