"use client";

import { useEffect, useId, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DiagramSyntaxError, renderDiagram } from "@/lib/renderDiagram";
import { useStore } from "@/store/useStore";

function normalizeReplyDiagram(code: string) {
  const source = code.trim().replace(/\\?<br(?:\s*\/?>|\/)/gi, " ").replace(/<\/?(?:i|b|em|strong)>/gi, "");
  if (!/^(?:flowchart|graph)\s/.test(source)) return source;
  let depth = 0;
  return source.split("\n").filter((line) => {
    if (/^\s*subgraph\b/.test(line)) depth++;
    if (!/^\s*end\s*$/.test(line)) return true;
    if (!depth) return false;
    depth--;
    return true;
  }).join("\n");
}

function repairLegacyFlowchart(source: string) {
  if (!/^(?:flowchart|graph)\s/.test(source)) return source;
  const lines = source.split("\n");
  const repaired: string[] = [];
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const match = /^(\s*)(\w+)\s*(---|-->|--)\s*\|(.+)$/.exec(line);
    if (!match) {
      repaired.push(line);
      continue;
    }
    const [, indent, start, arrow, rest] = match;
    const parts = rest.split("|").map((part) => part.trim());
    const target = parts.at(-1);
    if (parts.length > 2 && target && /^\w+$/.test(target)) {
      const label = parts.slice(0, -1).filter(Boolean).join(" · ").replace(/"/g, "#34;");
      repaired.push(`${indent}${start} ${arrow === "---" ? "---" : "-->"}|"${label}"| ${target}`);
    } else if (parts.length === 1 && /^\s*\\?\|/.test(lines[index + 1] ?? "")) {
      const notes = [rest.trim()];
      while (/^\s*\\?\|/.test(lines[index + 1] ?? "")) notes.push(lines[++index].replace(/^\s*\\?\|\s*-?\s*/, "").trim());
      let noteId = `studyMateDiagramNote${index}`;
      while (source.includes(noteId)) noteId += "_";
      repaired.push(`${indent}${start} --- ${noteId}["${notes.join(" · ").replace(/"/g, "#34;")}"]`);
    } else {
      repaired.push(line);
    }
  }
  return repaired.join("\n");
}

export default function ChatDiagram({ code, turnId }: { code: string; turnId?: number }) {
  const id = useId().replace(/[^a-z0-9]/gi, "");
  const courseId = useStore((state) => state.activeCourse?.id);
  const queryClient = useQueryClient();
  const [submitted, setSubmitted] = useState(() => normalizeReplyDiagram(code));
  const [edit, setEdit] = useState<string>();
  const [result, setResult] = useState<{ source: string; svg: string; error?: string }>();
  const [repairing, setRepairing] = useState(false);
  const save = useMutation({
    mutationFn: () => api.saveReplyDiagram(courseId!, turnId!, submitted),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["diagrams", courseId] }),
  });

  useEffect(() => {
    let cancelled = false;
    async function preview() {
      try {
        const svg = await renderDiagram(`chat-diagram-${id}`, submitted);
        if (!cancelled) setResult({ source: submitted, svg });
      } catch (error) {
        if (cancelled) return;
        let message = error instanceof Error ? error.message.slice(0, 600) : "Preview failed.";
        if (error instanceof DiagramSyntaxError && submitted === normalizeReplyDiagram(code)) {
          const local = repairLegacyFlowchart(submitted);
          if (local !== submitted) {
            try {
              const svg = await renderDiagram(`chat-diagram-${id}`, local);
              if (!cancelled) {
                setResult({ source: local, svg });
                setSubmitted(local);
              }
              return;
            } catch (localError) {
              if (localError instanceof DiagramSyntaxError) message = localError.message.slice(0, 600);
            }
          }
        }
        if (cancelled) return;
        if (error instanceof DiagramSyntaxError && courseId && turnId !== undefined
            && submitted.length <= 4000 && submitted === normalizeReplyDiagram(code)) {
          setRepairing(true);
          try {
            const repair = await queryClient.fetchQuery({
              queryKey: ["diagram-repair", courseId, turnId, submitted],
              queryFn: () => api.repairReplyDiagram(courseId, turnId, submitted, message || "Invalid Mermaid syntax.").catch(() => null),
              staleTime: Infinity,
              retry: false,
            });
            if (!cancelled && repair && repair.mermaid !== submitted) {
              const svg = await renderDiagram(`chat-diagram-${id}`, repair.mermaid);
              if (!cancelled) {
                setResult({ source: repair.mermaid, svg });
                setSubmitted(repair.mermaid);
                return;
              }
            }
          } catch {
            // Keep the original draft available for inline editing.
          } finally {
            if (!cancelled) setRepairing(false);
          }
        }
        if (!cancelled) setResult({ source: submitted, svg: "", error: message });
      }
    }
    if (result?.source !== submitted) void preview();
    return () => { cancelled = true; };
  }, [submitted, id, code, courseId, turnId, queryClient, result?.source]);

  if (result?.source !== submitted) return <p role="status" className="text-sm">{repairing ? "Repairing diagram…" : "Rendering diagram…"}</p>;
  const saved = save.data?.mermaid === submitted.trim();
  return (
    <div className="rounded-panel border border-line bg-surface p-4 text-sm">
      {result.svg ? (
        <figure className="overflow-auto rounded-control bg-white p-3">
          <img src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(result.svg)}`}
            alt="Diagram showing the tutor’s explanation" className="mx-auto max-w-full" />
        </figure>
      ) : (
        <>
          <p role="status">This diagram could not be rendered.</p>
          {result.error && <details className="mt-2"><summary>Preview error</summary>
            <pre className="overflow-auto whitespace-pre-wrap">{result.error}</pre>
          </details>}
        </>
      )}
      {edit === undefined ? <div className="mt-3 flex flex-wrap gap-2">
        {result.svg && courseId && turnId !== undefined && <button type="button" className="study-secondary"
          disabled={save.isPending || saved} onClick={() => save.mutate()}>
          {saved ? "Saved to Created" : save.isPending ? "Saving…" : "Save diagram"}
        </button>}
        <button type="button" className="study-secondary" onClick={() => setEdit(submitted)}>Edit Mermaid</button>
      </div> : (
        <form className="mt-3 space-y-2" onSubmit={(event) => { event.preventDefault(); setSubmitted(edit.trim()); setEdit(undefined); save.reset(); }}>
          <label className="block">Mermaid source
            <textarea value={edit} onChange={(event) => setEdit(event.target.value)} spellCheck={false} maxLength={12000}
              className="mt-1 block min-h-40 w-full rounded-control border border-line bg-background p-2 font-mono" />
          </label>
          <div className="flex gap-2">
            <button type="submit" className="study-action" disabled={!edit.trim()}>Preview diagram</button>
            <button type="button" className="study-secondary" onClick={() => setEdit(undefined)}>Cancel</button>
          </div>
        </form>
      )}
      {save.error && <p role="alert" className="mt-2 text-red-700 dark:text-red-300">{save.error.message}</p>}
    </div>
  );
}
