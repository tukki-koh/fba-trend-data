"""
毎週月曜日に GitHub Actions から自動実行されるスクリプト。
Amazon公開ベストセラーページ（無料・APIキー不要）からデータを収集し、
PDFレポートを生成して Supabase Storage にアップロード → 会員全員にメール送信。
さらに note.com へ週次トレンド記事を自動投稿。

必要な環境変数:
  SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY,
  FROM_EMAIL, NEXT_PUBLIC_SITE_URL,
  NOTE_SESSION_COOKIE (任意), NOTE_USER_SLUG (任意)
"""

import os
import json
import time
import datetime
import random
import requests
from bs4 import BeautifulSoup
from typing import Any

# ────────────────────────────────────────────
# 設定
# ────────────────────────────────────────────
SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL     = os.environ["FROM_EMAIL"]
SITE_URL       = os.environ["NEXT_PUBLIC_SITE_URL"]

TODAY      = datetime.date.today()
ISO_WEEK   = TODAY.strftime("%Y-W%V")
REPORT_DIR = "/tmp/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

# Amazon JP ベストセラーカテゴリ（公開URL）
CATEGORIES = {
    "ペット用品":    "https://www.amazon.co.jp/gp/bestsellers/pet-supplies/",
    "アウトドア":    "https://www.amazon.co.jp/gp/bestsellers/sports/",
    "キッチン":      "https://www.amazon.co.jp/gp/bestsellers/kitchen/",
    "ビューティー":  "https://www.amazon.co.jp/gp/bestsellers/beauty/",
    "ベビー":        "https://www.amazon.co.jp/gp/bestsellers/baby/",
}

# ブロック対策のための User-Agent ローテーション
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def make_headers() -> dict[str, str]:
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

# ────────────────────────────────────────────
# 1. Amazon ベストセラーページをスクレイピング
# ────────────────────────────────────────────
def scrape_bestsellers(url: str) -> list[dict[str, Any]]:
    """Amazon の公開ベストセラーページから商品情報を取得"""
    try:
        resp = requests.get(url, headers=make_headers(), timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] fetch failed: {url} → {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    products = []

    # ベストセラーの商品カード（複数のセレクタに対応）
    cards = soup.select("div.zg-grid-general-faceout") or soup.select("li.zg-item-immersion")

    for i, card in enumerate(cards[:20], 1):
        title_el = card.select_one("div.p13n-sc-truncate-desktop-type2, span.zg-text-center-align, div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y")
        price_el = card.select_one("span.p13n-sc-price, span._cDEzb_p13n-sc-price_3mJ9Z")
        asin_el  = card.select_one("a[href*='/dp/']")

        title = title_el.get_text(strip=True) if title_el else "商品名取得中"
        price = price_el.get_text(strip=True) if price_el else "-"
        asin  = ""
        if asin_el:
            href = asin_el.get("href", "")
            parts = [p for p in href.split("/") if p]
            if "dp" in parts:
                dp_idx = parts.index("dp")
                asin = parts[dp_idx + 1] if dp_idx + 1 < len(parts) else ""

        products.append({
            "rank":  i,
            "title": title[:50],
            "price": price,
            "asin":  asin,
            "url":   f"https://www.amazon.co.jp/dp/{asin}" if asin else "",
        })

    # リクエスト間隔（ブロック対策）
    time.sleep(random.uniform(3, 6))
    return products


def build_trend_data() -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for cat_name, url in CATEGORIES.items():
        print(f"  → {cat_name} を収集中...")
        result[cat_name] = scrape_bestsellers(url)
    return result

# ────────────────────────────────────────────
# 2. PDF 生成
# ────────────────────────────────────────────
def generate_pdf(trend_data: dict[str, Any]) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

    pdf_path = os.path.join(REPORT_DIR, f"report_{ISO_WEEK}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles   = getSampleStyleSheet()
    jp_style = ParagraphStyle("JP", fontName="HeiseiKakuGo-W5", fontSize=10, leading=14)
    story    = []

    # ─ タイトル ─
    story.append(Paragraph(
        f'<font name="HeiseiKakuGo-W5" size="18"><b>FBAトレンドレーダー {ISO_WEEK}</b></font>',
        styles["Title"]
    ))
    story.append(Paragraph(
        f'<font name="HeiseiKakuGo-W5">配信日: {TODAY.strftime("%Y年%m月%d日（月）")}</font>',
        jp_style
    ))
    story.append(Spacer(1, 8*mm))

    # ─ カテゴリ別テーブル ─
    for cat, products in trend_data.items():
        story.append(Paragraph(
            f'<font name="HeiseiKakuGo-W5" size="13"><b>■ {cat} ランキング</b></font>',
            styles["Heading2"]
        ))
        story.append(Spacer(1, 2*mm))

        if not products:
            story.append(Paragraph(
                '<font name="HeiseiKakuGo-W5">データ取得できませんでした。次週再試行します。</font>',
                jp_style
            ))
        else:
            table_data = [["順位", "商品名", "価格"]]
            for p in products[:10]:
                table_data.append([
                    str(p["rank"]),
                    Paragraph(f'<font name="HeiseiKakuGo-W5">{p["title"]}</font>', jp_style),
                    p["price"],
                ])
            t = Table(table_data, colWidths=[12*mm, 130*mm, 28*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#f97316")),
                ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
                ("FONTNAME",       (0, 0), (-1, 0), "HeiseiKakuGo-W5"),
                ("FONTSIZE",       (0, 0), (-1, 0), 9),
                ("FONTNAME",       (0, 1), (0, -1), "HeiseiKakuGo-W5"),
                ("FONTNAME",       (2, 1), (2, -1), "HeiseiKakuGo-W5"),
                ("FONTSIZE",       (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff7ed")]),
                ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
        story.append(Spacer(1, 7*mm))

    # ─ フッター ─
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f'<font name="HeiseiKakuGo-W5" size="8" color="#9ca3af">'
        f'© FBAトレンドレーダー — マイページ: {SITE_URL}/dashboard</font>',
        jp_style
    ))

    doc.build(story)
    print(f"[OK] PDF 生成: {pdf_path}")
    return pdf_path

# ────────────────────────────────────────────
# 3. Supabase Storage にアップロード
# ────────────────────────────────────────────
def upload_to_supabase(pdf_path: str) -> str:
    storage_path = f"reports/{ISO_WEEK}/report.pdf"
    with open(pdf_path, "rb") as f:
        content = f.read()

    url = f"{SUPABASE_URL}/storage/v1/object/reports/{storage_path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/pdf",
        "x-upsert":      "true",
    }
    resp = requests.post(url, headers=headers, data=content, timeout=60)
    resp.raise_for_status()
    print(f"[OK] Supabase アップロード完了: {storage_path}")
    return storage_path


def save_report_record(storage_path: str) -> None:
    url = f"{SUPABASE_URL}/rest/v1/reports"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey":        SUPABASE_KEY,
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates",
    }
    body = {
        "week_label":   ISO_WEEK,
        "plan":         "standard",
        "file_path":    storage_path,
        "published_at": datetime.datetime.utcnow().isoformat(),
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    resp.raise_for_status()
    print("[OK] DBレコード保存完了")

# ────────────────────────────────────────────
# 4. 会員全員にメール送信（Resend）
# ────────────────────────────────────────────
def get_active_members() -> list[str]:
    url = f"{SUPABASE_URL}/rest/v1/members?status=eq.active&select=email"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey":        SUPABASE_KEY,
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return [m["email"] for m in resp.json()]


def send_report_emails(emails: list[str]) -> None:
    if not emails:
        print("[SKIP] アクティブ会員なし")
        return

    dashboard_url = f"{SITE_URL}/dashboard"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;background:#f9fafb;padding:20px;border-radius:12px">
      <div style="background:#f97316;padding:20px 24px;border-radius:10px;margin-bottom:16px">
        <h1 style="color:white;margin:0;font-size:18px">FBAトレンドレーダー</h1>
        <p style="color:#fff7ed;margin:6px 0 0;font-size:13px">
          {TODAY.strftime("%Y年%m月%d日")} 週次レポートが届きました 📦
        </p>
      </div>
      <div style="background:white;padding:24px;border-radius:10px">
        <p style="color:#374151;font-size:14px;line-height:1.7">
          今週のAmazon JPベストセラートレンドをまとめました。<br>
          マイページからPDFレポートをダウンロードしてご確認ください。
        </p>
        <a href="{dashboard_url}"
           style="display:inline-block;background:#f97316;color:white;
                  padding:12px 28px;border-radius:999px;text-decoration:none;
                  font-weight:bold;font-size:14px;margin-top:8px">
          レポートをダウンロード →
        </a>
        <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb">
        <p style="font-size:12px;color:#9ca3af">
          プランの変更・解約は
          <a href="{dashboard_url}" style="color:#f97316">マイページ</a>
          からいつでも可能です。
        </p>
      </div>
    </div>
    """

    for i in range(0, len(emails), 100):
        chunk = emails[i:i + 100]
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "from":    FROM_EMAIL,
                "to":      chunk,
                "subject": f"【FBAトレンドレーダー】{TODAY.strftime('%m/%d')} 週次レポート配信",
                "html":    html,
            },
            timeout=30,
        )
        resp.raise_for_status()
        print(f"[OK] {len(chunk)} 名に送信完了")

# ────────────────────────────────────────────
# 5. note.com 用ビジュアル生成 & 自動投稿
# ────────────────────────────────────────────
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont


# ── フォント設定 ──────────────────────────────
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

def _find_font() -> str | None:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def _setup_mpl_font() -> None:
    fp = _find_font()
    if fp:
        fm.fontManager.addfont(fp)
        prop = fm.FontProperties(fname=fp)
        plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False


# ── ① ヘッダー画像（1200×630 OGPサイズ） ──────
def generate_header_image() -> bytes:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#1c1c2e")
    draw = ImageDraw.Draw(img)

    # オレンジのグラデーション帯
    for i in range(H):
        r = int(249 - (249 - 234) * i / H)
        g = int(115 - (115 - 88) * i / H)
        b = int(22 - (22 - 12) * i / H)
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # 暗いオーバーレイで文字読みやすく
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    draw = ImageDraw.Draw(img)

    font_path = _find_font()
    def pil_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    # ロゴバッジ
    draw.rounded_rectangle([(60, 60), (420, 120)], radius=10, fill="#f97316")
    draw.text((75, 72), "📦 FBAトレンドレーダー", font=pil_font(30), fill="white")

    # メインタイトル
    draw.text((60, 150), "Amazon FBA", font=pil_font(90), fill="white")
    draw.text((60, 255), "今週の売れ筋完全レポート", font=pil_font(58), fill="#fed7aa")

    # 週ラベル
    draw.text((60, 360), f"🗓  {ISO_WEEK}　|　毎週火曜 21:00 更新", font=pil_font(32), fill="#fde68a")

    # 下部バー
    draw.rectangle([(0, 520), (W, 630)], fill="#0f0f1a")
    badges = ["✅ 全5カテゴリ", "✅ TOP10完全公開", "✅ 価格データつき", "✅ 無料で読める"]
    x = 60
    for b in badges:
        draw.text((x, 548), b, font=pil_font(26), fill="#f97316")
        x += 280

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── ② カテゴリ別横棒グラフ ───────────────────
def generate_category_chart(cat_name: str, products: list[dict]) -> bytes:
    _setup_mpl_font()
    if not products:
        return b""

    items = products[:8]
    labels = []
    for p in items:
        t = p["title"]
        labels.append(t[:18] + "…" if len(t) > 18 else t)

    ranks  = [p["rank"] for p in items]
    values = [len(items) + 1 - r for r in ranks]   # 1位が最大値

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    colors_bar = ["#f97316" if i == 0 else "#fb923c" if i == 1 else "#fdba74"
                  for i in range(len(items))]
    bars = ax.barh(labels[::-1], values[::-1], color=colors_bar[::-1],
                   edgecolor="white", linewidth=1.2, height=0.65)

    # 価格ラベル
    for bar, p in zip(bars[::-1], items):
        price = p.get("price", "-")
        if price and price != "-":
            ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                    price, va="center", ha="left", fontsize=9.5, color="#374151",
                    fontweight="bold")

    # ランク番号
    for bar, rank in zip(bars[::-1], ranks):
        ax.text(0.12, bar.get_y() + bar.get_height() / 2,
                f"{rank}位", va="center", ha="left", fontsize=9, color="white",
                fontweight="bold")

    ax.set_xlim(0, len(items) + 1.8)
    ax.set_xlabel("")
    ax.set_title(f"📦  {cat_name}　ランキング TOP{len(items)}",
                 fontsize=15, fontweight="bold", pad=14, color="#1c1c2e")
    ax.xaxis.set_visible(False)
    for spine in ["top", "right", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#e5e7eb")

    gold  = mpatches.Patch(color="#f97316", label="1位")
    silv  = mpatches.Patch(color="#fb923c", label="2位")
    brnz  = mpatches.Patch(color="#fdba74", label="3位〜")
    ax.legend(handles=[gold, silv, brnz], loc="lower right",
              fontsize=9, framealpha=0.7)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="PNG", dpi=150, bbox_inches="tight",
                facecolor="#fafafa", edgecolor="none")
    plt.close()
    return buf.getvalue()


# ── ③ 全カテゴリ比較サマリーグラフ ──────────
def generate_summary_chart(trend_data: dict[str, list[dict]]) -> bytes:
    _setup_mpl_font()

    cats   = list(trend_data.keys())
    counts = [len(v) for v in trend_data.values()]

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    bar_colors = ["#f97316", "#fb923c", "#fdba74", "#fed7aa", "#ffedd5"]
    bars = ax.bar(cats, counts, color=bar_colors[:len(cats)],
                  edgecolor="white", linewidth=1.5, width=0.55)

    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{cnt}商品", ha="center", va="bottom", fontsize=11,
                fontweight="bold", color="#374151")

    ax.set_ylim(0, max(counts) + 4)
    ax.set_ylabel("取得商品数", fontsize=11, color="#6b7280")
    ax.set_title("📊  今週のカテゴリ別データ取得数",
                 fontsize=14, fontweight="bold", pad=12, color="#1c1c2e")
    ax.yaxis.set_visible(False)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(axis="x", labelsize=12)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="PNG", dpi=150, bbox_inches="tight",
                facecolor="#fafafa", edgecolor="none")
    plt.close()
    return buf.getvalue()


# ── ④ 画像をSupabase Storageにアップロード ──
def _ensure_public_bucket(bucket: str = "note-images") -> None:
    url     = f"{SUPABASE_URL}/storage/v1/bucket/{bucket}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 400 or (r.status_code == 200 and not r.json().get("public")):
        requests.post(f"{SUPABASE_URL}/storage/v1/bucket",
                      headers=headers,
                      json={"id": bucket, "name": bucket, "public": True},
                      timeout=10)
    elif r.status_code == 404:
        requests.post(f"{SUPABASE_URL}/storage/v1/bucket",
                      headers=headers,
                      json={"id": bucket, "name": bucket, "public": True},
                      timeout=10)


def upload_note_image(image_bytes: bytes, filename: str) -> str:
    """画像をSupabase公開バケットにアップしてpublic URLを返す"""
    _ensure_public_bucket()
    path = f"{ISO_WEEK}/{filename}"
    url  = f"{SUPABASE_URL}/storage/v1/object/note-images/{path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "image/png",
        "x-upsert":      "true",
    }
    requests.post(url, headers=headers, data=image_bytes, timeout=30)
    return f"{SUPABASE_URL}/storage/v1/object/public/note-images/{path}"


# ── ⑤ 記事本文ビルド ────────────────────────
def build_note_article(trend_data: dict[str, Any],
                       image_urls: dict[str, str]) -> str:
    date_str = TODAY.strftime("%Y年%m月%d日")

    header_img  = image_urls.get("header", "")
    summary_img = image_urls.get("summary", "")

    # ─ 導入 ─
    lines = []
    if header_img:
        lines.append(f"![ヘッダー画像]({header_img})\n")

    lines += [
        f"# 【{ISO_WEEK}】Amazon FBA 今週の売れ筋トレンド完全版",
        "",
        f"こんにちは！毎週火曜日に **Amazon FBAの売れ筋トレンドデータ** を無料公開しています。",
        f"（{date_str} 更新）",
        "",
        "FBA販売者・せどらーの方が「**今週どのカテゴリで何が売れているか**」を",
        "一目でわかるようにまとめました。仕入れ判断の参考にどうぞ！",
        "",
        "---",
        "",
        "## 📊 今週のデータ概要",
        "",
    ]

    if summary_img:
        lines.append(f"![カテゴリ別データ概要]({summary_img})\n")

    # データ概要テーブル
    lines += [
        "| カテゴリ | 取得商品数 | 今週の注目 |",
        "|---------|-----------|-----------|",
    ]
    for cat, products in trend_data.items():
        top = products[0]["title"][:20] + "…" if products else "データなし"
        lines.append(f"| {cat} | {len(products)}商品 | {top} |")

    lines += ["", "---", ""]

    # ─ カテゴリ別詳細 ─
    emoji_map = {
        "ペット用品": "🐾", "アウトドア": "⛺", "キッチン": "🍳",
        "ビューティー": "💄", "ベビー": "👶",
    }
    for cat, products in trend_data.items():
        emoji = emoji_map.get(cat, "📦")
        lines += ["", f"## {emoji} {cat} ランキング TOP10", ""]

        chart_img = image_urls.get(f"chart_{cat}", "")
        if chart_img:
            lines.append(f"![{cat}ランキンググラフ]({chart_img})\n")

        if not products:
            lines.append("> 今週はデータを取得できませんでした。次週再試行します。\n")
            continue

        lines += [
            "| 順位 | 商品名 | 価格 | チェック |",
            "|-----|-------|------|---------|",
        ]
        for p in products[:10]:
            price   = p.get("price", "-") or "-"
            asin    = p.get("asin", "")
            amz_url = f"https://www.amazon.co.jp/dp/{asin}" if asin else ""
            link    = f"[Amazon]({amz_url})" if amz_url else "-"
            medal   = "🥇" if p["rank"] == 1 else "🥈" if p["rank"] == 2 else "🥉" if p["rank"] == 3 else f"{p['rank']}位"
            lines.append(f"| {medal} | {p['title'][:30]} | {price} | {link} |")

        # 簡易コメント（1位商品の注目ポイント）
        if products:
            top1 = products[0]
            lines += [
                "",
                f"> **💡 注目商品：{top1['title'][:25]}**",
                f"> 今週1位のロングセラー商品です。"
                f"{'価格帯：' + top1['price'] if top1['price'] != '-' else ''}",
                f"> FBA手数料を考慮した仕入れ判断に活用ください。",
                "",
            ]

    # ─ まとめ & CTA ─
    lines += [
        "---",
        "",
        "## 🔥 今週のまとめ",
        "",
        "- 全5カテゴリのランキングを毎週無料公開しています",
        "- データはAmazon公式ページから自動収集（月曜AM更新）",
        "- **有料版では** TOP20・価格推移・競合分析・仕入れ利益率まで届きます",
        "",
        "---",
        "",
        "## 📬 もっと詳しいデータが欲しい方へ",
        "",
        "毎週月曜日の朝、**全カテゴリの詳細PDFレポート**をメールでお届けするサービスを提供しています。",
        "",
        "| プラン | 価格 | 内容 |",
        "|-------|------|------|",
        "| スタンダード | ¥3,980/月 | 全5カテゴリ TOP20・価格データ |",
        "| プロ | ¥9,800/月 | ↑＋仕入れ利益率・競合チェック・独自分析 |",
        "",
        f"👉 **[FBAトレンドレーダーを見てみる]({SITE_URL})**",
        "",
        "初月は返金保証あり。合わなければすぐ解約できます。",
        "",
        "---",
        "",
        "*このデータはAmazon公式の公開情報をもとに作成しています。*",
        "*仕入れの最終判断はご自身の責任でお願いします。*",
        "",
        "#Amazon #FBA #せどり #副業 #物販 #Amazonせどり #FBAトレンド #仕入れ #副業月収",
    ]

    return "\n".join(lines)


# ── ⑥ ログイン ──────────────────────────────
def _note_login(email: str, password: str) -> requests.Session:
    """メアドとパスワードでnote.comに自動ログインしてSessionを返す"""
    session = requests.Session()
    session.headers.update({
        "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Origin":          "https://note.com",
        "Referer":         "https://note.com/login",
        "Content-Type":    "application/json",
    })

    # ① ログインページを取得してCSRFトークンを拾う
    login_page = session.get("https://note.com/login", timeout=15)
    csrf = ""
    for cookie in session.cookies:
        if "csrf" in cookie.name.lower() or "token" in cookie.name.lower():
            csrf = cookie.value
            break
    soup_login = BeautifulSoup(login_page.text, "html.parser")
    meta_csrf = soup_login.find("meta", {"name": "csrf-token"})
    if meta_csrf:
        csrf = meta_csrf.get("content", csrf)
    if csrf:
        session.headers["X-CSRF-Token"] = csrf

    # ② ログインAPIを叩く
    resp = session.post(
        "https://note.com/api/v3/users/sign_in",
        json={"login": email, "password": password},
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"noteログイン失敗 ({resp.status_code}): {resp.text[:200]}")

    data = resp.json()
    # ログイン後のCSRFトークンを更新
    new_csrf = resp.headers.get("X-CSRF-Token") or data.get("csrf_token", "")
    if new_csrf:
        session.headers["X-CSRF-Token"] = new_csrf

    print(f"[OK] note.com ログイン成功: {data.get('nickname') or email}")
    return session


def post_to_note(trend_data: dict[str, Any]) -> None:
    """画像生成→アップロード→ログイン→note.comに記事を投稿する"""
    email    = os.environ.get("NOTE_EMAIL", "")
    password = os.environ.get("NOTE_PASSWORD", "")

    if not email or not password:
        print("[SKIP] NOTE_EMAIL / NOTE_PASSWORD が未設定 → note投稿をスキップ")
        return

    # ── 画像生成 & アップロード ──
    print("  [note] ヘッダー画像を生成中...")
    image_urls: dict[str, str] = {}
    try:
        header_bytes = generate_header_image()
        image_urls["header"] = upload_note_image(header_bytes, "header.png")
        print(f"  [note] ヘッダー: {image_urls['header']}")
    except Exception as e:
        print(f"  [note][WARN] ヘッダー画像スキップ: {e}")

    try:
        summary_bytes = generate_summary_chart(trend_data)
        image_urls["summary"] = upload_note_image(summary_bytes, "summary.png")
        print(f"  [note] サマリーグラフ: {image_urls['summary']}")
    except Exception as e:
        print(f"  [note][WARN] サマリーグラフスキップ: {e}")

    for cat, products in trend_data.items():
        try:
            chart_bytes = generate_category_chart(cat, products)
            if chart_bytes:
                key = f"chart_{cat}"
                safe_name = cat.replace(" ", "_").replace("/", "_")
                image_urls[key] = upload_note_image(chart_bytes, f"chart_{safe_name}.png")
                print(f"  [note] {cat}グラフ: {image_urls[key]}")
        except Exception as e:
            print(f"  [note][WARN] {cat}グラフスキップ: {e}")

    # ── ログイン ──
    try:
        session = _note_login(email, password)
    except Exception as e:
        print(f"[WARN] noteログインエラー: {e}")
        return

    # ── 記事本文生成 ──
    article_body = build_note_article(trend_data, image_urls)
    title = f"【{ISO_WEEK}】Amazon FBA 今週の売れ筋トレンド完全版｜全5カテゴリTOP10"

    # ── 投稿（公開） ──
    try:
        resp = session.post(
            "https://note.com/api/v2/text_notes",
            json={
                "name":   title,
                "body":   article_body,
                "status": "published",
                "hashtag_note_publishes_attributes": [
                    {"hashtag_name": "Amazon"},
                    {"hashtag_name": "FBA"},
                    {"hashtag_name": "せどり"},
                    {"hashtag_name": "副業"},
                    {"hashtag_name": "物販"},
                    {"hashtag_name": "Amazonせどり"},
                    {"hashtag_name": "副業月収"},
                ],
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            note_url = resp.json().get("data", {}).get("noteUrl", "")
            print(f"[OK] note投稿完了: {note_url or '(URL取得失敗)'}")
        else:
            print(f"[WARN] note投稿失敗 ({resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        print(f"[WARN] note投稿エラー: {e}")


# ────────────────────────────────────────────
# メイン（RUN_MODE で分岐）
#   report : 会員向けPDF生成・メール配信のみ
#   note   : Amazonデータ収集・note投稿のみ
#   all    : 両方（デフォルト）
# ────────────────────────────────────────────
if __name__ == "__main__":
    RUN_MODE = os.environ.get("RUN_MODE", "all")
    print(f"=== FBAトレンドレーダー [{RUN_MODE.upper()}] {ISO_WEEK} ===")

    print("[データ収集] Amazonベストセラーデータを取得中...")
    trends = build_trend_data()
    with open(os.path.join(REPORT_DIR, f"trends_{ISO_WEEK}.json"), "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in trends.values())
    print(f"          → {total} 商品を収集")

    if RUN_MODE in ("report", "all"):
        print("\n[REPORT] PDFレポート生成中...")
        pdf_path = generate_pdf(trends)

        print("[REPORT] Supabaseにアップロード中...")
        storage_path = upload_to_supabase(pdf_path)
        save_report_record(storage_path)

        print("[REPORT] 会員リスト取得中...")
        emails = get_active_members()
        print(f"       → {len(emails)} 名にメール送信")
        send_report_emails(emails)

    if RUN_MODE in ("note", "all"):
        print("\n[NOTE] note.com に記事を自動投稿中...")
        post_to_note(trends)

    print("\n=== 完了 ===")
