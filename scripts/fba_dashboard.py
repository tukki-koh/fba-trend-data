"""
FBAトレンドレーダー LIVE 稼働ダッシュボード — localhost:8788

このサービス専属のAI社員（GitHub Actions ジョブ + 常駐Claudeタスク）の
稼働状況・KPI・活動フィードをリアルタイムで可視化する。
ブラウザで http://localhost:8788 を開くと5秒ごとに自動更新される。

データ源（すべて実データ）:
 - GitHub Actions: weekly_report.yml (member-report/note-post/email-drip) と
   facebook_marketing.yml (facebook-post) の各ジョブ最新実行結果（gh CLI）
 - 常駐Claudeタスク: weekly-marketing / monthly-seo-geo（次回予定）
 - Supabase: members(trial/active) と reports 件数

標準ライブラリのみ。gh CLI（認証済み）と fba-trend-data/.env.local を利用。
"""

import json, os, re, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timedelta

PORT      = 8788
REPO      = "tukki-koh/fba-trend-data"
BASE_DIR  = Path(__file__).resolve().parent.parent           # ~/fba-trend-data
ENV_FILE  = BASE_DIR / ".env.local"
REFRESH_SEC = 90

# ─── ブランド：サイトと同じ amber / stone（明るい） ──────────

# ─── 組織構成（このサービス専属の社員） ─────────────────────
# src: "gh"（GitHub Actionsジョブ）/ "claude"（常駐Claudeタスク・次回予定のみ）
ORG = [
    {"dept": "データ・配信部", "icon": "📊", "members": [
        {"key": "member-report", "name": "会員レポート配信担当",
         "role": "Amazon収集→PDF生成→会員へメール配信", "src": "gh", "job": "member-report",
         "sched": {"type": "weekly", "slots": [(0, 7, 0)]}},   # 月7:00
        {"key": "email-drip", "name": "CRM ドリップ担当",
         "role": "登録者への育成メールを毎日自動配信", "src": "gh", "job": "email-drip",
         "sched": {"type": "daily", "h": 9, "m": 0}},          # 毎日9:00
    ]},
    {"dept": "コンテンツ部", "icon": "✍️", "members": [
        {"key": "note-post", "name": "note編集者",
         "role": "週次トレンド記事を自動生成・投稿", "src": "gh", "job": "note-post",
         "sched": {"type": "weekly", "slots": [(1, 21, 0)]}},  # 火21:00
        {"key": "instagram", "name": "Instagram制作担当",
         "role": "カルーセル画像を自動生成（note投稿時）", "src": "gh", "job": "note-post",
         "sched": {"type": "weekly", "slots": [(1, 21, 0)]}},
    ]},
    {"dept": "マーケティング部", "icon": "📣", "members": [
        {"key": "facebook-post", "name": "Facebook運用担当",
         "role": "週3回の自動投稿（日・水・金）", "src": "gh", "job": "facebook-post",
         "sched": {"type": "weekly", "slots": [(6, 8, 30), (2, 19, 0), (4, 18, 0)]}},
        {"key": "weekly-marketing", "name": "週次マーケ担当（Claude常駐）",
         "role": "ハッシュタグ最適化・GEO更新・コピー改善", "src": "claude",
         "sched": {"type": "weekly", "slots": [(2, 10, 0)]}},  # 水10:00
        {"key": "monthly-seo", "name": "月次SEO/GEO担当（Claude常駐）",
         "role": "構造化データ・メタ最適化・llms.txt更新", "src": "claude",
         "sched": {"type": "monthly", "day": 5, "h": 10, "m": 0}},
    ]},
    {"dept": "経営企画・成長室", "icon": "🚀", "members": [
        {"key": "growth-benchmark", "name": "成長・ベンチマーク担当（Claude常駐）",
         "role": "世界最高水準の企業を手本に毎週1改善を実装・本番反映", "src": "claude",
         "sched": {"type": "weekly", "slots": [(5, 10, 0)]}},  # 土10:00
    ]},
]

_state = {"now": "", "kpi": {}, "depts": [], "feed": [], "running_now": 0}
_lock = threading.Lock()


# ─── .env.local 読み込み（Supabase用） ─────────────────────
def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


# ─── 次回実行時刻 ─────────────────────────────────────────
def next_run(sched, now):
    t = sched.get("type")
    if t == "daily":
        cand = now.replace(hour=sched["h"], minute=sched["m"], second=0, microsecond=0)
        if cand <= now:
            cand += timedelta(days=1)
        return cand
    if t == "weekly":
        best = None
        for wd, h, m in sched["slots"]:
            cand = now.replace(hour=h, minute=m, second=0, microsecond=0)
            days = (wd - now.weekday()) % 7
            cand += timedelta(days=days)
            if cand <= now:
                cand += timedelta(days=7)
            if best is None or cand < best:
                best = cand
        return best
    if t == "monthly":
        y, mo = now.year, now.month
        for _ in range(3):
            try:
                cand = now.replace(year=y, month=mo, day=sched["day"],
                                   hour=sched["h"], minute=sched["m"], second=0, microsecond=0)
            except ValueError:
                cand = None
            if cand and cand > now:
                return cand
            mo += 1
            if mo > 12:
                mo = 1; y += 1
        return None
    return None


def humanize(seconds):
    seconds = int(abs(seconds))
    if seconds < 60:
        return f"{seconds}秒"
    if seconds < 3600:
        return f"{seconds // 60}分"
    if seconds < 86400:
        return f"{seconds // 3600}時間{(seconds % 3600) // 60}分"
    return f"{seconds // 86400}日{(seconds % 86400) // 3600}時間"


# ─── GitHub Actions 各ジョブの最新実行を収集 ───────────────
def collect_gh():
    """job名 → {state, conclusion, ts, title} と 活動フィード を返す"""
    job_status = {}
    feed = []
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{REPO}/actions/runs?per_page=25",
             "-q", ".workflow_runs[].id"],
            capture_output=True, text=True, timeout=25, cwd=str(BASE_DIR),
        )
        run_ids = [x for x in out.stdout.split() if x.strip()][:16]
    except Exception:
        run_ids = []

    for rid in run_ids:
        try:
            jr = subprocess.run(
                ["gh", "api", f"repos/{REPO}/actions/runs/{rid}/jobs",
                 "-q", ".jobs[] | \"\\(.name)\\t\\(.status)\\t\\(.conclusion)\\t\\(.completed_at)\""],
                capture_output=True, text=True, timeout=20, cwd=str(BASE_DIR),
            )
        except Exception:
            continue
        for line in jr.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            name, status, concl, completed = parts[0], parts[1], parts[2], parts[3]
            ts = 0
            if completed and completed not in ("", "null"):
                try:
                    ts = datetime.fromisoformat(completed.replace("Z", "+00:00")).timestamp()
                except Exception:
                    ts = 0
            # 実行中
            if status == "in_progress":
                job_status.setdefault(name, {"state": "running", "conclusion": "", "ts": time.time()})
                continue
            if concl in ("", "null", "skipped", None):
                continue
            # 最新（runsは新しい順）を1回だけ採用
            if name not in job_status:
                st = "done" if concl == "success" else "error"
                job_status[name] = {"state": st, "conclusion": concl, "ts": ts}
            # フィード用
            feed.append((ts, name, concl))

    feed.sort(reverse=True)
    return job_status, feed[:8]


# ─── Supabase KPI ─────────────────────────────────────────
def sb_count(env, table, filt=""):
    url = env.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return 0
    q = f"{url}/rest/v1/{table}?select=id{('&' + filt) if filt else ''}"
    req = urllib.request.Request(q, headers={
        "apikey": key, "Authorization": f"Bearer {key}",
        "Range": "0-0", "Prefer": "count=exact",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            cr = r.headers.get("content-range", "*/0")
            return int(cr.split("/")[-1])
    except Exception:
        return 0


# ─── 状態を組み立てて _state に格納 ────────────────────────
def refresh():
    now = datetime.now()
    env = load_env()
    job_status, feed_raw = collect_gh()

    active  = sb_count(env, "members", "status=eq.active")
    trial   = sb_count(env, "members", "status=eq.trial")
    reports = sb_count(env, "reports")

    depts = []
    running = 0
    resident = 0
    ok_cnt = err_cnt = 0
    for d in ORG:
        members = []
        for m in d["members"]:
            resident += 1
            if m["src"] == "gh":
                js = job_status.get(m["job"], {})
                state = js.get("state", "idle")
                ts = js.get("ts", 0)
            else:  # claude常駐（実行履歴はローカルに残らないため予定のみ）
                state = "resident"
                ts = 0
            if state == "running":
                running += 1
            if state == "done":
                ok_cnt += 1
            if state == "error":
                err_cnt += 1
            nr = next_run(m["sched"], now)
            next_txt = f"あと{humanize((nr - now).total_seconds())}" if nr else "-"
            last_txt = f"{humanize(now.timestamp() - ts)}前" if ts else ("常駐待機" if m["src"] == "claude" else "履歴なし")
            members.append({
                "name": m["name"], "role": m["role"], "state": state,
                "next": next_txt, "last": last_txt,
            })
        depts.append({"dept": d["dept"], "icon": d["icon"], "members": members})

    name_map = {
        "member-report": "会員配信", "note-post": "note編集", "email-drip": "CRMドリップ",
        "facebook-post": "Facebook運用",
    }
    concl_ja = {"success": "成功", "failure": "失敗", "cancelled": "中止"}
    feed = []
    for ts, name, concl in feed_raw:
        who = name_map.get(name, name)
        ago = humanize(now.timestamp() - ts) if ts else "-"
        feed.append({"who": who, "text": f"ジョブ実行: {concl_ja.get(concl, concl)}", "ago": f"{ago}前"})

    total = ok_cnt + err_cnt
    success_rate = int(ok_cnt / total * 100) if total else 100

    with _lock:
        _state.update({
            "now": now.strftime("%Y-%m-%d %H:%M:%S"),
            "running_now": running,
            "kpi": {"active": active, "trial": trial, "reports": reports,
                    "resident": resident, "success_rate": success_rate},
            "depts": depts, "feed": feed,
        })


def refresh_loop():
    while True:
        try:
            refresh()
        except Exception as e:
            print(f"[refresh error] {e}")
        time.sleep(REFRESH_SEC)


# ─── HTML（サイトと同じ amber/stone・明るいテーマ）─────────
INDEX_HTML = """<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FBAトレンドレーダー LIVE 稼働状況</title>
<style>
:root{--bg:#faf9f7;--panel:#fff;--bd:#e7e2db;--tx:#1c1917;--mut:#78716c;
--amber:#f59e0b;--amber2:#d97706;--green:#16a34a;--red:#dc2626;--violet:#7c3aed;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
font-family:"Hiragino Sans","Yu Gothic",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:22px 18px 60px}
header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px}
.logo{width:32px;height:32px;border-radius:9px;background:var(--amber);color:#fff;display:grid;place-items:center;font-size:13px;font-weight:800}
.sub{font-size:11px;color:var(--mut);font-weight:600}
.live{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--mut)}
.dot{width:9px;height:9px;border-radius:50%;background:var(--green);animation:pulse 1.6s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(22,163,74,.5)}70%{box-shadow:0 0 0 9px rgba(22,163,74,0)}100%{box-shadow:0 0 0 0 rgba(22,163,74,0)}}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.kpi{background:var(--panel);border:1px solid var(--bd);border-radius:14px;padding:14px 16px}
.kpi .l{font-size:11px;color:var(--mut);margin-bottom:6px}
.kpi .v{font-size:25px;font-weight:800;letter-spacing:-.02em}
.kpi .v small{font-size:12px;color:var(--mut);font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.dept{background:var(--panel);border:1px solid var(--bd);border-radius:16px;padding:14px 15px}
.dept h3{margin:0 0 12px;font-size:13px;color:var(--mut);font-weight:800;letter-spacing:.03em}
.mem{background:var(--bg);border:1px solid var(--bd);border-radius:12px;padding:12px 13px;margin-bottom:10px}
.mem:last-child{margin-bottom:0}.mem.run{border-color:var(--green);box-shadow:0 0 0 2px rgba(22,163,74,.12)}
.mrow{display:flex;align-items:center;gap:9px}
.sdot{width:10px;height:10px;border-radius:50%;flex:0 0 auto}
.sdot.run{background:var(--green);animation:pulse 1.4s infinite}.sdot.done{background:var(--green)}
.sdot.idle{background:#c9beb0}.sdot.error{background:var(--red)}.sdot.resident{background:var(--violet)}
.mname{font-weight:700;font-size:14px}.mrole{font-size:11px;color:var(--mut);margin-top:1px}
.badge{margin-left:auto;font-size:11px;padding:3px 10px;border-radius:999px;background:#f5f0e8;border:1px solid var(--bd);color:var(--mut);font-weight:700}
.badge.done{color:#166534;background:#dcfce7;border-color:#bbf7d0}
.badge.error{color:#991b1b;background:#fee2e2;border-color:#fecaca}
.badge.run{color:#166534;background:#dcfce7;border-color:#86efac}
.badge.resident{color:#5b21b6;background:#ede9fe;border-color:#ddd6fe}
.meta{display:flex;gap:14px;margin-top:9px;font-size:11px;color:var(--mut)}
.feed{margin-top:16px;background:var(--panel);border:1px solid var(--bd);border-radius:16px;padding:14px 16px}
.feed h3{margin:0 0 10px;font-size:13px;color:var(--mut)}
.fitem{display:flex;gap:10px;padding:7px 0;border-top:1px solid var(--bd);font-size:12.5px}
.fitem:first-of-type{border-top:0}.fwho{color:var(--amber2);font-weight:800;flex:0 0 110px}
.ftxt{color:#44403c;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.fago{color:var(--mut)}
@media(max-width:820px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
</style></head>
<body><div class="wrap">
<header>
  <div class="brand"><div class="logo">FB</div>
    <div>FBAトレンドレーダー<div class="sub">LIVE 稼働ダッシュボード</div></div></div>
  <div class="live"><span class="dot"></span><span id="clock">—</span>・稼働中 <b id="runct">0</b> 名</div>
</header>
<div class="kpis" id="kpis"></div>
<div class="grid" id="org"></div>
<div class="feed"><h3>🛰️ 活動フィード（GitHub Actions 実行履歴）</h3><div id="feed"></div></div>
</div>
<script>
const label={running:'稼働中',done:'完了',idle:'待機',error:'エラー',resident:'常駐'};
async function tick(){
 try{
  const s=await(await fetch('/api/state',{cache:'no-store'})).json();
  clock.textContent=s.now; runct.textContent=s.running_now;
  const k=s.kpi||{};
  kpis.innerHTML=[
   ['有効会員',(k.active||0)+'<small> 名</small>'],
   ['トライアル',(k.trial||0)+'<small> 名</small>'],
   ['配信レポート',(k.reports||0)+'<small> 本</small>'],
   ['直近ジョブ成功率',(k.success_rate||0)+'<small> %</small>'],
   ['稼働社員',(k.resident||0)+'<small> 名</small>'],
  ].map(([l,v])=>`<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div></div>`).join('');
  org.innerHTML=s.depts.map(d=>`<div class="dept"><h3>${d.icon} ${d.dept}</h3>${d.members.map(m=>{
    const cls=m.state; return `<div class="mem ${m.state==='running'?'run':''}">
      <div class="mrow"><span class="sdot ${cls}"></span>
      <div><div class="mname">${m.name}</div><div class="mrole">${m.role}</div></div>
      <span class="badge ${cls}">${label[m.state]||'待機'}</span></div>
      <div class="meta"><span>⏱ 次回: ${m.next}</span><span>最終稼働: ${m.last}</span></div>
    </div>`;}).join('')}</div>`).join('');
  feed.innerHTML=(s.feed||[]).map(f=>`<div class="fitem"><span class="fwho">${f.who}</span><span class="ftxt">${f.text}</span><span class="fago">${f.ago}</span></div>`).join('')||'<div class="fitem"><span class="ftxt">履歴を取得中…</span></div>';
 }catch(e){}
}
tick();setInterval(tick,5000);
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/api/state"):
            with _lock:
                body = json.dumps(_state, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    refresh()  # 起動時に一度同期収集
    threading.Thread(target=refresh_loop, daemon=True).start()
    print(f"🖥️  FBAトレンドレーダー LIVEダッシュボード: http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
