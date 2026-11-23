"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, ChevronDown, HardDrive } from "lucide-react";
import SetupShell from "@/components/setup/SetupShell";
import { api } from "@/lib/api";

const styles = [
  { id: "brief", title: "Brief", description: "Start with the main points.", detail: 0.2, structure: 0.5 },
  { id: "balanced", title: "Balanced", description: "Give a clear explanation with context.", detail: 0.5, structure: 0.5 },
  { id: "steps", title: "Step by step", description: "Break explanations into smaller steps.", detail: 0.5, structure: 0.9 },
] as const;
const input = "mt-2 h-11 w-full rounded-control border border-line bg-background px-3 transition-colors focus:border-accent";

export default function OnboardingPage() {
  const router = useRouter();
  const client = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile, retry: false });
  const [termsChecked, setTermsChecked] = useState<boolean>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || profile.isPending || profile.isError) return;
    const fields = new FormData(event.currentTarget);
    const name = String(fields.get("name") ?? "").trim();
    if (fields.get("terms") !== "on") {
      setError("Accept the terms to continue.");
      return;
    }
    if (!name) {
      setError("Enter a name to continue.");
      return;
    }
    const next = {
      ...profile.data,
      name,
      terms_accepted: true,
      academic: {
        grade: String(fields.get("grade") ?? "").trim(),
        subject: String(fields.get("subject") ?? "").trim(),
      },
    };
    const style = styles.find((item) => item.id === fields.get("style"));
    setSaving(true);
    setError("");
    try {
      if (style) {
        const previous = profile.data ? (await api.getPreferences()).prefs : {};
        const result = await api.saveSettings(next, {
          ...previous, detail_level: style.detail, structure_preference: style.structure,
        });
        client.setQueryData(["profile"], result.profile);
        client.setQueryData(["preferences"], { prefs: result.prefs });
      } else {
        client.setQueryData(["profile"], await api.saveProfile(next));
      }
      router.replace("/onboarding/setup");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not save your profile. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <SetupShell>
      <main className="onboarding-enter mx-auto w-full max-w-xl px-6 pb-12 pt-9 sm:pt-12">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-accent hover:underline">
          <ArrowLeft aria-hidden className="size-4" /> Back to welcome
        </Link>
        <p className="mt-4 text-xs font-medium text-accent">Step 1 of 3 / Profile</p>
        <h1 className="mt-2 font-display text-5xl leading-none tracking-tight sm:text-6xl">Set up your workspace</h1>
        <p className="mt-3 flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
          <HardDrive aria-hidden className="size-4 shrink-0 text-accent" /> Your profile is saved on this computer.
        </p>
        {profile.isError ? (
          <div className="mt-6">
            <p role="alert">Could not load your profile.</p>
            <button type="button" className="study-secondary mt-3" onClick={() => void profile.refetch()}>Try again</button>
          </div>
        ) : profile.isPending ? <p role="status" className="mt-6 text-sm">Loading your profile…</p> : (
          <form onSubmit={save} className="mt-6 space-y-5 rounded-panel border border-line bg-surface p-5 sm:p-6">
            <label className="block text-sm font-medium">
              What should StudyMate call you?
              <input name="name" required maxLength={80} autoComplete="given-name" defaultValue={profile.data?.name}
                placeholder="Your name" className={input} />
            </label>

            <details className="group border-t border-line pt-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-medium [&::-webkit-details-marker]:hidden">
                <span>Study details <span className="ml-1 font-normal text-neutral-600 dark:text-neutral-300">(optional)</span></span>
                <ChevronDown aria-hidden className="size-4 transition-transform group-open:rotate-180" />
              </summary>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <label className="text-sm">Study level<input name="grade" maxLength={80} defaultValue={profile.data?.academic.grade} placeholder="e.g. Undergraduate" className={input} /></label>
                <label className="text-sm">Field of study<input name="subject" maxLength={100} defaultValue={profile.data?.academic.subject} placeholder="e.g. Computer science" className={input} /></label>
              </div>
            </details>

            <details className="group border-t border-line pt-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-medium [&::-webkit-details-marker]:hidden">
                <span>Tutor style <span className="ml-1 font-normal text-neutral-600 dark:text-neutral-300">(optional)</span></span>
                <ChevronDown aria-hidden className="size-4 transition-transform group-open:rotate-180" />
              </summary>
              <fieldset className="mt-3 grid gap-2">
                <legend className="sr-only">How should the tutor explain things?</legend>
                {styles.map((style) => (
                  <label key={style.id} className="cursor-pointer">
                    <input type="radio" name="style" value={style.id} defaultChecked={!profile.data && style.id === "balanced"} className="peer sr-only" />
                    <span className="block rounded-control border border-line px-3 py-2 peer-checked:border-accent peer-checked:bg-[var(--accent-soft)] peer-focus-visible:outline peer-focus-visible:outline-offset-2">
                      <span className="block text-sm font-medium">{style.title}</span>
                      <span className="block text-xs text-neutral-600 dark:text-neutral-300">{style.description}</span>
                    </span>
                  </label>
                ))}
              </fieldset>
            </details>

            <label className="flex items-start gap-2 border-t border-line pt-4 text-sm">
              <input type="checkbox" name="terms" required checked={termsChecked ?? !!profile.data?.terms_accepted} onChange={(event) => setTermsChecked(event.target.checked)}
                className="mt-1 size-4 shrink-0 accent-[var(--accent)]" />
              <span>I agree to the <Link href="/onboarding/terms" target="_blank" rel="noopener noreferrer" aria-label="Terms and conditions (opens in a new tab)" className="text-accent underline underline-offset-2">Terms and conditions</Link>.</span>
            </label>
            {error && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{error}</p>}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
              <p className="text-xs text-neutral-600 dark:text-neutral-300">You can change these later in Settings.</p>
              <button disabled={saving || !(termsChecked ?? profile.data?.terms_accepted)} className="study-action" type="submit">
                {saving ? "Saving…" : "Continue to tutor setup"} <ArrowRight aria-hidden className="size-4" />
              </button>
            </div>
          </form>
        )}
      </main>
    </SetupShell>
  );
}
