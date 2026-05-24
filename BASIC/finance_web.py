"""
============================================================
 AI POWERED SMART FINANCE MANAGEMENT SYSTEM — WEB VERSION
============================================================

INSTALL:pip install flask pandas matplotlib openpyxl

RUN:
    python finance_web.py

OPEN:
    http://localhost:5005
============================================================
"""

import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import hashlib
import uuid
import csv
import io
import os
import base64
from datetime import datetime
from statistics import mean

from flask import (
    Flask, request, session, redirect,
    url_for, jsonify, send_file, make_response
)

# ============================================================
# APP & CONFIG
# ============================================================

app = Flask(__name__)
app.secret_key = "super_secret_finance_key_2025"
DB_NAME = "finance.db"

# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id        TEXT PRIMARY KEY,
            username  TEXT NOT NULL,
            name      TEXT NOT NULL,
            amount    REAL NOT NULL,
            category  TEXT NOT NULL,
            payment   TEXT NOT NULL,
            date      TEXT NOT NULL
        );
        """)

init_db()

# ============================================================
# AUTH HELPERS
# ============================================================

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def logged_in():
    return "user" in session

def current_user():
    return session.get("user")

# ============================================================
# CHART HELPER  — returns a base64 PNG data-URI
# ============================================================

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    enc = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{enc}"

# ============================================================
# INLINE HTML / CSS / JS  (the entire UI lives here)
# ============================================================

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FinanceOS</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet"/>
<style>
/* ── RESET & TOKENS ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #080c10;
  --surface:  #0e1420;
  --card:     #131c2b;
  --border:   #1e2d42;
  --accent:   #00d4ff;
  --accent2:  #ff6b35;
  --green:    #00e5a0;
  --red:      #ff4d6d;
  --yellow:   #ffd166;
  --text:     #e2eaf5;
  --muted:    #5a7090;
  --font-ui:  'Syne', sans-serif;
  --font-mono:'Space Mono', monospace;
  --r:        10px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-ui);
  min-height: 100vh;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── AUTH SCREEN ── */
#auth-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background:
    radial-gradient(ellipse 60% 50% at 30% 20%, rgba(0,212,255,.08) 0%, transparent 70%),
    radial-gradient(ellipse 50% 40% at 80% 80%, rgba(255,107,53,.07) 0%, transparent 70%),
    var(--bg);
}

.auth-box {
  width: 400px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  animation: fadeUp .5s ease;
}

.auth-logo {
  font-size: 13px;
  letter-spacing: 4px;
  color: var(--accent);
  font-family: var(--font-mono);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.auth-title {
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 32px;
  line-height: 1.1;
}

.auth-tabs { display: flex; gap: 8px; margin-bottom: 28px; }
.tab-btn {
  flex: 1; padding: 10px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); border-radius: var(--r);
  cursor: pointer; font-family: var(--font-ui); font-size: 13px; font-weight: 600;
  letter-spacing: 1px; text-transform: uppercase; transition: all .2s;
}
.tab-btn.active {
  background: var(--accent); color: #000; border-color: var(--accent);
}

.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; font-size: 11px; letter-spacing: 2px;
  text-transform: uppercase; color: var(--muted); margin-bottom: 6px;
  font-family: var(--font-mono);
}
.form-group input, .form-group select {
  width: 100%; padding: 12px 14px;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); border-radius: var(--r);
  font-family: var(--font-mono); font-size: 14px;
  outline: none; transition: border-color .2s;
}
.form-group input:focus, .form-group select:focus {
  border-color: var(--accent);
}

.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; border: none; border-radius: var(--r);
  cursor: pointer; font-family: var(--font-ui); font-size: 13px;
  font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  transition: all .2s; text-decoration: none;
}
.btn-primary { background: var(--accent); color: #000; width: 100%; justify-content: center; }
.btn-primary:hover { background: #33ddff; transform: translateY(-1px); }
.btn-danger  { background: rgba(255,77,109,.15); color: var(--red); border: 1px solid rgba(255,77,109,.3); }
.btn-danger:hover { background: rgba(255,77,109,.25); }
.btn-outline { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
.btn-outline:hover { background: rgba(0,212,255,.1); }
.btn-sm { padding: 7px 14px; font-size: 11px; }

.msg { font-size: 13px; padding: 10px 14px; border-radius: var(--r); margin-top: 12px; font-family: var(--font-mono); }
.msg-ok  { background: rgba(0,229,160,.12); color: var(--green); border: 1px solid rgba(0,229,160,.2); }
.msg-err { background: rgba(255,77,109,.12); color: var(--red);   border: 1px solid rgba(255,77,109,.2); }

/* ── APP SHELL ── */
#app-shell { display: none; }

.topbar {
  height: 56px; background: var(--surface); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 24px; gap: 16px;
  position: sticky; top: 0; z-index: 100;
}
.topbar-logo {
  font-family: var(--font-mono); font-size: 12px; letter-spacing: 3px;
  color: var(--accent); text-transform: uppercase; font-weight: 700;
}
.topbar-user {
  margin-left: auto; font-size: 12px; color: var(--muted);
  font-family: var(--font-mono);
}
.topbar-user span { color: var(--text); }

.layout { display: flex; min-height: calc(100vh - 56px); }

/* ── SIDEBAR ── */
.sidebar {
  width: 220px; min-height: 100%; background: var(--surface);
  border-right: 1px solid var(--border); padding: 20px 12px;
  flex-shrink: 0;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: var(--r);
  cursor: pointer; font-size: 13px; font-weight: 600;
  color: var(--muted); transition: all .2s; margin-bottom: 4px;
  border: 1px solid transparent;
}
.nav-item:hover { color: var(--text); background: var(--card); }
.nav-item.active {
  color: var(--accent); background: rgba(0,212,255,.08);
  border-color: rgba(0,212,255,.2);
}
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
.nav-section {
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--muted); margin: 16px 14px 8px; font-family: var(--font-mono);
}

/* ── MAIN CONTENT ── */
.main { flex: 1; padding: 28px; overflow-y: auto; }
.page { display: none; animation: fadeUp .3s ease; }
.page.active { display: block; }

.page-header { margin-bottom: 28px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-header p  { color: var(--muted); font-size: 13px; margin-top: 4px; font-family: var(--font-mono); }

/* ── STAT CARDS ── */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
.stat-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); padding: 20px;
}
.stat-label { font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); font-family: var(--font-mono); margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 800; }
.stat-sub   { font-size: 11px; color: var(--muted); margin-top: 4px; font-family: var(--font-mono); }
.c-accent { color: var(--accent); }
.c-green  { color: var(--green); }
.c-red    { color: var(--red); }
.c-yellow { color: var(--yellow); }

/* ── CARDS ── */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r); padding: 24px; margin-bottom: 20px;
}
.card-title { font-size: 13px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 18px; font-family: var(--font-mono); }

/* ── FORM GRID ── */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-grid .full { grid-column: 1/-1; }
@media(max-width:640px){ .form-grid { grid-template-columns: 1fr; } }

/* ── TABLE ── */
.tbl-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead tr { border-bottom: 2px solid var(--border); }
thead th { padding: 10px 14px; text-align: left; font-family: var(--font-mono); font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); }
tbody tr { border-bottom: 1px solid var(--border); transition: background .15s; }
tbody tr:hover { background: rgba(255,255,255,.02); }
tbody td { padding: 12px 14px; }
.badge {
  display: inline-block; padding: 3px 10px; border-radius: 100px;
  font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  font-family: var(--font-mono);
}
.badge-cat { background: rgba(0,212,255,.12); color: var(--accent); }
.badge-pay { background: rgba(255,209,102,.12); color: var(--yellow); }
.amount-cell { font-family: var(--font-mono); font-weight: 700; }

/* ── INSIGHTS ── */
.insight-row {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 0; border-bottom: 1px solid var(--border);
}
.insight-row:last-child { border-bottom: none; }
.insight-icon { font-size: 22px; margin-top: 2px; }
.insight-text { font-size: 14px; line-height: 1.5; }
.insight-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); font-family: var(--font-mono); margin-bottom: 4px; }

/* ── BUDGET BAR ── */
.budget-bar-wrap { background: var(--surface); border-radius: 100px; height: 10px; overflow: hidden; margin: 10px 0; }
.budget-bar { height: 100%; border-radius: 100px; transition: width .6s ease; }

/* ── CHART IMAGE ── */
.chart-img { max-width: 100%; border-radius: var(--r); margin-top: 8px; }

/* ── EMPTY STATE ── */
.empty {
  text-align: center; padding: 60px 20px; color: var(--muted);
  font-family: var(--font-mono); font-size: 13px;
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }

/* ── ANIMATIONS ── */
@keyframes fadeUp {
  from { opacity:0; transform:translateY(12px); }
  to   { opacity:1; transform:translateY(0); }
}

/* ── TOAST ── */
#toast {
  position: fixed; bottom: 24px; right: 24px;
  padding: 14px 20px; border-radius: var(--r);
  font-family: var(--font-mono); font-size: 13px;
  transition: all .3s; opacity: 0; pointer-events: none; z-index: 999;
  transform: translateY(10px);
}
#toast.show { opacity: 1; transform: translateY(0); }
#toast.ok  { background: rgba(0,229,160,.15); color: var(--green); border: 1px solid rgba(0,229,160,.3); }
#toast.err { background: rgba(255,77,109,.15); color: var(--red);   border: 1px solid rgba(255,77,109,.3); }
</style>
</head>
<body>

<!-- ── AUTH SCREEN ── -->
<div id="auth-screen">
  <div class="auth-box">
    <div class="auth-logo">FinanceOS</div>
    <h1 class="auth-title">Track every<br/>rupee. Always.</h1>
    <div class="auth-tabs">
      <button class="tab-btn active" onclick="switchTab('login')">Login</button>
      <button class="tab-btn"        onclick="switchTab('register')">Register</button>
    </div>

    <!-- LOGIN -->
    <div id="form-login">
      <div class="form-group"><label>Username</label><input id="l-user" placeholder="your username"/></div>
      <div class="form-group"><label>Password</label><input id="l-pass" type="password" placeholder="••••••••"/></div>
      <button class="btn btn-primary" onclick="doLogin()">Sign In →</button>
      <div id="login-msg"></div>
    </div>

    <!-- REGISTER -->
    <div id="form-register" style="display:none">
      <div class="form-group"><label>Username</label><input id="r-user" placeholder="choose a username"/></div>
      <div class="form-group"><label>Password</label><input id="r-pass" type="password" placeholder="••••••••"/></div>
      <button class="btn btn-primary" onclick="doRegister()">Create Account →</button>
      <div id="reg-msg"></div>
    </div>
  </div>
</div>

<!-- ── APP SHELL ── -->
<div id="app-shell">
  <div class="topbar">
    <div class="topbar-logo">◈ FinanceOS</div>
    <div class="topbar-user">Signed in as <span id="topbar-uname">—</span></div>
    <button class="btn btn-outline btn-sm" onclick="doLogout()">Logout</button>
  </div>
  <div class="layout">

    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="nav-section">Main</div>
      <div class="nav-item active" onclick="showPage('dashboard')"><span class="nav-icon">⬡</span>Dashboard</div>
      <div class="nav-item" onclick="showPage('add')"><span class="nav-icon">＋</span>Add Expense</div>
      <div class="nav-item" onclick="showPage('expenses')"><span class="nav-icon">≡</span>All Expenses</div>

      <div class="nav-section">Analytics</div>
      <div class="nav-item" onclick="showPage('insights')"><span class="nav-icon">◉</span>AI Insights</div>
      <div class="nav-item" onclick="showPage('charts')"><span class="nav-icon">◈</span>Charts</div>
      <div class="nav-item" onclick="showPage('budget')"><span class="nav-icon">◎</span>Budget</div>

      <div class="nav-section">Export</div>
      <div class="nav-item" onclick="exportFile('csv')"><span class="nav-icon">↓</span>Export CSV</div>
      <div class="nav-item" onclick="exportFile('excel')"><span class="nav-icon">↓</span>Export Excel</div>
    </aside>

    <!-- PAGES -->
    <main class="main">

      <!-- DASHBOARD -->
      <div class="page active" id="page-dashboard">
        <div class="page-header">
          <h1>Dashboard</h1>
          <p id="dash-date">—</p>
        </div>
        <div class="stats-grid" id="stats-grid"></div>
        <div class="card">
          <div class="card-title">Spending by Category</div>
          <div id="dash-categories"></div>
        </div>
      </div>

      <!-- ADD EXPENSE -->
      <div class="page" id="page-add">
        <div class="page-header">
          <h1>Add Expense</h1>
          <p>Record a new transaction</p>
        </div>
        <div class="card">
          <div class="form-grid">
            <div class="form-group full">
              <label>Expense Name</label>
              <input id="e-name" placeholder="e.g. Netflix Subscription"/>
            </div>
            <div class="form-group">
              <label>Amount (₹)</label>
              <input id="e-amount" type="number" placeholder="0.00"/>
            </div>
            <div class="form-group">
              <label>Date</label>
              <input id="e-date" type="date"/>
            </div>
            <div class="form-group">
              <label>Category</label>
              <select id="e-category">
                <option value="">Select category</option>
                <option>Food & Dining</option>
                <option>Transport</option>
                <option>Shopping</option>
                <option>Entertainment</option>
                <option>Utilities</option>
                <option>Healthcare</option>
                <option>Education</option>
                <option>Travel</option>
                <option>Other</option>
              </select>
            </div>
            <div class="form-group">
              <label>Payment Method</label>
              <select id="e-payment">
                <option value="">Select method</option>
                <option>UPI</option>
                <option>Cash</option>
                <option>Credit Card</option>
                <option>Debit Card</option>
                <option>Net Banking</option>
              </select>
            </div>
            <div class="form-group full" style="margin-top:8px">
              <button class="btn btn-primary" onclick="addExpense()">Add Expense →</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ALL EXPENSES -->
      <div class="page" id="page-expenses">
        <div class="page-header" style="display:flex;align-items:center;justify-content:space-between">
          <div>
            <h1>All Expenses</h1>
            <p>Your complete transaction history</p>
          </div>
        </div>
        <div class="card">
          <div class="tbl-wrap">
            <table id="expenses-table">
              <thead><tr>
                <th>ID</th><th>Name</th><th>Amount</th>
                <th>Category</th><th>Payment</th><th>Date</th><th></th>
              </tr></thead>
              <tbody id="expenses-tbody"></tbody>
            </table>
          </div>
          <div id="expenses-empty" class="empty" style="display:none">
            <div class="empty-icon">◌</div>No expenses recorded yet.
          </div>
        </div>
      </div>

      <!-- AI INSIGHTS -->
      <div class="page" id="page-insights">
        <div class="page-header">
          <h1>AI Insights</h1>
          <p>Smart analysis of your spending patterns</p>
        </div>
        <div class="card" id="insights-card">
          <div class="empty"><div class="empty-icon">◌</div>Loading insights…</div>
        </div>
      </div>

      <!-- CHARTS -->
      <div class="page" id="page-charts">
        <div class="page-header">
          <h1>Charts</h1>
          <p>Visual breakdown of your finances</p>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
          <div class="card">
            <div class="card-title">Category Distribution</div>
            <img id="pie-chart" class="chart-img"/>
          </div>
          <div class="card">
            <div class="card-title">Monthly Trend</div>
            <img id="line-chart" class="chart-img"/>
          </div>
        </div>
      </div>

      <!-- BUDGET -->
      <div class="page" id="page-budget">
        <div class="page-header">
          <h1>Budget Tracker</h1>
          <p>Set a monthly limit and stay on track</p>
        </div>
        <div class="card" style="max-width:480px">
          <div class="form-group">
            <label>Monthly Budget (₹)</label>
            <input id="budget-input" type="number" placeholder="e.g. 50000"/>
          </div>
          <button class="btn btn-primary" onclick="checkBudget()">Check Budget</button>
          <div id="budget-result" style="margin-top:20px"></div>
        </div>
      </div>

    </main>
  </div>
</div>

<div id="toast"></div>

<script>
// ── STATE ──
let currentUser = null;

// ── UTILS ──
function toast(msg, type='ok') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.className = '', 3000);
}

async function api(path, data=null) {
  const opts = { headers: {'Content-Type':'application/json'} };
  if (data) { opts.method = 'POST'; opts.body = JSON.stringify(data); }
  const r = await fetch(path, opts);
  return r.json();
}

// ── AUTH ──
function switchTab(tab) {
  document.getElementById('form-login').style.display    = tab==='login'    ? '' : 'none';
  document.getElementById('form-register').style.display = tab==='register' ? '' : 'none';
  document.querySelectorAll('.tab-btn').forEach((b,i)=>
    b.classList.toggle('active', (i===0&&tab==='login')||(i===1&&tab==='register'))
  );
}

async function doLogin() {
  const user = document.getElementById('l-user').value.trim();
  const pass = document.getElementById('l-pass').value;
  const res  = await api('/api/login', {username:user, password:pass});
  const el   = document.getElementById('login-msg');
  if (res.ok) {
    currentUser = user;
    el.innerHTML = '';
    enterApp(user);
  } else {
    el.innerHTML = `<div class="msg msg-err">${res.error}</div>`;
  }
}

async function doRegister() {
  const user = document.getElementById('r-user').value.trim();
  const pass = document.getElementById('r-pass').value;
  const res  = await api('/api/register', {username:user, password:pass});
  const el   = document.getElementById('reg-msg');
  if (res.ok) {
    el.innerHTML = `<div class="msg msg-ok">Account created! Please login.</div>`;
    setTimeout(()=>switchTab('login'), 1500);
  } else {
    el.innerHTML = `<div class="msg msg-err">${res.error}</div>`;
  }
}

async function doLogout() {
  await api('/api/logout', {});
  currentUser = null;
  document.getElementById('auth-screen').style.display = 'flex';
  document.getElementById('app-shell').style.display   = 'none';
}

function enterApp(user) {
  document.getElementById('auth-screen').style.display = 'none';
  document.getElementById('app-shell').style.display   = 'block';
  document.getElementById('topbar-uname').textContent  = user;
  // set default date
  document.getElementById('e-date').value = new Date().toISOString().split('T')[0];
  loadDashboard();
}

// ── NAV ──
function showPage(id) {
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  event.currentTarget.classList.add('active');
  if (id==='dashboard') loadDashboard();
  if (id==='expenses')  loadExpenses();
  if (id==='insights')  loadInsights();
  if (id==='charts')    loadCharts();
}

// ── DASHBOARD ──
async function loadDashboard() {
  const d = new Date();
  document.getElementById('dash-date').textContent =
    d.toLocaleDateString('en-IN',{weekday:'long',year:'numeric',month:'long',day:'numeric'});

  const res = await api('/api/stats');
  const g   = document.getElementById('stats-grid');

  g.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Total Spent</div>
      <div class="stat-value c-accent">₹${res.total.toLocaleString('en-IN')}</div>
      <div class="stat-sub">${res.count} transactions</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Expense</div>
      <div class="stat-value c-yellow">₹${res.avg.toLocaleString('en-IN')}</div>
      <div class="stat-sub">per transaction</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Top Category</div>
      <div class="stat-value" style="font-size:18px;color:var(--green)">${res.top_cat || '—'}</div>
      <div class="stat-sub">${res.top_cat_pct}% of spending</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">This Month</div>
      <div class="stat-value c-green">₹${res.this_month.toLocaleString('en-IN')}</div>
      <div class="stat-sub">${new Date().toLocaleString('en-IN',{month:'long'})}</div>
    </div>
  `;

  // Category bars
  const cat = document.getElementById('dash-categories');
  if (!res.categories || res.categories.length === 0) {
    cat.innerHTML = '<div class="empty"><div class="empty-icon">◌</div>No data yet</div>';
    return;
  }
  const max = Math.max(...res.categories.map(c=>c.amount));
  cat.innerHTML = res.categories.map(c => `
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:13px">
        <span>${c.name}</span>
        <span class="amount-cell c-accent">₹${c.amount.toLocaleString('en-IN')}</span>
      </div>
      <div class="budget-bar-wrap">
        <div class="budget-bar" style="width:${(c.amount/max*100).toFixed(1)}%;background:var(--accent)"></div>
      </div>
    </div>
  `).join('');
}

// ── ADD EXPENSE ──
async function addExpense() {
  const name     = document.getElementById('e-name').value.trim();
  const amount   = parseFloat(document.getElementById('e-amount').value);
  const date     = document.getElementById('e-date').value;
  const category = document.getElementById('e-category').value;
  const payment  = document.getElementById('e-payment').value;

  if (!name || !amount || !date || !category || !payment) {
    toast('Fill in all fields', 'err'); return;
  }

  const res = await api('/api/expense/add', {name, amount, date, category, payment});
  if (res.ok) {
    toast('Expense added ✓');
    document.getElementById('e-name').value = '';
    document.getElementById('e-amount').value = '';
    document.getElementById('e-category').value = '';
    document.getElementById('e-payment').value = '';
  } else {
    toast(res.error, 'err');
  }
}

// ── EXPENSES LIST ──
async function loadExpenses() {
  const res   = await api('/api/expenses');
  const tbody = document.getElementById('expenses-tbody');
  const empty = document.getElementById('expenses-empty');

  if (!res.expenses || res.expenses.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = res.expenses.map(e => `
    <tr>
      <td><code style="font-size:11px;color:var(--muted)">${e.id}</code></td>
      <td>${e.name}</td>
      <td class="amount-cell c-accent">₹${e.amount.toLocaleString('en-IN')}</td>
      <td><span class="badge badge-cat">${e.category}</span></td>
      <td><span class="badge badge-pay">${e.payment}</span></td>
      <td style="font-family:var(--font-mono);font-size:12px;color:var(--muted)">${e.date}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteExpense('${e.id}')">✕</button>
      </td>
    </tr>
  `).join('');
}

async function deleteExpense(id) {
  if (!confirm('Delete this expense?')) return;
  const res = await api('/api/expense/delete', {id});
  if (res.ok) { toast('Deleted'); loadExpenses(); }
  else toast(res.error, 'err');
}

// ── INSIGHTS ──
async function loadInsights() {
  const res = await api('/api/insights');
  const el  = document.getElementById('insights-card');

  if (!res.insights || res.insights.length === 0) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">◌</div>Add expenses to see insights</div>';
    return;
  }

  el.innerHTML = '<div class="card-title">AI Financial Insights</div>' +
    res.insights.map(i => `
      <div class="insight-row">
        <div class="insight-icon">${i.icon}</div>
        <div>
          <div class="insight-label">${i.label}</div>
          <div class="insight-text">${i.text}</div>
        </div>
      </div>
    `).join('');
}

// ── CHARTS ──
async function loadCharts() {
  const res = await api('/api/charts');
  if (res.pie)  document.getElementById('pie-chart').src  = res.pie;
  if (res.line) document.getElementById('line-chart').src = res.line;
}

// ── BUDGET ──
async function checkBudget() {
  const budget = parseFloat(document.getElementById('budget-input').value);
  if (!budget || budget <= 0) { toast('Enter a valid budget', 'err'); return; }

  const res = await api('/api/budget', {budget});
  const el  = document.getElementById('budget-result');
  const pct = Math.min((res.spent / budget * 100), 100).toFixed(1);
  const over = res.spent > budget;
  const color = over ? 'var(--red)' : pct > 75 ? 'var(--yellow)' : 'var(--green)';

  el.innerHTML = `
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px">
        <span style="color:var(--muted)">Spent</span>
        <span class="amount-cell" style="color:${color}">₹${res.spent.toLocaleString('en-IN')} / ₹${budget.toLocaleString('en-IN')}</span>
      </div>
      <div class="budget-bar-wrap" style="height:14px">
        <div class="budget-bar" style="width:${pct}%;background:${color}"></div>
      </div>
    </div>
    <div style="font-size:14px;font-weight:600">
      ${over
        ? `<span style="color:var(--red)">⚠ Budget exceeded by ₹${Math.abs(res.remaining).toLocaleString('en-IN')}</span>`
        : `<span style="color:var(--green)">✓ ₹${res.remaining.toLocaleString('en-IN')} remaining (${(100-pct).toFixed(1)}%)</span>`
      }
    </div>
  `;
}

// ── EXPORT ──
function exportFile(type) {
  window.location.href = `/api/export/${type}`;
}

// ── BOOT: check session ──
(async () => {
  const res = await api('/api/me');
  if (res.user) {
    currentUser = res.user;
    enterApp(res.user);
  }
})();
</script>
</body>
</html>
"""

# ============================================================
# API ROUTES
# ============================================================

@app.route("/")
def index():
    return PAGE

# ---- AUTH ----

@app.route("/api/register", methods=["POST"])
def api_register():
    d = request.json
    username = d.get("username", "").strip()
    password = d.get("password", "")
    if not username or not password:
        return jsonify(ok=False, error="Username and password required")
    with get_db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username=?", (username,)
        ).fetchone()
        if exists:
            return jsonify(ok=False, error="Username already taken")
        conn.execute(
            "INSERT INTO users VALUES (?,?)", (username, hash_pw(password))
        )
    return jsonify(ok=True)

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    username = d.get("username", "").strip()
    password = d.get("password", "")
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username=? AND password=?",
            (username, hash_pw(password))
        ).fetchone()
    if not row:
        return jsonify(ok=False, error="Invalid credentials")
    session["user"] = username
    return jsonify(ok=True, user=username)

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify(ok=True)

@app.route("/api/me")
def api_me():
    return jsonify(user=session.get("user"))

# ---- EXPENSES ----

@app.route("/api/expense/add", methods=["POST"])
def api_add_expense():
    if not logged_in():
        return jsonify(ok=False, error="Not logged in")
    d = request.json
    eid  = str(uuid.uuid4())[:8]
    date = d.get("date") or datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO expenses VALUES (?,?,?,?,?,?,?)",
            (eid, current_user(), d["name"], float(d["amount"]),
             d["category"], d["payment"], date)
        )
    return jsonify(ok=True, id=eid)

@app.route("/api/expenses")
def api_expenses():
    if not logged_in():
        return jsonify(ok=False, error="Not logged in")
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, amount, category, payment, date "
            "FROM expenses WHERE username=? ORDER BY date DESC",
            (current_user(),)
        ).fetchall()
    return jsonify(expenses=[dict(r) for r in rows])

@app.route("/api/expense/delete", methods=["POST"])
def api_delete_expense():
    if not logged_in():
        return jsonify(ok=False, error="Not logged in")
    eid = request.json.get("id")
    with get_db() as conn:
        conn.execute(
            "DELETE FROM expenses WHERE id=? AND username=?",
            (eid, current_user())
        )
    return jsonify(ok=True)

# ---- STATS ----

@app.route("/api/stats")
def api_stats():
    if not logged_in():
        return jsonify(ok=False)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT amount, category, date FROM expenses WHERE username=?",
            (current_user(),)
        ).fetchall()

    if not rows:
        return jsonify(
            total=0, count=0, avg=0,
            top_cat="—", top_cat_pct=0,
            this_month=0, categories=[]
        )

    amounts    = [r["amount"] for r in rows]
    total      = round(sum(amounts), 2)
    count      = len(amounts)
    avg        = round(mean(amounts), 2)

    # top category
    cat_sums = {}
    for r in rows:
        cat_sums[r["category"]] = cat_sums.get(r["category"], 0) + r["amount"]
    top_cat = max(cat_sums, key=cat_sums.get)
    top_pct = round(cat_sums[top_cat] / total * 100, 1) if total else 0

    # this month
    now     = datetime.now()
    this_m  = sum(r["amount"] for r in rows
                  if r["date"].startswith(f"{now.year}-{now.month:02d}"))

    # categories sorted
    categories = sorted(
        [{"name": k, "amount": round(v, 2)} for k, v in cat_sums.items()],
        key=lambda x: -x["amount"]
    )

    return jsonify(
        total=total, count=count, avg=avg,
        top_cat=top_cat, top_cat_pct=top_pct,
        this_month=round(this_m, 2),
        categories=categories
    )

# ---- INSIGHTS ----

@app.route("/api/insights")
def api_insights():
    if not logged_in():
        return jsonify(ok=False)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT amount, category, payment, date FROM expenses WHERE username=?",
            (current_user(),)
        ).fetchall()

    if not rows:
        return jsonify(insights=[])

    amounts   = [r["amount"] for r in rows]
    total     = sum(amounts)
    avg       = mean(amounts)

    cat_sums  = {}
    pay_count = {}
    for r in rows:
        cat_sums[r["category"]] = cat_sums.get(r["category"], 0) + r["amount"]
        pay_count[r["payment"]]  = pay_count.get(r["payment"], 0) + 1

    top_cat   = max(cat_sums, key=cat_sums.get)
    top_pay   = max(pay_count, key=pay_count.get)
    top_pct   = round(cat_sums[top_cat] / total * 100, 1)

    insights  = [
        {"icon": "📊", "label": "Total Spending",
         "text": f"You have spent ₹{total:,.2f} across {len(amounts)} transactions."},
        {"icon": "📌", "label": "Top Category",
         "text": f"<b>{top_cat}</b> accounts for {top_pct}% of your total spending (₹{cat_sums[top_cat]:,.2f})."},
        {"icon": "💳", "label": "Favourite Payment Method",
         "text": f"You mostly pay via <b>{top_pay}</b> ({pay_count[top_pay]} transactions)."},
        {"icon": "📈", "label": "Average Transaction",
         "text": f"Your average expense is ₹{avg:,.2f} per transaction."},
    ]

    if top_pct > 40:
        insights.append({
            "icon": "⚠️", "label": "Spending Alert",
            "text": f"Heavy concentration in <b>{top_cat}</b>. Consider diversifying or reducing this category."
        })

    if avg > 5000:
        insights.append({
            "icon": "💡", "label": "Tip",
            "text": "Your average transaction is above ₹5,000. Review large recurring expenses."
        })

    max_exp  = max(amounts)
    min_exp  = min(amounts)
    insights.append({
        "icon": "🔎", "label": "Range",
        "text": f"Largest transaction: ₹{max_exp:,.2f} · Smallest: ₹{min_exp:,.2f}"
    })

    return jsonify(insights=insights)

# ---- CHARTS ----

@app.route("/api/charts")
def api_charts():
    if not logged_in():
        return jsonify(ok=False)

    BG   = "#080c10"
    SURF = "#0e1420"
    FG   = "#e2eaf5"
    COLORS = ["#00d4ff","#ff6b35","#00e5a0","#ffd166",
              "#c77dff","#ff4d6d","#4cc9f0","#f77f00"]

    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, amount, date FROM expenses WHERE username=?",
            (current_user(),)
        ).fetchall()

    # --- PIE ---
    cat_sums = {}
    for r in rows:
        cat_sums[r["category"]] = cat_sums.get(r["category"], 0) + r["amount"]

    pie_b64 = ""
    if cat_sums:
        fig, ax = plt.subplots(figsize=(5, 5), facecolor=BG)
        ax.set_facecolor(BG)
        wedges, texts, autotexts = ax.pie(
            list(cat_sums.values()),
            labels=list(cat_sums.keys()),
            autopct="%1.1f%%",
            colors=COLORS[:len(cat_sums)],
            pctdistance=0.82,
            wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
        )
        for t in texts:      t.set_color(FG); t.set_fontsize(9)
        for a in autotexts:  a.set_color("#000"); a.set_fontsize(8); a.set_fontweight("bold")
        ax.set_title("Category Distribution", color=FG, fontsize=11, pad=10)
        pie_b64 = fig_to_b64(fig)

    # --- LINE ---
    line_b64 = ""
    if rows:
        monthly = {}
        for r in rows:
            try:
                m = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b %Y")
            except:
                m = "Unknown"
            monthly[m] = monthly.get(m, 0) + r["amount"]

        fig, ax = plt.subplots(figsize=(6, 4), facecolor=BG)
        ax.set_facecolor(SURF)
        labels = list(monthly.keys())
        values = list(monthly.values())
        ax.plot(labels, values, color="#00d4ff", linewidth=2.5,
                marker="o", markersize=7, markerfacecolor="#ff6b35",
                markeredgecolor=BG, markeredgewidth=2)
        ax.fill_between(range(len(labels)), values, alpha=0.12, color="#00d4ff")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right", color=FG, fontsize=8)
        ax.tick_params(axis="y", colors=FG, labelsize=8)
        ax.spines[:].set_color("#1e2d42")
        ax.set_facecolor(SURF)
        ax.set_title("Monthly Spending Trend", color=FG, fontsize=11, pad=10)
        ax.set_ylabel("Amount (₹)", color=FG, fontsize=8)
        fig.patch.set_facecolor(BG)
        line_b64 = fig_to_b64(fig)

    return jsonify(pie=pie_b64, line=line_b64)

# ---- BUDGET ----

@app.route("/api/budget", methods=["POST"])
def api_budget():
    if not logged_in():
        return jsonify(ok=False)
    budget = float(request.json.get("budget", 0))
    with get_db() as conn:
        rows = conn.execute(
            "SELECT amount FROM expenses WHERE username=?",
            (current_user(),)
        ).fetchall()
    spent     = round(sum(r["amount"] for r in rows), 2)
    remaining = round(budget - spent, 2)
    return jsonify(budget=budget, spent=spent, remaining=remaining)

# ---- EXPORT ----

@app.route("/api/export/csv")
def api_export_csv():
    if not logged_in():
        return redirect("/")
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, amount, category, payment, date "
            "FROM expenses WHERE username=?", (current_user(),)
        ).fetchall()

    buf = io.StringIO()
    w   = csv.writer(buf)
    w.writerow(["ID","Name","Amount","Category","Payment","Date"])
    for r in rows:
        w.writerow([r["id"], r["name"], r["amount"],
                    r["category"], r["payment"], r["date"]])
    buf.seek(0)
    resp = make_response(buf.getvalue())
    resp.headers["Content-Type"]        = "text/csv"
    resp.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    return resp

@app.route("/api/export/excel")
def api_export_excel():
    if not logged_in():
        return redirect("/")
    with get_db() as conn:
        df = pd.read_sql_query(
            "SELECT id, name, amount, category, payment, date "
            "FROM expenses WHERE username=?", conn,
            params=(current_user(),)
        )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="expenses.xlsx"
    )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n  FinanceOS Web App")
    print("  Running at: http://localhost:5005\n")
    app.run(debug=True, port=5005)
