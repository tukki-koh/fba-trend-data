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
# 5. note.com 自動投稿
# ────────────────────────────────────────────
def build_note_article(trend_data: dict[str, Any]) -> str:
    """note掲載用のMarkdown記事を生成"""
    lines = [
        f"# Amazon FBA 今週の売れ筋トレンド TOP10【{ISO_WEEK}】\n",
        f"毎週月曜日に**FBA販売者向けのトレンドデータ**を無料公開しています。\n",
        f"有料版（週次PDFレポート）では全5カテゴリの詳細データ・仕入れ分析が届きます。\n",
        "---\n",
    ]

    for cat, products in trend_data.items():
        lines.append(f"## 📦 {cat} ランキング TOP10\n")
        if not products:
            lines.append("（今週はデータ取得できませんでした）\n")
            continue
        for p in products[:10]:
            price_str = f"　{p['price']}" if p["price"] != "-" else ""
            lines.append(f"{p['rank']}. **{p['title']}**{price_str}")
        lines.append("")

    lines += [
        "---\n",
        "## 📊 もっと詳しいデータが欲しい方へ\n",
        "このデータの**完全版PDF**（全カテゴリ・より詳細な分析つき）を\n"
        "毎週月曜日に配信するサービスをやっています。\n",
        f"👉 [FBAトレンドレーダーを見てみる]({SITE_URL})\n",
        "- スタンダード：¥3,980/月（全カテゴリTOP20）",
        "- プロ：¥9,800/月（仕入れ分析・競合チェックつき）\n",
        "#Amazon #FBA #せどり #副業 #物販 #Amazonせどり #FBAトレンド",
    ]
    return "\n".join(lines)


def post_to_note(trend_data: dict[str, Any]) -> None:
    """note.com の内部APIを使って記事を自動投稿する"""
    session_cookie = os.environ.get("NOTE_SESSION_COOKIE", "")
    user_slug      = os.environ.get("NOTE_USER_SLUG", "")

    if not session_cookie or not user_slug:
        print("[SKIP] NOTE_SESSION_COOKIE / NOTE_USER_SLUG が未設定 → note投稿をスキップ")
        return

    article_body = build_note_article(trend_data)
    title = f"Amazon FBA 今週の売れ筋トレンド TOP10【{ISO_WEEK}】"

    session = requests.Session()
    session.headers.update({
        "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Origin":          "https://note.com",
        "Referer":         "https://note.com/",
    })
    session.cookies.set("note_session_v5", session_cookie, domain=".note.com")

    # CSRFトークン取得
    try:
        me_resp = session.get(f"https://note.com/api/v2/creators/{user_slug}", timeout=10)
        me_resp.raise_for_status()
        csrf_token = me_resp.cookies.get("_note_token") or ""
        if csrf_token:
            session.headers["X-CSRF-Token"] = csrf_token
    except Exception as e:
        print(f"[WARN] note CSRF取得失敗: {e}")

    # 記事を投稿（公開）
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
# メイン
# ────────────────────────────────────────────
if __name__ == "__main__":
    print(f"=== FBAトレンドレーダー 自動配信 {ISO_WEEK} ===")

    print("[1/6] Amazonベストセラーデータを収集中...")
    trends = build_trend_data()

    with open(os.path.join(REPORT_DIR, f"trends_{ISO_WEEK}.json"), "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=2)
    print(f"      → {sum(len(v) for v in trends.values())} 商品を収集")

    print("[2/6] PDFレポートを生成中...")
    pdf_path = generate_pdf(trends)

    print("[3/6] Supabaseにアップロード中...")
    storage_path = upload_to_supabase(pdf_path)
    save_report_record(storage_path)

    print("[4/6] 会員リスト取得中...")
    emails = get_active_members()
    print(f"      → {len(emails)} 名にメール送信")

    print("[5/6] メール送信中...")
    send_report_emails(emails)

    print("[6/6] note.com に記事を自動投稿中...")
    post_to_note(trends)

    print("=== 完了 ===")
