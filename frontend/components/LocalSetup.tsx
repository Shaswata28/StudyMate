"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AudioLines, Bot, Cpu, Download, RefreshCw } from "lucide-react";
import SystemVoiceSetup from "./SystemVoiceSetup";
import { api } from "@/lib/api";

function memory(bytes: number | null) {
  return bytes == null ? "Not detected" : `${(bytes / 1024 ** 3).toFixed(1)} GiB`;
}

export default function LocalSetup() {
  const client = useQueryClient();
  const device = useQuery({ queryKey: ["device"], queryFn: api.getDevice });
  const runtime = useQuery({ queryKey: ["settings"], queryFn: api.getSettings });
  const refresh = () => Promise.all([
    client.invalidateQueries({ queryKey: ["settings"] }),
    client.invalidateQueries({ queryKey: ["device"] }),
    client.invalidateQueries({ queryKey: ["kokoro"] }),
  ]);
  const tutor = useMutation({ mutationFn: api.downloadModel, onSuccess: refresh });
  const voice = useMutation({ mutationFn: api.downloadVoice, onSuccess: refresh });
  const spec = device.data;
  const tools = runtime.data;
  const busy = tutor.isPending || voice.isPending;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-neutral-600 dark:text-neutral-300">Manage your device, tutor, and voice tools.</p>
        <button type="button" disabled={device.isFetching || runtime.isFetching} onClick={() => void refresh()} className="study-secondary">
          <RefreshCw aria-hidden className="size-4" /> Refresh status
        </button>
      </div>
      <section className="rounded-panel border border-line bg-background p-4 sm:p-5">
        <h3 className="flex items-center gap-2 font-semibold"><Cpu aria-hidden className="size-4 text-accent" /> This computer</h3>
        {spec ? (
          <>
            <dl className="mt-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
              {[
                ["Platform", `${spec.system === "Darwin" ? "macOS" : spec.system} · ${spec.arch}`],
                ["Processor", `${spec.cpu}${spec.threads ? ` · ${spec.threads} threads` : ""}`],
                ["System memory", memory(spec.ram_bytes)],
                [spec.unified_memory ? "Graphics memory" : "Dedicated VRAM", spec.unified_memory ? "Shared with system memory" : memory(spec.vram_bytes)],
                ["Graphics", spec.gpu ?? "Not detected"],
              ].map(([label, value]) => (
                <div key={label} className="rounded-control border border-line bg-surface px-3 py-2"><dt className="text-xs text-neutral-600 dark:text-neutral-300">{label}</dt><dd className="mt-1 break-words font-medium">{value}</dd></div>
              ))}
            </dl>
            <p className="mt-4 text-xs text-neutral-600 dark:text-neutral-300">Suggested models are based on detected memory. Available memory, other running apps, and context length affect performance.</p>
          </>
        ) : <p role="status" className="mt-3 text-sm">{device.isError ? "Could not detect this computer." : "Detecting hardware…"}</p>}
      </section>

      <section className="rounded-panel border border-line bg-background p-4 sm:p-5">
        <h3 className="flex items-center gap-2 font-semibold"><Bot aria-hidden className="size-4 text-accent" /> Tutor model</h3>
        <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-300">
          {runtime.isError ? "Could not check Ollama." : !tools ? "Checking Ollama..." : tools.status === "ready" ? `Active · ${tools.model}` : tools?.status === "missing" ? "Ollama is ready. Choose a model." : "Ollama is not running."}
        </p>
        {spec && tools?.status === "unavailable" && (
          <p className="mt-2 text-sm">
            {spec.ollama_auto ? "Setup installs the local Ollama runtime if needed, then downloads the tutor model."
              : <>Install and start <a href="https://ollama.com/download" className="text-accent underline" target="_blank" rel="noreferrer">Ollama for your platform</a>, then retry.</>}
          </p>
        )}
        <ul className="mt-4 divide-y divide-[var(--line)] border-y border-line">
          {spec?.models.map((model) => {
            const installed = tools?.installed_models?.includes(model.id);
            const active = tools?.status === "ready" && tools.model === model.id;
            const installing = tutor.isPending && tutor.variables === model.id;
            return (
              <li key={model.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
                    <span>{model.name}</span>
                    {spec.recommended === model.id && <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-accent">Recommended</span>}
                  </div>
                  <p className="mt-1 break-all text-xs text-neutral-600 dark:text-neutral-300">{model.id} · {model.size}</p>
                </div>
                <button type="button" className={spec.recommended === model.id && !active ? "study-action" : "study-secondary"}
                  disabled={active || busy} onClick={() => tutor.mutate(model.id)}>
                  {!active && !installed && <Download aria-hidden className="size-4" />}
                  {active ? "Active" : installing ? "Setting up…" : installed ? "Use model" : tools?.status === "unavailable" && spec.ollama_auto ? "Set up Ollama & model" : "Download & use"}
                </button>
              </li>
            );
          })}
        </ul>
        {tutor.isError && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{tutor.error.message}</p>}
      </section>

      <section aria-labelledby="local-voice-heading" className="space-y-3">
        <h3 id="local-voice-heading" className="font-display text-2xl">Voice tools</h3>
        <div className="space-y-3">
          <section className="rounded-panel border border-line bg-background p-4 sm:p-5">
            <h4 className="flex items-center gap-2 font-semibold"><AudioLines aria-hidden className="size-4 text-accent" /> Voice input</h4>
            <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
              {tools?.whisper_available ? "Whisper is ready for offline dictation." : "Whisper Tiny English · 78 MB. Transcribes speech on this computer."}
            </p>
            {spec && !spec.voice_auto && !tools?.whisper_available && (
              <p className="mt-2 text-sm">Install <a href="https://github.com/ggml-org/whisper.cpp" className="text-accent underline" target="_blank" rel="noreferrer">whisper-cli</a> first. StudyMate can then download the voice model.</p>
            )}
            {!tools?.whisper_available && <button type="button" className="study-secondary mt-4 disabled:opacity-50"
              disabled={busy || !spec?.voice_auto} onClick={() => voice.mutate()}>
              <Download aria-hidden className="size-4" />{voice.isPending ? "Setting up voice…" : "Download Whisper"}
            </button>}
            {voice.isError && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{voice.error.message}</p>}
          </section>
          <SystemVoiceSetup platform={spec?.system} />
        </div>
      </section>
    </div>
  );
}
