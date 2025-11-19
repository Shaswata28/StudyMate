import { useTheme } from "./ThemeProvider";
import { Sun, Moon } from "lucide-react";

export default function Header() {
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="h-[70px] px-6 md:px-8 lg:pl-8 lg:pr-12 flex items-center justify-between border-b border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950 transition-colors duration-200">
      <h1 className="font-koulen text-3xl md:text-4xl lg:text-[32px] tracking-[3.2px] text-black dark:text-white">
        STUDYMATE
      </h1>

      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors btn-micro"
        aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      >
        {isDark ? (
          <Sun className="w-6 h-6 text-yellow-500" strokeWidth={2} />
        ) : (
          <Moon className="w-6 h-6 text-slate-700" strokeWidth={2} />
        )}
      </button>
    </header>
  );
}
