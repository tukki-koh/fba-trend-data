#!/usr/bin/env python3
"""
FBAトレンドレーダー メールドリップ配信スクリプト（毎日 AM9:00 JST 実行）

対象テーブル: public.members（列: id, email, status, plan, created_at, reengage_sent_at）
 - status = "trial" … 無料サンプル登録者（未課金）
 - status = "active" … 有料会員（課金済み）

処理:
 - Day7 再エンゲージメール: 登録から7〜10日経過・未課金(status=trial)・未送信の人へ1回だけ送信
   ※ウェルカムメールは登録時（/api/free-sample）に送信済みのため、ここでは送らない
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ─── 環境変数 ───────────────────────────────────────────────
SUPABASE_URL   = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY   = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL     = os.environ["FROM_EMAIL"]
SITE_URL       = os.environ.get("NEXT_PUBLIC_SITE_URL", "https://fba-trend-data.vercel.app").rstrip("/")


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


# ─── メール本文（Day7 再エンゲージ） ───────────────────────

def reengage_html(email: str) -> str:
    pricing_url = f"{SITE_URL}/#pricing"
    return f"""
<div style="font-family:sans-serif;font-size:15px;line-height:1.7;color:#1c1917;max-width:560px">
  <p>先週のサンプルレポート、目を通してもらえましたか？</p>
  <p>
    毎週月曜の朝、Amazonの売れ筋TOP10を5カテゴリぶんまとめてお届けしています。<br>
    月額1,480円〜（人気AIツール1つ分より安く）、最初の14日間は返金保証つきです。
  </p>
  <p style="margin:24px 0">
    <a href="{pricing_url}"
       style="background:#f59e0b;color:#fff;padding:12px 24px;border-radius:999px;text-decoration:none;font-weight:bold">
      プランを確認する
    </a>
  </p>
  <p style="color:#78716c;font-size:13px;margin-top:32px">
    FBAトレンドレーダー<br>
    <a href="{SITE_URL}" style="color:#78716c">{SITE_URL}</a>
  </p>
</div>
"""


# ─── メイン処理 ───────────────────────────────────────────

def main() -> None:
    now = datetime.now(timezone.utc)

    # 未課金(trial)会員のみ取得
    recipients = supabase_get(
        "members"
        "?select=id,email,status,created_at,reengage_sent_at"
        "&status=eq.trial"
    )

    reengage_sent = 0

    for r in recipients:
        email = r.get("email", "")
        if not email:
            continue

        raw = r.get("created_at")
        if not raw:
            continue
        try:
            created_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            continue

        age_days = (now - created_at).total_seconds() / 86400

        # Day7 再エンゲージ: 7〜10日経過・未送信の人へ1回だけ
        if 7 <= age_days < 10 and r.get("reengage_sent_at") is None:
            print(f"[Day7] {email}")
            ok = send_email(
                to=email,
                subject="先週のFBAトレンドを見ましたか？",
                html=reengage_html(email),
            )
            if ok:
                supabase_patch(
                    "members",
                    {"email": email},
                    {"reengage_sent_at": now.isoformat()},
                )
                reengage_sent += 1

    print(f"\n完了 — Day7 再エンゲージ: {reengage_sent}件（trial対象 {len(recipients)}名）")


if __name__ == "__main__":
    main()
