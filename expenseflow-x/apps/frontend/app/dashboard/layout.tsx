"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Receipt, BarChart3, Brain, Target,
  CreditCard, Bell, Settings, LogOut, Wallet, Menu, X,
  TrendingUp, Shield, PiggyBank, Zap
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/dashboard/expenses", icon: Receipt, label: "Expenses" },
  { href: "/dashboard/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/dashboard/investments", icon: TrendingUp, label: "Investments" },
  { href: "/dashboard/budgets", icon: PiggyBank, label: "Budgets" },
  { href: "/dashboard/goals", icon: Target, label: "Goals" },
  { href: "/dashboard/subscriptions", icon: CreditCard, label: "Subscriptions" },
  { href: "/dashboard/copilot", icon: Brain, label: "AI Copilot" },
  { href: "/dashboard/fraud", icon: Shield, label: "Fraud Alerts" },
  { href: "/dashboard/notifications", icon: Bell, label: "Notifications" },
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();

  return (
    <div className="min-h-screen flex bg-[#050814]">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed left-0 top-0 bottom-0 z-40 w-64 flex flex-col"
            style={{
              background: "rgba(13, 17, 23, 0.95)",
              backdropFilter: "blur(20px)",
              borderRight: "1px solid rgba(255,255,255,0.05)",
            }}
          >
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-6 border-b border-white/5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00ff88] to-[#00b4ff] flex items-center justify-center">
                <Wallet className="w-5 h-5 text-[#050814]" />
              </div>
              <span className="text-lg font-bold text-gradient">ExpenseFlow X</span>
            </div>

            {/* AI Health Score Pill */}
            <div className="mx-4 mt-4 p-3 rounded-xl border border-[#00ff88]/15 bg-[#00ff88]/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Financial Health</span>
                <span className="text-xs font-bold text-[#00ff88]">91/100</span>
              </div>
              <div className="progress-neon">
                <motion.div
                  className="progress-neon-fill"
                  initial={{ width: 0 }}
                  animate={{ width: "91%" }}
                  transition={{ delay: 0.5, duration: 1, ease: "easeOut" }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">Grade: A+ · Excellent</div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 overflow-y-auto no-scrollbar">
              <div className="space-y-1">
                {navItems.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link key={item.href} href={item.href}>
                      <motion.div
                        whileHover={{ x: 3 }}
                        className={`nav-item ${isActive ? "active" : ""}`}
                      >
                        <item.icon className="w-5 h-5 flex-shrink-0" />
                        <span className="text-sm font-medium">{item.label}</span>
                        {item.label === "Fraud Alerts" && (
                          <span className="ml-auto w-2 h-2 bg-[#f72585] rounded-full animate-pulse" />
                        )}
                        {item.label === "Notifications" && (
                          <span className="ml-auto badge-warning py-0.5 px-1.5 text-[10px]">3</span>
                        )}
                      </motion.div>
                    </Link>
                  );
                })}
              </div>
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-white/5">
              <div className="flex items-center gap-3 px-2 py-2">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold">
                  T
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">Tejas</div>
                  <div className="text-xs text-gray-500 truncate">tejas@example.com</div>
                </div>
                <button className="text-gray-600 hover:text-red-400 transition-colors">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}>
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex items-center gap-4 px-6 py-4 border-b border-white/5"
          style={{ background: "rgba(5, 8, 20, 0.9)", backdropFilter: "blur(20px)" }}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex-1" />

          {/* Quick Stats in Header */}
          <div className="hidden md:flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs text-gray-500">Total Balance</div>
              <div className="text-sm font-bold text-white tabular-nums">₹7,03,000</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">This Month</div>
              <div className="text-sm font-bold text-[#f72585] tabular-nums">-₹54,200</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">Invested</div>
              <div className="text-sm font-bold text-[#00ff88] tabular-nums">₹3,50,000</div>
            </div>
          </div>

          {/* Notifications Bell */}
          <button className="relative p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-[#f72585] rounded-full" />
          </button>

          {/* AI Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#00ff88]/20 bg-[#00ff88]/5">
            <Zap className="w-3.5 h-3.5 text-[#00ff88]" />
            <span className="text-xs text-[#00ff88] font-medium">AI Active</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
