import { Moon, Sun } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors btn-micro"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-yellow-500" strokeWidth={2} />
      ) : (
        <Moon className="w-5 h-5 text-gray-700" strokeWidth={2} />
      )}
    </button>
  );
}
