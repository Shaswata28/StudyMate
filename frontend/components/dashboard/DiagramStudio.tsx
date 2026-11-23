"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { renderDiagram } from "@/lib/renderDiagram";
import { Download, X } from "lucide-react";
import { api, type DiagramOrigin, type DiagramType, type SavedDiagram } from "@/lib/api";

export type DiagramSelection = DiagramOrigin | SavedDiagram;

function saveFile(data: Blob, name: string) {
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function DiagramStudio({ courseId, selection, close }: {
  courseId: string; selection: DiagramSelection; close: () => void;
}) {
  const cache = useQueryClient();
  const dialog = useRef<HTMLDialogElement>(null);
  const renderId = useId().replace(/[^a-z0-9]/gi, "");
  const [diagram, setDiagram] = useState<SavedDiagram | null>("id" in selection ? selection : null);
  const [diagramType, setDiagramType] = useState<DiagramType>("flowchart");
  const [question, setQuestion] = useState("");
  const [title, setTitle] = useState(diagram?.title ?? "");
  const [code, setCode] = useState(diagram?.mermaid ?? "");
  const [preview, setPreview] = useState<{ code: string; svg: string }>();
  const [previewError, setPreviewError] = useState("");
  const [exportError, setExportError] = useState("");
  const [exporting, setExporting] = useState(false);
  const ready = preview?.code === code;
  const image = preview ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(preview.svg)}` : "";

  useEffect(() => { dialog.current?.showModal(); }, []);

  useEffect(() => {
    if (!diagram) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const svg = await renderDiagram(`study-diagram-${renderId}`, code);
        if (!cancelled) {
          setPreview({ code, svg });
          setPreviewError("");
        }
      } catch {
        if (!cancelled) setPreviewError("The current Mermaid text could not be rendered.");
      }
    }, 300);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [code, diagram, renderId]);

  const save = useMutation({
    mutationFn: () => diagram
      ? api.updateDiagram(courseId, diagram, title, code)
      : api.createDiagram(courseId, selection as DiagramOrigin, question, diagramType),
    onSuccess: (saved) => {
      setDiagram(saved);
      setTitle(saved.title);
      setCode(saved.mermaid);
      void cache.invalidateQueries({ queryKey: ["diagrams", courseId] });
    },
  });

  async function exportPng() {
    setExportError("");
    setExporting(true);
    try {
      const picture = new Image();
      picture.src = image;
      await picture.decode();
      const scale = Math.min(2, 4096 / Math.max(picture.naturalWidth, picture.naturalHeight));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(picture.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(picture.naturalHeight * scale));
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Canvas unavailable");
      context.drawImage(picture, 0, 0, canvas.width, canvas.height);
      const png = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!png) throw new Error("PNG unavailable");
      saveFile(png, `${title.trim() || "flowchart"}.png`);
    } catch {
      setExportError("Could not export this diagram as PNG.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <dialog ref={dialog} onClose={close} aria-labelledby="diagram-title"
      className="fixed inset-0 m-auto max-h-[90vh] w-[min(66rem,calc(100%-2rem))] overflow-auto rounded-panel border border-line bg-surface p-5 text-foreground shadow-xl backdrop:bg-black/45 sm:p-7">
      <header className="flex items-center justify-between gap-4">
        <h2 id="diagram-title" className="font-display text-3xl">{diagram ? "Edit diagram" : "Create diagram"}</h2>
        <button className="study-secondary" type="button" aria-label="Close diagram" onClick={() => dialog.current?.close()}><X className="size-4" /></button>
      </header>
      {!diagram ? (
        <form className="mt-5 space-y-4" onSubmit={(event) => { event.preventDefault(); save.mutate(); }}>
          <label className="block text-sm">Diagram type
            <select className="mt-2 block w-full rounded-control border border-line bg-background p-2" value={diagramType}
              disabled={save.isPending} onChange={(event) => setDiagramType(event.target.value as DiagramType)}>
              <option value="flowchart">Flowchart</option><option value="sequence">Sequence diagram</option>
            </select>
          </label>
          <label className="block text-sm">What should the diagram show?
            <textarea disabled={save.isPending} className="mt-2 block min-h-24 w-full rounded-control border border-line bg-background p-3" value={question}
              maxLength={4000} onChange={(event) => setQuestion(event.target.value)} placeholder="Optional. Describe the process or interaction." />
          </label>
          {diagramType === "flowchart" && <p className="text-xs text-neutral-600 dark:text-neutral-300">For branching flowcharts, select the Balanced tutor model in Local setup.</p>}
          <button type="submit" className="study-action" disabled={save.isPending}>{save.isPending ? "Generating…" : "Generate diagram"}</button>
        </form>
      ) : (
        <>
          <label className="mt-5 block text-sm">Title
            <input className="mt-2 block w-full rounded-control border border-line bg-background p-2" value={title}
              maxLength={100} disabled={save.isPending} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="text-sm">Mermaid
              <textarea spellCheck={false} className="mt-2 block min-h-64 w-full rounded-control border border-line bg-background p-3 font-mono"
                value={code} maxLength={12000} disabled={save.isPending} onChange={(event) => setCode(event.target.value)} />
            </label>
            <div className="text-sm">
              <p>Preview</p>
              <div className="mt-2 flex min-h-64 items-center justify-center overflow-auto rounded-control border border-line bg-white p-3 text-neutral-700">
                {image ? <img src={image} alt={title || "Diagram preview"} className="max-w-full" /> : previewError ? "Preview unavailable." : "Rendering preview…"}
              </div>
              {previewError && <p role="alert" className="mt-2 text-red-700 dark:text-red-300">{previewError}{preview ? " Showing the last valid preview." : ""}</p>}
            </div>
          </div>
          {diagram.sources.length > 0 && <ul aria-label="Sources" className="mt-3 flex flex-wrap gap-2 text-xs">
            {diagram.sources.map((source, index) => <li key={index} className="rounded-full border border-line px-2 py-1">
              {source.name}{source.page ? ` · p. ${source.page}` : ""}
            </li>)}
          </ul>}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <button type="button" className="study-action" disabled={!ready || !title.trim() || save.isPending || (code === diagram.mermaid && title === diagram.title)}
              onClick={() => save.mutate()}>Save changes</button>
            <button type="button" className="study-secondary" disabled={!ready} onClick={() => {
              if (preview) saveFile(new Blob([preview.svg], { type: "image/svg+xml" }), `${title.trim() || "flowchart"}.svg`);
            }}><Download className="size-4" /> SVG</button>
            <button type="button" className="study-secondary" disabled={!ready || exporting} onClick={() => void exportPng()}><Download className="size-4" /> PNG</button>
          </div>
        </>
      )}
      {(save.error || exportError) && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{save.error?.message || exportError}</p>}
    </dialog>
  );
}
