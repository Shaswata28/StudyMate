"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Volume2 } from "lucide-react";
import { api } from "@/lib/api";
import { playKokoro } from "@/lib/playKokoro";
import { findEnglishVoice, getVoiceMode, setVoiceMode, type VoiceMode } from "@/lib/systemVoice";

const windowsGuide = "https://support.microsoft.com/en-au/accessibility/windows/narrator/appendix-a-supported-languages-and-voices";
const macGuide = "https://support.apple.com/guide/mac-help/change-the-voice-your-mac-uses-to-speak-text-mchlp2290/mac";
const linuxGuide = "https://github.com/brailcom/speechd/blob/master/INSTALL";

export default function SystemVoiceSetup({ platform }: { platform?: string }) {
  const [mode, setMode] = useState<VoiceMode>("system");
  const [voices, setVoices] = useState<Partial<Record<VoiceMode, SpeechSynthesisVoice>>>({});
  const cache = useQueryClient();
  const preview = useRef<AbortController | null>(null);
  const download = useMutation({
    mutationFn: api.downloadKokoro,
    onSuccess: () => {
      cache.setQueryData(["kokoro"], { supported: true, installed: true, progress: null });
      selectMode("kokoro");
    },
  });
  const kokoro = useQuery({
    queryKey: ["kokoro"],
    queryFn: api.getKokoro,
    refetchInterval: (query) => download.isPending || query.state.data?.progress ? 750 : false,
  });
  const progress = kokoro.data?.progress;
  const installing = progress?.phase === "installing";
  const packageName = progress?.package === "runtime" ? "Kokoro runtime" : "Kokoro voice";
  const received = ((progress?.received ?? 0) / 1_000_000).toFixed(1);
  const total = progress?.total ? (progress.total / 1_000_000).toFixed(1) : null;
  const percent = progress?.total ? Math.min(100, (progress.received / progress.total) * 100) : undefined;
  const voice = voices[mode];
  const [message, setMessage] = useState("");
  const [testing, setTesting] = useState(false);
  const section = useRef<HTMLElement>(null);

  useEffect(() => {
    setMode(getVoiceMode());
    const engine = window.speechSynthesis;
    if (engine) {
      const refresh = () => setVoices({ system: findEnglishVoice(engine, "system"), chrome: findEnglishVoice(engine, "chrome") });
      refresh();
      engine.addEventListener("voiceschanged", refresh);
      return () => engine.removeEventListener("voiceschanged", refresh);
    }
  }, []);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("section") === "read-aloud") {
      section.current?.scrollIntoView({ block: "start" });
    }
  }, []);

  useEffect(() => () => preview.current?.abort(), []);

  function selectMode(next: VoiceMode) {
    preview.current?.abort();
    setTesting(false);
    setVoiceMode(next);
    setMode(next);
    setMessage("");
  }

  async function testKokoro() {
    if (testing) {
      preview.current?.abort();
      setTesting(false);
      setMessage("");
      return;
    }
    const controller = new AbortController();
    preview.current = controller;
    setTesting(true);
    setMessage("Preparing the Kokoro sample…");
    try {
      await playKokoro("Your StudyMate offline voice is ready.", controller.signal, () => setMessage("Playing Kokoro sample."));
      if (!controller.signal.aborted) setMessage("Kokoro is ready.");
    } catch (error) {
      if (!controller.signal.aborted) setMessage(error instanceof Error ? error.message : "Could not play the Kokoro sample.");
    } finally {
      if (!controller.signal.aborted) setTesting(false);
    }
  }

  function testVoice() {
    if (mode === "kokoro") { void testKokoro(); return; }
    const engine = window.speechSynthesis;
    const selected = findEnglishVoice(engine, mode);
    if (!engine || !selected) {
      setMessage(mode === "chrome" ? "This browser does not offer an online Google English voice." : "This browser does not see a local English voice.");
      return;
    }
    const test = new SpeechSynthesisUtterance("Your StudyMate read aloud voice is ready.");
    test.voice = selected;
    test.onstart = () => setMessage(`Playing ${selected.name}.`);
    test.onend = () => setMessage(`${selected.name} is ready.`);
    test.onerror = () => setMessage("Could not play the installed voice in this browser.");
    engine.cancel();
    engine.speak(test);
  }

  return (
    <section ref={section} className="scroll-mt-4 rounded-panel border border-line bg-background p-4 sm:p-5">
      <h4 className="flex items-center gap-2 font-semibold"><Volume2 aria-hidden className="size-4 text-accent" /> Read aloud</h4>
      <fieldset className="mt-4 grid gap-2 sm:grid-cols-3">
        <legend className="sr-only">Read aloud voice provider</legend>
        {([
          ["kokoro", "Kokoro · offline"],
          ["system", "System voice · offline"],
          ["chrome", "Chrome Google voice · online"],
        ] as const).map(([option, label]) => (
          <label key={option} className="cursor-pointer">
            <input type="radio" name="read-aloud-provider" value={option} checked={mode === option} className="peer sr-only"
              onChange={() => selectMode(option)} />
            <span className="block rounded-control border border-line px-3 py-2 text-sm peer-checked:border-accent peer-checked:bg-[var(--accent-soft)] peer-focus-visible:outline peer-focus-visible:outline-offset-2">{label}</span>
          </label>
        ))}
      </fieldset>
      {mode === "kokoro" ? (
        <div className="mt-3 space-y-3 text-sm">
          <p>{kokoro.isError ? "Could not check Kokoro’s installation." : kokoro.data?.installed
            ? "Kokoro English is installed. It runs on this computer."
            : "Download the English voice and CPU runtime for offline playback (roughly 125–136 MB)."} </p>
          {kokoro.data?.supported === false && <p>Kokoro is unavailable on this operating system or processor.</p>}
          {(progress || download.isPending) ? (
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                <span role="status">{progress
                  ? (installing ? `Installing ${packageName}…` : `Downloading ${packageName}…`)
                  : "Preparing Kokoro download…"}</span>
                {progress && <span className="tabular-nums">{received}{total && ` / ${total}`} MB</span>}
              </div>
              <progress
                aria-label={installing ? "Kokoro installation" : "Kokoro download"}
                max={100}
                value={installing ? 100 : percent}
                className="block h-2 w-full overflow-hidden rounded-full bg-[var(--accent-soft)] [&::-webkit-progress-bar]:bg-[var(--accent-soft)] [&::-webkit-progress-value]:rounded-full [&::-webkit-progress-value]:bg-accent [&::-webkit-progress-value]:transition-[width] [&::-moz-progress-bar]:rounded-full [&::-moz-progress-bar]:bg-accent"
              />
            </div>
          ) : kokoro.data?.supported && !kokoro.data.installed && (
            <button type="button" className="study-action" onClick={() => download.mutate()}>
              <Download aria-hidden className="size-4" /> Download Kokoro
            </button>
          )}
          {download.error && <p role="alert" className="text-red-700 dark:text-red-300">{download.error.message}</p>}
        </div>
      ) : <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-300">
        {voice ? `Voice available: ${voice.name}.` : mode === "chrome" ? "This browser does not offer an online Google English voice." : "This browser has not reported a local English voice."}
      </p>}
      {mode === "chrome" && (
        <p className="mt-2 text-sm">Chrome's Google voice requires internet access and may send the text you choose to read aloud to Google.</p>
      )}
      {mode === "system" && (
      <div className="mt-3 space-y-3 text-sm">
        {(!platform || platform === "Windows") && <p><strong>Windows.</strong> Open <strong>Settings → Time &amp; language → Speech → Manage voices → Add voices</strong> and choose English. <a href={windowsGuide} target="_blank" rel="noreferrer" className="text-accent underline">Windows voice guide</a></p>}
        {(!platform || platform === "Darwin") && <p><strong>macOS.</strong> Open <strong>System Settings → Accessibility → Read &amp; Speak → System voice</strong> and download an English voice. The section is called <strong>Spoken Content</strong> on some versions. <a href={macGuide} target="_blank" rel="noreferrer" className="text-accent underline">Mac voice guide</a></p>}
        {(!platform || platform === "Linux") && <p><strong>Linux.</strong> Install Speech Dispatcher with an English voice engine such as eSpeak NG through your distribution's package manager. Browser support varies. <a href={linuxGuide} target="_blank" rel="noreferrer" className="text-accent underline">Speech Dispatcher guide</a></p>}
        <p>Restart the browser after installing the voice, then use <strong>Test voice</strong>.</p>
      </div>
      )}
      <button type="button" onClick={testVoice} disabled={mode === "kokoro" && !kokoro.data?.installed} className="study-secondary mt-4 disabled:opacity-50">{testing ? "Stop sample" : "Test voice"}</button>
      {message && <p role="status" className="mt-2 text-sm">{message}</p>}
    </section>
  );
}
