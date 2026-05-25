"""
Facebook ページ自動投稿スクリプト
GitHub Actions から週3回自動実行される。

投稿スケジュール（JST）:
  月曜 AM8:30 → 週次トレンド速報（noteへの誘導）
  水曜 PM7:00 → 注目商品ピックアップ
  金曜 PM6:00 → 週末仕込みヒント

必要な環境変数（GitHub Secrets）:
  FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN
  SUPABASE_URL, SUPABASE_SERVICE_KEY
  NEXT_PUBLIC_SITE_URL
  FB_POST_MODE: monday / wednesday / friday
"""

import os
import json
import random
import datetime
import requests
from bs4 import BeautifulSoup
from typing import Any

# ── 設定 ──────────────────────────────────────
FB_PAGE_ID    = os.environ.get("FB_PAGE_ID", "")
FB_TOKEN      = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL      = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://fba-trend-data.vercel.app")
POST_MODE     = os.environ.get("FB_POST_MODE", "monday")

TODAY    = datetime.date.today()
ISO_WEEK = TODAY.strftime("%Y-W%V")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
]

CATEGORIES = {
    "ペット用品":   "https://www.amazon.co.jp/gp/bestsellers/pet-supplies/",
    "アウトドア":   "https://www.amazon.co.jp/gp/bestsellers/sports/",
    "キッチン":     "https://www.amazon.co.jp/gp/bestsellers/kitchen/",
    "ビューティー": "https://www.amazon.co.jp/gp/bestsellers/beauty/",
    "ベビー":       "https://www.amazon.co.jp/gp/bestsellers/baby/",
}

# ── スクレイピング（軽量版） ───────────────────
def scrape_top3(url: str) -> list[dict[str, Any]]:
    try:
        resp = requests.get(url, headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ja-JP,ja;q=0.9"
        }, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.zg-grid-general-faceout") or soup.select("li.zg-item-immersion")
        result = []
        for i, card in enumerate(cards[:3], 1):
            title_el = card.select_one(
                "div.p13n-sc-truncate-desktop-type2, span.zg-text-center-align, "
                "div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y"
            )
            price_el = card.select_one("span.p13n-sc-price, span._cDEzb_p13n-sc-price_3mJ9Z")
            title = title_el.get_text(strip=True)[:28] if title_el else "商品名取得中"
            price = price_el.get_text(strip=True) if price_el else ""
            result.append({"rank": i, "title": title, "price": price})
        return result
    except Exception:
        return []

def get_trend_data() -> dict[str, list[dict]]:
    data: dict[str, list[dict]] = {}
    for cat, url in list(CATEGORIES.items())[:3]:
        data[cat] = scrape_top3(url)
    return data

# ── 投稿文生成 ────────────────────────────────
def _shorten(text: str, n: int = 24) -> str:
    return text[:n] + "…" if len(text) > n else text

def build_monday_post(trend_data: dict) -> str:
    lines = [
        f"【{ISO_WEEK}】📦 Amazon FBA 今週の売れ筋速報",
        "",
        "FBA販売者・せどらーの皆さん、今週のトレンドです👇",
        "",
    ]
    for cat, products in list(trend_data.items())[:3]:
        if products:
            p = products[0]
            price = f"（{p['price']}）" if p.get("price") else ""
            lines.append(f"🔥 {cat} 1位：{_shorten(p['title'])}{price}")
    lines += [
        "",
        "全5カテゴリのTOP10データは毎週火曜に無料公開中📊",
        "仕入れリサーチの時間をゼロにしませんか？",
        "",
        f"👇 無料でサンプルレポートを受け取る",
        SITE_URL,
        "",
        "#AmazonFBA #せどり #副業 #物販 #仕入れ #Amazonせどり",
    ]
    return "\n".join(lines)

def build_wednesday_post(trend_data: dict) -> str:
    available = [(cat, prods) for cat, prods in trend_data.items() if prods]
    cat, products = random.choice(available) if available else ("ペット用品", [])
    top = products[0] if products else None

    lines = [
        f"【水曜トレンドPICK UP】🎯",
        "",
        f"今週注目の {cat} カテゴリをピックアップ！",
        "",
    ]
    if top:
        lines += [
            f"🥇 {_shorten(top['title'], 30)}",
            f"   価格：{top['price'] or '調査中'}",
            "",
            "FBA手数料を差し引いても利益率が高いカテゴリです💡",
            "週の真ん中に仕入れ計画を見直してみてください！",
        ]
    lines += [
        "",
        "毎週火曜日に全カテゴリのデータを無料公開中📊",
        f"👇 無料サンプルはこちら",
        SITE_URL,
        "",
        "#せどり #Amazon転売 #FBA #副業 #物販仕入れ",
    ]
    return "\n".join(lines)

def build_friday_post(trend_data: dict) -> str:
    top_items = [(cat, prods[0]) for cat, prods in trend_data.items() if prods]

    lines = [
        "【週末仕込みリスト】🛒",
        "",
        "明日・明後日に仕入れるならこのカテゴリが熱い🔥",
        "",
    ]
    for cat, p in top_items[:3]:
        lines.append(f"✅ {cat}：{_shorten(p['title'])}")

    lines += [
        "",
        "週末のせどり・店舗仕入れの参考にどうぞ！",
        "詳細データは毎週火曜に無料公開📊",
        "",
        "まだ登録していない方は👇",
        SITE_URL,
        "",
        "#週末せどり #仕入れ #Amazon #FBA #副業 #物販",
    ]
    return "\n".join(lines)

# ── Facebook Graph API 投稿 ───────────────────
def post_to_facebook(message: str) -> None:
    if not FB_PAGE_ID or not FB_TOKEN:
        print("[SKIP] FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN が未設定")
        return

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    resp = requests.post(url, data={
        "message":      message,
        "access_token": FB_TOKEN,
        "link":         SITE_URL,
    }, timeout=30)

    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        print(f"[OK] Facebook投稿完了: https://www.facebook.com/{post_id}")
    else:
        print(f"[WARN] Facebook投稿失敗 ({resp.status_code}): {resp.text[:200]}")

# ── メイン ────────────────────────────────────
if __name__ == "__main__":
    print(f"=== Facebook自動投稿 [{POST_MODE.upper()}] {TODAY} ===")

    print("  データ収集中...")
    trend_data = get_trend_data()

    if POST_MODE == "monday":
        text = build_monday_post(trend_data)
    elif POST_MODE == "wednesday":
        text = build_wednesday_post(trend_data)
    elif POST_MODE == "friday":
        text = build_friday_post(trend_data)
    else:
        text = build_monday_post(trend_data)

    print(f"\n--- 投稿内容 ---\n{text}\n---\n")
    post_to_facebook(text)
    print("=== 完了 ===")
