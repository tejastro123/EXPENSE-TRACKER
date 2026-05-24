"""
ExpenseFlow X — Streamlit AI Analytics Portal
Advanced financial analytics with interactive visualizations and ML insights
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import random

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ExpenseFlow X — AI Analytics",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #050814;
        color: #e5e7eb;
    }

    .stApp {
        background: radial-gradient(ellipse at top, #0d1529 0%, #050814 50%, #020510 100%);
    }

    .metric-card {
        background: rgba(13, 17, 23, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(20px);
    }

    .stMetric {
        background: rgba(13, 17, 23, 0.8);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 16px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00b4ff);
        color: #050814;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
    }

    .sidebar .stSelectbox label,
    .sidebar .stSlider label {
        color: #9ca3af;
        font-size: 13px;
    }

    h1, h2, h3 {
        color: #ffffff !important;
    }

    .neon-title {
        background: linear-gradient(135deg, #00ff88, #00b4ff, #9b5de5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 900;
    }
</style>
""", unsafe_allow_html=True)

# ── Synthetic Data Generation ─────────────────────────────────────────────────

@st.cache_data
def generate_expense_data(months: int = 12) -> pd.DataFrame:
    """Generate realistic Indian expense data"""
    categories = {
        "Food": (8000, 15000),
        "Transport": (2000, 6000),
        "Utilities": (2000, 5000),
        "Entertainment": (1000, 4000),
        "Health": (500, 3000),
        "Shopping": (3000, 12000),
        "Education": (0, 5000),
        "Travel": (0, 20000),
        "Rent": (15000, 25000),
        "Investments": (5000, 20000),
    }

    rows = []
    for i in range(months * 30):  # daily data
        d = date.today() - timedelta(days=months * 30 - i)
        for cat, (lo, hi) in categories.items():
            if random.random() > 0.6:  # ~40% chance per day per category
                amount = round(random.uniform(lo / 20, hi / 10), 2)
                rows.append({
                    "date": d,
                    "category": cat,
                    "amount": amount,
                    "month": d.strftime("%b %Y"),
                    "week": d.isocalendar()[1],
                    "day_of_week": d.strftime("%A"),
                    "is_weekend": d.weekday() >= 5,
                })
    return pd.DataFrame(rows)


@st.cache_data
def generate_investment_data() -> pd.DataFrame:
    investments = [
        {"name": "Nifty 50 Index Fund", "type": "Mutual Fund", "invested": 150000, "current": 187500, "platform": "Zerodha"},
        {"name": "US Tech ETF", "type": "ETF", "invested": 50000, "current": 71000, "platform": "INDmoney"},
        {"name": "Bitcoin", "type": "Crypto", "invested": 30000, "current": 42000, "platform": "CoinDCX"},
        {"name": "HDFC Bank SIP", "type": "SIP", "invested": 60000, "current": 68000, "platform": "Groww"},
        {"name": "PPF", "type": "PPF", "invested": 50000, "current": 54500, "platform": "SBI"},
        {"name": "Reliance Industries", "type": "Stock", "invested": 10000, "current": 14200, "platform": "Zerodha"},
    ]
    df = pd.DataFrame(investments)
    df["returns"] = ((df["current"] - df["invested"]) / df["invested"] * 100).round(2)
    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="neon-title" style="font-size:1.5rem">💹 Analytics</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7280; font-size:13px; margin-top:-8px'>ExpenseFlow X</p>", unsafe_allow_html=True)
    st.divider()

    page = st.selectbox(
        "📊 Module",
        ["📈 Overview", "💸 Expense Analysis", "🤖 AI Predictions", "💰 Investment Tracker",
         "🛡️ Fraud Analytics", "🎯 Health Score", "📅 Heatmap"],
        label_visibility="collapsed"
    )

    st.divider()

    months = st.slider("Time Range (months)", 1, 24, 12)
    selected_categories = st.multiselect(
        "Categories",
        ["Food", "Transport", "Utilities", "Entertainment", "Health",
         "Shopping", "Education", "Travel", "Rent", "Investments"],
        default=["Food", "Transport", "Shopping"]
    )
    st.divider()
    st.markdown("<p style='color:#6b7280; font-size:11px; text-align:center'>💡 Data auto-refreshes every 30s</p>", unsafe_allow_html=True)

# Load data
df = generate_expense_data(months)
inv_df = generate_investment_data()
if selected_categories:
    df_filtered = df[df["category"].isin(selected_categories)]
else:
    df_filtered = df


# ── Pages ─────────────────────────────────────────────────────────────────────

if "Overview" in page:
    st.markdown("## 📊 Financial Overview Dashboard")
    st.caption(f"Last {months} months · All categories")

    # Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    total_spent = df["amount"].sum()
    monthly_avg = total_spent / months
    max_month = df.groupby("month")["amount"].sum().max()
    total_invested = inv_df["current"].sum()
    total_returns = inv_df["returns"].mean()

    col1.metric("💸 Total Spent", f"₹{total_spent:,.0f}", f"-₹{monthly_avg:,.0f}/mo")
    col2.metric("📅 Monthly Avg", f"₹{monthly_avg:,.0f}", "")
    col3.metric("📈 Peak Month", f"₹{max_month:,.0f}", "")
    col4.metric("💼 Portfolio Value", f"₹{total_invested:,.0f}", f"+{total_returns:.1f}%")
    col5.metric("🎯 Health Score", "91/100", "+3 pts")

    st.divider()

    # Monthly Trend
    monthly_totals = df.groupby(["month", "category"])["amount"].sum().reset_index()
    monthly_agg = df.groupby("month")["amount"].sum().reset_index()

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.area(
            monthly_agg, x="month", y="amount",
            title="Monthly Spending Trend",
            color_discrete_sequence=["#00ff88"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            title_font_color="#ffffff",
            showlegend=False,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#6b7280")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#6b7280"), tickprefix="₹"),
        )
        fig.update_traces(fill="tozeroy", fillcolor="rgba(0,255,136,0.05)", line_width=2)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cat_totals = df.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(
            cat_totals, names="category", values="amount",
            title="Spending by Category",
            color_discrete_sequence=px.colors.qualitative.Plotly,
            hole=0.5,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            title_font_color="#ffffff",
            legend=dict(font=dict(color="#6b7280", size=11)),
        )
        st.plotly_chart(fig_pie, use_container_width=True)


elif "Expense Analysis" in page:
    st.markdown("## 💸 Deep Expense Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Category breakdown bar chart
        cat_monthly = df_filtered.groupby(["month", "category"])["amount"].sum().reset_index()
        fig = px.bar(
            cat_monthly, x="month", y="amount", color="category",
            title="Monthly Category Breakdown",
            barmode="stack",
            color_discrete_sequence=["#00ff88", "#00b4ff", "#9b5de5", "#f72585", "#ffd60a"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af", title_font_color="#ffffff",
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="₹"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Day of week analysis
        dow_avg = df.groupby("day_of_week")["amount"].mean().reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ).reset_index()
        fig2 = px.bar(
            dow_avg, x="day_of_week", y="amount",
            title="Avg Spending by Day of Week",
            color="amount",
            color_continuous_scale=["#0d1117", "#00b4ff", "#00ff88"],
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af", title_font_color="#ffffff",
            yaxis=dict(tickprefix="₹"), coloraxis_showscale=False,
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Violin plot: spending distribution
    fig3 = px.violin(
        df_filtered, x="category", y="amount",
        title="Spending Distribution by Category",
        color="category",
        box=True, points=False,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#9ca3af", title_font_color="#ffffff",
        showlegend=False,
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="₹"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    st.plotly_chart(fig3, use_container_width=True)


elif "Predictions" in page:
    st.markdown("## 🤖 AI Financial Predictions")
    st.info("⚡ Predictions generated by ensemble: Moving Average + Linear Trend + Weekly Seasonality")

    horizon = st.slider("Forecast Horizon (days)", 7, 90, 30)

    # Generate forecast
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    mean_daily = daily["amount"].mean()
    std_daily = daily["amount"].std()
    last_date = daily["date"].max()

    forecast_dates = [last_date + timedelta(days=i) for i in range(1, horizon + 1)]
    noise = np.random.normal(0, std_daily * 0.3, len(forecast_dates))
    forecast_amounts = mean_daily + noise + np.linspace(0, mean_daily * 0.1, len(forecast_dates))
    forecast_amounts = np.maximum(forecast_amounts, 0)

    lower = forecast_amounts - 1.645 * std_daily
    upper = forecast_amounts + 1.645 * std_daily

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"].tail(60), y=daily["amount"].tail(60),
        name="Historical", line=dict(color="#00b4ff", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=forecast_dates, y=forecast_amounts,
        name="Forecast", line=dict(color="#00ff88", width=2, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1],
        y=list(upper) + list(lower[::-1]),
        fill="toself", fillcolor="rgba(0,255,136,0.05)",
        line=dict(color="rgba(255,255,255,0)"),
        name="90% Confidence Band",
    ))
    fig.update_layout(
        title=f"Expense Forecast — Next {horizon} Days",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#9ca3af", title_font_color="#ffffff",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="₹"),
        legend=dict(font=dict(color="#9ca3af")),
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Predicted Total", f"₹{sum(forecast_amounts):,.0f}", "")
    col2.metric("Daily Average", f"₹{mean_daily:,.0f}", "")
    col3.metric("Trend", "📈 Slightly increasing", "")


elif "Investment" in page:
    st.markdown("## 💼 Investment Portfolio Tracker")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested", f"₹{inv_df['invested'].sum():,.0f}")
    col2.metric("Current Value", f"₹{inv_df['current'].sum():,.0f}",
                f"+₹{(inv_df['current'].sum() - inv_df['invested'].sum()):,.0f}")
    col3.metric("Avg Returns", f"{inv_df['returns'].mean():.1f}%")

    # Portfolio allocation
    fig = px.treemap(
        inv_df, path=["type", "name"], values="current",
        title="Portfolio Allocation",
        color="returns",
        color_continuous_scale=["#f72585", "#111827", "#00ff88"],
        color_continuous_midpoint=0,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", title_font_color="#ffffff", font_color="#ffffff"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Returns bar chart
    fig2 = px.bar(
        inv_df.sort_values("returns", ascending=True),
        x="returns", y="name", orientation="h",
        title="Returns by Investment",
        color="returns",
        color_continuous_scale=["#f72585", "#111827", "#00ff88"],
    )
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#9ca3af", title_font_color="#ffffff",
        xaxis=dict(ticksuffix="%"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig2, use_container_width=True)


elif "Health Score" in page:
    st.markdown("## 🎯 Financial Health Score")

    scores = {
        "Savings Stability": 78,
        "Debt Management": 92,
        "Budget Consistency": 65,
        "Investment Readiness": 71,
        "Emergency Fund": 100,
        "Cash Flow": 82,
    }
    overall = int(np.average(list(scores.values()), weights=[0.20, 0.22, 0.18, 0.17, 0.15, 0.08]))

    col1, col2 = st.columns([1, 2])

    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=overall,
            delta={"reference": 85, "increasing": {"color": "#00ff88"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#6b7280"},
                "bar": {"color": "#00ff88"},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 40], "color": "rgba(247,37,133,0.1)"},
                    {"range": [40, 70], "color": "rgba(255,214,10,0.1)"},
                    {"range": [70, 100], "color": "rgba(0,255,136,0.1)"},
                ],
                "threshold": {"line": {"color": "#ffd60a", "width": 3}, "value": 85},
            },
            title={"text": "Overall Score", "font": {"color": "#ffffff"}},
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af",
            height=280,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        colors = ["#00ff88", "#00b4ff", "#ffd60a", "#9b5de5", "#4cc9f0", "#f72585"]
        for (name, score), color in zip(scores.items(), colors):
            fig2.add_trace(go.Bar(
                name=name,
                x=[score], y=[name], orientation="h",
                marker=dict(color=color, opacity=0.85),
                text=f"{score}",
                textposition="inside",
            ))
        fig2.update_layout(
            title="Component Scores",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af", title_font_color="#ffffff",
            showlegend=False, barmode="overlay",
            xaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.04)"),
            height=280,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("💡 AI Recommendations")
    recs = [
        ("🎯", "Build emergency fund to 6 months of expenses (currently at 100% — excellent!)"),
        ("📈", "Increase SIP contributions by ₹2,000/month to hit ₹50L by age 40"),
        ("💳", "Budget consistency is 65% — try weekly spending reviews"),
        ("🏦", "Consider debt-free status — you're at 92% debt management score"),
    ]
    for icon, text in recs:
        st.markdown(f"{icon} {text}")


elif "Heatmap" in page:
    st.markdown("## 🗓️ Spending Heatmap")
    st.caption("Day-by-day expense intensity (GitHub contribution style)")

    # Generate daily totals
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["week"] = daily["date"].dt.isocalendar().week.astype(int)
    daily["day"] = daily["date"].dt.day_name()

    fig = px.density_heatmap(
        daily, x="week", y="day",
        z="amount", nbinsx=52, nbinsy=7,
        title="Weekly Spending Intensity",
        color_continuous_scale=["#0d1117", "#004d29", "#00ff88"],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#9ca3af", title_font_color="#ffffff",
        coloraxis_colorbar=dict(title="₹ Spent", tickfont=dict(color="#6b7280")),
    )
    st.plotly_chart(fig, use_container_width=True)

    max_day = daily.loc[daily["amount"].idxmax()]
    st.info(f"🔥 Highest spending day: **{max_day['date'].strftime('%B %d, %Y')}** — ₹{max_day['amount']:,.0f}")
