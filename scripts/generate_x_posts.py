"""
X（旧Twitter）用の週次投稿素材を生成する。

なぜ必要か:
  半年の自動配信（note/Instagram/Facebook/SEO）でリード獲得は0だった。
  日本の せどり・物販層が最も密集しているXだけが手つかずなので、そこへ
  「商品そのもの（売れ筋データ）を出し惜しみせず公開する」形で参入する。

生成物（out/x_posts/ に出力）:
  - cover.png        … 今週の総括カード（1枚目・固定で使う）
  - 01〜05_*.png     … カテゴリ別TOP5カード
  - posts.md         … そのままコピペできる投稿文（スレッド構成）

使い方:
  python scripts/generate_x_posts.py
  → out/x_posts/ の画像とposts.mdをXに貼るだけ。

注意: 投稿自体は手動。新規アカウントの自動投稿は凍結リスクが高く、
      最初の顧客獲得フェーズでは1対1の対話そのものが目的のため。
"""

import os
import sys
import json
import glob
import datetime
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "out" / "x_posts"
SITE = "https://fba-trend-data.vercel.app"

W, H = 1600, 900          # Xのタイムラインで切れにくい16:9

# ブランド色（サイトと統一: amber / stone）
C_BG      = "#fffdf8"
C_CARD    = "#ffffff"
C_INK     = "#1c1917"
C_SUB     = "#78716c"
C_LINE    = "#e7e5e4"
C_ACCENT  = "#f59e0b"
C_DARK    = "#292524"
RANK_COL  = ["#f59e0b", "#a8a29e", "#c2a06e", "#d6d3d1", "#d6d3d1"]

FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
] + FONT_CANDIDATES


def _find(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    for pat in ["/usr/share/fonts/**/*CJK*.ttc", "/System/Library/Fonts/*.ttc"]:
        m = glob.glob(pat, recursive=True)
        if m:
            return m[0]
    return None


FONT_R, FONT_B = _find(FONT_CANDIDATES), _find(FONT_BOLD_CANDIDATES)


def f(size, bold=False):
    p = FONT_B if bold else FONT_R
    if p:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def safe(t):
    """PILで描けない絵文字・4バイト文字を除去"""
    return "".join(c for c in str(t) if ord(c) < 0x10000)


def fit(draw, text, font, max_w):
    """max_w に収まるよう末尾を … で詰める"""
    text = safe(text)
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def card_base(title, subtitle):
    img = Image.new("RGB", (W, H), C_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (W, 14)], fill=C_ACCENT)
    d.text((72, 62), safe(title), font=f(64, True), fill=C_INK)
    d.text((74, 152), safe(subtitle), font=f(30), fill=C_SUB)
    # フッター（出典を必ず明記する。信頼の土台）
    d.line([(72, H - 92), (W - 72, H - 92)], fill=C_LINE, width=2)
    d.text((72, H - 72), safe("出典: Amazon.co.jp 売れ筋ランキング（公開情報）"), font=f(24), fill=C_SUB)
    tag = "FBAトレンドレーダー"
    d.text((W - 72 - d.textlength(tag, font=f(26, True)), H - 74),
           tag, font=f(26, True), fill=C_ACCENT)
    return img, d


def row(d, y, rank, title, price, w_left=72):
    """1商品ぶんの行"""
    col = RANK_COL[min(rank - 1, len(RANK_COL) - 1)]
    d.rounded_rectangle([w_left, y, w_left + 74, y + 74], radius=16, fill=col)
    num = str(rank)
    d.text((w_left + 37 - d.textlength(num, font=f(40, True)) / 2, y + 13),
           num, font=f(40, True), fill="#ffffff")
    tx = w_left + 100
    price_w = 210
    d.text((tx, y + 6), fit(d, title, f(34, True), W - tx - price_w - 90),
           font=f(34, True), fill=C_INK)
    p = safe(price or "-")
    d.text((W - 72 - d.textlength(p, font=f(34, True)), y + 8),
           p, font=f(34, True), fill=C_DARK)
    d.line([(tx, y + 88), (W - 72, y + 88)], fill=C_LINE, width=1)


def make_category_card(cat, items, week):
    img, d = card_base(f"{cat} 今週のTOP5", f"{week}｜Amazon JP 売れ筋ランキング")
    y = 232
    for i, it in enumerate(items[:5], 1):
        row(d, y, i, it.get("title", ""), it.get("price", ""))
        y += 112
    return img


def make_cover(data, week):
    img, d = card_base("今週Amazonで売れた商品",
                       f"{week}｜5カテゴリ × TOP10 を無料公開")
    y = 236
    for cat, items in data.items():
        if not items:
            continue
        # 絵文字はヒラギノに字形が無く豆腐になるため使わない
        d.rounded_rectangle([72, y, 340, y + 60], radius=14, fill="#fef3c7")
        d.text((92, y + 12), safe(cat), font=f(30, True), fill="#b45309")
        t = items[0].get("title", "")
        d.text((372, y + 12), fit(d, t, f(30), W - 372 - 220),
               font=f(30), fill=C_INK)
        p = safe(items[0].get("price", ""))
        d.text((W - 72 - d.textlength(p, font=f(30, True)), y + 12),
               p, font=f(30, True), fill=C_DARK)
        y += 84
    d.text((72, y + 20), safe("↓ カテゴリ別のTOP5は続くツリーに全部貼ります"),
           font=f(28), fill=C_SUB)
    return img


# ─── 投稿文 ───────────────────────────────────────────
def build_posts(data, week):
    """スレッド構成の投稿文。売り込みは最後の1回だけ。"""
    lines = []
    lines.append(f"""## 1投稿目（画像: cover.png）

今週Amazonで実際に売れた商品、5カテゴリぶん全部出します。

{week} のデータです。

・ペット用品
・アウトドア
・キッチン
・ビューティー
・ベビー

各TOP5をこのツリーにぶら下げます。
仕入れリサーチの最初の30分、これで省いてください。

#せどり #Amazon物販 #物販副業
""")
    n = 2
    for cat, items in data.items():
        if not items:
            continue
        top = items[0]
        lines.append(f"""## {n}投稿目（画像: {n-1:02d}_{cat}.png）

【{cat}】

1位 {top.get('title','')[:40]}
{top.get('price','')}

TOP5は画像に。
""")
        n += 1

    lines.append(f"""## 最後の投稿（売り込みはここだけ）

以上、{week} のAmazon売れ筋でした。

毎週月曜の朝7時に、TOP10（この倍）をPDFでまとめて配ってます。
価格・商品リンク付きで、そのまま仕入れリサーチに使える形です。

無料サンプルはカード登録なしで受け取れます。
{SITE}

来週も月曜に出します。
""")
    return "\n---\n\n".join(lines)


def main():
    today = datetime.date.today()
    week = today.strftime("%Y年%m月第%W週").replace("第0週", "第1週")
    iso = today.strftime("%Y-W%V")

    # 引数でJSONを渡せる（取得済みデータの再利用用）
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(f"[data] {sys.argv[1]} を使用")
    else:
        sys.path.insert(0, str(BASE / "scripts"))
        os.environ.setdefault("SUPABASE_URL", os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "x"))
        os.environ.setdefault("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "x"))
        for k in ("RESEND_API_KEY", "NOTE_EMAIL", "NOTE_PASSWORD"):
            os.environ.setdefault(k, "x")
        import importlib.util
        spec = importlib.util.spec_from_file_location("ct", BASE / "scripts" / "collect_trends.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        data = m.build_trend_data()
        print("[data] Amazonから新規取得")

    OUT.mkdir(parents=True, exist_ok=True)
    make_cover(data, iso).save(OUT / "cover.png")
    print("  cover.png")
    for i, (cat, items) in enumerate(data.items(), 1):
        if not items:
            continue
        p = OUT / f"{i:02d}_{cat}.png"
        make_category_card(cat, items, iso).save(p)
        print(f"  {p.name}")
    (OUT / "posts.md").write_text(build_posts(data, iso), encoding="utf-8")
    print(f"  posts.md\n\n→ {OUT} を開いて、画像と文をXに貼るだけ")


if __name__ == "__main__":
    main()
