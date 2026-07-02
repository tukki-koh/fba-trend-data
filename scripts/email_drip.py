#!/usr/bin/env python3
"""
FBAトレンドレーダー メールドリップ配信スクリプト

必要なマイグレーション（未適用の場合は先に実行）:
-- ALTER TABLE free_sample_recipients ADD COLUMN IF NOT EXISTS welcome_sent_at TIMESTAMPTZ;
-- ALTER TABLE free_sample_recipients ADD COLUMN IF NOT EXISTS reengage_sent_at TIMESTAMPTZ;
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ─── 環境変数 ───────────────────────────────────────────────
SUPABASE_URL      = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY      = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]
FROM_EMAIL        = os.environ["FROM_EMAIL"]
SITE_URL          = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://fba-trend-radar.com").rstrip("/")


# ─── Supabase ヘルパー ──────────────────────────────────────

def supabase_get(path: str) -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def supabase_patch(table: str, match: dict, data: dict) -> None:
    params = "&".join(f"{k}=eq.{v}" for k, v in match.items())
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, method="PATCH", headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    with urllib.request.urlopen(req):
        pass


# ─── Resend メール送信 ─────────────────────────────────────

def send_email(to: str, subject: str, html: str) -> bool:
    payload = json.dumps({
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"  送信成功: {to} (id={result.get('id')})")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  送信失敗: {to} — {e.code} {body}")
        return False


# ─── メール本文 ───────────────────────────────────────────

def welcome_html(email: str) -> str:
    sample_url = f"{SITE_URL}/sample"
    return f"""
<div style="font-family:sans-serif;font-size:15px;line-height:1.7;color:#222;max-width:560px">
  <p>登録ありがとうございます。</p>
  <p>
    最新のAmazonベストセラーデータをまとめたサンプルレポートを用意しました。<br>
    下のリンクから確認できます。
  </p>
  <p style="margin:24px 0">
    <a href="{sample_url}"
       style="background:#FF9900;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold">
      サンプルレポートを見る
    </a>
  </p>
  <p>
    カテゴリ別の売上ランキングや価格帯分布など、仕入れ判断に使えるデータを週次で更新しています。<br>
    気になる点があれば、このメールに返信してください。
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px">
    FBAトレンドレーダー<br>
    <a href="{SITE_URL}" style="color:#888">{SITE_URL}</a>
  </p>
</div>
"""


def reengage_html(email: str) -> str:
    pricing_url = f"{SITE_URL}/#pricing"
    return f"""
<div style="font-family:sans-serif;font-size:15px;line-height:1.7;color:#222;max-width:560px">
  <p>先週のFBAトレンドレポート、チェックしてもらえましたか？</p>
  <p>
    毎週月曜に最新データをお届けしています。<br>
    月額3,980円〜、最初の14日間は返金保証つきです。
  </p>
  <p style="margin:24px 0">
    <a href="{pricing_url}"
       style="background:#FF9900;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold">
      プランを確認する
    </a>
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px">
    FBAトレンドレーダー<br>
    <a href="{SITE_URL}" style="color:#888">{SITE_URL}</a>
  </p>
</div>
"""


# ─── メイン処理 ───────────────────────────────────────────

def main() -> None:
    now = datetime.now(timezone.utc)

    # Supabaseから全レコード取得（カラムが存在しない場合に備えてエラーをキャッチ）
    try:
        recipients = supabase_get(
            "free_sample_recipients"
            "?select=id,email,created_at,converted_at,welcome_sent_at,reengage_sent_at"
        )
    except Exception as e:
        print(f"[ERROR] Supabaseからのデータ取得に失敗: {e}")
        print("マイグレーションが未適用の可能性があります。スクリプト冒頭のSQLコメントを確認してください。")
        raise

    welcome_sent = 0
    reengage_sent = 0

    for r in recipients:
        email = r.get("email", "")
        if not email:
            continue

        try:
            created_at = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        except Exception:
            continue

        age_days = (now - created_at).total_seconds() / 86400

        # ── Day 1 ウェルカムメール ─────────────────────────
        if 0 <= age_days < 1 and r.get("welcome_sent_at") is None:
            print(f"[Day1] {email}")
            ok = send_email(
                to=email,
                subject="サンプルレポートをお届けします — FBAトレンドレーダー",
                html=welcome_html(email),
            )
            if ok:
                supabase_patch(
                    "free_sample_recipients",
                    {"email": email},
                    {"welcome_sent_at": now.isoformat()},
                )
                welcome_sent += 1

        # ── Day 7 再エンゲージメントメール ────────────────
        elif 7 <= age_days < 10 \
                and r.get("converted_at") is None \
                and r.get("reengage_sent_at") is None:
            print(f"[Day7] {email}")
            ok = send_email(
                to=email,
                subject="先週のFBAトレンドを見ましたか？",
                html=reengage_html(email),
            )
            if ok:
                supabase_patch(
                    "free_sample_recipients",
                    {"email": email},
                    {"reengage_sent_at": now.isoformat()},
                )
                reengage_sent += 1

    print(f"\n完了 — Day1: {welcome_sent}件 / Day7: {reengage_sent}件")


if __name__ == "__main__":
    main()
