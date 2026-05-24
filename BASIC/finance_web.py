"""
╔══════════════════════════════════════════════════════════════╗
║   ExpenseFlow X — AI-Native Finance Platform (plan.md v2)  ║
╠══════════════════════════════════════════════════════════════╣
║  pip install flask pandas matplotlib openpyxl PyJWT numpy   ║
║  python finance_web.py  →  http://localhost:5000             ║
║  Set ANTHROPIC_API_KEY for full AI Copilot                   ║
╚══════════════════════════════════════════════════════════════╝
Implemented from plan.md:
  JWT auth + refresh tokens, PBKDF2 hashing, RBAC (user/admin)
  Financial Health Score (5 sub-scores → unified grade)
  AI Copilot via Claude API (rule-based fallback)
  Fraud Detection: z-score + IQR fence + duplicate check
  Subscription Intelligence, Goal-Based Planning
  Investment Tracker + P&L, Category Budgets
  Admin Portal + Audit Log, 4-chart analytics
"""
import sqlite3, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
import hashlib, uuid, csv, io, os, base64, json
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev
from functools import wraps
import jwt as pyjwt
from flask import Flask, request, jsonify, send_file, make_response, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","xfk_2025")
JWT_SECRET = os.environ.get("JWT_SECRET","xfk_jwt_2025")
JWT_ALGO = "HS256"; DB = "expenseflowx.db"

import traceback
@app.errorhandler(Exception)
def handle_exception(e):
    try:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"=== ERROR {datetime.now().isoformat()} ===\n")
            traceback.print_exc(file=f)
    except:
        pass
    return jsonify(ok=False, error=str(e)), 500


# ── DATABASE ────────────────────────────────────────────────
def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def init_db():
    with get_db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE NOT NULL,
            email TEXT,password TEXT NOT NULL,salt TEXT NOT NULL,role TEXT DEFAULT 'user',
            created TEXT NOT NULL,last_login TEXT);
        CREATE TABLE IF NOT EXISTS refresh_tokens(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS expenses(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            name TEXT NOT NULL,amount REAL NOT NULL,category TEXT NOT NULL,
            payment TEXT NOT NULL,date TEXT NOT NULL,note TEXT,is_fraud INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS subscriptions(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            name TEXT NOT NULL,amount REAL NOT NULL,cycle TEXT NOT NULL,next_due TEXT,active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS goals(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            name TEXT NOT NULL,target REAL NOT NULL,saved REAL DEFAULT 0,
            deadline TEXT,category TEXT,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS investments(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            name TEXT NOT NULL,type TEXT NOT NULL,amount REAL NOT NULL,
            units REAL,buy_price REAL,curr_price REAL,date TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS budgets(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            category TEXT NOT NULL,monthly REAL NOT NULL,month TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_logs(id TEXT PRIMARY KEY,user_id TEXT,
            action TEXT NOT NULL,detail TEXT,ip TEXT,ts TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS fraud_alerts(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,
            expense_id TEXT,reason TEXT NOT NULL,score REAL,ts TEXT NOT NULL,dismissed INTEGER DEFAULT 0);
        """)
init_db()


# ── AUTH ────────────────────────────────────────────────────
def hash_pw(pw,salt): return hashlib.pbkdf2_hmac("sha256",pw.encode(),salt.encode(),260000).hex()
def new_salt(): return uuid.uuid4().hex+uuid.uuid4().hex
def mk_access(uid,role):
    token = pyjwt.encode({"sub":uid,"role":role,
        "exp":datetime.now(timezone.utc)+timedelta(minutes=60),
        "jti":uuid.uuid4().hex},JWT_SECRET,algorithm=JWT_ALGO)
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token
def mk_refresh(uid):
    tok=uuid.uuid4().hex*2
    exp=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
    with get_db() as c: c.execute("INSERT INTO refresh_tokens (token,user_id,expires) VALUES(?,?,?)",(tok,uid,exp))
    return tok
def decode_tok(tok): return pyjwt.decode(tok,JWT_SECRET,algorithms=[JWT_ALGO])
def audit(uid,action,detail="",ip=""):
    with get_db() as c:
        c.execute("INSERT INTO audit_logs (id,user_id,action,detail,ip,ts) VALUES(?,?,?,?,?,?)",
                  (uuid.uuid4().hex[:8],uid,action,detail,ip,datetime.now().isoformat()))
def get_token():
    h=request.headers.get("Authorization","").replace("Bearer ","").strip()
    return h or request.cookies.get("access_token","")
def require_auth(f):
    @wraps(f)
    def wrap(*a,**kw):
        tok=get_token()
        if not tok: return jsonify(ok=False,error="Not authenticated"),401
        try:
            d=decode_tok(tok); g.user_id=d["sub"]; g.role=d.get("role","user")
        except pyjwt.ExpiredSignatureError: return jsonify(ok=False,error="Token expired"),401
        except: return jsonify(ok=False,error="Invalid token"),401
        return f(*a,**kw)
    return wrap
def require_admin(f):
    @wraps(f)
    @require_auth
    def wrap(*a,**kw):
        if g.role!="admin": return jsonify(ok=False,error="Admin only"),403
        return f(*a,**kw)
    return wrap


# ── FRAUD DETECTION ─────────────────────────────────────────
def run_fraud(uid,exp):
    alerts=[]
    with get_db() as c:
        rows=c.execute("SELECT amount,category FROM expenses WHERE user_id=? ORDER BY date DESC LIMIT 200",(uid,)).fetchall()
    if len(rows)<5: return []
    amounts=[r["amount"] for r in rows]; amt=exp["amount"]; cat=exp["category"]
    if len(amounts)>=10:
        mu=mean(amounts); sd=stdev(amounts) or 1; z=(amt-mu)/sd
        if z>3.5: alerts.append({"reason":f"Amount ₹{amt:,.0f} is {z:.1f}σ above normal","score":round(z,2)})
    s=sorted(amounts); q1,q3=s[len(s)//4],s[3*len(s)//4]; iqr=q3-q1
    if iqr>0 and amt>q3+3*iqr:
        alerts.append({"reason":f"Exceeds IQR fence (₹{q3+3*iqr:,.0f})","score":0.9})
    ca=[r["amount"] for r in rows if r["category"]==cat]
    if len(ca)>=3:
        cmu=mean(ca); csd=stdev(ca) or 1; zc=(amt-cmu)/csd
        if zc>3: alerts.append({"reason":f"Spike in {cat}: ₹{amt:,.0f} vs avg ₹{cmu:,.0f}","score":round(zc,2)})
    with get_db() as c:
        dup=c.execute("SELECT id FROM expenses WHERE user_id=? AND name=? AND amount=? AND date>=date('now','-3 days')",(uid,exp["name"],amt)).fetchone()
    if dup: alerts.append({"reason":"Possible duplicate within 3 days","score":0.8})
    return alerts

def store_fraud(uid,eid,alerts):
    with get_db() as c:
        for a in alerts:
            c.execute("INSERT INTO fraud_alerts (id,user_id,expense_id,reason,score,ts,dismissed) VALUES(?,?,?,?,?,?,0)",
                      (uuid.uuid4().hex[:8],uid,eid,a["reason"],a.get("score",0),datetime.now().isoformat()))


# ── HEALTH SCORE ────────────────────────────────────────────
def health_score(uid):
    with get_db() as c:
        exps=c.execute("SELECT amount,date,category FROM expenses WHERE user_id=?",(uid,)).fetchall()
        budgs=c.execute("SELECT category,monthly FROM budgets WHERE user_id=?",(uid,)).fetchall()
        gls=c.execute("SELECT name,target,saved FROM goals WHERE user_id=?",(uid,)).fetchall()
        invs=c.execute("SELECT amount FROM investments WHERE user_id=?",(uid,)).fetchall()
    sc={}
    if len(exps)>=5:
        a=[e["amount"] for e in exps]; cv=(stdev(a)/mean(a)) if mean(a) else 1
        sc["savings_stability"]=max(0,min(100,round(100-cv*40)))
    else: sc["savings_stability"]=50
    if budgs and exps:
        cs={}
        for e in exps: cs[e["category"]]=cs.get(e["category"],0)+e["amount"]
        ok=sum(1 for b in budgs if cs.get(b["category"],0)<=b["monthly"])
        sc["budget_consistency"]=round(ok/len(budgs)*100)
    else: sc["budget_consistency"]=50
    if exps:
        mo={}
        for e in exps: mo[e["date"][:7]]=mo.get(e["date"][:7],0)+e["amount"]
        risky=sum(1 for v in mo.values() if v>80000)
        sc["debt_risk"]=round(max(0,100-risky/len(mo)*100))
    else: sc["debt_risk"]=70
    ti=sum(i["amount"] for i in invs); ts=sum(e["amount"] for e in exps) or 1
    sc["investment_readiness"]=min(100,round(ti/ts*200))
    ef=[g for g in gls if "emergency" in g["name"].lower()]
    sc["emergency_fund"]=round(min(ef[0]["saved"]/ef[0]["target"],1)*100) if ef and ef[0]["target"] else 20
    w={"savings_stability":.25,"budget_consistency":.20,"debt_risk":.25,"investment_readiness":.15,"emergency_fund":.15}
    ov=round(sum(sc[k]*w[k] for k in sc))
    gr=("A+" if ov>=90 else "A" if ov>=80 else "B+" if ov>=70 else "B" if ov>=60 else "C" if ov>=50 else "D")
    lb={"savings_stability":"Savings Stability","budget_consistency":"Budget Consistency",
        "debt_risk":"Debt Risk Score","investment_readiness":"Investment Readiness","emergency_fund":"Emergency Fund"}
    return {"overall":ov,"grade":gr,"scores":sc,"labels":lb}


# ── CHARTS ──────────────────────────────────────────────────
BG="#080c10"; SURF="#0e1420"; FG="#e2eaf5"; MUT="#5a7090"
COLS=["#00d4ff","#ff6b35","#00e5a0","#ffd166","#c77dff","#ff4d6d","#4cc9f0","#f77f00","#06ffa5","#ffbe0b"]
def fig64(fig):
    buf=io.BytesIO(); fig.savefig(buf,format="png",bbox_inches="tight",facecolor=fig.get_facecolor(),dpi=110)
    buf.seek(0); enc=base64.b64encode(buf.read()).decode(); plt.close(fig)
    return "data:image/png;base64,"+enc
def chart_pie(cs):
    fig,ax=plt.subplots(figsize=(5,5),facecolor=BG); ax.set_facecolor(BG)
    lbs=list(cs.keys()); vs=list(cs.values())
    w,texts,au=ax.pie(vs,labels=lbs,autopct="%1.1f%%",colors=COLS[:len(vs)],pctdistance=0.82,wedgeprops=dict(width=0.55,edgecolor=BG,linewidth=2))
    for t in texts: t.set_color(FG); t.set_fontsize(8)
    for a in au: a.set_color("#000"); a.set_fontsize(7); a.set_fontweight("bold")
    ax.set_title("Category Breakdown",color=FG,fontsize=11,pad=8); return fig64(fig)
def chart_line(rows):
    mo={}
    for r in rows:
        try: m=datetime.strptime(r["date"],"%Y-%m-%d").strftime("%b %y")
        except: m="?"
        mo[m]=mo.get(m,0)+r["amount"]
    fig,ax=plt.subplots(figsize=(7,4),facecolor=BG); ax.set_facecolor(SURF)
    lbs=list(mo.keys()); vs=list(mo.values())
    ax.plot(lbs,vs,color="#00d4ff",lw=2.5,marker="o",markersize=7,markerfacecolor="#ff6b35",markeredgecolor=BG,markeredgewidth=2)
    ax.fill_between(range(len(lbs)),vs,alpha=0.10,color="#00d4ff")
    ax.set_xticks(range(len(lbs))); ax.set_xticklabels(lbs,rotation=28,ha="right",color=FG,fontsize=8)
    ax.tick_params(axis="y",colors=FG,labelsize=8)
    for sp in ax.spines.values(): sp.set_color("#1e2d42")
    ax.set_title("Monthly Trend",color=FG,fontsize=11,pad=8); ax.set_ylabel("₹",color=FG,fontsize=9)
    fig.patch.set_facecolor(BG); return fig64(fig)
def chart_radar(scores,labels):
    cats=list(labels.values()); vals=[scores[k] for k in labels]; N=len(cats)
    angles=[n/N*2*np.pi for n in range(N)]+[0]; vals_=vals+[vals[0]]
    fig,ax=plt.subplots(figsize=(5,5),subplot_kw=dict(polar=True),facecolor=BG); ax.set_facecolor(BG)
    ax.plot(angles,vals_,color="#00d4ff",lw=2); ax.fill(angles,vals_,color="#00d4ff",alpha=0.15)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats,color=FG,fontsize=8)
    ax.set_ylim(0,100); ax.set_yticks([20,40,60,80,100])
    ax.set_yticklabels(["20","40","60","80","100"],color=MUT,fontsize=6)
    ax.spines["polar"].set_color("#1e2d42"); ax.grid(color="#1e2d42",linewidth=0.8)
    ax.set_title("Health Radar",color=FG,fontsize=11,pad=14); fig.patch.set_facecolor(BG); return fig64(fig)
def chart_invest(rows):
    if not rows: return ""
    bt={}
    for r in rows: bt[r["type"]]=bt.get(r["type"],0)+r["amount"]
    fig,ax=plt.subplots(figsize=(6,3.5),facecolor=BG); ax.set_facecolor(SURF)
    ax.bar(list(bt.keys()),list(bt.values()),color=COLS[:len(bt)],edgecolor=BG,linewidth=1.5)
    for sp in ax.spines.values(): sp.set_color("#1e2d42")
    ax.tick_params(colors=FG,labelsize=9); ax.set_title("Investments by Type",color=FG,fontsize=11,pad=8)
    ax.set_ylabel("₹",color=FG,fontsize=9); fig.patch.set_facecolor(BG); return fig64(fig)


# ── AI COPILOT ───────────────────────────────────────────────
def fin_ctx(uid):
    with get_db() as c:
        exps=c.execute("SELECT amount,category FROM expenses WHERE user_id=? LIMIT 60",(uid,)).fetchall()
        gls=c.execute("SELECT name,target,saved FROM goals WHERE user_id=?",(uid,)).fetchall()
        invs=c.execute("SELECT type,amount FROM investments WHERE user_id=?",(uid,)).fetchall()
        subs=c.execute("SELECT name,amount,cycle FROM subscriptions WHERE user_id=? AND active=1",(uid,)).fetchall()
    total=sum(e["amount"] for e in exps); cs={}
    for e in exps: cs[e["category"]]=cs.get(e["category"],0)+e["amount"]
    return (f"Total: ₹{total:,.0f}\nCategories: {json.dumps({k:round(v) for k,v in cs.items()})}\n"
            f"Subs: {[dict(s) for s in subs]}\nInvests: {[dict(i) for i in invs]}\nGoals: {[dict(g) for g in gls]}")

def copilot_fallback(uid,q):
    with get_db() as c:
        rows=c.execute("SELECT amount,category FROM expenses WHERE user_id=?",(uid,)).fetchall()
    if not rows: return "No data yet. Add expenses first."
    total=sum(r["amount"] for r in rows); cs={}
    for r in rows: cs[r["category"]]=cs.get(r["category"],0)+r["amount"]
    top=max(cs,key=cs.get)
    return (f"**Your Summary:**\n\u2022 Total: ₹{total:,.0f} ({len(rows)} txns)\n"
            f"\u2022 Top: **{top}** ({cs[top]/total*100:.1f}%)\n"
            f"\u2022 Avg: \u20b9{mean([r['amount'] for r in rows]):,.0f}\n\n"
            f"*Set ANTHROPIC_API_KEY for full Claude AI.*")


# ── HTML UI ─────────────────────────────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ExpenseFlow X</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#080c10;--surface:#0e1420;--card:#131c2b;--border:#1e2d42;
  --accent:#00d4ff;--accent2:#ff6b35;--green:#00e5a0;--red:#ff4d6d;
  --yellow:#ffd166;--purple:#c77dff;--text:#e2eaf5;--muted:#5a7090;
  --ui:'Syne',sans-serif;--mono:'Space Mono',monospace;--r:10px}
body{background:var(--bg);color:var(--text);font-family:var(--ui);min-height:100vh}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
#auth-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:radial-gradient(ellipse 60% 50% at 30% 20%,rgba(0,212,255,.08) 0%,transparent 70%),
  radial-gradient(ellipse 50% 40% at 80% 80%,rgba(255,107,53,.07) 0%,transparent 70%),var(--bg)}
.auth-box{width:420px;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:40px;animation:fadeUp .5s ease}
.auth-logo{font-size:11px;letter-spacing:4px;color:var(--accent);font-family:var(--mono);margin-bottom:6px}
.auth-title{font-size:26px;font-weight:800;margin-bottom:28px;line-height:1.1}
.auth-tabs{display:flex;gap:8px;margin-bottom:24px}
.tab-btn{flex:1;padding:9px;border:1px solid var(--border);background:transparent;color:var(--muted);
  border-radius:var(--r);cursor:pointer;font-family:var(--ui);font-size:12px;font-weight:700;
  letter-spacing:1px;text-transform:uppercase;transition:all .2s}
.tab-btn.active{background:var(--accent);color:#000;border-color:var(--accent)}
.fg{margin-bottom:14px}
.fg label{display:block;font-size:10px;letter-spacing:2px;text-transform:uppercase;
  color:var(--muted);margin-bottom:5px;font-family:var(--mono)}
.fg input,.fg select,.fg textarea{width:100%;padding:11px 13px;background:var(--surface);
  border:1px solid var(--border);color:var(--text);border-radius:var(--r);
  font-family:var(--mono);font-size:13px;outline:none;transition:border-color .2s}
.fg textarea{resize:vertical;min-height:70px}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--accent)}
.btn{display:inline-flex;align-items:center;gap:7px;padding:11px 22px;border:none;border-radius:var(--r);
  cursor:pointer;font-family:var(--ui);font-size:12px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;transition:all .2s}
.btn-p{background:var(--accent);color:#000;width:100%;justify-content:center}.btn-p:hover{background:#33ddff;transform:translateY(-1px)}
.btn-d{background:rgba(255,77,109,.15);color:var(--red);border:1px solid rgba(255,77,109,.3)}.btn-d:hover{background:rgba(255,77,109,.25)}
.btn-o{background:transparent;color:var(--accent);border:1px solid var(--accent)}.btn-o:hover{background:rgba(0,212,255,.1)}
.btn-g{background:transparent;color:var(--muted);border:1px solid var(--border)}.btn-g:hover{color:var(--text);border-color:var(--text)}
.btn-s{background:rgba(0,229,160,.15);color:var(--green);border:1px solid rgba(0,229,160,.3)}.btn-s:hover{background:rgba(0,229,160,.25)}
.btn-sm{padding:6px 13px;font-size:10px}
.msg{font-size:12px;padding:9px 13px;border-radius:var(--r);margin-top:10px;font-family:var(--mono)}
.msg-ok{background:rgba(0,229,160,.12);color:var(--green);border:1px solid rgba(0,229,160,.2)}
.msg-err{background:rgba(255,77,109,.12);color:var(--red);border:1px solid rgba(255,77,109,.2)}
#app-shell{display:none}
.topbar{height:54px;background:var(--surface);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 22px;gap:14px;position:sticky;top:0;z-index:100}
.tl{font-family:var(--mono);font-size:11px;letter-spacing:3px;color:var(--accent);font-weight:700}
.tu{margin-left:auto;font-size:11px;color:var(--muted);font-family:var(--mono)}
.tu span{color:var(--text)}
.layout{display:flex;min-height:calc(100vh - 54px)}
.sidebar{width:215px;background:var(--surface);border-right:1px solid var(--border);padding:18px 10px;flex-shrink:0}
.ni{display:flex;align-items:center;gap:9px;padding:9px 13px;border-radius:var(--r);cursor:pointer;
  font-size:12px;font-weight:600;color:var(--muted);transition:all .2s;margin-bottom:3px;border:1px solid transparent}
.ni:hover{color:var(--text);background:var(--card)}
.ni.active{color:var(--accent);background:rgba(0,212,255,.08);border-color:rgba(0,212,255,.2)}
.ni-ic{font-size:14px;width:18px;text-align:center}
.ns{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin:14px 13px 7px;font-family:var(--mono)}
.nbadge{margin-left:auto;background:var(--red);color:#fff;font-size:9px;padding:1px 6px;border-radius:100px;font-family:var(--mono)}
.main{flex:1;padding:26px;overflow-y:auto}
.page{display:none;animation:fadeUp .3s ease}.page.active{display:block}
.ph{margin-bottom:24px;display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px}
.ph h1{font-size:24px;font-weight:800}.ph p{color:var(--muted);font-size:12px;margin-top:3px;font-family:var(--mono)}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:14px;margin-bottom:22px}
.sc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:18px}
.sl{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);font-family:var(--mono);margin-bottom:7px}
.sv{font-size:26px;font-weight:800}.ss{font-size:10px;color:var(--muted);margin-top:3px;font-family:var(--mono)}
.ca{color:var(--accent)}.cg{color:var(--green)}.cr{color:var(--red)}.cy{color:var(--yellow)}.cp{color:var(--purple)}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:22px;margin-bottom:18px}
.ct{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:16px;font-family:var(--mono)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.three{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
@media(max-width:800px){.two,.three{grid-template-columns:1fr}}
.fgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.fgrid .full{grid-column:1/-1}
@media(max-width:640px){.fgrid{grid-template-columns:1fr}}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
thead tr{border-bottom:2px solid var(--border)}
thead th{padding:9px 13px;text-align:left;font-family:var(--mono);font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}
tbody tr{border-bottom:1px solid var(--border);transition:background .15s}
tbody tr:hover{background:rgba(255,255,255,.02)}
tbody td{padding:11px 13px}
.badge{display:inline-block;padding:2px 9px;border-radius:100px;font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;font-family:var(--mono)}
.bc{background:rgba(0,212,255,.12);color:var(--accent)}.bp{background:rgba(255,209,102,.12);color:var(--yellow)}
.bw{background:rgba(255,77,109,.15);color:var(--red)}.bok{background:rgba(0,229,160,.12);color:var(--green)}
.bad{background:rgba(199,125,255,.15);color:var(--purple)}.amc{font-family:var(--mono);font-weight:700}
.fr-row{background:rgba(255,77,109,.05)!important}
.chat-wrap{display:flex;flex-direction:column;height:400px}
.chat-msgs{flex:1;overflow-y:auto;padding:12px;background:var(--surface);border-radius:var(--r);
  border:1px solid var(--border);margin-bottom:12px;display:flex;flex-direction:column;gap:10px}
.cm{max-width:80%;padding:10px 14px;border-radius:10px;font-size:13px;line-height:1.5}
.cm.user{align-self:flex-end;background:rgba(0,212,255,.12);border:1px solid rgba(0,212,255,.2)}
.cm.ai{align-self:flex-start;background:var(--card);border:1px solid var(--border)}
.cm.ai .ail{font-size:9px;letter-spacing:2px;color:var(--accent);font-family:var(--mono);margin-bottom:4px}
.cir{display:flex;gap:10px}
.cir input{flex:1;padding:11px 13px;background:var(--surface);border:1px solid var(--border);
  color:var(--text);border-radius:var(--r);font-family:var(--mono);font-size:13px;outline:none}
.cir input:focus{border-color:var(--accent)}
.csend{padding:11px 18px;background:var(--accent);color:#000;border:none;border-radius:var(--r);cursor:pointer;font-weight:700;font-family:var(--ui);font-size:12px}
.typing{color:var(--muted);font-size:12px;font-family:var(--mono);padding:6px 0}
.hr-num{font-size:52px;font-weight:800;line-height:1}
.hr-grade{font-size:14px;color:var(--muted);font-family:var(--mono)}
.sr{display:flex;align-items:center;gap:10px;margin-bottom:10px;font-size:12px}
.sb-w{flex:1;height:7px;background:var(--surface);border-radius:100px;overflow:hidden}
.sb{height:100%;border-radius:100px;transition:width .7s ease}
.sv2{width:30px;text-align:right;font-family:var(--mono);font-size:11px}
.pw{background:var(--surface);border-radius:100px;height:9px;overflow:hidden;margin:7px 0}
.pb{height:100%;border-radius:100px;transition:width .6s ease}
.fa{background:rgba(255,77,109,.08);border:1px solid rgba(255,77,109,.2);border-radius:var(--r);padding:14px 16px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start}
.fa-ic{font-size:20px;flex-shrink:0}.fa-l{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--red);font-family:var(--mono);margin-bottom:3px}
.gc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:18px;position:relative}
.gp{position:absolute;top:16px;right:16px;font-size:20px;font-weight:800;color:var(--accent);font-family:var(--mono)}
.ip{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:100px;font-size:11px;font-family:var(--mono);font-weight:700}
.ipos{background:rgba(0,229,160,.12);color:var(--green)}.ineg{background:rgba(255,77,109,.12);color:var(--red)}
.empty{text-align:center;padding:50px 20px;color:var(--muted);font-family:var(--mono);font-size:12px}
.ei{font-size:36px;margin-bottom:10px}
#toast{position:fixed;bottom:22px;right:22px;padding:13px 18px;border-radius:var(--r);
  font-family:var(--mono);font-size:12px;transition:all .3s;opacity:0;pointer-events:none;z-index:9999;transform:translateY(10px)}
#toast.show{opacity:1;transform:translateY(0)}
#toast.ok{background:rgba(0,229,160,.15);color:var(--green);border:1px solid rgba(0,229,160,.3)}
#toast.err{background:rgba(255,77,109,.15);color:var(--red);border:1px solid rgba(255,77,109,.3)}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div id="auth-screen">
  <div class="auth-box">
    <div class="auth-logo">ExpenseFlow X</div>
    <h1 class="auth-title">AI-Native Finance<br/>Intelligence Platform</h1>
    <div class="auth-tabs">
      <button class="tab-btn active" onclick="switchTab('login')">Login</button>
      <button class="tab-btn" onclick="switchTab('register')">Register</button>
    </div>
    <div id="form-login">
      <div class="fg"><label>Username</label><input id="l-u" placeholder="username"/></div>
      <div class="fg"><label>Password</label><input id="l-p" type="password" placeholder="••••••••"/></div>
      <button class="btn btn-p" onclick="doLogin()">Sign In →</button>
      <div id="lmsg"></div>
    </div>
    <div id="form-register" style="display:none">
      <div class="fg"><label>Username</label><input id="r-u" placeholder="username"/></div>
      <div class="fg"><label>Email</label><input id="r-e" placeholder="optional"/></div>
      <div class="fg"><label>Password</label><input id="r-p" type="password" placeholder="min 8 chars"/></div>
      <button class="btn btn-p" onclick="doRegister()">Create Account →</button>
      <div id="rmsg"></div>
    </div>
  </div>
</div>

<div id="app-shell">
  <div class="topbar">
    <div class="tl">◈ ExpenseFlow X</div>
    <div style="display:flex;align-items:center;gap:10px;margin-left:auto">
      <div class="tu">Signed in as <span id="tname">—</span></div>
      <span id="trole" class="badge" style="display:none"></span>
      <button class="btn btn-o btn-sm" onclick="doLogout()">Logout</button>
    </div>
  </div>
  <div class="layout">
    <aside class="sidebar">
      <div class="ns">Main</div>
      <div class="ni active" onclick="nav('dashboard',this)"><span class="ni-ic">⬡</span>Dashboard</div>
      <div class="ni" onclick="nav('add',this)"><span class="ni-ic">＋</span>Add Expense</div>
      <div class="ni" onclick="nav('expenses',this)"><span class="ni-ic">≡</span>All Expenses</div>
      <div class="ns">AI & Analytics</div>
      <div class="ni" onclick="nav('copilot',this)"><span class="ni-ic">◉</span>AI Copilot</div>
      <div class="ni" onclick="nav('health',this)"><span class="ni-ic">♥</span>Health Score</div>
      <div class="ni" onclick="nav('charts',this)"><span class="ni-ic">◈</span>Charts</div>
      <div class="ns">Finance</div>
      <div class="ni" onclick="nav('budget',this)"><span class="ni-ic">◎</span>Budget</div>
      <div class="ni" onclick="nav('goals',this)"><span class="ni-ic">◇</span>Goals</div>
      <div class="ni" onclick="nav('subs',this)"><span class="ni-ic">↺</span>Subscriptions</div>
      <div class="ni" onclick="nav('invest',this)"><span class="ni-ic">△</span>Investments</div>
      <div class="ns">Security</div>
      <div class="ni" onclick="nav('fraud',this)"><span class="ni-ic">⚠</span>Fraud Alerts<span id="fbadge" class="nbadge" style="display:none">0</span></div>
      <div class="ns">Export</div>
      <div class="ni" onclick="exportFile('csv')"><span class="ni-ic">↓</span>Export CSV</div>
      <div class="ni" onclick="exportFile('excel')"><span class="ni-ic">↓</span>Export Excel</div>
      <div class="ns" id="adm-ns" style="display:none">Admin</div>
      <div class="ni" id="adm-ni" style="display:none" onclick="nav('admin',this)"><span class="ni-ic">◆</span>Admin Portal</div>
    </aside>
    <main class="main">

      <div class="page active" id="page-dashboard">
        <div class="ph"><div><h1>Dashboard</h1><p id="ddate">—</p></div></div>
        <div class="sg" id="sg"></div>
        <div class="two">
          <div class="card"><div class="ct">Spending by Category</div><div id="dcats"></div></div>
          <div class="card"><div class="ct">Recent Transactions</div><div id="drec"></div></div>
        </div>
      </div>

      <div class="page" id="page-add">
        <div class="ph"><div><h1>Add Expense</h1><p>Record a transaction</p></div></div>
        <div class="card">
          <div class="fgrid">
            <div class="fg full"><label>Expense Name</label><input id="e-name" placeholder="e.g. Netflix"/></div>
            <div class="fg"><label>Amount (₹)</label><input id="e-amt" type="number" placeholder="0"/></div>
            <div class="fg"><label>Date</label><input id="e-date" type="date"/></div>
            <div class="fg"><label>Category</label><select id="e-cat"><option value="">Select</option>
              <option>Food & Dining</option><option>Transport</option><option>Shopping</option>
              <option>Entertainment</option><option>Utilities</option><option>Healthcare</option>
              <option>Education</option><option>Travel</option><option>Subscriptions</option><option>Other</option>
            </select></div>
            <div class="fg"><label>Payment</label><select id="e-pay"><option value="">Select</option>
              <option>UPI</option><option>Cash</option><option>Credit Card</option>
              <option>Debit Card</option><option>Net Banking</option>
            </select></div>
            <div class="fg full"><label>Note</label><input id="e-note" placeholder="Optional details"/></div>
            <div class="fg full"><button class="btn btn-p" onclick="addExpense()">Add Expense →</button></div>
          </div>
        </div>
        <div id="fwarn"></div>
      </div>

      <div class="page" id="page-expenses">
        <div class="ph">
          <div><h1>All Expenses</h1><p>Full transaction history</p></div>
          <input id="fsearch" placeholder="Search…" style="padding:8px 12px;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:var(--r);font-family:var(--mono);font-size:12px;outline:none" oninput="filterExp()"/>
        </div>
        <div class="card"><div class="tw">
          <table><thead><tr><th>ID</th><th>Name</th><th>Amount</th><th>Category</th><th>Payment</th><th>Date</th><th>Note</th><th></th></tr></thead>
          <tbody id="etbody"></tbody></table>
        </div><div id="eempty" class="empty" style="display:none"><div class="ei">◌</div>No expenses yet.</div></div>
      </div>

      <div class="page" id="page-copilot">
        <div class="ph"><div><h1>AI Copilot</h1><p>Your personal financial intelligence</p></div></div>
        <div class="card">
          <div class="ct">◉ ExpenseFlow AI</div>
          <div class="chat-wrap">
            <div class="chat-msgs" id="chatmsgs">
              <div class="cm ai"><div class="ail">EXPENSEFLOW AI</div>Hello! I have full context of your spending, goals, investments and subscriptions. Ask me anything — "Can I afford a ₹50k laptop?", "Where am I overspending?", "How should I cut costs?"</div>
            </div>
            <div class="cir">
              <input id="cinput" placeholder="Ask your AI copilot…" onkeydown="if(event.key==='Enter')sendChat()"/>
              <button class="csend" onclick="sendChat()">→</button>
            </div>
          </div>
        </div>
        <div class="card"><div class="ct">Quick Prompts</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            <button class="btn btn-g btn-sm" onclick="qc('Where am I overspending?')">Overspending?</button>
            <button class="btn btn-g btn-sm" onclick="qc('Suggest ways to reduce monthly expenses')">Cut expenses</button>
            <button class="btn btn-g btn-sm" onclick="qc('Am I on track with savings goals?')">Savings check</button>
            <button class="btn btn-g btn-sm" onclick="qc('Analyse my subscription spending')">Subscriptions</button>
            <button class="btn btn-g btn-sm" onclick="qc('Give me a 3-month budget plan')">Budget plan</button>
          </div>
        </div>
      </div>

      <div class="page" id="page-health">
        <div class="ph"><div><h1>Financial Health Score</h1><p>AI-weighted composite across 5 dimensions</p></div></div>
        <div id="hcontent"></div>
      </div>

      <div class="page" id="page-charts">
        <div class="ph"><div><h1>Charts</h1><p>Visual analytics</p></div></div>
        <div class="two"><div class="card"><div class="ct">Category Distribution</div><img id="cpie" style="max-width:100%;border-radius:var(--r)"/></div>
        <div class="card"><div class="ct">Monthly Trend</div><img id="cline" style="max-width:100%;border-radius:var(--r)"/></div></div>
        <div class="two"><div class="card"><div class="ct">Health Radar</div><img id="cradar" style="max-width:100%;border-radius:var(--r)"/></div>
        <div class="card"><div class="ct">Investments by Type</div><img id="cinvest" style="max-width:100%;border-radius:var(--r)"/></div></div>
      </div>

      <div class="page" id="page-budget">
        <div class="ph"><div><h1>Budget Manager</h1><p>Category-wise monthly limits</p></div>
          <button class="btn btn-o btn-sm" onclick="tog('bform')">+ Set Budget</button></div>
        <div id="bform" style="display:none" class="card"><div class="ct">Set Monthly Budget</div>
          <div class="fgrid">
            <div class="fg"><label>Category</label><select id="b-cat"><option value="">Select</option>
              <option>Food & Dining</option><option>Transport</option><option>Shopping</option>
              <option>Entertainment</option><option>Utilities</option><option>Healthcare</option>
              <option>Education</option><option>Travel</option><option>Subscriptions</option><option>Other</option>
            </select></div>
            <div class="fg"><label>Monthly Limit (₹)</label><input id="b-amt" type="number" placeholder="0"/></div>
            <div class="fg full"><button class="btn btn-p" onclick="saveBudget()">Save →</button></div>
          </div>
        </div>
        <div id="boverview"></div>
      </div>

      <div class="page" id="page-goals">
        <div class="ph"><div><h1>Financial Goals</h1><p>Goal-based financial planning</p></div>
          <button class="btn btn-o btn-sm" onclick="tog('gform')">+ New Goal</button></div>
        <div id="gform" style="display:none" class="card"><div class="fgrid">
          <div class="fg"><label>Goal Name</label><input id="g-name" placeholder="Emergency Fund"/></div>
          <div class="fg"><label>Target (₹)</label><input id="g-tgt" type="number" placeholder="0"/></div>
          <div class="fg"><label>Saved So Far (₹)</label><input id="g-saved" type="number" placeholder="0"/></div>
          <div class="fg"><label>Deadline</label><input id="g-dl" type="date"/></div>
          <div class="fg"><label>Category</label><select id="g-cat"><option>Emergency Fund</option><option>Travel</option><option>Gadget</option><option>Vehicle</option><option>Education</option><option>Retirement</option><option>Other</option></select></div>
          <div class="fg full"><button class="btn btn-p" onclick="saveGoal()">Create Goal →</button></div>
        </div></div>
        <div id="ggrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px"></div>
        <div id="gempty" class="empty" style="display:none"><div class="ei">◇</div>No goals set.</div>
      </div>

      <div class="page" id="page-subs">
        <div class="ph"><div><h1>Subscription Intelligence</h1><p>Track recurring payments</p></div>
          <button class="btn btn-o btn-sm" onclick="tog('sform')">+ Add</button></div>
        <div id="sform" style="display:none" class="card"><div class="fgrid">
          <div class="fg"><label>Service Name</label><input id="s-name" placeholder="Netflix"/></div>
          <div class="fg"><label>Amount (₹)</label><input id="s-amt" type="number" placeholder="0"/></div>
          <div class="fg"><label>Billing Cycle</label><select id="s-cyc"><option>Monthly</option><option>Quarterly</option><option>Annual</option></select></div>
          <div class="fg"><label>Next Due</label><input id="s-due" type="date"/></div>
          <div class="fg full"><button class="btn btn-p" onclick="saveSub()">Add →</button></div>
        </div></div>
        <div id="scontent"></div>
      </div>

      <div class="page" id="page-invest">
        <div class="ph"><div><h1>Investment Tracker</h1><p>Stocks, MF, Crypto, SIP, ETF</p></div>
          <button class="btn btn-o btn-sm" onclick="tog('iform')">+ Add</button></div>
        <div id="iform" style="display:none" class="card"><div class="fgrid">
          <div class="fg"><label>Asset Name</label><input id="i-name" placeholder="NIFTY 50 ETF"/></div>
          <div class="fg"><label>Type</label><select id="i-type"><option>Mutual Fund</option><option>Stock</option><option>Crypto</option><option>SIP</option><option>ETF</option><option>Fixed Deposit</option><option>Gold</option><option>Other</option></select></div>
          <div class="fg"><label>Amount Invested (₹)</label><input id="i-amt" type="number" placeholder="0"/></div>
          <div class="fg"><label>Current Value (₹)</label><input id="i-curr" type="number" placeholder="0"/></div>
          <div class="fg"><label>Units</label><input id="i-units" type="number" placeholder="optional"/></div>
          <div class="fg"><label>Date</label><input id="i-date" type="date"/></div>
          <div class="fg full"><button class="btn btn-p" onclick="saveInvest()">Add Investment →</button></div>
        </div></div>
        <div class="sg" id="isum" style="margin-bottom:18px"></div>
        <div class="card"><div class="tw">
          <table><thead><tr><th>Asset</th><th>Type</th><th>Invested</th><th>Current</th><th>P&L</th><th>Date</th><th></th></tr></thead>
          <tbody id="itbody"></tbody></table>
        </div><div id="iempty" class="empty" style="display:none"><div class="ei">△</div>No investments tracked.</div></div>
      </div>

      <div class="page" id="page-fraud">
        <div class="ph"><div><h1>Fraud Detection</h1><p>Statistical anomaly alerts</p></div></div>
        <div id="fraud-content"></div>
      </div>

      <div class="page" id="page-admin">
        <div class="ph"><div><h1>Admin Portal</h1><p>Platform metrics & management</p></div></div>
        <div id="adm-content"></div>
      </div>

    </main>
  </div>
</div>
<div id="toast"></div>
<script>
let AT=localStorage.getItem('at')||'',RT=localStorage.getItem('rt')||'',CU=null,CR=null,AE=[];
function toast(m,t='ok'){const el=document.getElementById('toast');el.textContent=m;el.className='show '+t;clearTimeout(el._t);el._t=setTimeout(()=>el.className='',3200)}
async function api(path,data=null,method=null){
  const o={headers:{'Content-Type':'application/json','Authorization':'Bearer '+AT}};
  if(data||method){o.method=method||'POST';if(data)o.body=JSON.stringify(data)}
  const r=await fetch(path,o),j=await r.json();
  if(j.error==='Token expired'){const ok=await doRefresh();if(ok){o.headers['Authorization']='Bearer '+AT;const r2=await fetch(path,o);return r2.json()}}
  return j}
async function doRefresh(){if(!RT)return false;const r=await fetch('/api/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:RT})});const j=await r.json();if(j.access_token){AT=j.access_token;localStorage.setItem('at',AT);return true}return false}
function switchTab(t){document.getElementById('form-login').style.display=t==='login'?'':'none';document.getElementById('form-register').style.display=t==='register'?'':'none';document.querySelectorAll('.tab-btn').forEach((b,i)=>b.classList.toggle('active',(i===0&&t==='login')||(i===1&&t==='register')))}
async function doLogin(){const u=document.getElementById('l-u').value.trim(),p=document.getElementById('l-p').value;const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})}).then(x=>x.json());const el=document.getElementById('lmsg');if(r.ok){AT=r.access_token;RT=r.refresh_token;localStorage.setItem('at',AT);localStorage.setItem('rt',RT);el.innerHTML='';enterApp(u,r.role)}else el.innerHTML=`<div class="msg msg-err">${r.error}</div>`}
async function doRegister(){const u=document.getElementById('r-u').value.trim(),e=document.getElementById('r-e').value.trim(),p=document.getElementById('r-p').value;const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})}).then(x=>x.json());const el=document.getElementById('rmsg');if(r.ok){el.innerHTML='<div class="msg msg-ok">Account created! Please login.</div>';setTimeout(()=>switchTab('login'),1500)}else el.innerHTML=`<div class="msg msg-err">${r.error}</div>`}
async function doLogout(){await api('/api/logout',{});localStorage.removeItem('at');localStorage.removeItem('rt');AT='';CU=null;document.getElementById('auth-screen').style.display='flex';document.getElementById('app-shell').style.display='none'}
function enterApp(u,role){CU=u;CR=role;document.getElementById('auth-screen').style.display='none';document.getElementById('app-shell').style.display='block';document.getElementById('tname').textContent=u;document.getElementById('e-date').value=new Date().toISOString().split('T')[0];document.getElementById('i-date').value=new Date().toISOString().split('T')[0];if(role==='admin'){const rb=document.getElementById('trole');rb.textContent='ADMIN';rb.className='badge bad';rb.style.display='';document.getElementById('adm-ns').style.display='';document.getElementById('adm-ni').style.display=''}loadDash();loadFraudBadge()}
function nav(id,el){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.ni').forEach(n=>n.classList.remove('active'));document.getElementById('page-'+id).classList.add('active');el.classList.add('active');const loaders={dashboard:loadDash,expenses:loadExp,health:loadHealth,charts:loadCharts,budget:loadBudget,goals:loadGoals,subs:loadSubs,invest:loadInvest,fraud:loadFraud,admin:loadAdmin};if(loaders[id])loaders[id]()}
function tog(id){const el=document.getElementById(id);el.style.display=el.style.display==='none'?'':'none'}

async function loadDash(){
  document.getElementById('ddate').textContent=new Date().toLocaleDateString('en-IN',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  const r=await api('/api/stats');
  document.getElementById('sg').innerHTML=`
    <div class="sc"><div class="sl">Total Spent</div><div class="sv ca">₹${r.total.toLocaleString('en-IN')}</div><div class="ss">${r.count} transactions</div></div>
    <div class="sc"><div class="sl">This Month</div><div class="sv cg">₹${r.this_month.toLocaleString('en-IN')}</div><div class="ss">${new Date().toLocaleString('en-IN',{month:'long'})}</div></div>
    <div class="sc"><div class="sl">Avg Transaction</div><div class="sv cy">₹${r.avg.toLocaleString('en-IN')}</div><div class="ss">per expense</div></div>
    <div class="sc"><div class="sl">Health Score</div><div class="sv cp">${r.health_score}/100</div><div class="ss">Grade ${r.health_grade}</div></div>
    <div class="sc"><div class="sl">Total Invested</div><div class="sv ca">₹${r.total_invested.toLocaleString('en-IN')}</div><div class="ss">${r.invest_count} positions</div></div>
    <div class="sc"><div class="sl">Subscriptions</div><div class="sv" style="font-size:20px;color:var(--accent2)">₹${r.sub_monthly.toLocaleString('en-IN')}/mo</div><div class="ss">${r.sub_count} services</div></div>`;
  const cats=document.getElementById('dcats');
  if(!r.categories?.length){cats.innerHTML='<div class="empty"><div class="ei">◌</div>No data</div>';return}
  const mx=Math.max(...r.categories.map(c=>c.amount));
  cats.innerHTML=r.categories.map(c=>`<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px"><span>${c.name}</span><span class="amc ca">₹${c.amount.toLocaleString('en-IN')}</span></div><div class="pw"><div class="pb" style="width:${(c.amount/mx*100).toFixed(1)}%;background:var(--accent)"></div></div></div>`).join('');
  const rec=document.getElementById('drec');
  if(!r.recent?.length){rec.innerHTML='<div class="empty"><div class="ei">◌</div>No transactions</div>';return}
  rec.innerHTML=r.recent.map(e=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);font-size:12px"><div><div style="font-weight:600">${e.name}</div><div style="color:var(--muted);font-family:var(--mono);font-size:10px">${e.category} · ${e.date}</div></div><div class="amc ca" style="font-size:14px">₹${e.amount.toLocaleString('en-IN')}</div></div>`).join('')}

async function addExpense(){
  const d={name:document.getElementById('e-name').value.trim(),amount:parseFloat(document.getElementById('e-amt').value),date:document.getElementById('e-date').value,category:document.getElementById('e-cat').value,payment:document.getElementById('e-pay').value,note:document.getElementById('e-note').value.trim()};
  if(!d.name||!d.amount||!d.date||!d.category||!d.payment){toast('Fill all required fields','err');return}
  const r=await api('/api/expense/add',d);
  if(r.ok){toast('Expense added ✓');['e-name','e-amt','e-note'].forEach(id=>document.getElementById(id).value='');document.getElementById('e-cat').value='';document.getElementById('e-pay').value='';const fw=document.getElementById('fwarn');if(r.fraud_alerts?.length){fw.style.display='';fw.innerHTML=r.fraud_alerts.map(a=>`<div class="fa"><div class="fa-ic">⚠️</div><div><div class="fa-l">Fraud Alert</div><div style="font-size:12px;line-height:1.5">${a.reason}</div></div></div>`).join('');loadFraudBadge()}else fw.style.display='none'}else toast(r.error,'err')}

async function loadExp(){const r=await api('/api/expenses');AE=r.expenses||[];renderExp(AE)}
function renderExp(list){const tb=document.getElementById('etbody'),em=document.getElementById('eempty');if(!list.length){tb.innerHTML='';em.style.display='';return}em.style.display='none';tb.innerHTML=list.map(e=>`<tr class="${e.is_fraud?'fr-row':''}"><td><code style="font-size:10px;color:var(--muted)">${e.id}</code></td><td>${e.name} ${e.is_fraud?'<span class="badge bw">⚠ flagged</span>':''}</td><td class="amc ca">₹${e.amount.toLocaleString('en-IN')}</td><td><span class="badge bc">${e.category}</span></td><td><span class="badge bp">${e.payment}</span></td><td style="font-family:var(--mono);font-size:10px;color:var(--muted)">${e.date}</td><td style="font-size:11px;color:var(--muted)">${e.note||''}</td><td><button class="btn btn-d btn-sm" onclick="delExp('${e.id}')">✕</button></td></tr>`).join('')}
function filterExp(){const q=document.getElementById('fsearch').value.toLowerCase();renderExp(AE.filter(e=>e.name.toLowerCase().includes(q)||e.category.toLowerCase().includes(q)))}
async function delExp(id){if(!confirm('Delete?'))return;const r=await api('/api/expense/delete',{id});if(r.ok){toast('Deleted');loadExp()}else toast(r.error,'err')}

async function sendChat(){const inp=document.getElementById('cinput');const msg=inp.value.trim();if(!msg)return;inp.value='';addCM(msg,'user');const ty=addTyping();const r=await api('/api/copilot',{message:msg});ty.remove();addCM(r.reply||r.error||'Error.','ai')}
function qc(m){document.getElementById('cinput').value=m;sendChat()}
function addCM(t,role){const w=document.getElementById('chatmsgs');const d=document.createElement('div');d.className='cm '+role;d.innerHTML=role==='ai'?`<div class="ail">EXPENSEFLOW AI</div>${t}`:t;w.appendChild(d);w.scrollTop=w.scrollHeight;return d}
function addTyping(){const w=document.getElementById('chatmsgs');const d=document.createElement('div');d.className='typing';d.textContent='AI is thinking…';w.appendChild(d);w.scrollTop=w.scrollHeight;return d}

async function loadHealth(){
  const r=await api('/api/health');const s=r.scores;const l=r.labels;
  const col=r.overall>=80?'var(--green)':r.overall>=60?'var(--yellow)':'var(--red)';
  document.getElementById('hcontent').innerHTML=`
    <div class="two">
      <div class="card"><div class="ct">Overall Score</div>
        <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap">
          <div style="text-align:center"><div class="hr-num" style="color:${col}">${r.overall}</div><div class="hr-grade">/ 100 · Grade ${r.grade}</div></div>
          <div style="flex:1">${Object.entries(s).map(([k,v])=>`<div class="sr"><div style="width:130px;font-size:11px;color:var(--muted)">${l[k]}</div><div class="sb-w"><div class="sb" style="width:${v}%;background:${v>=70?'var(--green)':v>=40?'var(--yellow)':'var(--red)'}"></div></div><div class="sv2" style="color:${v>=70?'var(--green)':v>=40?'var(--yellow)':'var(--red)'}">${v}</div></div>`).join('')}</div>
        </div>
      </div>
      <div class="card"><div class="ct">Radar</div><img id="hradar" style="max-width:100%"/></div>
    </div>
    <div class="card"><div class="ct">Recommendations</div><div id="hrecs"></div></div>`;
  const charts=await api('/api/charts');if(charts.radar)document.getElementById('hradar').src=charts.radar;
  const recs=[];
  if(s.emergency_fund<50)recs.push({i:'🏦',t:'Build emergency fund. Target 6 months of expenses.'});
  if(s.investment_readiness<30)recs.push({i:'📈',t:'Start investing. Even ₹500/month in SIPs compounds massively.'});
  if(s.budget_consistency<60)recs.push({i:'📋',t:'Set category budgets and track consistently for 3 months.'});
  if(s.savings_stability<50)recs.push({i:'📉',t:'Volatile spending detected. Aim for consistent monthly expenditure.'});
  if(s.debt_risk<60)recs.push({i:'⚠️',t:'Some months exceed ₹80k spending. Review large irregular expenses.'});
  if(!recs.length)recs.push({i:'🎉',t:'Excellent financial health! Keep up these habits.'});
  document.getElementById('hrecs').innerHTML=recs.map(r=>`<div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);align-items:flex-start"><div style="font-size:20px">${r.i}</div><div style="font-size:13px;line-height:1.5">${r.t}</div></div>`).join('')}

async function loadCharts(){const r=await api('/api/charts');if(r.pie)document.getElementById('cpie').src=r.pie;if(r.line)document.getElementById('cline').src=r.line;if(r.radar)document.getElementById('cradar').src=r.radar;if(r.invest)document.getElementById('cinvest').src=r.invest}

async function saveBudget(){const cat=document.getElementById('b-cat').value,amt=parseFloat(document.getElementById('b-amt').value);if(!cat||!amt){toast('Fill all fields','err');return}const r=await api('/api/budget/set',{category:cat,amount:amt});if(r.ok){toast('Budget saved ✓');loadBudget();tog('bform')}else toast(r.error,'err')}
async function loadBudget(){const r=await api('/api/budget/overview');const el=document.getElementById('boverview');if(!r.items?.length){el.innerHTML='<div class="empty"><div class="ei">◎</div>No budgets set.</div>';return}el.innerHTML=r.items.map(b=>{const pct=Math.min(b.spent/b.budget*100,100).toFixed(0);const over=b.spent>b.budget;const col=over?'var(--red)':pct>75?'var(--yellow)':'var(--green)';return`<div class="card" style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><div style="font-weight:700">${b.category}</div><div class="amc" style="color:${col}">₹${b.spent.toLocaleString('en-IN')} / ₹${b.budget.toLocaleString('en-IN')}</div></div><div class="pw" style="height:11px"><div class="pb" style="width:${pct}%;background:${col}"></div></div><div style="font-size:11px;color:${col};margin-top:7px;font-family:var(--mono)">${over?`⚠ Over by ₹${(b.spent-b.budget).toLocaleString('en-IN')}`:`✓ ₹${(b.budget-b.spent).toLocaleString('en-IN')} remaining`}</div></div>`}).join('')}

async function saveGoal(){const d={name:document.getElementById('g-name').value.trim(),target:parseFloat(document.getElementById('g-tgt').value),saved:parseFloat(document.getElementById('g-saved').value)||0,deadline:document.getElementById('g-dl').value,category:document.getElementById('g-cat').value};if(!d.name||!d.target){toast('Name and target required','err');return}const r=await api('/api/goal/add',d);if(r.ok){toast('Goal created ✓');loadGoals();tog('gform')}else toast(r.error,'err')}
async function loadGoals(){const r=await api('/api/goals');const grid=document.getElementById('ggrid'),em=document.getElementById('gempty'),gs=r.goals||[];if(!gs.length){grid.innerHTML='';em.style.display='';return}em.style.display='none';grid.innerHTML=gs.map(g=>{const pct=Math.min(g.saved/g.target*100,100).toFixed(0);const col=pct>=100?'var(--green)':pct>=50?'var(--yellow)':'var(--accent)';return`<div class="gc"><div class="gp" style="color:${col}">${pct}%</div><div style="font-size:13px;color:var(--muted);font-family:var(--mono);margin-bottom:4px">${g.category||'Goal'}</div><div style="font-size:16px;font-weight:800;margin-bottom:10px">${g.name}</div><div class="pw"><div class="pb" style="width:${pct}%;background:${col}"></div></div><div style="display:flex;justify-content:space-between;font-size:11px;margin-top:8px;font-family:var(--mono)"><span style="color:var(--muted)">Saved: <span style="color:${col}">₹${g.saved.toLocaleString('en-IN')}</span></span><span style="color:var(--muted)">Target: ₹${g.target.toLocaleString('en-IN')}</span></div>${g.deadline?`<div style="font-size:10px;color:var(--muted);margin-top:6px;font-family:var(--mono)">📅 ${g.deadline}</div>`:''}<div style="margin-top:12px;display:flex;gap:8px"><input type="number" id="topup-${g.id}" placeholder="Add ₹" style="flex:1;padding:7px;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:var(--r);font-family:var(--mono);font-size:12px;outline:none"/><button class="btn btn-s btn-sm" onclick="topup('${g.id}')">+ Add</button><button class="btn btn-d btn-sm" onclick="delGoal('${g.id}')">✕</button></div></div>`}).join('')}
async function topup(id){const amt=parseFloat(document.getElementById('topup-'+id).value);if(!amt||amt<=0){toast('Enter valid amount','err');return}const r=await api('/api/goal/topup',{id,amount:amt});if(r.ok){toast('Savings updated ✓');loadGoals()}else toast(r.error,'err')}
async function delGoal(id){if(!confirm('Delete goal?'))return;const r=await api('/api/goal/delete',{id});if(r.ok){toast('Deleted');loadGoals()}}

async function saveSub(){const d={name:document.getElementById('s-name').value.trim(),amount:parseFloat(document.getElementById('s-amt').value),cycle:document.getElementById('s-cyc').value,due:document.getElementById('s-due').value};if(!d.name||!d.amount){toast('Fill required fields','err');return}const r=await api('/api/sub/add',d);if(r.ok){toast('Subscription added ✓');loadSubs();tog('sform')}else toast(r.error,'err')}
async function loadSubs(){const r=await api('/api/subs');const subs=r.subs||[];const el=document.getElementById('scontent');if(!subs.length){el.innerHTML='<div class="empty"><div class="ei">↺</div>No subscriptions tracked.</div>';return}const mo=subs.filter(s=>s.active).reduce((a,s)=>a+(s.cycle==='Monthly'?s.amount:s.cycle==='Quarterly'?s.amount/3:s.amount/12),0);el.innerHTML=`<div class="sg" style="margin-bottom:16px"><div class="sc"><div class="sl">Monthly Cost</div><div class="sv ca">₹${mo.toFixed(0)}</div></div><div class="sc"><div class="sl">Annual Cost</div><div class="sv cy">₹${(mo*12).toFixed(0)}</div></div></div><div class="card"><div class="tw"><table><thead><tr><th>Service</th><th>Amount</th><th>Cycle</th><th>Monthly</th><th>Next Due</th><th>Status</th><th></th></tr></thead><tbody>${subs.map(s=>{const mc=s.cycle==='Monthly'?s.amount:s.cycle==='Quarterly'?s.amount/3:s.amount/12;return`<tr><td style="font-weight:700">${s.name}</td><td class="amc">₹${s.amount.toLocaleString('en-IN')}</td><td><span class="badge bc">${s.cycle}</span></td><td class="amc ca">₹${mc.toFixed(0)}/mo</td><td style="font-family:var(--mono);font-size:11px;color:var(--muted)">${s.next_due||'—'}</td><td><span class="badge ${s.active?'bok':'bw'}">${s.active?'Active':'Paused'}</span></td><td><button class="btn btn-d btn-sm" onclick="delSub('${s.id}')">✕</button></td></tr>`}).join('')}</tbody></table></div></div>`}
async function delSub(id){if(!confirm('Remove?'))return;const r=await api('/api/sub/delete',{id});if(r.ok){toast('Removed');loadSubs()}}

async function saveInvest(){const d={name:document.getElementById('i-name').value.trim(),type:document.getElementById('i-type').value,amount:parseFloat(document.getElementById('i-amt').value),curr_price:parseFloat(document.getElementById('i-curr').value)||0,units:parseFloat(document.getElementById('i-units').value)||null,date:document.getElementById('i-date').value};if(!d.name||!d.amount||!d.date){toast('Fill required fields','err');return}const r=await api('/api/invest/add',d);if(r.ok){toast('Investment added ✓');loadInvest();tog('iform')}else toast(r.error,'err')}
async function loadInvest(){const r=await api('/api/investments');const items=r.investments||[];const tb=document.getElementById('itbody'),em=document.getElementById('iempty'),sum=document.getElementById('isum');if(!items.length){tb.innerHTML='';em.style.display='';sum.innerHTML='';return}em.style.display='none';const ti=items.reduce((a,i)=>a+i.amount,0),tc=items.reduce((a,i)=>a+(i.curr_price||i.amount),0),pnl=tc-ti,pct=ti?(pnl/ti*100).toFixed(1):0;sum.innerHTML=`<div class="sc"><div class="sl">Total Invested</div><div class="sv ca">₹${ti.toLocaleString('en-IN')}</div></div><div class="sc"><div class="sl">Current Value</div><div class="sv cg">₹${tc.toLocaleString('en-IN')}</div></div><div class="sc"><div class="sl">Total P&L</div><div class="sv ${pnl>=0?'cg':'cr'}">${pnl>=0?'+':''}₹${Math.abs(pnl).toLocaleString('en-IN')}</div><div class="ss">${pct}% ${pnl>=0?'gain':'loss'}</div></div>`;tb.innerHTML=items.map(i=>{const p=(i.curr_price||i.amount)-i.amount;const pc=i.amount?(p/i.amount*100).toFixed(1):0;return`<tr><td style="font-weight:700">${i.name}</td><td><span class="badge bc">${i.type}</span></td><td class="amc">₹${i.amount.toLocaleString('en-IN')}</td><td class="amc cg">₹${(i.curr_price||i.amount).toLocaleString('en-IN')}</td><td><span class="ip ${p>=0?'ipos':'ineg'}">${p>=0?'▲':'▼'} ${Math.abs(pc)}%</span></td><td style="font-family:var(--mono);font-size:11px;color:var(--muted)">${i.date}</td><td><button class="btn btn-d btn-sm" onclick="delInvest('${i.id}')">✕</button></td></tr>`}).join('')}
async function delInvest(id){if(!confirm('Delete?'))return;const r=await api('/api/invest/delete',{id});if(r.ok){toast('Deleted');loadInvest()}}

async function loadFraud(){const r=await api('/api/fraud/alerts');const el=document.getElementById('fraud-content');if(!r.alerts?.length){el.innerHTML='<div class="card"><div class="empty"><div class="ei">✓</div>No fraud alerts. Transactions look normal.</div></div>';return}el.innerHTML=r.alerts.map(a=>`<div class="fa"><div class="fa-ic">⚠️</div><div style="flex:1"><div class="fa-l">Score: ${a.score}</div><div style="font-size:12px;line-height:1.5">${a.reason}</div><div style="font-size:10px;color:var(--muted);margin-top:4px;font-family:var(--mono)">${a.ts}</div></div><button class="btn btn-g btn-sm" onclick="dismissFraud('${a.id}')">Dismiss</button></div>`).join('')}
async function loadFraudBadge(){const r=await api('/api/fraud/count');const b=document.getElementById('fbadge');if(r.count>0){b.textContent=r.count;b.style.display=''}else b.style.display='none'}
async function dismissFraud(id){const r=await api('/api/fraud/dismiss',{id});if(r.ok){loadFraud();loadFraudBadge()}}

async function loadAdmin(){if(CR!=='admin')return;const r=await api('/api/admin/stats');const el=document.getElementById('adm-content');el.innerHTML=`<div class="sg"><div class="sc"><div class="sl">Total Users</div><div class="sv ca">${r.users}</div></div><div class="sc"><div class="sl">Total Expenses</div><div class="sv cy">${r.expenses}</div></div><div class="sc"><div class="sl">Platform Volume</div><div class="sv cg">₹${r.volume.toLocaleString('en-IN')}</div></div><div class="sc"><div class="sl">Fraud Alerts</div><div class="sv cr">${r.fraud_count}</div></div></div><div class="two"><div class="card"><div class="ct">User Registry</div><div class="tw"><table><thead><tr><th>Username</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead><tbody>${(r.user_list||[]).map(u=>`<tr><td style="font-weight:700">${u.username}</td><td style="font-size:11px;color:var(--muted)">${u.email||'—'}</td><td><span class="badge ${u.role==='admin'?'bad':'bok'}">${u.role}</span></td><td style="font-family:var(--mono);font-size:10px;color:var(--muted)">${(u.created||'').split('T')[0]}</td></tr>`).join('')}</tbody></table></div></div><div class="card"><div class="ct">Audit Log (Last 20)</div><div class="tw"><table><thead><tr><th>Action</th><th>User</th><th>Detail</th><th>Time</th></tr></thead><tbody>${(r.audit||[]).map(a=>`<tr><td><span class="badge bc">${a.action}</span></td><td style="font-size:11px">${a.user_id||'—'}</td><td style="font-size:11px;color:var(--muted)">${(a.detail||'').slice(0,30)}</td><td style="font-family:var(--mono);font-size:10px;color:var(--muted)">${(a.ts||'').replace('T',' ').slice(0,16)}</td></tr>`).join('')}</tbody></table></div></div></div>`}

function exportFile(t){window.location.href='/api/export/'+t}
(async()=>{if(AT){const r=await api('/api/me');if(r.user)enterApp(r.user,r.role);else{localStorage.removeItem('at');localStorage.removeItem('rt')}}})();
</script>
</body>
</html>"""


# ── ROUTES: AUTH ────────────────────────────────────────────
@app.route("/")
def index(): return PAGE

@app.route("/api/register", methods=["POST"])
def reg():
    d=request.json or {}; u=d.get("username","").strip(); pw=d.get("password",""); em=d.get("email","").strip() or None
    if not u or not pw: return jsonify(ok=False,error="Username and password required")
    if len(pw)<8: return jsonify(ok=False,error="Password min 8 chars")
    with get_db() as c:
        if c.execute("SELECT 1 FROM users WHERE username=?",(u,)).fetchone(): return jsonify(ok=False,error="Username taken")
    salt=new_salt(); uid=uuid.uuid4().hex[:12]
    with get_db() as c:
        c.execute("INSERT INTO users (id,username,email,password,salt,role,created,last_login) VALUES(?,?,?,?,?,?,?,?)",(uid,u,em,hash_pw(pw,salt),salt,"user",datetime.now().isoformat(),None))
    audit(uid,"register",u,request.remote_addr); return jsonify(ok=True)

@app.route("/api/login", methods=["POST"])
def login():
    d=request.json or {}; u=d.get("username","").strip(); pw=d.get("password","")
    with get_db() as c: row=c.execute("SELECT * FROM users WHERE username=?",(u,)).fetchone()
    if not row or hash_pw(pw,row["salt"])!=row["password"]: return jsonify(ok=False,error="Invalid credentials")
    with get_db() as c: c.execute("UPDATE users SET last_login=? WHERE id=?",(datetime.now().isoformat(),row["id"]))
    access=mk_access(row["id"],row["role"])
    if isinstance(access, bytes):
        access = access.decode('utf-8')
    refresh=mk_refresh(row["id"])
    if isinstance(refresh, bytes):
        refresh = refresh.decode('utf-8')
    audit(row["id"],"login",u,request.remote_addr)
    return jsonify(ok=True,access_token=access,refresh_token=refresh,role=row["role"],user=u)

@app.route("/api/refresh", methods=["POST"])
def refresh_token():
    d=request.json or {}
    rt=d.get("refresh_token","")
    with get_db() as c: row=c.execute("SELECT * FROM refresh_tokens WHERE token=?",(rt,)).fetchone()
    if not row: return jsonify(ok=False,error="Invalid refresh token")
    if datetime.fromisoformat(row["expires"])<datetime.now(timezone.utc): return jsonify(ok=False,error="Refresh token expired")
    with get_db() as c: user=c.execute("SELECT id,role FROM users WHERE id=?",(row["user_id"],)).fetchone()
    return jsonify(ok=True,access_token=mk_access(user["id"],user["role"]))

@app.route("/api/logout", methods=["POST"])
@require_auth
def logout(): audit(g.user_id,"logout","",request.remote_addr); return jsonify(ok=True)

@app.route("/api/me")
def me():
    tok=get_token()
    if not tok: return jsonify(user=None)
    try:
        d=decode_tok(tok)
        with get_db() as c: row=c.execute("SELECT username,role FROM users WHERE id=?",(d["sub"],)).fetchone()
        return jsonify(user=row["username"],role=row["role"]) if row else jsonify(user=None)
    except: return jsonify(user=None)

# ── ROUTES: EXPENSES ────────────────────────────────────────
@app.route("/api/expense/add", methods=["POST"])
@require_auth
def add_expense():
    d=request.json or {}; eid=uuid.uuid4().hex[:8]; date=d.get("date") or datetime.now().strftime("%Y-%m-%d")
    exp=dict(name=d.get("name",""),amount=float(d.get("amount",0)),category=d.get("category",""))
    alerts=run_fraud(g.user_id,exp); is_fraud=1 if alerts else 0
    with get_db() as c:
        c.execute("INSERT INTO expenses (id,user_id,name,amount,category,payment,date,note,is_fraud) VALUES(?,?,?,?,?,?,?,?,?)",
                  (eid,g.user_id,d.get("name",""),float(d.get("amount",0)),d.get("category",""),d.get("payment",""),date,d.get("note",""),is_fraud))
    if alerts: store_fraud(g.user_id,eid,alerts)
    audit(g.user_id,"add_expense",f"{d['name']} {d['amount']}")
    return jsonify(ok=True,id=eid,fraud_alerts=alerts)

@app.route("/api/expenses")
@require_auth
def get_expenses():
    with get_db() as c:
        rows=c.execute("SELECT id,name,amount,category,payment,date,note,is_fraud FROM expenses WHERE user_id=? ORDER BY date DESC",(g.user_id,)).fetchall()
    return jsonify(expenses=[dict(r) for r in rows])

@app.route("/api/expense/delete", methods=["POST"])
@require_auth
def del_expense():
    d=request.json or {}
    eid=d.get("id")
    with get_db() as c: c.execute("DELETE FROM expenses WHERE id=? AND user_id=?",(eid,g.user_id))
    audit(g.user_id,"delete_expense",eid); return jsonify(ok=True)

# ── ROUTES: STATS ────────────────────────────────────────────
@app.route("/api/stats")
@require_auth
def stats():
    with get_db() as c:
        rows=c.execute("SELECT amount,category,date FROM expenses WHERE user_id=?",(g.user_id,)).fetchall()
        invs=c.execute("SELECT amount FROM investments WHERE user_id=?",(g.user_id,)).fetchall()
        subs=c.execute("SELECT amount,cycle FROM subscriptions WHERE user_id=? AND active=1",(g.user_id,)).fetchall()
        rec=c.execute("SELECT name,amount,category,date FROM expenses WHERE user_id=? ORDER BY date DESC LIMIT 5",(g.user_id,)).fetchall()
    if not rows: return jsonify(total=0,count=0,avg=0,this_month=0,categories=[],recent=[],health_score=0,health_grade="—",total_invested=0,invest_count=0,sub_monthly=0,sub_count=0)
    amounts=[r["amount"] for r in rows]; total=round(sum(amounts),2); count=len(amounts); avg=round(mean(amounts),2)
    cs={}
    for r in rows: cs[r["category"]]=cs.get(r["category"],0)+r["amount"]
    now=datetime.now(); this_m=sum(r["amount"] for r in rows if r["date"].startswith(f"{now.year}-{now.month:02d}"))
    cats=sorted([{"name":k,"amount":round(v,2)} for k,v in cs.items()],key=lambda x:-x["amount"])[:6]
    h=health_score(g.user_id)
    ti=sum(i["amount"] for i in invs)
    smo=sum((s["amount"] if s["cycle"]=="Monthly" else s["amount"]/3 if s["cycle"]=="Quarterly" else s["amount"]/12) for s in subs)
    return jsonify(total=total,count=count,avg=avg,this_month=round(this_m,2),categories=cats,recent=[dict(r) for r in rec],health_score=h["overall"],health_grade=h["grade"],total_invested=round(ti,2),invest_count=len(invs),sub_monthly=round(smo,2),sub_count=len(subs))

# ── ROUTES: AI COPILOT ───────────────────────────────────────
@app.route("/api/copilot", methods=["POST"])
@require_auth
def copilot():
    d=request.json or {}
    msg=d.get("message","")
    if not msg: return jsonify(ok=False,error="Empty message")
    ctx=fin_ctx(g.user_id)
    import urllib.request, json as _j
    payload=_j.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1000,
        "system":f"You are ExpenseFlow AI, expert personal finance advisor. Be concise, specific, actionable. Use ₹ for INR. Under 200 words. Bullet points for recommendations.\n\nUser data:\n{ctx}",
        "messages":[{"role":"user","content":msg}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,
        headers={"Content-Type":"application/json","x-api-key":os.environ.get("ANTHROPIC_API_KEY",""),"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req,timeout=20) as resp:
            data=_j.loads(resp.read()); reply=data["content"][0]["text"]
    except: reply=copilot_fallback(g.user_id,msg)
    return jsonify(ok=True,reply=reply)

# ── ROUTES: HEALTH ────────────────────────────────────────────
@app.route("/api/health")
@require_auth
def health(): return jsonify(**health_score(g.user_id))

# ── ROUTES: CHARTS ────────────────────────────────────────────
@app.route("/api/charts")
@require_auth
def charts():
    with get_db() as c:
        rows=c.execute("SELECT category,amount,date FROM expenses WHERE user_id=?",(g.user_id,)).fetchall()
        invrows=c.execute("SELECT type,amount FROM investments WHERE user_id=?",(g.user_id,)).fetchall()
    cs={}
    for r in rows: cs[r["category"]]=cs.get(r["category"],0)+r["amount"]
    h=health_score(g.user_id)
    return jsonify(
        pie=chart_pie(cs) if cs else "",
        line=chart_line(rows) if rows else "",
        radar=chart_radar(h["scores"],h["labels"]),
        invest=chart_invest([dict(r) for r in invrows]) if invrows else "")

# ── ROUTES: BUDGET ────────────────────────────────────────────
@app.route("/api/budget/set", methods=["POST"])
@require_auth
def budget_set():
    d=request.json or {}; cat=d.get("category",""); amt=float(d.get("amount",0)); now=datetime.now().strftime("%Y-%m")
    with get_db() as c:
        ex=c.execute("SELECT id FROM budgets WHERE user_id=? AND category=? AND month=?",(g.user_id,cat,now)).fetchone()
        if ex: c.execute("UPDATE budgets SET monthly=? WHERE id=?",(amt,ex["id"]))
        else: c.execute("INSERT INTO budgets (id,user_id,category,monthly,month) VALUES(?,?,?,?,?)",(uuid.uuid4().hex[:8],g.user_id,cat,amt,now))
    return jsonify(ok=True)

@app.route("/api/budget/overview")
@require_auth
def budget_overview():
    now=datetime.now().strftime("%Y-%m")
    with get_db() as c:
        budgs=c.execute("SELECT category,monthly FROM budgets WHERE user_id=? AND month=?",(g.user_id,now)).fetchall()
        exps=c.execute("SELECT category,amount FROM expenses WHERE user_id=? AND date LIKE ?",(g.user_id,now+"%")).fetchall()
    cs={}
    for e in exps: cs[e["category"]]=cs.get(e["category"],0)+e["amount"]
    return jsonify(items=[{"category":b["category"],"budget":b["monthly"],"spent":round(cs.get(b["category"],0),2)} for b in budgs])

# ── ROUTES: GOALS ─────────────────────────────────────────────
@app.route("/api/goal/add", methods=["POST"])
@require_auth
def goal_add():
    d=request.json or {}
    with get_db() as c:
        c.execute("INSERT INTO goals (id,user_id,name,target,saved,deadline,category,created) VALUES(?,?,?,?,?,?,?,?)",
                  (uuid.uuid4().hex[:8],g.user_id,d.get("name",""),float(d.get("target",0)),float(d.get("saved",0)),d.get("deadline",""),d.get("category",""),datetime.now().isoformat()))
    return jsonify(ok=True)

@app.route("/api/goals")
@require_auth
def get_goals():
    with get_db() as c: rows=c.execute("SELECT * FROM goals WHERE user_id=? ORDER BY created DESC",(g.user_id,)).fetchall()
    return jsonify(goals=[dict(r) for r in rows])

@app.route("/api/goal/topup", methods=["POST"])
@require_auth
def goal_topup():
    d=request.json or {}
    with get_db() as c:
        row=c.execute("SELECT saved FROM goals WHERE id=? AND user_id=?",(d.get("id"),g.user_id)).fetchone()
        if not row: return jsonify(ok=False,error="Not found")
        ns=round(row["saved"]+float(d.get("amount",0)),2)
        c.execute("UPDATE goals SET saved=? WHERE id=?",(ns,d.get("id")))
    return jsonify(ok=True,saved=ns)

@app.route("/api/goal/delete", methods=["POST"])
@require_auth
def goal_delete():
    d=request.json or {}
    with get_db() as c: c.execute("DELETE FROM goals WHERE id=? AND user_id=?",(d.get("id"),g.user_id))
    return jsonify(ok=True)

# ── ROUTES: SUBSCRIPTIONS ─────────────────────────────────────
@app.route("/api/sub/add", methods=["POST"])
@require_auth
def sub_add():
    d=request.json or {}
    with get_db() as c:
        c.execute("INSERT INTO subscriptions (id,user_id,name,amount,cycle,next_due,active) VALUES(?,?,?,?,?,?,1)",
                  (uuid.uuid4().hex[:8],g.user_id,d.get("name",""),float(d.get("amount",0)),d.get("cycle",""),d.get("due","")))
    return jsonify(ok=True)

@app.route("/api/subs")
@require_auth
def get_subs():
    with get_db() as c: rows=c.execute("SELECT * FROM subscriptions WHERE user_id=? ORDER BY name",(g.user_id,)).fetchall()
    return jsonify(subs=[dict(r) for r in rows])

@app.route("/api/sub/delete", methods=["POST"])
@require_auth
def sub_delete():
    d=request.json or {}
    with get_db() as c: c.execute("DELETE FROM subscriptions WHERE id=? AND user_id=?",(d.get("id"),g.user_id))
    return jsonify(ok=True)

# ── ROUTES: INVESTMENTS ───────────────────────────────────────
@app.route("/api/invest/add", methods=["POST"])
@require_auth
def invest_add():
    d=request.json or {}
    with get_db() as c:
        c.execute("INSERT INTO investments (id,user_id,name,type,amount,units,buy_price,curr_price,date) VALUES(?,?,?,?,?,?,?,?,?)",
                  (uuid.uuid4().hex[:8],g.user_id,d.get("name",""),d.get("type",""),float(d.get("amount",0)),
                   d.get("units"),float(d.get("amount",0)),float(d.get("curr_price") or d.get("amount",0)),d.get("date","")))
    return jsonify(ok=True)

@app.route("/api/investments")
@require_auth
def get_investments():
    with get_db() as c:
        rows=c.execute("SELECT id,name,type,amount,curr_price,units,date FROM investments WHERE user_id=? ORDER BY date DESC",(g.user_id,)).fetchall()
    return jsonify(investments=[dict(r) for r in rows])

@app.route("/api/invest/delete", methods=["POST"])
@require_auth
def invest_delete():
    d=request.json or {}
    with get_db() as c: c.execute("DELETE FROM investments WHERE id=? AND user_id=?",(d.get("id"),g.user_id))
    return jsonify(ok=True)

# ── ROUTES: FRAUD ─────────────────────────────────────────────
@app.route("/api/fraud/alerts")
@require_auth
def fraud_alerts():
    with get_db() as c:
        rows=c.execute("SELECT id,reason,score,ts FROM fraud_alerts WHERE user_id=? AND dismissed=0 ORDER BY ts DESC",(g.user_id,)).fetchall()
    return jsonify(alerts=[dict(r) for r in rows])

@app.route("/api/fraud/count")
@require_auth
def fraud_count():
    with get_db() as c:
        n=c.execute("SELECT COUNT(*) FROM fraud_alerts WHERE user_id=? AND dismissed=0",(g.user_id,)).fetchone()[0]
    return jsonify(count=n)

@app.route("/api/fraud/dismiss", methods=["POST"])
@require_auth
def fraud_dismiss():
    d=request.json or {}
    with get_db() as c: c.execute("UPDATE fraud_alerts SET dismissed=1 WHERE id=? AND user_id=?",(d.get("id"),g.user_id))
    return jsonify(ok=True)

# ── ROUTES: ADMIN ─────────────────────────────────────────────
@app.route("/api/admin/stats")
@require_admin
def admin_stats():
    with get_db() as c:
        users=c.execute("SELECT * FROM users ORDER BY created DESC").fetchall()
        ec=c.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        ev=c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        fc=c.execute("SELECT COUNT(*) FROM fraud_alerts WHERE dismissed=0").fetchone()[0]
        al=c.execute("SELECT action,user_id,detail,ts FROM audit_logs ORDER BY ts DESC LIMIT 20").fetchall()
    return jsonify(users=len(users),expenses=ec,volume=round(ev,2),fraud_count=fc,user_list=[dict(u) for u in users],audit=[dict(a) for a in al])

# ── ROUTES: EXPORT ────────────────────────────────────────────
@app.route("/api/export/csv")
@require_auth
def export_csv():
    with get_db() as c:
        rows=c.execute("SELECT id,name,amount,category,payment,date,note FROM expenses WHERE user_id=?",(g.user_id,)).fetchall()
    buf=io.StringIO(); w=csv.writer(buf)
    w.writerow(["ID","Name","Amount","Category","Payment","Date","Note"])
    for r in rows: w.writerow(list(r))
    buf.seek(0); resp=make_response(buf.getvalue())
    resp.headers["Content-Type"]="text/csv"; resp.headers["Content-Disposition"]="attachment; filename=expenseflowx.csv"
    return resp

@app.route("/api/export/excel")
@require_auth
def export_excel():
    with get_db() as c:
        df=pd.read_sql_query("SELECT id,name,amount,category,payment,date,note FROM expenses WHERE user_id=?",c,params=(g.user_id,))
    buf=io.BytesIO(); df.to_excel(buf,index=False); buf.seek(0)
    return send_file(buf,mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",as_attachment=True,download_name="expenseflowx.xlsx")

# ── MAIN ──────────────────────────────────────────────────────
if __name__=="__main__":
    print("""
\033[36m
  ╔══════════════════════════════════════╗
  ║   ExpenseFlow X — AI Finance OS     ║
  ║   http://localhost:8000              ║
  ║   ANTHROPIC_API_KEY for AI Copilot  ║
  ╚══════════════════════════════════════╝
\033[0m""")
    app.run(debug=True,port=8000,use_reloader=False)
