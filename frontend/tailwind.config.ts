import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      borderRadius: { panel: "16px", control: "10px" },
      colors: {
        slate: { 950: "#1c1b18", 900: "#26241f", 800: "#302e29", 700: "#45423b" },
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: "var(--surface)",
        line: "var(--line)",
        accent: "var(--accent)",
        "on-accent": "var(--on-accent)",
        studymate: {
          orange: "#FEAE01",
          green: "#1FC209",
          gray: "#D9D9D9",
          darkgray: "#404040",
          black: "#1E1E1E",
        },
      },
      fontFamily: {
        sans: ["Instrument Sans", "system-ui", "sans-serif"],
        display: ["Instrument Serif", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;

