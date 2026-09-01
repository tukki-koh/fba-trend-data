"""
週次トレンドデータからInstagram投稿素材を自動生成するスクリプト。
- カルーセル用1080×1080画像（カバー + カテゴリ別 + CTA）
- 投稿キャプション（ハッシュタグ込み）
- Supabase Storageにアップロード
- /tmp/instagram_post.txt に投稿文を保存

GitHub Actionsから collect_trends.py の後に呼び出す、または
collect_trends.py の post_to_note() 後に呼び出す。
"""

import os
import io
import json
import time
import datetime
import random
import requests
import urllib.parse
import glob
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ── 設定 ──────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL     = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://fba-trend-data.vercel.app")

TODAY    = datetime.date.today()
ISO_WEEK = TODAY.strftime("%Y-W%V")
ISO_WEEK_NUM = int(TODAY.strftime("%V"))  # 1〜53 の整数（季節判定用）

W, H = 1080, 1080  # Instagram正方形サイズ

# ブランドカラー
C_BG       = "#fafaf9"   # 温かみのある白（サイトと統一）
C_ACCENT   = "#f59e0b"   # アンバー
C_DARK     = "#1c1917"   # ダークテキスト
C_SUB      = "#78716c"   # サブテキスト（stone-500）
C_CARD     = "#ffffff"   # カード背景
C_RANK1    = "#f59e0b"   # 1位: アンバー
C_RANK2    = "#a8a29e"   # 2位: stone-400
C_RANK3    = "#c2a06e"   # 3位: ブロンズ

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
]

CAT_EMOJI = {
    "ペット用品": "🐾", "アウトドア": "⛺",
    "キッチン": "🍳", "ビューティー": "💄", "ベビー": "👶",
}
CAT_COLOR = {
    "ペット用品": "#fde68a", "アウトドア": "#bbf7d0",
    "キッチン":   "#fed7aa", "ビューティー": "#fce7f3", "ベビー": "#e0f2fe",
}
CAT_ACCENT = {
    "ペット用品": "#d97706", "アウトドア": "#16a34a",
    "キッチン":   "#ea580c", "ビューティー": "#db2777", "ベビー": "#0284c7",
}


def _find_font() -> str | None:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    for pattern in ["/usr/share/fonts/**/*CJK*.ttc", "/usr/share/fonts/**/*.otf"]:
        m = glob.glob(pattern, recursive=True)
        if m:
            return m[0]
    try:
        r = subprocess.run(["fc-match", ":lang=ja", "-f", "%{file}"],
                           capture_output=True, text=True, timeout=5)
        p = r.stdout.strip()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    return None


FONT_PATH = _find_font()


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _pil_safe(text: str) -> str:
    """絵文字・4バイト文字を除去（PIL描画用）"""
    return "".join(c for c in text if ord(c) < 0x10000)


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill: str) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ── スライド1: カバー ──────────────────────────────
def generate_cover() -> bytes:
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)

    # 上部アクセントバー
    draw.rectangle([(0, 0), (W, 12)], fill=C_ACCENT)

    # ロゴエリア
    _draw_rounded_rect(draw, [60, 50, 420, 110], radius=20, fill=C_ACCENT)
    draw.text((80, 63), _pil_safe("FBAトレンドレーダー"), font=_font(32), fill="white")

    # メインタイトル
    draw.text((60, 150), _pil_safe("今週"), font=_font(52), fill=C_DARK)
    draw.text((60, 215), _pil_safe("Amazon で"), font=_font(72), fill=C_DARK)
    draw.text((60, 300), _pil_safe("売れた商品"), font=_font(72), fill=C_ACCENT)
    draw.text((60, 385), _pil_safe("TOP3 公開"), font=_font(52), fill=C_DARK)

    # 週ラベル
    _draw_rounded_rect(draw, [60, 470, 420, 520], radius=12, fill="#f5f5f4")
    draw.text((80, 480), _pil_safe(f"{ISO_WEEK}  データ"), font=_font(26), fill=C_SUB)

    # 季節コメント（ISO週番号で切り替え）
    if ISO_WEEK_NUM <= 12:
        season_comment = "春の仕入れシーズン到来"
    elif ISO_WEEK_NUM <= 25:
        season_comment = "夏物需要が動き始めました"
    elif ISO_WEEK_NUM <= 38:
        season_comment = "秋の売れ筋チェック"
    else:
        season_comment = "年末商戦の仕入れリサーチ"
    draw.text((80, 535), _pil_safe(f"▶  {season_comment}"), font=_font(22), fill=C_ACCENT)

    # カテゴリバッジ一覧
    cats = ["ペット用品", "アウトドア", "キッチン", "ビューティー", "ベビー"]
    y = 600
    x = 60
    for cat in cats:
        color = CAT_ACCENT.get(cat, C_ACCENT)
        bg = CAT_COLOR.get(cat, "#fde68a")
        text = _pil_safe(cat)
        fw = _font(22).getbbox(text)[2] + 30
        _draw_rounded_rect(draw, [x, y, x + fw, y + 44], radius=22, fill=bg)
        draw.text((x + 15, y + 10), text, font=_font(22), fill=color)
        x += fw + 14
        if x > W - 200:
            x = 60
            y += 60

    # 下部CTA
    draw.rectangle([(0, H - 160), (W, H)], fill=C_DARK)
    draw.text((60, H - 130), _pil_safe("スワイプして見る →"), font=_font(30), fill="white")
    draw.text((60, H - 85), _pil_safe("毎週火曜 21:00 更新"), font=_font(24), fill=C_ACCENT)

    # 下部アクセントバー
    draw.rectangle([(0, H - 12), (W, H)], fill=C_ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── スライド2〜6: カテゴリ別TOP3 ─────────────────
def generate_category_slide(cat_name: str, products: list[dict]) -> bytes:
    bg_color  = CAT_COLOR.get(cat_name, "#fde68a")
    accent    = CAT_ACCENT.get(cat_name, C_ACCENT)

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # 上部アクセントバー
    draw.rectangle([(0, 0), (W, 12)], fill=accent)

    # カテゴリ名
    draw.text((60, 40), _pil_safe(f"{cat_name}"), font=_font(52), fill=accent)
    draw.text((60, 108), _pil_safe("今週のTOP3"), font=_font(36), fill=C_DARK)

    # 週ラベル
    draw.text((W - 200, 60), _pil_safe(ISO_WEEK), font=_font(22), fill=C_SUB)

    # TOP3 商品カード
    top3 = products[:3] if products else []
    rank_colors = [C_RANK1, C_RANK2, C_RANK3]
    rank_labels = ["1位", "2位", "3位"]

    for i, (prod, rank_color, rank_label) in enumerate(zip(top3, rank_colors, rank_labels)):
        y_top = 200 + i * 240
        # カード
        _draw_rounded_rect(draw, [40, y_top, W - 40, y_top + 210], radius=24, fill=C_CARD)
        # 順位バッジ
        _draw_rounded_rect(draw, [60, y_top + 20, 140, y_top + 68], radius=16, fill=rank_color)
        draw.text((73, y_top + 28), _pil_safe(rank_label), font=_font(26), fill="white")
        # 商品名
        title = _pil_safe(prod.get("title", ""))
        if len(title) > 24:
            title = title[:24] + "…"
        draw.text((160, y_top + 28), title, font=_font(30), fill=C_DARK)
        # 価格
        price = prod.get("price", "-")
        draw.text((160, y_top + 72), _pil_safe(f"現在価格  {price}"), font=_font(26), fill=C_SUB)
        # ASIN
        asin = prod.get("asin", "")
        if asin:
            draw.text((160, y_top + 110), _pil_safe(f"Amazon → {asin}"), font=_font(20), fill=C_SUB)

    # 下部
    draw.rectangle([(0, H - 100), (W, H)], fill=C_DARK)
    draw.text((60, H - 75), _pil_safe("詳細データは毎週月曜にメール配信中"), font=_font(24), fill="white")
    draw.text((60, H - 40), _pil_safe(f"@ {SITE_URL.replace('https://', '')}"), font=_font(20), fill=C_ACCENT)
    draw.rectangle([(0, H - 12), (W, H)], fill=accent)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── スライド最終: CTA ────────────────────────────
def generate_cta_slide() -> bytes:
    img = Image.new("RGB", (W, H), C_DARK)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 12)], fill=C_ACCENT)

    draw.text((60, 80), _pil_safe("もっと詳しいデータが"), font=_font(44), fill="white")
    draw.text((60, 140), _pil_safe("欲しい方へ"), font=_font(44), fill=C_ACCENT)

    features = [
        "全5カテゴリ TOP10 完全データ",
        "各商品の現在価格つき",
        "Amazon直リンクで即リサーチ",
        "毎週月曜 AM7:00 自動配信",
        "14日間返金保証",
    ]
    y = 240
    for f in features:
        _draw_rounded_rect(draw, [60, y, W - 60, y + 62], radius=14, fill="#292524")
        draw.text((100, y + 14), _pil_safe(f"✓  {f}"), font=_font(28), fill="white")
        y += 82

    # 価格
    _draw_rounded_rect(draw, [60, y + 20, W - 60, y + 120], radius=20, fill=C_ACCENT)
    draw.text((110, y + 36), _pil_safe("月額 3,980円〜 · 無料サンプルあり"), font=_font(30), fill="white")

    draw.text((60, H - 100), _pil_safe(f"プロフィールのリンクから登録"), font=_font(28), fill=C_ACCENT)
    draw.text((60, H - 55), _pil_safe(SITE_URL.replace("https://", "")), font=_font(24), fill="#a8a29e")
    draw.rectangle([(0, H - 12), (W, H)], fill=C_ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Supabase アップロード ─────────────────────────
def _ensure_bucket(bucket: str = "instagram") -> None:
    url     = f"{SUPABASE_URL}/storage/v1/bucket/{bucket}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code in (400, 404) or (r.status_code == 200 and not r.json().get("public")):
        requests.post(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers,
                      json={"id": bucket, "name": bucket, "public": True}, timeout=10)


def upload_image(image_bytes: bytes, filename: str) -> str:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return ""
    _ensure_bucket()
    safe = urllib.parse.quote(filename, safe="-._~")
    path = f"{ISO_WEEK}/{safe}"
    url  = f"{SUPABASE_URL}/storage/v1/object/instagram/{path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "image/png",
        "x-upsert":      "true",
    }
    resp = requests.post(url, headers=headers, data=image_bytes, timeout=30)
    print(f"  [instagram] upload {filename} → {resp.status_code}")
    return f"{SUPABASE_URL}/storage/v1/object/public/instagram/{path}"


# ── 季節コメント ────────────────────────────────
def _season_comment() -> str:
    """ISO週番号をもとに季節に応じたコメントを返す"""
    if ISO_WEEK_NUM <= 12:
        return "春の仕入れシーズン、動き出しています。"
    elif ISO_WEEK_NUM <= 25:
        return "夏物需要が上がり始める時期。早めのチェックを。"
    elif ISO_WEEK_NUM <= 38:
        return "秋の売れ筋が見えてきました。"
    else:
        return "年末商戦に向けた仕入れリサーチの時期です。"


# ── キャプション生成 ──────────────────────────────
def _load_hashtags() -> str:
    """SNSハッシュタグ担当（週次AI社員）が更新したファイルを読む。
    無い・壊れている場合は既定値に自動で戻すので、投稿は必ず成立する。"""
    default = (
        "#Amazon物販 #FBA副業 #物販副業 #せどり女子 #副業初心者 "
        "#仕入れリサーチ #Amazonせどり #FBAせどり #副業月収 #在宅副業 "
        "#国内せどり #電脳せどり #物販ビジネス #Amazon #せどり"
    )
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "instagram_content", "hashtags_current.md",
    )
    try:
        with open(path, encoding="utf-8") as fh:
            tags = []
            for ln in fh:
                t = ln.strip().lstrip("- ").strip()
                # 見出し（"# 今週の…"）は # の後ろに空白が入るので除外できる
                if t.startswith("#") and not t.startswith("# "):
                    tags += [w for w in t.split() if w.startswith("#")]
        tags = list(dict.fromkeys(tags))  # 重複除去（順序は維持）
        if len(tags) >= 10:
            print(f"  [caption] ハッシュタグ担当の更新を使用（{len(tags)}個）")
            return " ".join(tags[:15])
        print("  [caption] タグ数が不足のため既定値を使用")
    except FileNotFoundError:
        print("  [caption] ハッシュタグ未生成のため既定値を使用")
    except Exception as e:
        print(f"  [caption] 読込エラー({e})のため既定値を使用")
    return default


def build_caption(trend_data: dict) -> str:
    # 注目カテゴリ（最も商品数が多い）
    top_cat = max(trend_data, key=lambda c: len(trend_data[c]), default="ペット用品")
    top_product = trend_data.get(top_cat, [{}])[0].get("title", "")[:20]

    # ISO週番号をシードにしてパターンをランダム選択（週ごとに固定）
    rng = random.Random(ISO_WEEK_NUM)
    pattern = rng.randint(0, 3)

    season = _season_comment()

    openers = [
        f"今週の売れ筋データ、更新しました。\n\n{top_cat}で動いているのは「{top_product}」。\n{season}",
        f"📊 {top_cat}のランキングを公開。\n\n1位は「{top_product}」でした。\n{season}",
        f"今週注目は{top_cat}。\n\n「{top_product}」がトップ入り。\n{season}",
        f"FBAトレンドデータ、{ISO_WEEK}版。\n\n{top_cat}から「{top_product}」が浮上。\n{season}",
    ]
    opener = openers[pattern]

    hashtags = _load_hashtags()

    caption = f"""{opener}

スワイプして全カテゴリをチェック↓

━━━━━━━━━━━━━━━
毎週火曜、5カテゴリのAmazon売れ筋TOP3を無料公開中。
全TOP10データはプロフィールのリンクから。
━━━━━━━━━━━━━━━

{hashtags}"""

    return caption


# ── Instagram Meta Graph API 自動投稿 ────────────────────────────────────────
def _wait_for_ig_media(container_id: str, token: str, max_wait: int = 60) -> bool:
    """メディアコンテナの処理完了を待つ"""
    url = f"https://graph.facebook.com/v18.0/{container_id}"
    for _ in range(max_wait // 3):
        time.sleep(3)
        r = requests.get(url, params={"fields": "status_code", "access_token": token}, timeout=10)
        status = r.json().get("status_code", "")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            return False
    return False


def post_to_instagram(image_urls: dict, caption: str) -> str | None:
    """
    Meta Graph API でInstagramカルーセル投稿。
    必要環境変数: META_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
    画像URLはSupabaseのpublic URL (already uploaded)。
    Returns: 投稿パーマリンク or None
    """
    token   = os.environ.get("META_ACCESS_TOKEN", "").strip()
    ig_id   = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()

    if not token or not ig_id:
        print("[Instagram] META_ACCESS_TOKEN / INSTAGRAM_ACCOUNT_ID 未設定 → スキップ")
        print("  設定方法: GitHubリポジトリ Settings → Secrets → Actions に追加")
        return None

    # 公開済みSupabaseのURLだけを使う（最大10枚）
    public_urls = [v for v in image_urls.values() if v and v.startswith("http")][:10]
    if not public_urls:
        print("[Instagram] 公開画像URLなし → スキップ")
        return None

    api_base = f"https://graph.facebook.com/v18.0/{ig_id}"

    if len(public_urls) == 1:
        # シングル投稿
        r = requests.post(f"{api_base}/media",
                          params={"image_url": public_urls[0], "caption": caption,
                                  "access_token": token}, timeout=30)
        d = r.json()
        if "id" not in d:
            print(f"[Instagram] media作成失敗: {d}")
            return None
        container_id = d["id"]
    else:
        # カルーセル: 各画像をコンテナとして登録
        child_ids = []
        for url in public_urls:
            r = requests.post(f"{api_base}/media",
                              params={"image_url": url, "is_carousel_item": "true",
                                      "access_token": token}, timeout=30)
            d = r.json()
            if "id" not in d:
                print(f"[Instagram] carousel item作成失敗: {d}")
                continue
            child_ids.append(d["id"])

        if not child_ids:
            print("[Instagram] カルーセルアイテムなし → スキップ")
            return None

        # 処理完了待ち
        for cid in child_ids:
            _wait_for_ig_media(cid, token)

        # カルーセルコンテナ作成
        r = requests.post(f"{api_base}/media",
                          params={"media_type": "CAROUSEL",
                                  "children": ",".join(child_ids),
                                  "caption": caption,
                                  "access_token": token}, timeout=30)
        d = r.json()
        if "id" not in d:
            print(f"[Instagram] carousel container作成失敗: {d}")
            return None
        container_id = d["id"]
        _wait_for_ig_media(container_id, token)

    # 公開
    r = requests.post(f"{api_base}/media_publish",
                      params={"creation_id": container_id, "access_token": token}, timeout=30)
    d = r.json()
    if "id" not in d:
        print(f"[Instagram] 公開失敗: {d}")
        return None

    # パーマリンク取得
    post_id = d["id"]
    r2 = requests.get(f"https://graph.facebook.com/v18.0/{post_id}",
                      params={"fields": "permalink", "access_token": token}, timeout=10)
    permalink = r2.json().get("permalink", f"https://www.instagram.com/fba_trend_radar/")
    print(f"[Instagram] 投稿完了: {permalink}")
    return permalink


# ── メイン ───────────────────────────────────────
def generate_instagram_content(trend_data: dict) -> dict:
    print("\n[Instagram] 画像生成開始...")

    image_urls: dict[str, str] = {}
    local_paths: list[str] = []

    # カバー
    cover = generate_cover()
    url = upload_image(cover, "ig_cover.png")
    image_urls["cover"] = url
    # ローカルにも保存
    local = f"/tmp/instagram_{ISO_WEEK}_01_cover.png"
    with open(local, "wb") as f:
        f.write(cover)
    local_paths.append(local)
    print(f"  [instagram] cover → {url or local}")

    # カテゴリ別
    cats = list(trend_data.keys())
    for i, cat in enumerate(cats, 2):
        products = trend_data.get(cat, [])
        slide = generate_category_slide(cat, products)
        filename = f"ig_cat_{i:02d}_{cat}.png"
        url = upload_image(slide, filename)
        image_urls[f"cat_{cat}"] = url
        local = f"/tmp/instagram_{ISO_WEEK}_{i:02d}_{cat}.png"
        with open(local, "wb") as f:
            f.write(slide)
        local_paths.append(local)
        print(f"  [instagram] {cat} → {url or local}")

    # CTA
    cta = generate_cta_slide()
    url = upload_image(cta, "ig_cta.png")
    image_urls["cta"] = url
    local = f"/tmp/instagram_{ISO_WEEK}_{len(cats)+2:02d}_cta.png"
    with open(local, "wb") as f:
        f.write(cta)
    local_paths.append(local)
    print(f"  [instagram] cta → {url or local}")

    # キャプション
    caption = build_caption(trend_data)
    caption_path = f"/tmp/instagram_{ISO_WEEK}_caption.txt"
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)
    print(f"\n[Instagram] キャプション保存: {caption_path}")
    print("\n" + "═" * 50)
    print(caption)
    print("═" * 50)

    # 画像URLリスト
    summary_path = f"/tmp/instagram_{ISO_WEEK}_images.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"week": ISO_WEEK, "images": image_urls, "local": local_paths}, f,
                  ensure_ascii=False, indent=2)

    print(f"\n[OK] Instagram素材生成完了 — {len(local_paths)}枚")
    print(f"     画像: /tmp/instagram_{ISO_WEEK}_*.png")
    print(f"     投稿文: {caption_path}")

    # Meta Graph API で自動投稿
    post_url = post_to_instagram(image_urls, caption)

    return {"image_urls": image_urls, "caption": caption, "local_paths": local_paths,
            "post_url": post_url}


if __name__ == "__main__":
    # 単体実行時はダミーデータで動作確認
    dummy = {
        cat: [
            {"rank": i, "title": f"サンプル商品{i} {cat}", "price": f"¥{1000*i:,}", "asin": f"B0{i:08d}"}
            for i in range(1, 11)
        ]
        for cat in ["ペット用品", "アウトドア", "キッチン", "ビューティー", "ベビー"]
    }
    generate_instagram_content(dummy)
