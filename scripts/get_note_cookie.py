"""
note.com のCookieを取得するスクリプト。
ブラウザが自動で開くので、ログインしてEnterを押すだけ。
_csrft_（CSRFトークン）も含めた全Cookieを取得します。
"""
from playwright.sync_api import sync_playwright

print("=" * 50)
print("  note.com Cookie取得ツール")
print("=" * 50)
print()
print("ブラウザが開きます。")
print("note.comに普通にログインしてください。")
print("ログイン完了後、この画面に戻ってEnterを押してください。")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()
    page.goto("https://note.com/login")

    input("▶ ログインが完了したらEnterを押してください...")

    # ログイン後にメインページとエディタを訪問して _csrft_ を確実に取得
    print("  追加Cookieを取得中...")
    page.goto("https://note.com/", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2000)

    # エディタページを開いて _csrft_ を発行させる
    try:
        page.goto("https://note.com/notes/new", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    # 全Cookieを取得（HttpOnly含む）
    cookies = context.cookies()
    browser.close()

# Cookieを "name=value; name2=value2" 形式にまとめる
cookie_str = "; ".join(
    f"{c['name']}={c['value']}"
    for c in cookies
    if "note.com" in c.get("domain", "")
)

# _csrft_ が含まれているか確認
has_csrf = any(c["name"] == "_csrft_" for c in cookies if "note.com" in c.get("domain", ""))
has_session = any(c["name"] == "_note_session_v5" for c in cookies if "note.com" in c.get("domain", ""))

print()
print("━" * 50)
print(f"✅ 取得成功！（Cookie数: {len(cookies)}件）")
print(f"   _csrft_（CSRFトークン）: {'✅ あり' if has_csrf else '⚠️ なし'}")
print(f"   _note_session_v5（セッション）: {'✅ あり' if has_session else '⚠️ なし'}")
print("━" * 50)
print()
print(cookie_str)
print()
print("━" * 50)
print()
print("次の手順：")
print("1. 上の文字列を全部コピー（Command+A → Command+C）")
print("2. ブラウザでこのURLを開く：")
print("   https://github.com/tukki-koh/fba-trend-data/settings/secrets/actions")
print("3. 「NOTE_SESSION_COOKIE」を探して「Update」をクリック")
print("   （なければ「New repository secret」→ NOTE_SESSION_COOKIE）")
print("4. 古い値を全て消して新しい文字列を貼り付け")
print("5. 「Update secret」または「Add secret」をクリック")
