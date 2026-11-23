"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useIsMutating, useQuery } from "@tanstack/react-query";
import LocalSetup from "@/components/LocalSetup";
import SetupShell from "@/components/setup/SetupShell";
import { api } from "@/lib/api";

export default function OnboardingSetupPage() {
  const [stage, setStage] = useState<"tutor" | "voice">("tutor");
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile, retry: false });
  const accepted = !!profile.data?.terms_accepted;
  const runtime = useQuery({ queryKey: ["settings"], queryFn: api.getSettings, enabled: accepted });
  const busy = useIsMutating({ mutationKey: ["local-download"] }) > 0;
  const ready = runtime.data?.status === "ready";
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (accepted) heading.current?.focus();
  }, [accepted, stage]);

  return (
    <SetupShell>
      <main className="mx-auto max-w-3xl px-6 py-10">
        {!accepted && (profile.isPending ? <p role="status">Checking your profile...</p> : profile.isError ? (
          <button type="button" className="study-secondary" onClick={() => void profile.refetch()}>Could not load profile. Retry</button>
        ) : <Link href="/onboarding" className="study-action">Complete your profile</Link>)}
        {accepted && (
          <section className="onboarding-enter" key={stage} aria-labelledby="setup-title">
            <header className="mb-5">
                <p className="text-xs font-medium text-accent">Step {stage === "tutor" ? 2 : 3} of 3</p>
                <h1 ref={heading} tabIndex={-1} id="setup-title" className="mt-1 font-display text-4xl">{stage === "tutor" ? "Set up your local tutor" : "Set up voice tools"}</h1>
                <p className="mt-2 text-sm">
                  {stage === "tutor" ? "Check your hardware, then install Ollama and a recommended tutor model." : "Optional. Add Whisper for dictation or Kokoro for read aloud."}
                </p>
              </header>
              <div className="rounded-panel border border-line bg-surface p-4 sm:p-6">
                <LocalSetup stage={stage} />
              </div>
              <footer className="flex flex-wrap items-center justify-between gap-3 mt-5 border-t border-line py-4">
                {stage === "tutor" ? (
                  <>
                    {busy ? <span role="status" className="text-sm">Setting up your tutor...</span> : <Link href="/onboarding" className="study-secondary">Back to profile</Link>}
                    <button type="button" className="study-action disabled:opacity-50" disabled={busy} onClick={() => setStage("voice")}>
                      {ready ? "Continue to voice setup" : "Set up tutor later"}
                    </button>
                  </>
                ) : (
                  <>
                    <button type="button" className="study-secondary disabled:opacity-50" disabled={busy} onClick={() => setStage("tutor")}>Back to tutor setup</button>
                    {busy ? <span role="status" className="text-sm">Setting up voice...</span> : <Link href="/app" className="study-action">Open StudyMate</Link>}
                  </>
                )}
              </footer>
          </section>
        )}
      </main>
    </SetupShell>
  );
}
