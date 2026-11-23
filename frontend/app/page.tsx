"use client";

import appPackage from "@/package.json";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, AudioLines, BookOpen, CircleHelp, Cpu, FileText, Github, HardDrive } from "lucide-react";
import SetupShell from "@/components/setup/SetupShell";
import { api } from "@/lib/api";

export default function LandingPage() {
  const { data: profile, isPending, isError, refetch } = useQuery({
    queryKey: ["profile"], queryFn: api.getProfile, retry: false,
  });

  return (
    <SetupShell>
      <div className="flex min-h-[calc(100svh-85px)] flex-col">
        <main className="study-enter mx-auto grid w-full flex-1 max-w-[1320px] content-center items-center gap-x-10 gap-y-7 px-6 py-12 sm:px-12 lg:grid-cols-[minmax(0,.9fr)_minmax(0,1fr)] lg:gap-x-16 lg:px-16">
          <section className="min-w-0">
            <h1 className="max-w-xl break-words font-display text-[clamp(3.25rem,7vw,6.25rem)] leading-[.92] tracking-tight">
              {profile ? <>Welcome back, <span className="text-accent">{profile.name}.</span></> : <>Make sense of <span className="text-accent">what you study.</span></>}
            </h1>
            <p className="mt-5 max-w-[33ch] text-base leading-relaxed text-neutral-600 dark:text-neutral-300 sm:text-lg">
              {profile ? "Pick up your last conversation or open a course from your study overview." : "Bring your notes and questions together in a workspace that runs on your computer."}
            </p>
            <div className="mt-7">
              {isError ? (
                <div className="space-y-2">
                  <p role="alert" className="text-sm">Could not connect to StudyMate.</p>
                  <button type="button" onClick={() => void refetch()} className="study-secondary">Try again</button>
                </div>
              ) : isPending ? (
                <p role="status" className="text-sm text-neutral-600 dark:text-neutral-300">Opening StudyMate…</p>
              ) : (
                <Link href={profile ? "/app" : "/onboarding"} className="study-action">
                  {profile ? "Open workspace" : "Set up StudyMate"}
                  <ArrowRight aria-hidden className="size-4" />
                </Link>
              )}
            </div>
            {!profile && <p className="mt-5 flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
              <HardDrive aria-hidden className="size-4 text-accent" /> Notes and chats stay on this device.
            </p>}
          </section>

          <figure className="rounded-panel border border-line bg-[var(--accent-soft)] p-3 sm:p-6 lg:p-8">
            <div className="overflow-hidden rounded-panel border border-line bg-surface">
              <div className="flex items-center gap-2 border-b border-line px-4 py-3 text-sm font-semibold sm:px-5">
                <BookOpen aria-hidden className="size-4 text-accent" /> Physics
              </div>
              <div className="grid sm:grid-cols-[minmax(0,1fr)_8.25rem]">
                <div className="space-y-4 p-4 sm:p-5">
                  <p className="ml-auto w-fit max-w-full rounded-control border border-line bg-background px-3 py-2 text-sm">Why does mass affect momentum?</p>
                  <div className="space-y-3 text-sm leading-relaxed">
                    <p>Momentum is mass times velocity. At the same speed, doubling the mass doubles the momentum.</p>
                    <p className="inline-flex items-center gap-1.5 rounded-control bg-[var(--accent-soft)] px-2 py-1 text-xs text-accent">
                      <FileText aria-hidden className="size-3.5" /> Mechanics notes · p. 4
                    </p>
                  </div>
                </div>
                <div className="border-t border-line px-4 py-3 text-xs sm:border-l sm:border-t-0">
                  <p className="font-semibold">Materials</p>
                  <p className="mt-2 break-words text-neutral-600 dark:text-neutral-300">Mechanics notes</p>
                </div>
              </div>
            </div>
            <figcaption className="px-1 pt-3 text-xs text-neutral-600 dark:text-neutral-300">Example workspace</figcaption>
          </figure>
          <ul aria-label="StudyMate features" className="grid gap-4 border-t border-line pt-5 sm:grid-cols-3 lg:col-span-2">
            {([
              [Cpu, "Local models", "Use a tutor that runs on your own computer."],
              [BookOpen, "Course workspaces", "Keep notes, questions, and saved answers together."],
              [AudioLines, "Voice input", "Speak a question with on-device dictation."],
            ] as const).map(([Icon, title, description]) => (
              <li key={title} className="flex items-start gap-2.5 text-sm">
                <Icon aria-hidden className="mt-0.5 size-4 shrink-0 text-accent" />
                <div>
                  <p className="font-semibold">{title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-neutral-600 dark:text-neutral-300">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </main>
        <footer className="border-t border-line">
          <nav aria-label="About StudyMate" className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-x-6 gap-y-3 px-6 py-4 text-sm text-neutral-600 dark:text-neutral-300 sm:px-12 lg:px-16">
            {([
              ["/terms", "Terms and conditions", FileText],
              ["/help", "Help", CircleHelp],
              ["/credits", "Credits", Github],
            ] as const).map(([href, label, Icon]) => (
              <Link key={href} href={href} className="inline-flex items-center gap-2 transition-colors hover:text-accent">
                <Icon aria-hidden className="size-4 shrink-0 text-accent" />
                {label}
              </Link>
            ))}
            <span className="ml-auto whitespace-nowrap tabular-nums">v{appPackage.version}</span>
          </nav>
        </footer>
      </div>
    </SetupShell>
  );
}
