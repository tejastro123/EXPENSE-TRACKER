import type { Config } from "tailwindcss";
import { fontFamily } from "tailwindcss/defaultTheme";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        // ExpenseFlow X Brand Colors — neon fintech dark theme
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom EFX colors
        neon: {
          green: "#00ff88",
          blue: "#00b4ff",
          purple: "#9b5de5",
          pink: "#f72585",
          gold: "#ffd60a",
          cyan: "#4cc9f0",
        },
        efx: {
          dark: "#050814",
          darker: "#020510",
          surface: "#0d1117",
          card: "#111827",
          border: "#1f2937",
          muted: "#374151",
        },
      },
      fontFamily: {
        sans: ["Inter", "Outfit", ...fontFamily.sans],
        mono: ["JetBrains Mono", "Fira Code", ...fontFamily.mono],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "slide-in-from-bottom": {
          from: { transform: "translateY(100%)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 5px rgba(0, 255, 136, 0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(0, 255, 136, 0.8), 0 0 40px rgba(0, 255, 136, 0.4)" },
        },
        "neon-pulse": {
          "0%, 100%": { textShadow: "0 0 4px #00ff88, 0 0 8px #00ff88" },
          "50%": { textShadow: "0 0 10px #00ff88, 0 0 20px #00ff88, 0 0 40px #00ff88" },
        },
        "counter-up": {
          from: { transform: "translateY(20px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "slide-in": "slide-in-from-bottom 0.4s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "pulse-glow": "pulse-glow 2s infinite",
        "neon-pulse": "neon-pulse 2s infinite",
        "counter-up": "counter-up 0.5s ease-out",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-gradient": "linear-gradient(135deg, #050814 0%, #0d1117 50%, #0a0f1e 100%)",
        "card-gradient": "linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)",
        "neon-gradient": "linear-gradient(135deg, #00ff88 0%, #00b4ff 50%, #9b5de5 100%)",
        "gold-gradient": "linear-gradient(135deg, #ffd60a 0%, #ff9500 100%)",
      },
      boxShadow: {
        "neon-green": "0 0 20px rgba(0, 255, 136, 0.3), 0 0 40px rgba(0, 255, 136, 0.1)",
        "neon-blue": "0 0 20px rgba(0, 180, 255, 0.3), 0 0 40px rgba(0, 180, 255, 0.1)",
        "neon-purple": "0 0 20px rgba(155, 93, 229, 0.3), 0 0 40px rgba(155, 93, 229, 0.1)",
        "glass": "0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)",
        "card-hover": "0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 255, 136, 0.05)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
