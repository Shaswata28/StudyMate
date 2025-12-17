import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./client/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
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
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
        studymate: {
          orange: "#FEAE01",
          green: "#1FC209",
          gray: "#D9D9D9",
          darkgray: "#404040",
          black: "#1E1E1E",
        },
      },
      fontFamily: {
        audiowide: ["Audiowide", "sans-serif"],
        koulen: ["Koulen", "sans-serif"],
        "roboto-slab": ["Roboto Slab", "serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      // ... keep existing keyframes/animation ...
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "expand-collapse": {
          from: { maxHeight: "0", opacity: "0" },
          to: { maxHeight: "1000px", opacity: "1" },
        },
        "scale-pulse": {
          "0%, 100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(0.95)", opacity: "0.8" },
        },
        "float-up": {
          from: { transform: "translateY(0px)", opacity: "0" },
          to: { transform: "translateY(-20px)", opacity: "1" },
        },
        "bounce-subtle": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-2px)" },
        },
        "success-checkmark": {
          "0%": { strokeDashoffset: "100", opacity: "0" },
          "50%": { opacity: "1" },
          "100%": { strokeDashoffset: "0", opacity: "1" },
        },
        "progress-fill": {
          "0%": { width: "0%" },
          "100%": { width: "var(--progress-width)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "expand-collapse": "expand-collapse 0.3s ease-in-out",
        "scale-pulse": "scale-pulse 1.5s ease-in-out infinite",
        "float-up": "float-up 0.5s ease-out",
        "bounce-subtle": "bounce-subtle 2s ease-in-out infinite",
        "success-checkmark": "success-checkmark 0.6s ease-out forwards",
        "progress-fill": "progress-fill 0.8s ease-out forwards",
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"), 
    require("tailwind-scrollbar")({ nocompatible: true }),
    require("@tailwindcss/typography"), // <--- ADD THIS LINE
  ],
} satisfies Config;