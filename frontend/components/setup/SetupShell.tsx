import Link from "next/link";
import type { ReactNode } from "react";

export default function SetupShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-line">
        <div className="mx-auto flex h-[84px] max-w-[1320px] items-center justify-between gap-3 px-4 sm:px-12 lg:px-16">
          <Link href="/" className="font-display text-3xl leading-none tracking-tight sm:text-4xl">StudyMate</Link>
        </div>
      </header>
      {children}
    </div>
  );
}
