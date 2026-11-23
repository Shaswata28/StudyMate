"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight } from "lucide-react";
import LocalSetup from "@/components/LocalSetup";
import SetupShell from "@/components/setup/SetupShell";
import { api } from "@/lib/api";

export default function OnboardingSetupPage() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile, retry: false });
  const runtime = useQuery({ queryKey: ["settings"], queryFn: api.getSettings, enabled: !!profile.data?.terms_accepted });

  return (
    <SetupShell>
      <main className="study-enter mx-auto max-w-3xl px-6 py-10 sm:px-10">
        <Link href="/onboarding" className="inline-flex items-center gap-2 text-sm text-accent hover:underline">
          <ArrowLeft aria-hidden className="size-4" /> Back to profile
        </Link>
        <p className="mt-4 text-xs font-medium text-accent">Step 2 of 2 ? Device setup</p>
        <h1 className="mt-2 font-display text-5xl leading-none tracking-tight sm:text-6xl">Set up your local tutor</h1>
        <p className="mt-3 text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
          StudyMate detects this computer and suggests a model. You can download one now or finish setup later from Settings.
        </p>
        {profile.isPending ? <p role="status" className="mt-5 text-sm">Checking your profile?</p> : profile.isError ? (
          <button type="button" className="study-secondary mt-5" onClick={() => void profile.refetch()}>Could not load profile. Retry</button>
        ) : !profile.data?.terms_accepted ? (
          <Link href="/onboarding" className="study-action mt-5">Complete your profile</Link>
        ) : (
          <>
            <div className="sticky top-0 z-10 -mx-1 mt-4 flex flex-wrap items-center justify-end gap-3 bg-background px-1 py-3">
              <Link href="/app" className="study-action">
                {runtime.data?.status === "ready" ? "Start studying" : "Continue without downloads"}
                <ArrowRight aria-hidden className="size-4" />
              </Link>
            </div>
            <div className="mt-2 rounded-panel border border-line bg-surface p-4 sm:p-6">
              <LocalSetup />
            </div>
          </>
        )}
      </main>
    </SetupShell>
  );
}
