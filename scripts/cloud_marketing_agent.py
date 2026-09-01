"""
クラウド版・週次マーケ社員（GitHub Actionsで毎週水曜に実行）

このアプリ(Claude Code)の起動状態に依存せず、クラウドで確実に稼働する。
【役割】SNS（Instagram）のハッシュタグ最適化 "専任"。
  - instagram_content/hashtags_current.md … 今週の推奨ハッシュタグ15個（全面再生成）
    → generate_instagram.py がこのファイルを読んで実際の投稿に使う

※ public/llms.txt は「月次SEO/GEO担当」(scripts/cloud_agents.py seo) の担当。
   二重管理を避けるため、この社員は触らない。

必要な環境変数: ANTHROPIC_API_KEY
LP本体(page.tsx)などコードの判断編集は、ローカルのAI社員が担当（本ジョブでは触らない）。
"""

import os
import sys
import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HASH = BASE / "instagram_content" / "hashtags_current.md"

KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
if not KEY:
    print("[SKIP] ANTHROPIC_API_KEY 未設定のため終了")
    sys.exit(0)

try:
    import anthropic
except ImportError:
    sys.exit("anthropic 未インストール")

client = anthropic.Anthropic(api_key=KEY, max_retries=4, timeout=180.0)
TODAY = datetime.date.today().isoformat()

SERVICE_FACTS = """
サービス名: FBAトレンドレーダー（https://fba-trend-data.vercel.app）
内容: Amazon JPの売れ筋ランキングTOP10を5カテゴリ（ペット用品・アウトドア・キッチン・ビューティー・ベビー）、毎週月曜AM7:00にPDFでメール配信。
料金: スタンダード月額1,480円 / プロ月額2,480円（いずれも人気AIツール1つ分より安い）。14日間全額返金保証。無料サンプルあり（カード登録不要）。
対象: 副業でAmazon FBA物販・せどりをする初心者〜中級者、30〜40代。
特徴: 仕入れリサーチを週1通のメールに置き換え、時間を大幅短縮。価格・Amazonリンク付き。
"""


def ask(prompt: str, max_tokens: int = 1200) -> str:
    msg = client.messages.create(
        model="claude-haiku-4-5", max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def update_hashtags():
    prompt = f"""あなたはInstagram集客の専門家です。以下のサービスのアカウント(@fba_trend_radar)向けに、
今週おすすめの日本語ハッシュタグを「ちょうど15個」選んでください。

{SERVICE_FACTS}

要件:
- 副業・Amazon物販・せどり・仕入れリサーチ・在宅ワーク系のリーチが取れるもの中心
- 大・中・小の規模をバランス良く混ぜる
- 各ハッシュタグは # で始め、1行に1つ、15行だけを出力（説明・前置き不要）。"""
    out = ask(prompt, 400)
    tags = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("#")][:15]
    if len(tags) < 10:
        print("[hashtags] 取得数不足のためスキップ")
        return False
    body = (
        f"# 今週の推奨ハッシュタグ（自動更新: {TODAY}）\n\n"
        "投稿時にこの15個をコピーして使用してください。\n\n"
        + " ".join(tags) + "\n\n"
        "---\n" + "\n".join(f"- {t}" for t in tags) + "\n"
    )
    HASH.parent.mkdir(parents=True, exist_ok=True)
    HASH.write_text(body, encoding="utf-8")
    print(f"[hashtags] 更新 ({len(tags)}個)")
    return True


def main():
    print(f"=== SNSハッシュタグ担当（週次） {TODAY} ===")
    changed = False
    try:
        changed |= update_hashtags()
    except Exception as e:
        print(f"[hashtags] エラー: {e}")
    print("変更あり" if changed else "変更なし")


if __name__ == "__main__":
    main()
