"use client";

import { version } from "@/package.json";
import Link from "next/link";
import { ArrowLeft, AudioLines, BookOpen, CircleUserRound, ImagePlus, SunMoon, CircleHelp, FileText, Github } from "lucide-react";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import SetupShell from "@/components/setup/SetupShell";
import LocalSetup from "@/components/LocalSetup";
import ThemeControl from "@/components/ThemeControl";
import { api } from "@/lib/api";

const categories = ["Profile", "Learning", "Appearance", "Local setup"] as const;
const icons = { Profile: CircleUserRound, Learning: BookOpen, Appearance: SunMoon, "Local setup": AudioLines };
const choices = [
  ["detail_level", "Detail", ["Brief", "Balanced", "In depth"]],
  ["example_preference", "Examples", ["Few", "Some", "Frequent"]],
  ["analogy_preference", "Analogies", ["Literal explanations", "Occasional", "Frequent"]],
  ["technical_language", "Technical rigor", ["Plain language", "Standard", "Formal"]],
  ["structure_preference", "Structure", ["Conversational", "Balanced", "Step by step"]],
] as const;
const field = "mt-2 block w-full rounded-control border border-line bg-background px-3 py-2.5";
const action = "study-action";
const numeric = ["0.2", "0.5", "0.9"] as const;

function ChoiceRow({ name, label, options, selected }: {
  name: string;
  label: string;
  options: readonly (readonly [string, string])[];
  selected: string;
}) {
  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-sm font-medium">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map(([value, text]) => (
          <label key={value} className="cursor-pointer">
            <input type="radio" name={name} value={value} defaultChecked={selected === value} className="peer sr-only" />
            <span className="block rounded-control border border-line px-3 py-2 text-sm transition-colors peer-checked:border-[#879478] peer-checked:bg-[#eef0e5] peer-focus-visible:outline peer-focus-visible:outline-offset-2 dark:peer-checked:bg-[#353a2f]">{text}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function SettingsPage() {
  const [category, setCategory] = useState<(typeof categories)[number]>("Profile");
  useEffect(() => {
    const section = new URLSearchParams(window.location.search).get("section");
    if (section === "models" || section === "voice" || section === "setup" || section === "read-aloud") setCategory("Local setup");
  }, []);
  const client = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });
  const prefs = useQuery({ queryKey: ["preferences"], queryFn: api.getPreferences });
  const [avatarDraft, setAvatarDraft] = useState<string | null>();
  const avatar = avatarDraft === undefined ? profile.data?.avatar : avatarDraft;

  async function chooseAvatar(file?: File) {
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 290_000) {
      toast.error("Choose a PNG, JPEG, or WebP image under 290 KB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setAvatarDraft(String(reader.result));
    reader.onerror = () => toast.error("Could not open that image.");
    reader.readAsDataURL(file);
  }

  const save = useMutation({
    mutationFn: async ({ section, fields }: { section: "Profile" | "Learning"; fields: FormData }) => {
      const value = (name: string) => String(fields.get(name) ?? "");
      if (section === "Profile") {
        const result = await api.saveProfile({
          ...profile.data,
          name: value("name"), academic: { grade: value("grade"), subject: value("subject") },
          avatar: avatar ?? null, institution: value("institution"), goal: value("goal"),
        });
        client.setQueryData(["profile"], result);
        setAvatarDraft(undefined);
      } else {
        const result = await api.savePreferences({
          ...Object.fromEntries(choices.map(([key]) => [key, Number(value(key))])),
          learning_pace: value("learning_pace"), prior_experience: value("prior_experience"),
        });
        client.setQueryData(["preferences"], result);
      }
    },
    onSuccess: () => toast.success("Settings saved."),
    onError: (error) => toast.error(error.message),
  });

  return (
    <SetupShell>
      <main className="study-enter mx-auto max-w-6xl px-6 py-10 sm:px-10">
        <header className="flex items-center gap-3 sm:gap-4">
          <Link href="/app" aria-label="Back to workspace" title="Back to workspace"
            className="grid size-10 shrink-0 place-items-center rounded-control border border-line bg-surface transition-colors hover:bg-[var(--accent-soft)]">
            <ArrowLeft aria-hidden className="size-5" />
          </Link>
          <h1 className="font-display text-5xl leading-none sm:text-6xl">Settings</h1>
        </header>
        <div className="mt-8 grid gap-6 sm:grid-cols-[12rem_minmax(0,1fr)]">
          <nav aria-label="Settings categories" className="flex flex-wrap content-start gap-1 sm:flex-col">
            {categories.map((item) => {
              const Icon = icons[item];
              return (
              <button key={item} type="button" aria-current={category === item ? "page" : undefined}
                onClick={() => setCategory(item)}
                className={`flex items-center gap-2 rounded-control px-3 py-2.5 text-left text-sm transition-colors ${category === item ? "bg-[#e9ecdf] font-semibold dark:bg-[#353a2f]" : "hover:bg-black/5 dark:hover:bg-white/5"}`}>
                <Icon aria-hidden className="size-4 shrink-0" /> {item}
              </button>
            ); })}
            <div className="mt-1 flex w-full flex-wrap gap-1 border-t border-line pt-2 sm:mt-3 sm:flex-col">
              {([
                ["/how-to", "How to", BookOpen],
                ["/help", "Help", CircleHelp],
                ["/terms", "Terms and conditions", FileText],
                ["/credits", "Credits", Github],
              ] as const).map(([href, label, Icon]) => (
                <Link key={href} href={href}
                  className="flex items-center gap-2 rounded-control px-3 py-2.5 text-sm transition-colors hover:bg-black/5 dark:hover:bg-white/5">
                  <Icon aria-hidden className="size-4 shrink-0" /> {label}
                </Link>
              ))}
            </div>
            <span className="px-3 pt-2 text-xs tabular-nums text-neutral-600 dark:text-neutral-300">v{version}</span>
          </nav>
          <section className="min-w-0 rounded-panel border border-line bg-surface p-5 sm:p-8" aria-labelledby="settings-category">
            <h2 id="settings-category" className="mb-5 font-display text-4xl">{category}</h2>
            {category === "Profile" && (
              profile.data ? (
                <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); save.mutate({ section: "Profile", fields: new FormData(e.currentTarget) }); }}>
                  <div className="flex flex-wrap items-center gap-4 border-b border-line pb-5">
                    {avatar ? <img src={avatar} alt="" className="size-20 rounded-full object-cover" /> : (
                      <span aria-hidden className="grid size-20 place-items-center rounded-full bg-[var(--accent-soft)] font-display text-3xl text-accent">{profile.data.name.slice(0, 1).toUpperCase()}</span>
                    )}
                    <div>
                      <p className="font-semibold">{profile.data.name}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3">
                        <label className="inline-flex cursor-pointer items-center gap-1 text-sm text-accent">
                          <ImagePlus className="size-4" /> Change avatar
                          <input type="file" accept="image/png,image/jpeg,image/webp" className="sr-only"
                            onChange={(event) => { void chooseAvatar(event.target.files?.[0]); event.target.value = ""; }} />
                        </label>
                        {avatar && <button type="button" className="text-sm underline" onClick={() => setAvatarDraft(null)}>Remove</button>}
                      </div>
                    </div>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="block text-sm">Display name<input className={field} name="name" maxLength={80} required defaultValue={profile.data.name} /></label>
                    <label className="block text-sm">Study level<input className={field} name="grade" maxLength={80} defaultValue={profile.data.academic.grade} /></label>
                    <label className="block text-sm">Field of study<input className={field} name="subject" maxLength={100} defaultValue={profile.data.academic.subject} /></label>
                    <label className="block text-sm">School or institution <span className="text-neutral-500">(optional)</span><input className={field} name="institution" maxLength={120} defaultValue={profile.data.institution} /></label>
                  </div>
                  <label className="block text-sm">Current study goal <span className="text-neutral-500">(optional)</span>
                    <textarea className={field} name="goal" maxLength={240} rows={2} defaultValue={profile.data.goal} placeholder="What are you working toward?" />
                  </label>
                  <button className={action} disabled={save.isPending}>Save profile</button>
                </form>
              ) : profile.data === null ? <Link href="/onboarding" className="underline">Set up your profile</Link>
                : profile.isError ? <button className="underline" onClick={() => profile.refetch()}>Could not load profile. Retry</button>
                : <p role="status">Loading profile…</p>
            )}
            {category === "Learning" && (
              prefs.data ? (
                <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); save.mutate({ section: "Learning", fields: new FormData(e.currentTarget) }); }}>
                  <p className="text-sm text-neutral-600 dark:text-neutral-300">Set the tutor?s starting style for new course conversations.</p>
                  <section className="space-y-4 rounded-panel border border-line bg-background p-4 sm:p-5">
                    <h3 className="font-display text-2xl">Explanations</h3>
                  {choices.map(([key, label, labels]) => {
                    const current = prefs.data.prefs[key] ?? 0.5;
                    return <ChoiceRow key={key} name={key} label={label}
                      options={labels.map((text, index) => [numeric[index], text] as const)}
                      selected={numeric[current < 0.4 ? 0 : current > 0.6 ? 2 : 1]} />;
                  })}
                  </section>
                  <section className="space-y-4 rounded-panel border border-line bg-background p-4 sm:p-5">
                    <h3 className="font-display text-2xl">Pace and experience</h3>
                  <ChoiceRow name="learning_pace" label="Learning pace"
                    options={[["slow", "Take it slowly"], ["moderate", "Moderate"], ["fast", "Move quickly"]]}
                    selected={prefs.data.prefs.learning_pace ?? "moderate"} />
                  <ChoiceRow name="prior_experience" label="Prior experience"
                    options={[["beginner", "Beginner"], ["intermediate", "Intermediate"], ["advanced", "Advanced"]]}
                    selected={prefs.data.prefs.prior_experience ?? "intermediate"} />
                  </section>
                  <button className={action} disabled={save.isPending}>Save preferences</button>
                </form>
              ) : prefs.isError ? <button className="underline" onClick={() => prefs.refetch()}>Could not load preferences. Retry</button>
                : <p role="status">Loading preferences…</p>
            )}
            {category === "Appearance" && <ThemeControl />}
            {category === "Local setup" && <LocalSetup />}
          </section>
        </div>
      </main>
    </SetupShell>
  );
}
