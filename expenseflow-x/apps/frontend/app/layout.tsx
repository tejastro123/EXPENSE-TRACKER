import type { Metadata, Viewport } from "next";
import { Inter, Outfit } from "next/font/google";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: {
    default: "ExpenseFlow X — AI-Powered Financial Operating System",
    template: "%s | ExpenseFlow X",
  },
  description:
    "The most intelligent personal finance platform. AI-powered expense tracking, fraud detection, investment analytics, and your personal financial copilot.",
  keywords: [
    "expense tracker",
    "personal finance",
    "AI finance",
    "budget planner",
    "investment tracking",
    "fraud detection",
    "financial planning",
    "fintech",
  ],
  authors: [{ name: "ExpenseFlow X" }],
  creator: "ExpenseFlow X",
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://expenseflowx.com",
    title: "ExpenseFlow X — AI-Powered Financial Operating System",
    description:
      "The most intelligent personal finance platform powered by AI.",
    siteName: "ExpenseFlow X",
  },
  twitter: {
    card: "summary_large_image",
    title: "ExpenseFlow X",
    description: "AI-Powered Financial Operating System",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#050814",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${outfit.variable} font-sans`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
            <Toaster
              position="top-right"
              toastOptions={{
                style: {
                  background: "#111827",
                  color: "#e5e7eb",
                  border: "1px solid rgba(255,255,255,0.08)",
                },
                success: {
                  iconTheme: { primary: "#00ff88", secondary: "#050814" },
                },
                error: {
                  iconTheme: { primary: "#f72585", secondary: "#050814" },
                },
              }}
            />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
