import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import SetupShell from "./SetupShell";

export default function InfoPage({ title, summary, children }: { title: string; summary: string; children: ReactNode }) {
  return (
    <SetupShell>
      <main className="study-enter mx-auto max-w-3xl px-6 py-10 sm:px-10 sm:py-14">
        <Link href="/settings" className="mb-4 inline-flex items-center gap-2 text-sm text-accent hover:underline">
          <ArrowLeft aria-hidden className="size-4" /> Back to Settings
        </Link>
        <h1 className="font-display text-5xl leading-none tracking-tight sm:text-6xl">{title}</h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-neutral-600 dark:text-neutral-300">{summary}</p>
        <div className="mt-7 divide-y divide-[var(--line)] rounded-panel border border-line bg-surface px-5 text-sm leading-relaxed
          [&>section]:py-5 [&_h2]:mb-2 [&_h2]:font-display [&_h2]:text-2xl
          [&_a]:text-accent [&_a]:underline [&_a]:underline-offset-4 sm:px-7">
          {children}
        </div>
      </main>
    </SetupShell>
  );
}
