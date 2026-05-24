"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  TrendingUp, Shield, Brain, Zap, BarChart3,
  ArrowRight, ChevronRight, Star, CheckCircle2,
  Wallet, Target, Bell, CreditCard
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI Financial Copilot",
    description: "Ask anything. Get instant, personalized financial advice powered by GPT-4.",
    color: "neon-green",
    gradient: "from-emerald-500/20 to-cyan-500/20",
  },
  {
    icon: Shield,
    title: "Real-Time Fraud Detection",
    description: "ML-powered anomaly detection monitors every transaction for suspicious activity.",
    color: "neon-blue",
    gradient: "from-blue-500/20 to-purple-500/20",
  },
  {
    icon: TrendingUp,
    title: "Predictive Analytics",
    description: "Forecast your expenses, cash flow, and savings trajectory with XGBoost + LSTM.",
    color: "neon-purple",
    gradient: "from-purple-500/20 to-pink-500/20",
  },
  {
    icon: Target,
    title: "Goal-Based Planning",
    description: "AI creates personalized roadmaps for every financial goal you set.",
    color: "neon-gold",
    gradient: "from-yellow-500/20 to-orange-500/20",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Sankey diagrams, heatmaps, radar charts, and trend analysis — all in real-time.",
    color: "neon-cyan",
    gradient: "from-cyan-500/20 to-blue-500/20",
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description: "Budget alerts, fraud warnings, and AI insights delivered instantly.",
    color: "neon-pink",
    gradient: "from-pink-500/20 to-red-500/20",
  },
];

const stats = [
  { label: "Transactions Analyzed", value: "2M+", suffix: "" },
  { label: "Fraud Detected", value: "₹4.2Cr", suffix: "saved" },
  { label: "Active Users", value: "50K+", suffix: "" },
  { label: "AI Accuracy", value: "94.7", suffix: "%" },
];

const testimonials = [
  {
    name: "Priya Sharma",
    role: "Software Engineer, Bangalore",
    text: "ExpenseFlow X completely transformed how I think about money. The AI copilot is like having a personal CFO.",
    rating: 5,
  },
  {
    name: "Rahul Menon",
    role: "Freelance Designer, Mumbai",
    text: "The fraud detection caught a suspicious transaction before I even noticed. Absolutely incredible.",
    rating: 5,
  },
  {
    name: "Ananya Iyer",
    role: "Product Manager, Hyderabad",
    text: "The financial health score gave me a clear picture of where I stand and exactly what to improve.",
    rating: 5,
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050814] text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-5 border-b border-white/5 backdrop-glass bg-[#050814]/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00ff88] to-[#00b4ff] flex items-center justify-center">
            <Wallet className="w-5 h-5 text-[#050814]" />
          </div>
          <span className="text-xl font-bold text-gradient">ExpenseFlow X</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          {["Features", "AI Modules", "Pricing", "Docs"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase().replace(" ", "-")}`}
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              {item}
            </a>
          ))}
        </div>
        <div className="flex items-center gap-4">
          <Link href="/auth/login" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">
            Sign In
          </Link>
          <Link href="/auth/register" className="btn-neon text-sm">
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20">
        {/* Background Grid */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0,255,136,0.05) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0,255,136,0.05) 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
          }}
        />

        {/* Radial glow orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#00ff88]/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#00b4ff]/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#9b5de5]/3 rounded-full blur-3xl" />

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 text-center max-w-5xl mx-auto px-6"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#00ff88]/20 bg-[#00ff88]/5 mb-8"
          >
            <Zap className="w-4 h-4 text-[#00ff88]" />
            <span className="text-[#00ff88] text-sm font-medium">AI-Native Fintech Intelligence Platform</span>
          </motion.div>

          <h1 className="text-6xl md:text-8xl font-black mb-6 leading-tight tracking-tight">
            Your Money,{" "}
            <span className="text-gradient">
              Supercharged
            </span>{" "}
            by AI
          </h1>

          <p className="text-xl text-gray-400 mb-10 max-w-3xl mx-auto leading-relaxed">
            Not just an expense tracker. An{" "}
            <span className="text-white font-semibold">AI-powered financial operating system</span>{" "}
            that thinks, predicts, and protects your wealth — 24/7.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/auth/register" className="btn-neon text-base px-8 py-4 flex items-center gap-2 w-full sm:w-auto justify-center">
              Start for Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/dashboard" className="btn-ghost text-base px-8 py-4 flex items-center gap-2 w-full sm:w-auto justify-center">
              View Live Demo
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>

          {/* Social Proof */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex items-center justify-center gap-2 mt-8 text-gray-500 text-sm"
          >
            <div className="flex -space-x-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="w-7 h-7 rounded-full border-2 border-[#050814] bg-gradient-to-br from-gray-600 to-gray-800"
                />
              ))}
            </div>
            <span>Join <strong className="text-white">50,000+</strong> users managing ₹500Cr+ in finances</span>
          </motion.div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8"
          >
            {stats.map((stat) => (
              <motion.div key={stat.label} variants={itemVariants} className="text-center">
                <div className="text-3xl md:text-4xl font-black text-gradient mb-1">
                  {stat.value}
                  <span className="text-lg ml-1">{stat.suffix}</span>
                </div>
                <div className="text-gray-500 text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-black mb-4">
            Everything you need to{" "}
            <span className="text-gradient">master your money</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            7 AI modules. Dozens of features. One unified financial intelligence platform.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              whileHover={{ y: -4, scale: 1.01 }}
              className="glass-card p-8 group cursor-pointer"
            >
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-5 group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-white">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              <div className="mt-5 flex items-center gap-2 text-[#00ff88] text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                Learn more <ChevronRight className="w-4 h-4" />
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* AI Copilot Demo */}
      <section id="ai-modules" className="py-24 border-y border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="badge-success inline-flex mb-6">AI Copilot</div>
              <h2 className="text-4xl font-black mb-6">
                Ask anything about{" "}
                <span className="text-gradient">your finances</span>
              </h2>
              <p className="text-gray-400 text-lg mb-8 leading-relaxed">
                Your personal CFO, powered by GPT-4 with real financial context.
                It knows your income, expenses, debts, and goals — and gives advice that actually applies to you.
              </p>
              <ul className="space-y-4">
                {[
                  "Can I afford a ₹1.2L laptop next month?",
                  "How much should I invest to retire at 45?",
                  "Which subscriptions am I wasting money on?",
                  "Explain my biggest expense categories this year",
                ].map((q) => (
                  <li key={q} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#00ff88] mt-0.5 flex-shrink-0" />
                    <span className="text-gray-300 italic">"{q}"</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Chat Demo Preview */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00ff88] to-[#00b4ff] flex items-center justify-center">
                  <Brain className="w-5 h-5 text-[#050814]" />
                </div>
                <div>
                  <div className="font-semibold text-white">FinanceIQ Copilot</div>
                  <div className="text-xs text-[#00ff88] flex items-center gap-1">
                    <span className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse" />
                    Online & analyzing your data
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="chat-bubble-ai text-sm leading-relaxed">
                  👋 Hi! I'm FinanceIQ. I've analyzed your last 90 days of transactions.
                  Your spending is <strong className="text-[#00ff88]">18% above average</strong> this month —
                  mainly due to dining (₹8,400 vs ₹5,200 usual). Want a detailed breakdown?
                </div>
                <div className="chat-bubble-user text-sm">
                  Can I afford a ₹1.2L laptop next month?
                </div>
                <div className="chat-bubble-ai text-sm leading-relaxed">
                  📊 Based on your finances:
                  <br/><br/>
                  • Monthly surplus: <strong className="text-[#00ff88]">₹14,200</strong><br/>
                  • Current savings: <strong className="text-white">₹1,85,000</strong><br/>
                  • Emergency fund: ✅ 6 months covered<br/><br/>
                  <strong className="text-[#00ff88]">Yes!</strong> You can comfortably afford it.
                  I'd recommend EMI at 0% for 6 months to preserve cash flow. 💡
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <input
                  type="text"
                  placeholder="Ask FinanceIQ anything..."
                  className="flex-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-[#00ff88]/30"
                />
                <button className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#00ff88] to-[#00b4ff] text-[#050814] font-semibold text-sm">
                  Send
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl font-black mb-4">
            Trusted by <span className="text-gradient">financially savvy</span> Indians
          </h2>
        </motion.div>
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {testimonials.map((t) => (
            <motion.div key={t.name} variants={itemVariants} className="glass-card p-6">
              <div className="flex mb-4">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 text-[#ffd60a] fill-[#ffd60a]" />
                ))}
              </div>
              <p className="text-gray-300 mb-6 leading-relaxed italic">"{t.text}"</p>
              <div>
                <div className="font-semibold text-white">{t.name}</div>
                <div className="text-gray-500 text-sm">{t.role}</div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="py-24 border-t border-white/5">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto px-6 text-center"
        >
          <h2 className="text-5xl font-black mb-6">
            Ready to take control of{" "}
            <span className="text-gradient">your financial future?</span>
          </h2>
          <p className="text-gray-400 text-lg mb-10 max-w-2xl mx-auto">
            Join 50,000+ users who have already transformed their relationship with money.
          </p>
          <Link href="/auth/register" className="btn-neon text-lg px-10 py-5 inline-flex items-center gap-3">
            Start Free Today
            <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="text-gray-600 text-sm mt-4">No credit card required. Free forever plan available.</p>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00ff88] to-[#00b4ff] flex items-center justify-center">
              <Wallet className="w-4 h-4 text-[#050814]" />
            </div>
            <span className="text-lg font-bold text-gradient">ExpenseFlow X</span>
          </div>
          <p className="text-gray-600 text-sm">
            © 2024 ExpenseFlow X. AI-Powered Financial Intelligence Platform.
          </p>
        </div>
      </footer>
    </div>
  );
}
