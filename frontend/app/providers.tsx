"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Toaster } from "sonner";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }));

  const [dark, setDark] = useState(false);

  useEffect(() => {
    const system = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => {
      const theme = localStorage.getItem("studymate-theme") ?? "system";
      const active = theme === "dark" || (theme === "system" && system.matches);
      document.documentElement.classList.toggle("dark", active);
      setDark(active);
    };
    sync();
    system.addEventListener("change", sync);
    window.addEventListener("studymate-theme", sync);
    window.addEventListener("storage", sync);
    return () => {
      system.removeEventListener("change", sync);
      window.removeEventListener("studymate-theme", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster theme={dark ? "dark" : "light"} position="top-right" richColors />
    </QueryClientProvider>
  );
}

