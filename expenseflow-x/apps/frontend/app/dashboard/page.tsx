"use client";

import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, Wallet, Shield, Brain,
  ArrowUpRight, ArrowDownRight, CreditCard, Target,
  AlertTriangle, Zap, ChevronRight, DollarSign
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar
} from "recharts";

// ── Mock Data ─────────────────────────────────────────────────────────────────

const monthlyData = [
  { month: "Jun", income: 80000, expenses: 52000, savings: 28000 },
  { month: "Jul", income: 80000, expenses: 58000, savings: 22000 },
  { month: "Aug", income: 85000, expenses: 48000, savings: 37000 },
  { month: "Sep", income: 80000, expenses: 61000, savings: 19000 },
  { month: "Oct", income: 90000, expenses: 55000, savings: 35000 },
  { month: "Nov", income: 80000, expenses: 54200, savings: 25800 },
];

const categoryData = [
  { name: "Food", value: 12000, color: "#00ff88" },
  { name: "Transport", value: 5000, color: "#00b4ff" },
  { name: "Utilities", value: 4000, color: "#9b5de5" },
  { name: "Entertainment", value: 3000, color: "#f72585" },
  { name: "Shopping", value: 8000, color: "#ffd60a" },
  { name: "Health", value: 2500, color: "#4cc9f0" },
  { name: "Other", value: 19700, color: "#374151" },
];

const recentTransactions = [
  { id: 1, title: "Swiggy Order", category: "Food", amount: -420, date: "Today", icon: "🍔", flagged: false },
  { id: 2, title: "Salary Credit", category: "Income", amount: 80000, date: "Nov 1", icon: "💰", flagged: false },
  { id: 3, title: "Netflix", category: "Subscriptions", amount: -799, date: "Oct 31", icon: "📺", flagged: false },
  { id: 4, title: "Unknown ATM TX", category: "Other", amount: -5000, date: "Oct 30", icon: "🚨", flagged: true },
  { id: 5, title: "Zepto Groceries", category: "Food", amount: -1240, date: "Oct 29", icon: "🛒", flagged: false },
];

const aiInsights = [
  {
    icon: AlertTriangle,
    color: "#f72585",
    bg: "rgba(247, 37, 133, 0.1)",
    title: "Unusual ATM Transaction",
    desc: "₹5,000 withdrawal flagged. 3σ above your norm.",
    cta: "Review",
  },
  {
    icon: TrendingDown,
    color: "#ffd60a",
    bg: "rgba(255, 214, 10, 0.1)",
    title: "Food spending is high",
    desc: "₹2,800 above your monthly food budget.",
    cta: "Optimize",
  },
  {
    icon: Zap,
    color: "#00ff88",
    bg: "rgba(0, 255, 136, 0.1)",
    title: "SIP Milestone!",
    desc: "Your mutual funds crossed ₹1L in total value.",
    cta: "View",
  },
];

const healthScores = [
  { label: "Savings", score: 78, color: "#00ff88" },
  { label: "Debt", score: 92, color: "#00b4ff" },
  { label: "Budget", score: 65, color: "#ffd60a" },
  { label: "Investment", score: 71, color: "#9b5de5" },
  { label: "Emergency", score: 100, color: "#4cc9f0" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const cardVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};

// ── Components ────────────────────────────────────────────────────────────────

const StatCard = ({ title, value, change, icon: Icon, color, prefix = "₹" }: any) => (
  <motion.div variants={cardVariants} className="stat-card glass-card-hover">
    <div className="flex items-start justify-between mb-4">
      <div>
        <p className="text-gray-500 text-sm font-medium">{title}</p>
        <p className="text-2xl font-black text-white mt-1 tabular-nums">
          {prefix}{typeof value === "number" ? value.toLocaleString("en-IN") : value}
        </p>
      </div>
      <div className="p-3 rounded-xl" style={{ background: `${color}15` }}>
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
    </div>
    {change !== undefined && (
      <div className={`flex items-center gap-1 text-sm font-medium ${change >= 0 ? "text-[#00ff88]" : "text-[#f72585]"}`}>
        {change >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
        {Math.abs(change)}% vs last month
      </div>
    )}
  </motion.div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-sm">
        <p className="text-gray-400 mb-2">{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ color: p.color }} className="font-semibold">
            {p.name}: ₹{p.value.toLocaleString("en-IN")}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function DashboardPage() {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={cardVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Good afternoon, Tejas 👋</h1>
          <p className="text-gray-500 mt-1">November 2024 · Financial Overview</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="glass-card px-4 py-2 flex items-center gap-2">
            <Brain className="w-4 h-4 text-[#00ff88]" />
            <span className="text-sm text-gray-300">AI Score: <strong className="text-[#00ff88]">91/100</strong></span>
          </div>
        </div>
      </motion.div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Balance" value={703000} change={4.2} icon={Wallet} color="#00ff88" />
        <StatCard title="Monthly Expenses" value={54200} change={-1.8} icon={TrendingDown} color="#f72585" />
        <StatCard title="Monthly Savings" value={25800} change={12.3} icon={TrendingUp} color="#00b4ff" />
        <StatCard title="Net Worth" value={703000} change={8.7} icon={DollarSign} color="#9b5de5" />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Cash Flow Chart */}
        <motion.div variants={cardVariants} className="glass-card p-6 xl:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Cash Flow</h2>
              <p className="text-gray-500 text-sm">Income vs Expenses vs Savings</p>
            </div>
            <select className="text-sm bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-gray-400 focus:outline-none">
              <option>Last 6 months</option>
              <option>Last 12 months</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={monthlyData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="income-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expense-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f72585" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#f72585" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="savings-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00b4ff" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#00b4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" stroke="#374151" tick={{ fill: "#6b7280", fontSize: 12 }} />
              <YAxis stroke="#374151" tick={{ fill: "#6b7280", fontSize: 12 }}
                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="income" name="Income" stroke="#00ff88" strokeWidth={2} fill="url(#income-grad)" />
              <Area type="monotone" dataKey="expenses" name="Expenses" stroke="#f72585" strokeWidth={2} fill="url(#expense-grad)" />
              <Area type="monotone" dataKey="savings" name="Savings" stroke="#00b4ff" strokeWidth={2} fill="url(#savings-grad)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Category Pie */}
        <motion.div variants={cardVariants} className="glass-card p-6">
          <h2 className="text-lg font-bold text-white mb-1">Spending by Category</h2>
          <p className="text-gray-500 text-sm mb-4">November 2024</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {categoryData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} opacity={0.85} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`} contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", color: "#e5e7eb" }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {categoryData.slice(0, 5).map((cat) => (
              <div key={cat.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: cat.color }} />
                  <span className="text-gray-400 text-xs">{cat.name}</span>
                </div>
                <span className="text-white text-xs font-semibold tabular-nums">
                  ₹{cat.value.toLocaleString("en-IN")}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent Transactions */}
        <motion.div variants={cardVariants} className="glass-card p-6 xl:col-span-1">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-white">Recent Transactions</h2>
            <button className="text-[#00ff88] text-sm hover:text-[#00ff88]/80 flex items-center gap-1">
              View all <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            {recentTransactions.map((tx) => (
              <div key={tx.id} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-base ${tx.flagged ? "bg-[#f72585]/10 border border-[#f72585]/20" : "bg-white/5"}`}>
                  {tx.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white truncate">{tx.title}</p>
                    {tx.flagged && <AlertTriangle className="w-3.5 h-3.5 text-[#f72585] flex-shrink-0" />}
                  </div>
                  <p className="text-xs text-gray-500">{tx.category} · {tx.date}</p>
                </div>
                <span className={`text-sm font-bold tabular-nums flex-shrink-0 ${tx.amount > 0 ? "text-[#00ff88]" : "text-white"}`}>
                  {tx.amount > 0 ? "+" : ""}₹{Math.abs(tx.amount).toLocaleString("en-IN")}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* AI Insights */}
        <motion.div variants={cardVariants} className="glass-card p-6">
          <div className="flex items-center gap-2 mb-5">
            <Brain className="w-5 h-5 text-[#00ff88]" />
            <h2 className="text-lg font-bold text-white">AI Insights</h2>
          </div>
          <div className="space-y-3">
            {aiInsights.map((insight) => (
              <div key={insight.title} className="p-4 rounded-xl border border-white/5" style={{ background: insight.bg }}>
                <div className="flex items-start gap-3">
                  <insight.icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: insight.color }} />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-white">{insight.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{insight.desc}</p>
                  </div>
                  <button className="text-xs font-medium flex-shrink-0" style={{ color: insight.color }}>
                    {insight.cta}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Health Score Breakdown */}
        <motion.div variants={cardVariants} className="glass-card p-6">
          <h2 className="text-lg font-bold text-white mb-1">Health Score Breakdown</h2>
          <div className="flex items-baseline gap-2 mb-5">
            <span className="text-4xl font-black text-gradient">91</span>
            <span className="text-gray-400">/100 · Grade A+</span>
          </div>
          <div className="space-y-4">
            {healthScores.map((s) => (
              <div key={s.label}>
                <div className="flex justify-between mb-1.5">
                  <span className="text-sm text-gray-400">{s.label}</span>
                  <span className="text-sm font-bold" style={{ color: s.color }}>{s.score}</span>
                </div>
                <div className="progress-neon">
                  <motion.div
                    className="progress-neon-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${s.score}%` }}
                    transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
                    style={{ background: `linear-gradient(90deg, ${s.color}88, ${s.color})` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-4 py-2.5 rounded-xl border border-[#00ff88]/20 text-[#00ff88] text-sm font-medium hover:bg-[#00ff88]/5 transition-colors flex items-center justify-center gap-2">
            <Brain className="w-4 h-4" /> Get AI Recommendations
          </button>
        </motion.div>
      </div>
    </motion.div>
  );
}
