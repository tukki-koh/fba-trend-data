"""
Twitter(X) 自動マーケティング投稿スクリプト
GitHub Actions から週3回自動実行される。

投稿スケジュール（JST）:
  月曜 AM8:00 → 週次トレンド速報（noteへの誘導）
  水曜 PM8:00 → 注目商品ピックアップ（エンゲージメント獲得）
  金曜 PM7:00 → 週末仕込みヒント（週末せどらー向け）

必要な環境変数（GitHub Secrets）:
  TWITTER_API_KEY, TWITTER_API_SECRET
  TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
  SUPABASE_URL, SUPABASE_SERVICE_KEY
  NEXT_PUBLIC_SITE_URL
  TWEET_MODE: monday / wednesday / friday
"""

import os
import json
import random
import datetime
import requests
import tweepy
from bs4 import BeautifulSoup
from typing import Any

# ── 設定 ──────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL     = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://fba-trend-data.vercel.app")
TWEET_MODE   = os.environ.get("TWEET_MODE", "monday")

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

# ── Twitter クライアント初期化 ─────────────────
def get_twitter_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key        = os.environ["TWITTER_API_KEY"],
        consumer_secret     = os.environ["TWITTER_API_SECRET"],
        access_token        = os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret = os.environ["TWITTER_ACCESS_SECRET"],
    )

# ── Amazon スクレイピング（軽量版） ───────────
def scrape_top3(url: str) -> list[dict[str, Any]]:
    try:
        resp = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS),
                                          "Accept-Language": "ja-JP,ja;q=0.9"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.zg-grid-general-faceout") or soup.select("li.zg-item-immersion")
        result = []
        for i, card in enumerate(cards[:3], 1):
            title_el = card.select_one(
                "div.p13n-sc-truncate-desktop-type2, span.zg-text-center-align, "
                "div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y"
            )
            price_el = card.select_one("span.p13n-sc-price, span._cDEzb_p13n-sc-price_3mJ9Z")
            title = title_el.get_text(strip=True)[:30] if title_el else "商品名取得中"
            price = price_el.get_text(strip=True) if price_el else ""
            result.append({"rank": i, "title": title, "price": price})
        return result
    except Exception:
        return []

def get_trend_from_supabase() -> dict[str, list[dict]]:
    """直近のトレンドデータをSupabaseから取得（なければスクレイピング）"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/reports?week_label=eq.{ISO_WEEK}&select=file_path"
        headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and r.json():
            # JSONデータがあればそれを使う（今週分）
            pass
    except Exception:
        pass

    # スクレイピングでTOP3だけ取得
    data: dict[str, list[dict]] = {}
    for cat, cat_url in list(CATEGORIES.items())[:3]:   # 3カテゴリで十分
        data[cat] = scrape_top3(cat_url)
    return data

# ── ツイート文生成 ────────────────────────────

def _shorten(text: str, length: int = 22) -> str:
    return text[:length] + "…" if len(text) > length else text


def build_monday_tweet(trend_data: dict[str, list[dict]]) -> str:
    """月曜：週次トレンド速報 → noteへ誘導"""
    lines = [f"【{ISO_WEEK}】Amazon FBA 今週の売れ筋速報🔥\n"]
    for cat, products in list(trend_data.items())[:3]:
        if products:
            p = products[0]
            price = f"（{p['price']}）" if p.get("price") else ""
            lines.append(f"📦{cat}1位：{_shorten(p['title'])}{price}")
    lines += [
        "",
        "全5カテゴリのTOP10データを毎週火曜に無料公開📊",
        f"👇詳細はnoteとサービスページへ",
        SITE_URL,
        "",
        "#Amazon #FBA #せどり #副業 #物販",
    ]
    return "\n".join(lines)


def build_wednesday_tweet(trend_data: dict[str, list[dict]]) -> str:
    """水曜：注目商品ピックアップ → エンゲージメント狙い"""
    # ランダムにカテゴリを選んで1位をフィーチャー
    available = [(cat, prods) for cat, prods in trend_data.items() if prods]
    if not available:
        cat, products = "ペット用品", []
    else:
        cat, products = random.choice(available)

    top = products[0] if products else None

    lines = [
        "【水曜トレンドPICK UP】🎯\n",
        f"今週 {cat} カテゴリで注目の商品はこちら👇",
        "",
    ]
    if top:
        lines += [
            f"🥇 {_shorten(top['title'], 28)}",
            f"   価格：{top['price'] or '調査中'}",
            "",
            "FBA手数料を差し引いても利益が出やすいカテゴリです💡",
        ]
    lines += [
        "",
        "仕入れ判断の参考に！毎週火曜に全データ無料公開中📊",
        f"→ {SITE_URL}",
        "",
        "#せどり #Amazon転売 #FBA #副業 #物販仕入れ",
    ]
    return "\n".join(lines)


def build_friday_tweet(trend_data: dict[str, list[dict]]) -> str:
    """金曜：週末仕込みヒント → 行動を促す"""
    top_items = []
    for cat, products in trend_data.items():
        if products:
            top_items.append((cat, products[0]))

    lines = [
        "【週末仕込みリスト】🛒\n",
        "明日・明後日に仕入れるなら今週のこのカテゴリが熱い🔥",
        "",
    ]
    for cat, p in top_items[:3]:
        lines.append(f"✅ {cat}：{_shorten(p['title'])}")

    lines += [
        "",
        "週末のせどり・仕入れ活動の参考にどうぞ！",
        "詳細データは毎週火曜に無料公開📊",
        "",
        f"▶ {SITE_URL}",
        "",
        "#週末せどり #仕入れ #Amazon #FBA #副業 #物販",
    ]
    return "\n".join(lines)


# ── 投稿実行 ──────────────────────────────────
def post_tweet(text: str) -> None:
    client = get_twitter_client()
    # 280文字制限チェック
    if len(text) > 280:
        text = text[:277] + "…"
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    print(f"[OK] ツイート投稿完了: https://twitter.com/i/web/status/{tweet_id}")


# ── メイン ────────────────────────────────────
if __name__ == "__main__":
    print(f"=== Twitter自動マーケティング [{TWEET_MODE.upper()}] {TODAY} ===")

    print("  Amazonデータを収集中...")
    trend_data = get_trend_from_supabase()

    if TWEET_MODE == "monday":
        tweet_text = build_monday_tweet(trend_data)
    elif TWEET_MODE == "wednesday":
        tweet_text = build_wednesday_tweet(trend_data)
    elif TWEET_MODE == "friday":
        tweet_text = build_friday_tweet(trend_data)
    else:
        tweet_text = build_monday_tweet(trend_data)

    print(f"\n--- ツイート内容 ---\n{tweet_text}\n---\n")
    post_tweet(tweet_text)
    print("=== 完了 ===")
