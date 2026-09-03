"""
FBAトレンドレーダー LIVE 稼働ダッシュボード — localhost:8788

このサービス専属のAI社員（GitHub Actions ジョブ + 常駐Claudeタスク）の
稼働状況・KPI・活動フィードをリアルタイムで可視化する。
ブラウザで http://localhost:8788 を開くと5秒ごとに自動更新される。

データ源（すべて実データ）:
 - GitHub Actions: weekly_report.yml (member-report/note-post/email-drip) と
   facebook_marketing.yml (facebook-post) の各ジョブ最新実行結果（gh CLI）
 - クラウドAI社員（cloud_agents.py 等）: コミット署名から最終稼働を判定
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
ASSET_DIR = BASE_DIR / "scripts" / "dashboard_assets"                 # 背景画像・3D画面(index.html)

# ─── ブランド：サイトと同じ amber / stone（明るい） ──────────

# ─── 組織構成（このサービス専属の社員） ─────────────────────
# src: "gh"（GitHub Actionsジョブ）/ "claude"（クラウドAI社員：gitコミット署名で稼働判定）
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
        {"key": "sns-hashtag", "name": "SNSハッシュタグ担当",
         "role": "Instagram用ハッシュタグを毎週最適化", "src": "claude",
         "sig": "^SNSハッシュタグ更新\\|^週次マーケ更新", "interval_days": 7,
         "sched": {"type": "weekly", "slots": [(2, 10, 0)]}},  # 水10:00
        {"key": "monthly-seo", "name": "月次SEO/GEO担当",
         "role": "llms.txt・メタ情報をAI検索向けに最適化", "src": "claude",
         "sig": "^AI社員(seo)\\|^月次SEO/GEO", "interval_days": 31,
         "sched": {"type": "monthly", "day": 5, "h": 10, "m": 0}},
    ]},
    {"dept": "広告本部", "icon": "🎯", "members": [
        {"key": "google-ads", "name": "Google広告最適化担当",
         "role": "最適化スコア向上のアセットを隔週で改善", "src": "claude",
         "sig": "^AI社員(ads)\\|^広告最適化", "interval_days": 14,
         "sched": {"type": "weekly", "slots": [(2, 9, 30)]}},  # 水9:30（隔週）
    ]},
    {"dept": "経営企画・成長室", "icon": "🚀", "members": [
        {"key": "growth-benchmark", "name": "成長・ベンチマーク担当",
         "role": "世界最高水準の企業を手本に毎週1改善を本番反映", "src": "claude",
         "sig": "^AI社員(growth)\\|^成長:", "interval_days": 7,
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


# ─── HTML（実写オフィス × ホログラムAI社員）──────────────────
INDEX_HTML = """<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FBA TREND RADAR ／ AIオフィス LIVE</title>
<style>
:root{
 --night:#04060d;--edge:#1e2c47;--tx:#e6ecfa;--mut:#8497bd;--mut2:#54648a;
 --cyan:#22d3ee;--amber:#f5b642;--green:#34d399;--red:#ff5d6c;--violet:#8b7bff;}
*{box-sizing:border-box}
body{margin:0;background:var(--night);color:var(--tx);
 font-family:"Hiragino Sans","Yu Gothic",system-ui,sans-serif;font-size:13px;overflow-x:hidden}
.mono{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1560px;margin:0 auto;padding:14px 16px 40px}

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

/* ── 実写オフィス（夜） ───────────────────── */
.scene{position:relative;border:1px solid var(--edge);border-radius:14px;overflow:hidden;
 aspect-ratio:1920/1071;background:#04060d url(/bg.jpg) center/cover no-repeat;
 box-shadow:0 20px 60px rgba(0,0,0,.6)}
.vig{position:absolute;inset:0;pointer-events:none;
 background:radial-gradient(ellipse 80% 70% at 50% 55%,transparent 55%,rgba(2,4,10,.7) 100%),
 linear-gradient(180deg,rgba(4,6,13,.45),transparent 28%,transparent 72%,rgba(4,6,13,.6))}
/* 空気感：ゆっくり流れる薄い霧 */
.haze{position:absolute;inset:-10%;pointer-events:none;opacity:.5;mix-blend-mode:screen;
 background:radial-gradient(ellipse 40% 30% at 50% 45%,rgba(120,190,240,.16),transparent 70%);
 animation:haze 18s ease-in-out infinite}
@keyframes haze{0%,100%{transform:translate(0,0)}50%{transform:translate(2%,1%)}}
/* 走査線（ホログラム全体の雰囲気） */
.scan{position:absolute;inset:0;pointer-events:none;opacity:.18;mix-blend-mode:overlay;
 background:repeating-linear-gradient(180deg,rgba(255,255,255,.35) 0 1px,transparent 1px 4px)}
.beam{position:absolute;left:0;right:0;height:14%;pointer-events:none;mix-blend-mode:screen;opacity:.35;
 background:linear-gradient(180deg,transparent,rgba(120,220,255,.25),transparent);animation:beam 9s linear infinite}
@keyframes beam{0%{top:-16%}100%{top:104%}}

/* ── 動画風の大見出し ─────────────────────── */
.cap{position:absolute;left:50%;top:7%;transform:translateX(-50%);text-align:center;pointer-events:none;z-index:40;width:96%}
.cap b{display:block;font-size:clamp(20px,3.3vw,50px);font-weight:900;color:#fff;letter-spacing:.02em;line-height:1.15;
 -webkit-text-stroke:2.2px #000;paint-order:stroke fill;text-shadow:0 5px 14px rgba(0,0,0,.85)}
.cap b em{font-style:normal;color:#ffd21f}
.cap b i{font-style:normal;color:#ff4d5a}
.cap small{display:inline-block;margin-top:8px;font-size:clamp(10px,1vw,14px);font-weight:800;color:#dff5ff;letter-spacing:.14em;
 background:rgba(4,8,18,.62);border:1px solid rgba(34,211,238,.35);padding:4px 12px;border-radius:999px;backdrop-filter:blur(3px)}

/* ── 社員（ホログラム） ───────────────────── */
.emp{position:absolute;height:var(--h);aspect-ratio:100/120;transform:translate(-50%,-100%);
 transform-origin:50% 100%}
/* 床・椅子への光のこぼれ */
.emp:before{content:"";position:absolute;left:50%;bottom:-6%;width:170%;height:34%;transform:translateX(-50%);
 background:radial-gradient(ellipse at 50% 50%,rgba(70,190,255,.45),rgba(40,120,255,.12) 45%,transparent 70%);
 mix-blend-mode:screen;pointer-events:none;animation:pool 3s ease-in-out infinite}
@keyframes pool{0%,100%{opacity:.75}50%{opacity:1}}
.emp .fig{position:absolute;inset:0;mix-blend-mode:screen;animation:flick 5.5s infinite}
.emp.r .fig{transform:scaleX(-1)}
.emp svg{width:100%;height:100%;overflow:visible;display:block;
 filter:drop-shadow(0 0 5px rgba(120,225,255,.95)) drop-shadow(0 0 20px rgba(50,150,255,.6))}
@keyframes flick{0%,100%{opacity:1}31%{opacity:1}32%{opacity:.55}33%{opacity:1}64%{opacity:1}65%{opacity:.7}66%{opacity:1}87%{opacity:1}88%{opacity:.8}89%{opacity:1}}
/* 稼働中：タイピング／うなずき */
.emp.on .handR{animation:type .26s ease-in-out infinite alternate}
.emp.on .handL{animation:type .26s ease-in-out .13s infinite alternate}
@keyframes type{from{transform:translate(0,0)}to{transform:translate(-1.5px,-2.6px)}}
.emp.on .head{animation:nod 3.4s ease-in-out infinite}
@keyframes nod{0%,100%{transform:rotate(0)}38%{transform:rotate(-3deg)}72%{transform:rotate(2.5deg)}}
.emp .head,.emp .handR,.emp .handL{transform-box:fill-box;transform-origin:50% 100%}
.emp.on .torso{animation:breath 4s ease-in-out infinite}
@keyframes breath{0%,100%{transform:translateY(0)}50%{transform:translateY(-.6px)}}
/* データ粒子 */
.emp .px{position:absolute;inset:0;pointer-events:none}
.emp .px i{position:absolute;bottom:25%;left:var(--l);width:3px;height:3px;border-radius:50%;background:#bff3ff;
 box-shadow:0 0 6px #7fe6ff;opacity:0;animation:rise var(--d) linear var(--dl) infinite}
@keyframes rise{0%{opacity:0;transform:translateY(0) scale(.6)}15%{opacity:1}100%{opacity:0;transform:translateY(-90px) scale(1.1)}}
.emp:not(.on) .px{display:none}
/* 実行中：強い脈動 */
.emp.run svg{animation:pulse 1.1s ease-in-out infinite}
@keyframes pulse{0%,100%{filter:drop-shadow(0 0 6px rgba(120,225,255,1)) drop-shadow(0 0 22px rgba(50,150,255,.7))}
 50%{filter:drop-shadow(0 0 12px rgba(160,240,255,1)) drop-shadow(0 0 44px rgba(80,180,255,.95))}}
/* 待機：薄い残像。動かない */
.emp.idle .fig{opacity:.26;animation:idleflick 7s infinite}
@keyframes idleflick{0%,100%{opacity:.26}48%{opacity:.26}50%{opacity:.12}52%{opacity:.26}}
.emp.idle:before{opacity:.25;animation:none}
/* 要確認：赤いホログラム＋グリッチ */
.emp.err svg{filter:drop-shadow(0 0 5px rgba(255,110,130,.95)) drop-shadow(0 0 22px rgba(255,60,90,.6))}
.emp.err .fig{animation:glitch .5s steps(2,end) infinite}
@keyframes glitch{0%,100%{transform:translate(0,0)}50%{transform:translate(1.5px,-1px) skewX(-2deg)}}
.emp.err.r .fig{animation:glitchR .5s steps(2,end) infinite}
@keyframes glitchR{0%,100%{transform:scaleX(-1) translate(0,0)}50%{transform:scaleX(-1) translate(1.5px,-1px) skewX(-2deg)}}
.emp.err:before{background:radial-gradient(ellipse,rgba(255,80,110,.4),transparent 70%)}
/* AR風ネームタグ */
.emp .lb{position:absolute;left:50%;bottom:104%;transform:translateX(var(--lx,-50%));white-space:nowrap;z-index:5;
 display:flex;flex-direction:column;align-items:center;gap:2px;pointer-events:auto}
/* 引き出し線：頭上から斜めに名札へ。奥の席ほど長い */
.emp .lb:after{content:"";width:1px;height:var(--ll,10px);background:linear-gradient(180deg,rgba(150,235,255,.9),rgba(150,235,255,.15))}
.emp .lb:before{content:"";position:absolute;bottom:0;left:50%;width:5px;height:5px;border-radius:50%;
 transform:translate(-50%,50%);background:#bff3ff;box-shadow:0 0 8px #7fe6ff}
.emp .nm{font-size:10.5px;font-weight:800;color:#e9fbff;letter-spacing:.04em;
 background:rgba(4,10,22,.72);border:1px solid rgba(90,220,255,.45);padding:2px 8px;border-radius:4px;
 box-shadow:0 0 12px rgba(34,211,238,.25);backdrop-filter:blur(3px)}
.emp .st{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:8.5px;font-weight:800;letter-spacing:.12em;
 color:#9be7f5;display:flex;align-items:center;gap:5px}
.emp .st i{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 7px var(--green);animation:blink 1.4s infinite}
.emp.run .st i{background:var(--cyan);box-shadow:0 0 7px var(--cyan);animation-duration:.5s}
.emp.idle .st{color:#6d7fa3}.emp.idle .st i{background:#3a4a6b;box-shadow:none;animation:none}
.emp.idle .nm{opacity:.75;border-color:rgba(120,140,180,.35);box-shadow:none}
.emp.err .st{color:#ffb3bc}.emp.err .st i{background:var(--red);box-shadow:0 0 7px var(--red)}
.emp.err .nm{border-color:rgba(255,93,108,.55)}
.emp .tip{position:absolute;top:100%;left:50%;transform:translateX(-50%);margin-top:6px;white-space:nowrap;display:none;
 background:rgba(4,10,22,.92);border:1px solid rgba(90,220,255,.4);border-radius:6px;padding:6px 9px;font-size:10px;color:#cfe6ff;
 text-align:left;line-height:1.5;z-index:9}
.emp .lb:hover .tip{display:block}
.emp .tip b{color:#9be7f5}
/* 小さい画面ではネームタグを縮小 */
@media(max-width:900px){.emp .nm{font-size:8px;padding:1px 5px}.emp .st{font-size:7px}}

/* ── 部署凡例（下部） ─────────────────────── */
.legend{position:absolute;left:12px;bottom:12px;z-index:40;display:flex;gap:6px;flex-wrap:wrap;max-width:70%}
.lg{display:flex;align-items:center;gap:7px;font-size:10.5px;font-weight:800;color:#cfe6ff;
 background:rgba(4,10,22,.78);border:1px solid var(--edge);border-radius:999px;padding:4px 10px;backdrop-filter:blur(3px)}
.lg b{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:9.5px;color:#9be7f5;font-weight:800}
.lg.lit{border-color:rgba(34,211,238,.45);box-shadow:0 0 12px rgba(34,211,238,.18)}
.clock{position:absolute;right:12px;bottom:12px;z-index:40;font-family:"SF Mono",ui-monospace,Menlo,monospace;
 font-size:12px;font-weight:800;color:#9be7f5;background:rgba(4,10,22,.78);border:1px solid rgba(34,211,238,.35);
 padding:5px 11px;border-radius:8px;letter-spacing:.1em}

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
.tg.r{background:rgba(255,93,108,.13);color:#ffb3bc;border-color:rgba(255,93,108,.35)}
.ttx{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tago{font-size:9.5px;color:var(--mut2);flex:0 0 auto}
.foot{margin-top:14px;text-align:center;font-size:10.5px;color:var(--mut2)}
@media(max-width:1180px){.stage{grid-template-columns:1fr}.side{position:static}}
</style></head>
<body><div class="wrap">

<!-- ホログラム用の共通定義（グラデーション・グリッド） -->
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
 <defs>
  <linearGradient id="hg" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="#c8f6ff" stop-opacity=".85"/>
   <stop offset=".45" stop-color="#4fc3ff" stop-opacity=".62"/>
   <stop offset="1" stop-color="#1f5cff" stop-opacity=".38"/></linearGradient>
  <linearGradient id="hgErr" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="#ffd0d6" stop-opacity=".85"/>
   <stop offset=".45" stop-color="#ff6b85" stop-opacity=".6"/>
   <stop offset="1" stop-color="#b3123a" stop-opacity=".4"/></linearGradient>
  <pattern id="grid" width="6" height="6" patternUnits="userSpaceOnUse">
   <path d="M6,0 L0,0 0,6" fill="none" stroke="rgba(200,245,255,.55)" stroke-width=".7"/></pattern>
  <pattern id="scanp" width="4" height="3" patternUnits="userSpaceOnUse">
   <rect width="4" height="1" fill="rgba(0,10,30,.35)"/></pattern>
 </defs>
</svg>

<header>
  <div class="brand"><span class="blogo">📡</span>
    <div>FBA TREND RADAR<div class="tag">AI OFFICE ／ LIVE MONITOR</div></div></div>
  <div class="hud">
    <div class="hd"><span class="l">STAFF</span><span class="v" id="hemp">–</span></div>
    <div class="hd"><span class="l">ON DUTY</span><span class="v gr" id="hrun">–</span></div>
    <div class="hd"><span class="l">TODAY</span><span class="v am" id="hact">–</span></div>
    <div class="hd"><span class="l">CLOCK</span><span class="v cy mono" id="hclock">–</span></div>
    <span class="live"><span class="dot"></span>SYSTEM ONLINE</span>
  </div>
</header>

<div class="stage">
  <div class="scene" id="scene">
    <div class="haze"></div>
    <div class="vig"></div>
    <div class="beam"></div>
    <div class="cap"><b><i>AI</i>社員 <em id="capN">–名</em>が自動運転中</b>
      <small>FBAトレンドレーダー ／ 24H 無人稼働 ／ <span id="capSub">–</span></small></div>
    <div id="staff"></div>
    <div class="scan"></div>
    <div class="legend" id="legend"></div>
    <div class="clock mono" id="sclock">--:--:--</div>
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
<div class="foot">⚡ GitHub Actions で 24時間365日 稼働中 ・ 8秒ごとに自動更新 ・ 名札にカーソルを合わせると詳細</div>
</div>

<script>
const LBL={run:'RUNNING',ok:'ACTIVE',error:'ERROR',warn:'STANDBY',idle:'STANDBY'};
const LBLJ={run:'実行中',ok:'稼働中',error:'要確認',warn:'待機',idle:'待機'};
function hash(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;return Math.abs(h)}
const short=n=>n.replace(/（.*?）/g,'').replace(/担当$/,'');

/* 座席（背景写真の椅子位置に合わせた % 座標）: [x, y(腰の位置), 身長%, 向き] */
/* 5,6番目 = 名札の引き出し線の長さ(px) と 横ずらし(%)。奥の席ほど高く・外側へ出して重なりを防ぐ */
const SEATS=[
 [33.4,74.5,26,'l',10,-70],[38.8,68.5,21.5,'l',40,-95],[41.7,65,18.5,'l',72,-120],[43.3,62.5,16,'l',104,-150],   /* 左列：手前→奥 */
 [65.2,74.5,26,'r',10,-30],[61.5,68.5,21.5,'r',40,-5],[58.2,65,18.5,'r',72,20],[56.9,62.5,16,'r',104,50],        /* 右列：手前→奥 */
 [8.5,79,25,'r',10,-50],[92,79,25,'l',10,-50],                                                                    /* 窓際の個室席 */
];
/* 社員→座席の固定割当（順序＝ORGの並び）。9人目(成長室)は窓際の個室席 */
const SEAT_ORDER=[0,1,2,3,4,5,6,7,8,9];

function figure(err){
  const g=err?'url(#hgErr)':'url(#hg)', mid='m'+Math.floor(Math.random()*1e9);
  const body=`
    <g class="torso"><path d="M27,54 C29,42 40,37 52,37 C64,37 75,42 77,54 L81,120 L23,120 Z"/></g>
    <path d="M46,29 L58,29 L59.5,40 L44.5,40 Z"/>
    <g class="head"><ellipse cx="52" cy="18.5" rx="12.5" ry="14.5"/></g>
    <g class="armF"><path d="M31,50 L16,73" fill="none" stroke-width="8" stroke-linecap="round"/>
      <g class="handL"><path d="M16,73 L3,66" fill="none" stroke-width="7" stroke-linecap="round"/></g></g>
    <g class="armN"><path d="M74,53 L64,83" fill="none" stroke-width="9.5" stroke-linecap="round"/>
      <g class="handR"><path d="M64,83 L38,88" fill="none" stroke-width="8.5" stroke-linecap="round"/></g></g>`;
  return `<svg viewBox="0 0 100 120">
    <mask id="${mid}"><g fill="#fff" stroke="#fff" stroke-width="1">${body}</g></mask>
    <g fill="${g}" stroke="${err?'#ffd6dc':'#c9f4ff'}" stroke-width="1" stroke-opacity=".9">${body}</g>
    <rect x="-2" y="-2" width="104" height="124" fill="url(#grid)" mask="url(#${mid})" opacity=".8"/>
    <rect x="-2" y="-2" width="104" height="124" fill="url(#scanp)" mask="url(#${mid})"/>
  </svg>`;
}
function particles(n){
  let s='';for(let i=0;i<n;i++){s+=`<i style="--l:${20+Math.random()*60}%;--d:${(2.2+Math.random()*2).toFixed(1)}s;--dl:${(-Math.random()*4).toFixed(1)}s"></i>`}
  return `<div class="px">${s}</div>`;
}
function empHTML(m,dept,seatIdx){
  const [x,y,h,side,ll,lx]=SEATS[seatIdx]||SEATS[0];
  const cls=m.state==='run'?'on run':m.state==='ok'?'on':m.state==='error'?'err':'idle';
  const z=100-Math.round(y);   /* 手前ほど前面 */
  return `<div class="emp ${cls} ${side}" style="left:${x}%;top:${y}%;--h:${h}%;--ll:${ll}px;--lx:${lx}%;z-index:${z}">
    <div class="fig">${figure(m.state==='error')}</div>
    ${particles(6)}
    <div class="lb"><div class="nm">${short(m.name)}</div>
      <div class="st"><i></i>${LBL[m.state]||'STANDBY'}</div>
      <div class="tip"><b>${m.name}</b><br>${dept}<br>${m.role||''}<br>
        状態: ${LBLJ[m.state]||''} ／ 最終: ${m.last||'-'}<br>次回: ${m.next}</div></div>
  </div>`;
}
const isActive=s=>s==='ok'||s==='run'||s==='error';

async function tick(){
 try{
  const s=await(await fetch('/api/state',{cache:'no-store'})).json();
  const k=s.kpi||{};
  hemp.textContent=(k.resident||0)+'名'; hrun.textContent=(s.running_now||0)+'名';
  hact.textContent=(s.today_activity||0)+'件'; hclock.textContent=s.hhmm||'–';
  sclock.textContent=s.hhmm||'–';
  capN.textContent=(s.running_now||0)+'名';
  capSub.textContent=`本日 ${s.today_activity||0} 件の業務を完了`;

  const depts=s.depts||[];
  let html='',i=0;
  const leg=[];
  depts.forEach(d=>{
    const on=d.members.filter(m=>isActive(m.state)&&m.state!=='error').length;
    leg.push(`<span class="lg ${on?'lit':''}">${d.icon} ${d.dept}<b>${on}/${d.members.length}</b></span>`);
    d.members.forEach(m=>{html+=empHTML(m,d.dept,SEAT_ORDER[i]??i);i++;});
  });
  /* 差分が無ければDOMを触らない（アニメーションを途切れさせない） */
  const key=JSON.stringify(depts.map(d=>d.members.map(m=>[m.name,m.state,m.next,m.last])));
  if(tick.key!==key){document.getElementById('staff').innerHTML=html;tick.key=key;}
  legend.innerHTML=leg.join('');

  document.getElementById('kpis').innerHTML=[
   ['有効会員',(k.active||0)+'名'],['トライアル',(k.trial||0)+'名'],
   ['配信レポート',(k.reports||0)+'本'],['成功率',(k.success_rate||0)+'%'],
  ].map(([l,v])=>`<div class="kbox"><div class="l">${l}</div><div class="v">${v}</div></div>`).join('');

  const next=[];depts.forEach(d=>d.members.forEach(m=>next.push({who:d.dept,name:m.name,next:m.next,state:m.state})));
  document.getElementById('board').innerHTML=
   `<div class="sect">▸ 次の出社予定</div>`+
   next.slice(0,6).map(t=>`<div class="task"><span class="tg ${t.state==='error'?'r':'a'}">${t.who.slice(0,4)}</span>
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
        # 画像などの静的アセット（ディレクトリ直下のファイル名のみ許可）
        if self.path.startswith("/assets/") or self.path == "/bg.jpg":
            name = os.path.basename(self.path.split("?")[0]) if self.path != "/bg.jpg" else "office_bg.jpg"
            f = ASSET_DIR / name
            if f.is_file() and f.parent == ASSET_DIR:
                ctype = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                         "webp": "image/webp", "js": "text/javascript"}.get(f.suffix[1:].lower(), "application/octet-stream")
                body = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404); self.end_headers()
            return
        if self.path.startswith("/api/state"):
            with _lock:
                body = json.dumps(_state, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            # 画面は dashboard_assets/index.html を優先（ファイル編集だけで反映、再起動不要）。無ければ内蔵HTML
            page = ASSET_DIR / "index.html"
            body = page.read_bytes() if page.is_file() else INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    refresh()  # 起動時に一度同期収集
    threading.Thread(target=refresh_loop, daemon=True).start()
    print(f"🖥️  FBAトレンドレーダー LIVEダッシュボード: http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
