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
         "sig": "週次マーケ", "interval_days": 7,
         "sched": {"type": "weekly", "slots": [(2, 10, 0)]}},  # 水10:00
        {"key": "monthly-seo", "name": "月次SEO/GEO担当（Claude常駐）",
         "role": "構造化データ・メタ最適化・llms.txt更新", "src": "claude",
         "sig": "月次SEO/GEO", "interval_days": 31,
         "sched": {"type": "monthly", "day": 5, "h": 10, "m": 0}},
    ]},
    {"dept": "広告本部", "icon": "📣", "members": [
        {"key": "google-ads", "name": "Google広告最適化担当（Claude常駐）",
         "role": "最適化スコア向上のアセットを毎週改善", "src": "claude",
         "sig": "広告最適化", "interval_days": 7,
         "sched": {"type": "weekly", "slots": [(2, 9, 30)]}},  # 水9:30
    ]},
    {"dept": "経営企画・成長室", "icon": "🚀", "members": [
        {"key": "growth-benchmark", "name": "成長・ベンチマーク担当（Claude常駐）",
         "role": "世界最高水準の企業を手本に毎週1改善を実装・本番反映", "src": "claude",
         "sig": "成長:", "interval_days": 7,
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


def git_last_ts(sig):
    """コミットメッセージに sig を含む最新コミットのUNIX時刻。無ければ0。"""
    if not sig:
        return 0
    try:
        r = subprocess.run(
            ["git", "-C", str(BASE_DIR), "log", "-1", "--format=%ct", "--grep", sig],
            capture_output=True, text=True, timeout=10,
        )
        s = r.stdout.strip()
        return float(s) if s else 0
    except Exception:
        return 0


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
                raw = js.get("state", "")
                ts = js.get("ts", 0)
                if raw == "running":
                    state = "run"          # いま実行中
                elif raw == "done":
                    state = "ok"           # 直近成功＝正常稼働
                elif raw == "error":
                    state = "error"        # 直近失敗＝要確認
                else:
                    state = "warn"         # 実行履歴を取得できず
            else:  # claude常駐：git履歴で実稼働を判定
                ts = git_last_ts(m.get("sig", ""))
                interval = m.get("interval_days", 7) * 86400
                if ts and (now.timestamp() - ts) < interval * 1.4:
                    state = "ok"           # 予定どおり稼働
                else:
                    state = "warn"         # 未実行 or 予定を超過

            # 「稼働中」= 正常に稼働している社員（実行中＋直近成功）
            if state in ("ok", "run"):
                running += 1
                ok_cnt += 1
            elif state == "error":
                err_cnt += 1

            nr = next_run(m["sched"], now)
            next_txt = f"あと{humanize((nr - now).total_seconds())}" if nr else "-"
            if ts:
                last_txt = f"{humanize(now.timestamp() - ts)}前"
            elif m["src"] == "claude":
                last_txt = "未実行"
            else:
                last_txt = "履歴なし"
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

    # 本日の活動（今日実行されたジョブ数）
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    today_activity = sum(1 for ts, _, _ in feed_raw if ts >= midnight)

    with _lock:
        _state.update({
            "now": now.strftime("%Y-%m-%d %H:%M:%S"),
            "hhmm": now.strftime("%H:%M:%S"),
            "running_now": running,
            "today_activity": today_activity,
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


# ─── HTML（WorkShield風・ダークテーマ）──────────────────────
INDEX_HTML = """<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FBA TREND RADAR ／ AI社屋</title>
<style>
:root{
 --night:#04060d;--sky1:#0a1024;--sky2:#0d1730;--edge:#1e2c47;
 --tx:#e6ecfa;--mut:#8497bd;--mut2:#54648a;
 --cyan:#22d3ee;--amber:#f5b642;--green:#34d399;--red:#ff5d6c;--violet:#8b7bff;
 /* ビルの寸法（3D空間） */
 --W:600px; --D:200px; --FH:128px; --RY:-24deg; --RX:8deg;}
*{box-sizing:border-box}
body{margin:0;background:var(--night);color:var(--tx);
 font-family:"Hiragino Sans","Yu Gothic",system-ui,sans-serif;font-size:13px;overflow-x:hidden}
.mono{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1480px;margin:0 auto;padding:14px 16px 40px}

/* ── ヘッダー ─────────────────────────────── */
header{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;
 background:linear-gradient(180deg,#0c1424,#080d18);border:1px solid var(--edge);
 border-radius:12px;padding:10px 16px;margin-bottom:14px;position:relative;overflow:hidden}
header:before{content:"";position:absolute;left:0;top:0;height:2px;width:100%;
 background:linear-gradient(90deg,transparent,var(--cyan),var(--amber),transparent);opacity:.8}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:16px}
.blogo{width:30px;height:30px;border-radius:7px;display:grid;place-items:center;font-size:15px;
 background:linear-gradient(145deg,#1b2b4d,#0d1526);border:1px solid #2b4270;
 box-shadow:0 0 16px rgba(34,211,238,.35) inset}
.tag{font-size:10px;color:var(--mut);letter-spacing:.18em;font-weight:700}
.hud{display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.hd{display:flex;flex-direction:column;line-height:1.15}
.hd .l{font-size:9.5px;color:var(--mut2);letter-spacing:.1em}
.hd .v{font-size:17px;font-weight:800}
.v.cy{color:var(--cyan)}.v.am{color:var(--amber)}.v.gr{color:var(--green)}
.live{display:inline-flex;align-items:center;gap:7px;font-size:11px;font-weight:800;color:var(--green);
 background:rgba(52,211,153,.10);border:1px solid rgba(52,211,153,.4);padding:5px 11px;border-radius:999px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);animation:blink 1.6s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}

.stage{display:grid;grid-template-columns:1fr 310px;gap:14px;align-items:start}

/* ── 夜景 ─────────────────────────────────── */
.scene{position:relative;border:1px solid var(--edge);border-radius:14px;overflow:hidden;min-height:1020px;
 background:linear-gradient(180deg,var(--night) 0%,var(--sky1) 50%,var(--sky2) 100%);
 perspective:1500px;perspective-origin:50% 42%}
.stars{position:absolute;inset:0;pointer-events:none}
.stars i{position:absolute;width:2px;height:2px;background:#cfe0ff;border-radius:50%;animation:tw 3.6s infinite}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:.9}}
.skyline{position:absolute;left:0;right:0;bottom:0;height:200px;opacity:.45;pointer-events:none}

/* ── 3D空間 ───────────────────────────────── */
/* rotateYで見かけが左に寄るため translateX で中央へ戻す */
.world{position:relative;width:var(--W);height:calc(6 * var(--FH));
 margin:150px auto 0;transform-style:preserve-3d;
 transform:translate3d(56px,0,-90px) rotateX(var(--RX)) rotateY(var(--RY))}
/* 各階＝奥行きのある箱（正面は開口） */
.fl{position:absolute;left:0;top:calc(var(--k) * var(--FH));width:var(--W);height:var(--FH);
 transform-style:preserve-3d}
.f{position:absolute;left:0;top:0}
.back{width:var(--W);height:var(--FH);transform:translateZ(calc(-1 * var(--D)));
 background:linear-gradient(180deg,#0e1728,#080e1a);border:1px solid #16233c}
.lft,.rgt{width:var(--D);height:var(--FH);transform-origin:0 0;transform:rotateY(90deg);
 background:linear-gradient(90deg,#0c1424,#060b15)}
.rgt{left:var(--W)}
.deck{width:var(--W);height:var(--D);top:var(--FH);transform-origin:0 0;transform:rotateX(-90deg);
 background:linear-gradient(180deg,#0b1220,#131e33)}
.ceilf{width:var(--W);height:var(--D);top:0;transform-origin:0 0;transform:rotateX(-90deg);
 background:linear-gradient(180deg,#0a101d,#0d1524)}
/* 点灯階 */
.fl.lit .back{background:linear-gradient(180deg,#1b2b49,#101a2e);box-shadow:0 0 40px rgba(60,150,220,.22) inset}
.fl.lit .lft,.fl.lit .rgt{background:linear-gradient(90deg,#16243d,#0b1220)}
.fl.lit .deck{background:linear-gradient(180deg,#16243d,#1e2f4d)}
.fl.lit .ceilf{background:linear-gradient(180deg,#0f1a2c,#16243d)}
.fl.rest .back{background:linear-gradient(180deg,#241b3d,#150f28)}
.fl.rest .deck{background:linear-gradient(180deg,#171029,#241b3d)}
/* スラブ（床の厚み） */
.slab{position:absolute;left:-6px;top:calc(var(--FH) - 5px);width:calc(var(--W) + 12px);height:10px;
 transform:translateZ(4px);background:linear-gradient(180deg,#31456e,#0b1120);border-radius:2px}
/* 奥の窓 */
.wins{position:absolute;left:0;top:0;width:var(--W);height:var(--FH);
 transform:translateZ(calc(-1 * var(--D) + 1px));display:flex;gap:12px;padding:22px 26px 46px}
.wins i{flex:1;border-radius:2px;background:#0b1424;border:1px solid #1a2a45}
.fl.lit .wins i{background:linear-gradient(180deg,#3a5c8e,#1a2b47);
 box-shadow:0 0 16px rgba(120,190,255,.35)}
/* 天井照明 */
.lamp{position:absolute;width:150px;height:26px;top:0;transform-origin:0 0;
 transform:translate3d(var(--x),6px,0) rotateX(-90deg);border-radius:3px;background:#111c30}
.fl.lit .lamp{background:#dff2ff;box-shadow:0 0 26px rgba(190,235,255,.85),0 0 60px rgba(120,200,255,.35)}

/* ── 机（3Dの箱） ─────────────────────────── */
.dsk{position:absolute;left:0;top:var(--FH);width:0;height:0;transform-style:preserve-3d;
 transform:translate3d(var(--x),0,var(--z))}
.dsk .dtop{position:absolute;left:-38px;top:0;width:76px;height:42px;transform-origin:0 0;
 transform:translateY(-30px) rotateX(-90deg);background:linear-gradient(180deg,#5a4630,#33261a);border-radius:2px}
.dsk .dfr{position:absolute;left:-38px;top:-30px;width:76px;height:30px;
 background:linear-gradient(180deg,#3a2c1d,#1d1610)}
.dsk .mon{position:absolute;left:-15px;bottom:30px;width:30px;height:20px;border-radius:2px;
 transform-origin:bottom center;transform:rotateY(calc(-1 * var(--RY))) rotateX(calc(-1 * var(--RX)));
 background:#0d1526;border:1px solid #22344f}
.fl.lit .dsk .mon{background:linear-gradient(180deg,#2f7d99,#0e2b3a);border-color:#4890ad;
 box-shadow:0 0 14px rgba(34,211,238,.6);animation:mon 2.4s steps(3,end) infinite}
@keyframes mon{0%{opacity:.7}50%{opacity:1}100%{opacity:.82}}
.plt{position:absolute;left:0;top:var(--FH);width:0;height:0;transform-style:preserve-3d;
 transform:translate3d(var(--x),0,var(--z))}
.plt i{position:absolute;left:-9px;bottom:0;width:18px;height:30px;
 transform-origin:bottom center;transform:rotateY(calc(-1 * var(--RY))) rotateX(calc(-1 * var(--RX)));
 border-radius:50% 50% 3px 3px;background:linear-gradient(180deg,#2f6647,#153021)}

/* ── 社員（3D空間を歩くビルボード） ───────── */
.pp{position:absolute;left:0;top:var(--FH);width:0;height:0;transform-style:preserve-3d}
.pp.walk{animation:walk3d var(--dur,18s) ease-in-out var(--delay,0s) infinite}
@keyframes walk3d{
 0%,7%    {transform:translate3d(calc(70px + var(--xo,0px)),0,calc(-30px + var(--zo,0px)))}
 27%,37%  {transform:translate3d(calc(230px + var(--xo,0px)),0,calc(-115px + var(--zo,0px)))}
 57%,67%  {transform:translate3d(calc(430px + var(--xo,0px)),0,calc(-55px + var(--zo,0px)))}
 88%,100% {transform:translate3d(calc(70px + var(--xo,0px)),0,calc(-30px + var(--zo,0px)))}}
.pp .bb{position:absolute;left:-17px;bottom:0;width:34px;
 transform-origin:bottom center;
 transform:rotateY(calc(-1 * var(--RY))) rotateX(calc(-1 * var(--RX)))}
.pp svg{width:100%;height:auto;display:block;image-rendering:pixelated;shape-rendering:crispEdges;
 filter:drop-shadow(0 4px 6px rgba(0,0,0,.7))}
.pp.walk .legL,.pp.walk .armR{animation:stepA .46s steps(2,end) infinite}
.pp.walk .legR,.pp.walk .armL{animation:stepB .46s steps(2,end) infinite}
@keyframes stepA{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}
@keyframes stepB{0%,100%{transform:translateY(-1.5px)}50%{transform:translateY(0)}}
.pp .legL,.pp .legR,.pp .armL,.pp .armR{transform-box:fill-box;transform-origin:top center}
/* 影 */
.pp .shadow{position:absolute;left:-14px;bottom:-3px;width:28px;height:10px;border-radius:50%;
 transform-origin:0 0;transform:rotateX(-90deg);background:radial-gradient(rgba(0,0,0,.55),transparent 70%)}
.pp.rest{opacity:.62}
.pp.rest svg{animation:doze 3.4s ease-in-out infinite}
@keyframes doze{0%,100%{transform:translateY(0)}50%{transform:translateY(1.5px)}}
.pp .zz{position:absolute;left:14px;bottom:34px;font-size:11px;color:#b6a8e6;animation:zz 2.8s ease-out infinite}
@keyframes zz{0%{opacity:0;transform:translate(0,4px)}35%{opacity:.95}100%{opacity:0;transform:translate(9px,-12px)}}
.pp.err svg{animation:panic .3s steps(2,end) infinite}
@keyframes panic{0%,100%{transform:translateX(-1px)}50%{transform:translateX(1px)}}
.pp .nm{position:absolute;top:100%;left:50%;transform:translateX(-50%);margin-top:3px;white-space:nowrap;
 font-size:8.5px;color:#b3c7e8;background:rgba(4,7,14,.8);border:1px solid var(--edge);
 padding:0 5px;border-radius:3px}
.pp .bub{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:6px;
 white-space:nowrap;background:#e2ecff;color:#0b1424;font-size:9px;font-weight:700;
 padding:2px 7px;border-radius:4px;animation:pop 10s ease-in-out infinite}
@keyframes pop{0%,82%,100%{opacity:0}86%,95%{opacity:1}}

/* ── 看板・階数（正面を向くビルボード） ───── */
.bbx{position:absolute;left:0;top:var(--FH);width:0;height:0;transform-style:preserve-3d;
 transform:translate3d(var(--x),var(--y,0px),var(--z))}
.bbx>span{position:absolute;bottom:0;left:0;white-space:nowrap;transform-origin:bottom left;
 transform:rotateY(calc(-1 * var(--RY))) rotateX(calc(-1 * var(--RX)))}
.dir{display:flex;align-items:center;gap:9px}
.plate{display:flex;align-items:center;gap:8px;background:rgba(6,11,22,.94);border:1px solid #2b4066;
 border-radius:5px;padding:4px 10px;font-weight:800;font-size:12px;
 box-shadow:0 3px 14px rgba(0,0,0,.6)}
.fl.lit .plate{border-color:rgba(34,211,238,.4);box-shadow:0 0 16px rgba(34,211,238,.18)}
.plate b{font-size:10px;font-weight:700;color:var(--mut);border-left:1px solid var(--edge);padding-left:8px}
.fl.lit .plate b{color:#9be7f5}
.fnum{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-weight:900;font-size:19px;color:#42557d;
 letter-spacing:.04em}
.fl.lit .fnum{color:var(--cyan);text-shadow:0 0 14px rgba(34,211,238,.8)}
.fl.rest .fnum{color:var(--violet)}
.led{display:inline-flex;align-items:center;gap:5px;font-family:"SF Mono",ui-monospace,Menlo,monospace;
 font-size:8.5px;font-weight:800;letter-spacing:.1em;color:#6d7fa3;
 border-left:1px solid var(--edge);padding-left:8px}
.led i{width:6px;height:6px;border-radius:50%;background:#3a4a6b}
.fl.lit .led{color:#9be7f5;border-color:rgba(34,211,238,.35)}
.fl.lit .led i{background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1.8s infinite}

/* ── 屋上・エレベーター・地面 ─────────────── */
.roof{position:absolute;left:-8px;top:-14px;width:calc(var(--W) + 16px);height:14px;
 transform-style:preserve-3d;background:linear-gradient(180deg,#2b3f66,#111a2c)}
.roof .top{position:absolute;left:0;top:0;width:100%;height:calc(var(--D) + 16px);
 transform-origin:0 0;transform:rotateX(-90deg);background:linear-gradient(180deg,#1a2740,#0d1524)}
.sign{position:absolute;left:0;top:-52px;width:0;height:0;transform-style:preserve-3d;
 transform:translate3d(calc(var(--W) / 2),0,-20px)}
.sign>span{position:absolute;bottom:0;left:0;transform:translateX(-50%) rotateY(calc(-1 * var(--RY))) rotateX(calc(-1 * var(--RX)));
 font-weight:900;letter-spacing:.16em;font-size:17px;white-space:nowrap;color:#c9f6ff;
 text-shadow:0 0 10px rgba(34,211,238,.95),0 0 30px rgba(34,211,238,.6);animation:neon 5s infinite}
@keyframes neon{0%,92%,100%{opacity:1}94%{opacity:.3}96%{opacity:1}97%{opacity:.55}}
.mast{position:absolute;left:calc(var(--W) / 2);top:-92px;width:2px;height:40px;background:#2b4270;
 transform:translateZ(-20px)}
.mast:after{content:"";position:absolute;top:-6px;left:-4px;width:9px;height:9px;border-radius:50%;
 background:var(--red);box-shadow:0 0 14px var(--red);animation:blink 2s infinite}
/* rotateY(-24deg)では左側が手前に来るため、左端に置くと視認しやすい */
.shaft{position:absolute;left:8px;top:0;width:42px;height:calc(6 * var(--FH));
 transform-style:preserve-3d;transform:translateZ(-56px)}
.shaft .glassf{position:absolute;inset:0;border:1px solid #3a5c8a;border-radius:2px;
 background:linear-gradient(180deg,rgba(24,44,74,.92),rgba(10,18,32,.92));
 background-image:repeating-linear-gradient(180deg,transparent 0 120px,#42679b 120px 128px);
 box-shadow:0 0 22px rgba(34,211,238,.22) inset}
.car{position:absolute;left:5px;width:32px;height:40px;border-radius:2px;
 background:linear-gradient(180deg,#4a86ad,#14263e);border:1px solid #5f9ec4;
 box-shadow:0 0 20px rgba(34,211,238,.7);animation:ride 15s ease-in-out infinite}
.car:after{content:"";position:absolute;top:50%;left:2px;right:2px;height:1px;background:rgba(200,245,255,.6)}
@keyframes ride{0%,100%{top:6px}25%{top:480px}50%{top:150px}75%{top:640px}}
.ground{position:absolute;left:calc(var(--W) / 2);top:calc(6 * var(--FH));width:0;height:0;transform-style:preserve-3d}
.ground>i{position:absolute;left:-700px;top:0;width:1400px;height:900px;transform-origin:0 0;
 transform:rotateX(-90deg);background:
 radial-gradient(ellipse 420px 260px at 700px 120px,rgba(70,150,220,.16),transparent 70%),
 linear-gradient(180deg,#080e1a,#05070f)}

/* ── サイドパネル ─────────────────────────── */
.side{display:flex;flex-direction:column;gap:12px;position:sticky;top:14px}
.panel{background:linear-gradient(180deg,#0c1424,#080e1a);border:1px solid var(--edge);border-radius:12px;padding:12px 13px}
.ptitle{font-size:11px;font-weight:800;color:var(--mut);letter-spacing:.1em;margin-bottom:10px;
 display:flex;align-items:center;justify-content:space-between}
.kgrid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.kbox{background:#0a1120;border:1px solid var(--edge);border-radius:8px;padding:8px 10px}
.kbox .l{font-size:9.5px;color:var(--mut2)}
.kbox .v{font-size:17px;font-weight:800;margin-top:2px}
.sect{font-size:10px;color:var(--mut);margin:11px 0 6px;font-weight:700;letter-spacing:.06em}
.task{display:flex;align-items:center;gap:7px;background:#0a1120;border:1px solid var(--edge);
 border-radius:6px;padding:6px 8px;margin-bottom:4px;font-size:11px}
.task.done{opacity:.7}
.tg{font-size:9px;font-weight:800;padding:1px 5px;border-radius:3px;flex:0 0 auto;
 background:rgba(34,211,238,.14);color:#9be7f5;border:1px solid rgba(34,211,238,.3)}
.tg.g{background:rgba(52,211,153,.13);color:#8ff0cb;border-color:rgba(52,211,153,.32)}
.tg.a{background:rgba(245,182,66,.13);color:#ffd899;border-color:rgba(245,182,66,.32)}
.ttx{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tago{font-size:9.5px;color:var(--mut2);flex:0 0 auto}
.foot{margin-top:14px;text-align:center;font-size:10.5px;color:var(--mut2)}
@media(max-width:1180px){.stage{grid-template-columns:1fr}.side{position:static}
 :root{--W:460px;--D:150px;--FH:112px}}
</style></head>
<body><div class="wrap">

<header>
  <div class="brand"><span class="blogo">📡</span>
    <div>FBA TREND RADAR<div class="tag">AI HEADQUARTERS ／ LIVE MONITOR</div></div></div>
  <div class="hud">
    <div class="hd"><span class="l">STAFF</span><span class="v" id="hemp">–</span></div>
    <div class="hd"><span class="l">ON DUTY</span><span class="v gr" id="hrun">–</span></div>
    <div class="hd"><span class="l">TODAY</span><span class="v am" id="hact">–</span></div>
    <div class="hd"><span class="l">CLOCK</span><span class="v cy mono" id="hclock">–</span></div>
    <span class="live"><span class="dot"></span>SYSTEM ONLINE</span>
  </div>
</header>

<div class="stage">
  <div class="scene">
    <div class="stars" id="stars"></div>
    <svg class="skyline" viewBox="0 0 1200 200" preserveAspectRatio="none" aria-hidden="true">
      <path fill="#080e1c" d="M0,200 L0,130 40,130 40,96 92,96 92,142 150,142 150,78 205,78 205,150
        260,150 260,110 320,110 320,68 372,68 372,156 430,156 430,120 495,120 495,160 560,160 560,100
        615,100 615,148 680,148 680,74 735,74 735,152 800,152 800,114 860,114 860,160 920,160 920,92
        975,92 975,146 1040,146 1040,122 1100,122 1100,158 1160,158 1160,104 1200,104 1200,200 Z"/>
      <g fill="#1a2b4a" opacity=".8" id="cityWin"></g>
    </svg>
    <div class="world" id="world"></div>
  </div>

  <div class="side">
    <div class="panel">
      <div class="ptitle">■ 経営指標<span style="color:var(--mut2);font-weight:600">LIVE</span></div>
      <div class="kgrid" id="kpis"></div>
    </div>
    <div class="panel">
      <div class="ptitle">■ 業務ログ<span style="color:var(--mut2);font-weight:600">AUTO</span></div>
      <div id="board"></div>
    </div>
  </div>
</div>
<div class="foot">⚡ GitHub Actions で 24時間365日 稼働中 ・ 8秒ごとに自動更新</div>
</div>

<script>
const LBL={run:'実行中',ok:'稼働中',error:'要確認',warn:'待機',idle:'待機',resident:'常駐'};
const PAL=['#f2884b','#ef6b8a','#f5c451','#5b8cff','#37d399','#b07be8','#e8724a','#4fc3d9'];
const LINES=['データ確認中','順調です','あと少し','数字いいね','ここ調整中','完了しました'];
function hash(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return Math.abs(h)}
const short=n=>n.replace(/（.*?）/g,'').replace(/担当$/,'');

(()=>{let s='';for(let i=0;i<80;i++){s+=`<i style="left:${(Math.random()*100).toFixed(1)}%;top:${(Math.random()*44).toFixed(1)}%;animation-delay:${(Math.random()*3.6).toFixed(1)}s"></i>`}
 document.getElementById('stars').innerHTML=s;
 let w='';for(let i=0;i<100;i++){w+=`<rect x="${(Math.random()*1190).toFixed(0)}" y="${(70+Math.random()*125).toFixed(0)}" width="3" height="4"/>`}
 document.getElementById('cityWin').innerHTML=w;})();

function person(name,rest){
  const c=PAL[hash(name)%PAL.length];
  return `<svg viewBox="0 0 16 23">
    <rect x="4" y="1" width="8" height="7" rx="1" fill="${c}"/>
    <rect x="6" y="4" width="1.6" height="${rest?0.8:2}" fill="#04060d"/>
    <rect x="8.6" y="4" width="1.6" height="${rest?0.8:2}" fill="#04060d"/>
    <rect x="4" y="8" width="8" height="8" fill="${c}"/>
    <rect x="5.5" y="9" width="5" height="3" fill="rgba(255,255,255,.2)"/>
    <rect class="armL" x="2" y="9" width="2" height="6" fill="${c}"/>
    <rect class="armR" x="12" y="9" width="2" height="6" fill="${c}"/>
    <rect class="legL" x="5" y="16" width="2.6" height="6" fill="#26314c"/>
    <rect class="legR" x="8.4" y="16" width="2.6" height="6" fill="#26314c"/>
  </svg>`;
}
function staffWalk(m){
  const dur=(15+hash(m.name)%10)+'s', delay=(-(hash(m.name+'d')%14))+'s';
  const zo=[0,-42,38,-20][hash(m.name+'z')%4], xo=[0,-38,42,18][hash(m.name+'x')%4];
  return `<div class="pp walk ${m.state==='error'?'err':''}" style="--dur:${dur};--delay:${delay};--zo:${zo}px;--xo:${xo}px"
     title="${m.name}｜${LBL[m.state]||''}｜次回 ${m.next}">
     <div class="shadow"></div>
     <div class="bb"><div class="bub">${LINES[hash(m.name)%LINES.length]}</div>
       ${person(m.name,false)}<div class="nm">${short(m.name)}</div></div></div>`;
}
function staffRest(m,i){
  return `<div class="pp rest" style="transform:translate3d(${90+i*120}px,0,-70px)"
     title="${m.name}｜${LBL[m.state]||''}｜次回 ${m.next}">
     <div class="shadow"></div>
     <div class="bb"><div class="zz">z</div>${person(m.name,true)}
       <div class="nm">${short(m.name)}</div></div></div>`;
}
const isActive=s=>s==='ok'||s==='run'||s==='error';

function floorHTML(d,k,label,cls,ledTxt,inner){
  return `<div class="fl ${cls}" style="--k:${k}">
    <div class="f back"></div><div class="f lft"></div><div class="f rgt"></div>
    <div class="f deck"></div><div class="f ceilf"></div>
    <div class="wins">${'<i></i>'.repeat(6)}</div>
    <div class="lamp" style="--x:110px"></div><div class="lamp" style="--x:340px"></div>
    <div class="slab"></div>
    <div class="bbx" style="--x:-252px;--y:-58px;--z:64px"><span class="dir">
      <b class="fnum">${label}</b>
      <span class="plate">${d.icon} ${d.dept}<b>${d.cnt}</b><span class="led"><i></i>${ledTxt}</span></span>
    </span></div>
    <div class="plt" style="--x:530px;--z:-150px"><i></i></div>
    ${inner}</div>`;
}

async function tick(){
 try{
  const s=await(await fetch('/api/state',{cache:'no-store'})).json();
  const k=s.kpi||{};
  hemp.textContent=(k.resident||0)+'名'; hrun.textContent=(s.running_now||0)+'名';
  hact.textContent=(s.today_activity||0)+'件'; hclock.textContent=s.hhmm||'–';

  const resting=[];
  const depts=(s.depts||[]).map((d,i)=>({...d,no:i+1}));
  // 上階ほど後ろの部署（5F=最後の部署）
  const order=depts.slice().reverse();
  let html=`<div class="roof"><div class="top"></div></div>
    <div class="mast"></div><div class="sign"><span>FBA TREND RADAR</span></div>
    <div class="shaft"><div class="glassf"></div><div class="car"></div></div>
    <div class="ground"><i></i></div>`;

  order.forEach((d,k)=>{
    const on=d.members.filter(m=>isActive(m.state));
    d.members.filter(m=>!isActive(m.state)).forEach(m=>resting.push(m));
    const desks=`<div class="dsk" style="--x:130px;--z:-120px"><div class="dtop"></div><div class="dfr"></div><div class="mon"></div></div>
      <div class="dsk" style="--x:300px;--z:-150px"><div class="dtop"></div><div class="dfr"></div><div class="mon"></div></div>
      <div class="dsk" style="--x:450px;--z:-110px"><div class="dtop"></div><div class="dfr"></div><div class="mon"></div></div>`;
    html+=floorHTML({...d,cnt:`稼働 ${on.length}/${d.members.length}`}, k, d.no+'F',
      on.length?'lit':'', on.length?'ACTIVE':'IDLE',
      desks+on.map(staffWalk).join(''));
  });

  html+=floorHTML({icon:'☕',dept:'休憩室',cnt:`${resting.length}名 休憩中`}, order.length, 'B1', 'rest','STANDBY',
    `<div class="dsk" style="--x:420px;--z:-140px"><div class="dtop"></div><div class="dfr"></div><div class="mon"></div></div>`
    + resting.map(staffRest).join(''));

  document.getElementById('world').innerHTML=html;

  document.getElementById('kpis').innerHTML=[
   ['有効会員',(k.active||0)+'名'],['トライアル',(k.trial||0)+'名'],
   ['配信レポート',(k.reports||0)+'本'],['成功率',(k.success_rate||0)+'%'],
  ].map(([l,v])=>`<div class="kbox"><div class="l">${l}</div><div class="v">${v}</div></div>`).join('');

  const next=[];depts.forEach(d=>d.members.forEach(m=>next.push({who:d.dept,name:m.name,next:m.next})));
  document.getElementById('board').innerHTML=
   `<div class="sect">▸ 次の出社予定</div>`+
   next.slice(0,5).map(t=>`<div class="task"><span class="tg a">${t.who.slice(0,4)}</span>
     <span class="ttx">${short(t.name)}</span><span class="tago">${t.next}</span></div>`).join('')+
   `<div class="sect">✓ 完了した仕事</div>`+
   ((s.feed||[]).map(f=>`<div class="task done"><span class="tg g">${f.who}</span>
     <span class="ttx">${f.text}</span><span class="tago">${f.ago}</span></div>`).join('')
     ||'<div class="task">履歴を取得中…</div>');
 }catch(e){}
}
tick();setInterval(tick,8000);
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
