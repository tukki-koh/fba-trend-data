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
 --night:#05070f;--sky1:#0a1024;--sky2:#0d1730;
 --steel:#101828;--steel2:#0b1220;--edge:#1e2c47;
 --slab:#16203a;--lit:#1b2742;--dark:#0a0f1c;
 --tx:#e6ecfa;--mut:#8497bd;--mut2:#54648a;
 --cyan:#22d3ee;--amber:#f5b642;--green:#34d399;--red:#ff5d6c;--violet:#8b7bff;}
*{box-sizing:border-box}
body{margin:0;background:var(--night);color:var(--tx);
 font-family:"Hiragino Sans","Yu Gothic",system-ui,sans-serif;font-size:13px;overflow-x:hidden}
.mono{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1460px;margin:0 auto;padding:14px 16px 40px}

/* ── ヘッダー（HUD風） ───────────────────────── */
header{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;
 background:linear-gradient(180deg,#0c1424,#080d18);border:1px solid var(--edge);
 border-radius:12px;padding:10px 16px;margin-bottom:14px;position:relative;overflow:hidden}
header:before{content:"";position:absolute;left:0;top:0;height:2px;width:100%;
 background:linear-gradient(90deg,transparent,var(--cyan),var(--amber),transparent);opacity:.8}
.brand{display:flex;align-items:center;gap:11px;font-weight:800;font-size:16px;letter-spacing:.02em}
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

/* ── レイアウト ─────────────────────────────── */
.stage{display:grid;grid-template-columns:1fr 310px;gap:14px;align-items:start}

/* ── 夜景 ──────────────────────────────────── */
.scene{position:relative;border:1px solid var(--edge);border-radius:14px;overflow:hidden;
 background:linear-gradient(180deg,var(--night) 0%,var(--sky1) 45%,var(--sky2) 100%);padding:0 0 0}
.stars{position:absolute;inset:0;pointer-events:none;opacity:.75}
.stars i{position:absolute;width:2px;height:2px;background:#cfe0ff;border-radius:50%;animation:tw 3.6s infinite}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:.9}}
.skyline{position:absolute;left:0;right:0;bottom:0;height:180px;opacity:.5;pointer-events:none}

/* ── ビル ──────────────────────────────────── */
/* 右に46pxの側面が生えるので、その半分だけ左へずらして全体を中央に見せる */
.tower{position:relative;width:min(100% - 80px,720px);margin:26px auto 0;transform:translateX(-23px)}
/* 屋上 */
.roof:after{content:"";position:absolute;left:100%;top:0;height:100%;width:46px;
 background:linear-gradient(100deg,#1d2c4a,#0b1220);border-right:1px solid var(--edge);
 border-top-right-radius:8px;clip-path:polygon(0 0,100% 13px,100% 100%,0 calc(100% - 13px))}
.roof{position:relative;margin:0 26px 0 26px;height:64px;
 background:linear-gradient(180deg,#16223c,#0e1728);border:1px solid var(--edge);
 border-bottom:none;border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center}
.sign{font-weight:900;letter-spacing:.16em;font-size:15px;color:#bff4ff;
 text-shadow:0 0 8px rgba(34,211,238,.9),0 0 26px rgba(34,211,238,.55);animation:neon 4s infinite}
@keyframes neon{0%,92%,100%{opacity:1}94%{opacity:.35}96%{opacity:1}97%{opacity:.5}}
.mast{position:absolute;top:-26px;left:50%;width:2px;height:26px;background:#2b4270}
.mast:after{content:"";position:absolute;top:-5px;left:-3px;width:8px;height:8px;border-radius:50%;
 background:var(--red);box-shadow:0 0 12px var(--red);animation:blink 2s infinite}
.beam{position:absolute;top:-4px;left:50%;width:2px;height:150px;transform-origin:top center;
 background:linear-gradient(180deg,rgba(34,211,238,.5),transparent);animation:sweep 9s ease-in-out infinite;pointer-events:none}
@keyframes sweep{0%,100%{transform:rotate(-38deg)}50%{transform:rotate(38deg)}}

/* 階 */
.floor{position:relative;display:grid;grid-template-columns:52px 1fr;
 border:1px solid var(--edge);border-top:none;background:var(--steel2)}
/* 右側面＝奥行き。各階を同じだけ下方向にずらした平行四辺形にすると角が立体に見える */
.floor:after{content:"";position:absolute;left:100%;top:0;height:100%;width:46px;pointer-events:none;
 background:linear-gradient(100deg,#16223a 0%,#0d1526 45%,#070c16 100%);
 border-right:1px solid var(--edge);
 clip-path:polygon(0 0,100% 13px,100% 100%,0 calc(100% - 13px))}
.floor.lit:after{background:linear-gradient(100deg,#1e2f4d 0%,#101c31 45%,#080e1a 100%)}
.tower .floor:last-of-type{border-radius:0 0 10px 10px}
/* 各階のスラブ（コンクリート厚み）で立体感を出す */
.floor .slab{position:absolute;left:0;right:0;top:0;height:6px;z-index:3;
 background:linear-gradient(180deg,#26375c 0%,#16203a 45%,#0a0f1c 100%)}
/* 階数 */
.fno{display:flex;align-items:center;justify-content:center;font-weight:900;font-size:15px;
 font-family:"SF Mono",ui-monospace,Menlo,monospace;
 color:var(--mut2);background:linear-gradient(180deg,#0d1424,#080d18);border-right:1px solid var(--edge);
 letter-spacing:.04em}
.floor.lit .fno{color:var(--cyan);text-shadow:0 0 12px rgba(34,211,238,.7)}
.floor.rest .fno{color:var(--violet)}
/* 室内 */
.room{position:relative;height:142px;overflow:hidden;background:var(--dark)}
.floor.lit .room{background:radial-gradient(120% 100% at 50% 0%,#22314f 0%,#131e35 55%,#0b1120 100%);
 box-shadow:0 0 34px rgba(56,150,220,.18) inset}
.floor.lit{box-shadow:0 0 26px rgba(40,120,200,.13)}
.floor.rest .room{background:radial-gradient(120% 100% at 50% 0%,#231b3d 0%,#151129 60%,#0b0918 100%)}
/* 奥の窓 */
.win{position:absolute;top:16px;left:0;right:0;height:52px;display:flex;gap:10px;padding:0 18px;opacity:.5}
.win span{flex:1;border-radius:2px;background:#0d1526;border:1px solid #1b2b47}
.floor.lit .win span{background:linear-gradient(180deg,#2b4570,#16233d);box-shadow:0 0 12px rgba(34,211,238,.18) inset}
/* 床面（奥行き） */
.ground{position:absolute;left:0;right:0;bottom:0;height:44px;
 background:linear-gradient(180deg,#16203a,#0c1322);
 clip-path:polygon(4% 0,96% 0,100% 100%,0 100%);border-top:1px solid #243455}
.floor.lit .ground{background:linear-gradient(180deg,#22314f,#101a2e)}
/* 天井の帯照明（点灯階のみ光る） */
.ceil{position:absolute;top:8px;left:0;right:0;height:3px;display:flex;gap:14%;justify-content:center;z-index:2}
.ceil i{width:14%;height:3px;border-radius:2px;background:#16223a}
.floor.lit .ceil i{background:#cfefff;box-shadow:0 0 14px rgba(180,235,255,.75),0 8px 34px rgba(120,200,255,.28)}
/* 室内のガラス反射 */
.glass{position:absolute;inset:0;z-index:7;pointer-events:none;
 background:linear-gradient(105deg,rgba(255,255,255,.055) 0 18%,transparent 18% 52%,rgba(255,255,255,.03) 52% 60%,transparent 60%)}
/* 備品 */
.prop{position:absolute;bottom:36px;z-index:4}
.desk{width:54px;height:9px;border-radius:2px;background:linear-gradient(180deg,#4a3b2a,#2a2016);
 box-shadow:0 7px 12px rgba(0,0,0,.55)}
.desk:after{content:"";position:absolute;bottom:-7px;left:6px;width:42px;height:7px;
 background:linear-gradient(180deg,#241b12,#171008)}
.desk:before{content:"";position:absolute;top:-14px;left:17px;width:21px;height:14px;border-radius:2px;
 background:#0d1526;border:1px solid #22344f}
.floor.lit .desk:before{background:linear-gradient(180deg,#2a6f88,#0e2b3a);border-color:#3d7f9b;
 box-shadow:0 0 12px rgba(34,211,238,.6);animation:mon 2.2s steps(3,end) infinite}
@keyframes mon{0%{opacity:.65}50%{opacity:1}100%{opacity:.8}}
.plant{width:13px;height:22px;border-radius:50% 50% 3px 3px;background:linear-gradient(180deg,#2b5a41,#16301f);
 box-shadow:0 5px 9px rgba(0,0,0,.55)}
/* 部署プレート */
.plate{position:absolute;top:9px;left:16px;display:flex;align-items:center;gap:9px;z-index:4}
.pname{font-weight:800;font-size:12.5px;letter-spacing:.01em}
.pcnt{font-size:10px;color:var(--mut);border:1px solid var(--edge);border-radius:4px;padding:1px 7px;
 background:rgba(6,10,20,.6)}
.floor.lit .pcnt{color:#9be7f5;border-color:rgba(34,211,238,.4)}
.proles{position:absolute;top:8px;right:48px;font-size:9px;font-weight:800;color:#6d7fa3;z-index:9;
 background:rgba(6,10,20,.72);border:1px solid var(--edge);border-radius:4px;padding:2px 8px;
 letter-spacing:.12em;display:flex;align-items:center;gap:6px;
 font-family:"SF Mono",ui-monospace,Menlo,monospace}
.proles b{width:6px;height:6px;border-radius:50%;background:#3a4a6b;display:inline-block}
.floor.lit .proles{color:#9be7f5;border-color:rgba(34,211,238,.35)}
.floor.lit .proles b{background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1.8s infinite}

/* ── 社員 ─────────────────────────────────── */
.per{position:absolute;bottom:var(--row,30px);width:30px;z-index:5;cursor:default}
.per svg{width:100%;height:auto;display:block;image-rendering:pixelated;shape-rendering:crispEdges;
 filter:drop-shadow(0 3px 5px rgba(0,0,0,.6))}
/* 歩く */
.per.walk{animation:stroll var(--dur,16s) ease-in-out var(--delay,0s) infinite}
@keyframes stroll{
 0%,5%   {left:5%;transform:scaleX(1)}
 26%,36% {left:38%;transform:scaleX(1)}
 58%,68% {left:70%;transform:scaleX(1)}
 70%     {left:70%;transform:scaleX(-1)}
 96%,100%{left:5%;transform:scaleX(-1)}}
.per.walk .legL{animation:stepA .46s steps(2,end) infinite}
.per.walk .legR{animation:stepB .46s steps(2,end) infinite}
.per.walk .armL{animation:stepB .46s steps(2,end) infinite}
.per.walk .armR{animation:stepA .46s steps(2,end) infinite}
@keyframes stepA{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.4px)}}
@keyframes stepB{0%,100%{transform:translateY(-1.4px)}50%{transform:translateY(0)}}
.per .legL,.per .legR,.per .armL,.per .armR{transform-box:fill-box;transform-origin:top center}
/* 休憩 */
.per.rest{opacity:.6}
.per.rest svg{animation:doze 3.4s ease-in-out infinite}
@keyframes doze{0%,100%{transform:translateY(0)}50%{transform:translateY(1.5px)}}
.zz{position:absolute;top:-10px;left:60%;font-size:10px;color:#a99bd6;animation:zz 2.8s ease-out infinite}
@keyframes zz{0%{opacity:0;transform:translate(0,4px)}35%{opacity:.95}100%{opacity:0;transform:translate(8px,-10px)}}
/* エラー */
.per.err svg{animation:panic .3s steps(2,end) infinite}
@keyframes panic{0%,100%{transform:translateX(-1px)}50%{transform:translateX(1px)}}
/* 名札 */
.per .tagn{position:absolute;bottom:-14px;left:50%;transform:translateX(-50%);white-space:nowrap;
 font-size:8.5px;color:#a9bde0;background:rgba(5,8,16,.75);border:1px solid var(--edge);
 padding:0 4px;border-radius:3px}
.per.walk .tagn{transform:translateX(-50%) scaleX(1)}
/* 吹き出し */
.per .bub{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:16px;
 white-space:nowrap;background:#dfe9ff;color:#0b1424;font-size:9px;font-weight:700;
 padding:2px 7px;border-radius:4px;animation:pop 9s ease-in-out infinite}
@keyframes pop{0%,80%,100%{opacity:0}84%,94%{opacity:1}}

/* ── エレベーター ─────────────────────────── */
.lift{position:absolute;top:64px;bottom:16px;right:16px;width:26px;background:#060a14;
 border:1px solid #24395e;border-radius:2px;z-index:8;overflow:hidden;
 background-image:repeating-linear-gradient(180deg,transparent 0 136px,#1b2c49 136px 142px)}
.car{position:absolute;left:3px;width:18px;height:30px;border-radius:2px;
 background:linear-gradient(180deg,#3a6f96,#12233a);border:1px solid #4d86ad;
 box-shadow:0 0 16px rgba(34,211,238,.65);animation:ride 14s ease-in-out infinite}
.car:after{content:"";position:absolute;top:50%;left:1px;right:1px;height:1px;background:rgba(190,240,255,.55)}
@keyframes ride{0%,100%{top:4%}25%{top:62%}50%{top:20%}75%{top:84%}}

/* ── 地上 ─────────────────────────────────── */
.base:after{content:"";position:absolute;left:100%;top:0;height:100%;width:46px;
 background:linear-gradient(100deg,#14213a,#070c16);border-right:1px solid var(--edge);
 clip-path:polygon(0 0,100% 13px,100% 100%,0 100%)}
.base{position:relative;margin:0 10px;height:16px;background:linear-gradient(180deg,#1a2740,#0a1120);
 border:1px solid var(--edge);border-top:none;border-radius:0 0 12px 12px}
.streetline{height:44px;background:linear-gradient(180deg,#080d18,#05070f);
 border-top:1px solid #12203a;position:relative}
.streetline:after{content:"";position:absolute;left:0;right:0;top:20px;height:1px;
 background:repeating-linear-gradient(90deg,#1d2f4d 0 22px,transparent 22px 44px)}

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
.foot{margin-top:14px;text-align:center;font-size:10.5px;color:var(--mut2);letter-spacing:.04em}
@media(max-width:1080px){.stage{grid-template-columns:1fr}.side{position:static}}
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
    <svg class="skyline" viewBox="0 0 1200 180" preserveAspectRatio="none" aria-hidden="true">
      <path fill="#0a1122" d="M0,180 L0,120 40,120 40,88 92,88 92,132 150,132 150,70 205,70 205,140
        260,140 260,100 320,100 320,60 372,60 372,146 430,146 430,110 495,110 495,150 560,150 560,92
        615,92 615,138 680,138 680,66 735,66 735,142 800,142 800,104 860,104 860,150 920,150 920,84
        975,84 975,136 1040,136 1040,112 1100,112 1100,148 1160,148 1160,96 1200,96 1200,180 Z"/>
      <g fill="#1b2c4d" opacity=".85" id="cityWin"></g>
    </svg>

    <div class="tower">
      <div class="roof">
        <span class="mast"></span><span class="beam"></span>
        <span class="sign">FBA TREND RADAR</span>
      </div>
      <div class="lift"><span class="car"></span></div>
      <div id="floors"></div>
      <div class="base"></div>
    </div>
    <div class="streetline"></div>
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

/* 星と街の灯り */
(()=>{let s='';for(let i=0;i<70;i++){s+=`<i style="left:${(Math.random()*100).toFixed(1)}%;top:${(Math.random()*46).toFixed(1)}%;animation-delay:${(Math.random()*3.6).toFixed(1)}s"></i>`}
 document.getElementById('stars').innerHTML=s;
 let w='';for(let i=0;i<90;i++){w+=`<rect x="${(Math.random()*1190).toFixed(0)}" y="${(60+Math.random()*110).toFixed(0)}" width="3" height="4"/>`}
 document.getElementById('cityWin').innerHTML=w;})();

/* ピクセル社員 */
function person(name,mood){
  const c=PAL[hash(name)%PAL.length];
  const closed=mood==='rest';
  return `<svg viewBox="0 0 16 23">
    <rect x="4" y="1" width="8" height="7" rx="1" fill="${c}"/>
    <rect x="6" y="4" width="1.6" height="${closed?0.8:2}" fill="#05070f"/>
    <rect x="8.6" y="4" width="1.6" height="${closed?0.8:2}" fill="#05070f"/>
    <rect x="4" y="8" width="8" height="8" fill="${c}"/>
    <rect x="5.5" y="9" width="5" height="3" fill="rgba(255,255,255,.18)"/>
    <rect class="armL" x="2" y="9" width="2" height="6" fill="${c}"/>
    <rect class="armR" x="12" y="9" width="2" height="6" fill="${c}"/>
    <rect class="legL" x="5" y="16" width="2.6" height="6" fill="#26314c"/>
    <rect class="legR" x="8.4" y="16" width="2.6" height="6" fill="#26314c"/>
  </svg>`;
}
function staff(m,kind,i){
  const dur=(13+hash(m.name)%9)+'s', delay=(-(hash(m.name+'d')%12))+'s';
  if(kind==='walk'){
    // 前後2列に振り分けて重なりを避ける
    const row=(i%2)?46:28;
    return `<div class="per walk ${m.state==='error'?'err':''}" title="${m.name}｜${LBL[m.state]||''}｜次回 ${m.next}"
      style="--dur:${dur};--delay:${delay};--row:${row}px;z-index:${i%2?4:6}">
      <div class="bub">${LINES[hash(m.name)%LINES.length]}</div>
      ${person(m.name,'act')}<div class="tagn">${short(m.name)}</div></div>`;
  }
  return `<div class="per rest" title="${m.name}｜${LBL[m.state]||''}｜次回 ${m.next}"
    style="left:${8+i*17}%"><div class="zz">z</div>${person(m.name,'rest')}
    <div class="tagn">${short(m.name)}</div></div>`;
}
const isActive=s=>s==='ok'||s==='run'||s==='error';

async function tick(){
 try{
  const s=await(await fetch('/api/state',{cache:'no-store'})).json();
  const k=s.kpi||{};
  hemp.textContent=(k.resident||0)+'名'; hrun.textContent=(s.running_now||0)+'名';
  hact.textContent=(s.today_activity||0)+'件'; hclock.textContent=s.hhmm||'–';

  const resting=[];
  const depts=(s.depts||[]).map((d,i)=>({...d,no:i+1}));
  const html=depts.slice().reverse().map(d=>{
    const on=d.members.filter(m=>isActive(m.state));
    d.members.filter(m=>!isActive(m.state)).forEach(m=>resting.push(m));
    const props=`<div class="prop desk" style="left:14%"></div>
      <div class="prop desk" style="left:46%"></div>
      <div class="prop desk" style="left:74%"></div>
      <div class="prop plant" style="left:92%"></div>`;
    return `<div class="floor ${on.length?'lit':''}">
      <div class="slab"></div>
      <div class="fno">${d.no}F</div>
      <div class="room">
        <div class="win">${'<span></span>'.repeat(7)}</div>
        <div class="ceil">${'<i></i>'.repeat(3)}</div>
        <div class="ground"></div>
        ${props}
        <div class="glass"></div>
        <div class="plate"><span class="pname">${d.icon} ${d.dept}</span>
          <span class="pcnt">稼働 ${on.length}/${d.members.length}</span></div>
        <div class="proles"><b></b>${on.length?'ACTIVE':'IDLE'}</div>
        ${on.map((m,i)=>staff(m,'walk',i)).join('')}
      </div></div>`;
  }).join('');

  const b1=`<div class="floor rest">
      <div class="slab"></div>
      <div class="fno">B1</div>
      <div class="room">
        <div class="win">${'<span></span>'.repeat(7)}</div>
        <div class="ceil">${'<i></i>'.repeat(3)}</div>
        <div class="ground"></div>
        <div class="prop desk" style="left:60%"></div>
        <div class="prop plant" style="left:90%"></div>
        <div class="glass"></div>
        <div class="plate"><span class="pname">☕ 休憩室</span>
          <span class="pcnt">${resting.length}名 休憩中</span></div>
        <div class="proles"><b></b>STANDBY</div>
        ${resting.map((m,i)=>staff(m,'rest',i)).join('')||''}
      </div></div>`;
  document.getElementById('floors').innerHTML=html+b1;

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
