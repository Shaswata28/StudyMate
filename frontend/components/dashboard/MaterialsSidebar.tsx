"use client";

import { useRef, useState } from "react";
import { useStore } from "@/store/useStore";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type CourseSource, type DiagramOrigin } from "@/lib/api";
import type { DiagramSelection } from "./DiagramStudio";
import { toast } from "sonner";
import { ArrowLeft, Download, X, Upload, Trash2, FileText } from "lucide-react";

export default function MaterialsSidebar({ source, setSource, onDiagram, onPractice }: {
  source: CourseSource | null; setSource: (source: CourseSource | null) => void;
  onDiagram: (selection: DiagramSelection) => void;
  onPractice: (origin?: DiagramOrigin) => void;
}) {
  const { isMaterialsOpen, setIsMaterialsOpen, activeCourse } = useStore();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragDepth = useRef(0);
  const uploadLock = useRef(false);
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);
  const [failures, setFailures] = useState<{ courseId: string; messages: string[] }>();
  const [tab, setTab] = useState<"sources" | "created">("sources");
  const [selected, setSelected] = useState<string[]>([]);
  const diagrams = useQuery({
    queryKey: ["diagrams", activeCourse?.id],
    queryFn: () => api.listDiagrams(activeCourse!.id),
    enabled: !!activeCourse && isMaterialsOpen && tab === "created",
  });
  const isUploading = progress !== null;

  const { data: materials = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["materials", activeCourse?.id],
    queryFn: () => (activeCourse ? api.listMaterials(activeCourse.id) : Promise.resolve([])),
    enabled: !!activeCourse && isMaterialsOpen,
    refetchInterval: (query) => query.state.data?.some((item) => !["completed", "failed"].includes(item.processing_status)) ? 900 : false,
  });

  const preview = useQuery({
    queryKey: ["materials", activeCourse?.id, source?.id, source?.page],
    queryFn: () => api.getMaterial(activeCourse!.id, source!),
    enabled: !!activeCourse && !!source && isMaterialsOpen,
  });

  const retryMutation = useMutation({
    mutationFn: api.retryMaterial,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["materials", activeCourse?.id] }),
    onError: (error) => toast.error(error.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteMaterial(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials", activeCourse?.id] });
      void queryClient.invalidateQueries({ queryKey: ["study"] });
      toast.success("Material deleted");
    },
    onError: (error) => toast.error(error.message),
  });

  if (!activeCourse) return null;
  const readySelection = materials.filter((item) => item.processing_status === "completed" && selected.includes(item.id)).map((item) => item.id);

  async function uploadFiles(files: File[]) {
    if (!activeCourse || files.length === 0 || uploadLock.current) return;
    const courseId = activeCourse.id;
    uploadLock.current = true;
    setFailures(undefined);
    const errors: string[] = [];
    try {
      for (const [index, file] of files.entries()) {
        setProgress({ current: index + 1, total: files.length });
        try {
          await api.uploadMaterial(courseId, file);
        } catch (error) {
          errors.push(`${file.name}: ${error instanceof Error ? error.message : "Upload failed"}`);
        }
      }
      setFailures({ courseId, messages: errors });
      const added = files.length - errors.length;
      if (added) {
        void queryClient.invalidateQueries({ queryKey: ["study"] });
        void queryClient.invalidateQueries({ queryKey: ["materials", courseId] });
        toast.success(added === 1 ? "1 file queued for processing." : `${added} files queued for processing.`);
      }
    } finally {
      uploadLock.current = false;
      setProgress(null);
    }
  }

  return (
    <aside aria-label="Course materials" className="flex h-full w-full flex-col border-l border-line bg-surface"
      onDragEnter={(event) => {
        if (!event.dataTransfer.types.includes("Files")) return;
        event.preventDefault();
        dragDepth.current++;
        if (!isUploading) setDragOver(true);
      }}
      onDragOver={(event) => {
        if (!event.dataTransfer.types.includes("Files")) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = isUploading ? "none" : "copy";
      }}
      onDragLeave={() => {
        dragDepth.current = Math.max(0, dragDepth.current - 1);
        if (!dragDepth.current) setDragOver(false);
      }}
      onDrop={(event) => {
        if (!event.dataTransfer.types.includes("Files")) return;
        event.preventDefault();
        dragDepth.current = 0;
        setDragOver(false);
        const files = Array.from(event.dataTransfer.files);
        if (files.length && !uploadLock.current) {
          setSource(null);
          void uploadFiles(files);
        }
      }}>
      <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line px-4">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">Materials</h2>
          <p className="truncate text-xs text-neutral-600 dark:text-neutral-300">{activeCourse.name}</p>
        </div>
        <button type="button" onClick={() => setIsMaterialsOpen(false)} aria-label="Close materials"
          className="rounded-control p-2 hover:bg-black/5 dark:hover:bg-white/10">
          <X className="size-4" />
        </button>
      </header>
      <div className="flex gap-1 border-b border-line px-3 py-2" aria-label="Materials view">
        <button type="button" className="study-secondary flex-1" aria-pressed={!!source || tab === "sources"}
          onClick={() => { setSource(null); setTab("sources"); }}>Sources</button>
        <button type="button" className="study-secondary flex-1" aria-pressed={!source && tab === "created"}
          onClick={() => { setSource(null); setTab("created"); }}>Created</button>
      </div>
      {!source && tab === "created" ? (
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4 text-sm">
          <button type="button" className="study-secondary w-full justify-start" onClick={() => onPractice()}>Flashcards and quizzes</button>
          {diagrams.isPending ? <p role="status">Loading diagrams?</p> : diagrams.isError ? (
            <button type="button" className="underline" onClick={() => void diagrams.refetch()}>Could not load diagrams. Retry</button>
          ) : diagrams.data.length === 0 ? <p>Saved diagrams appear here.</p> : (
            <ul className="space-y-2">{diagrams.data.map((diagram) => (
              <li key={diagram.id}><button type="button" className="study-secondary w-full justify-start text-left"
                onClick={() => onDiagram(diagram)}>{diagram.title}</button></li>
            ))}</ul>
          )}
        </div>
      ) : source ? (
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          <button type="button" onClick={() => { setSource(null); setTab("sources"); }} className="flex items-center gap-2 text-sm text-accent">
            <ArrowLeft className="size-4" /> All materials
          </button>
          <h3 className="mt-4 break-words text-sm font-semibold">{source.name}</h3>
          {source.page && <p className="mt-1 text-xs">Page {source.page}</p>}
          {preview.isPending ? <p role="status" className="mt-4 text-sm">Opening source?</p> : preview.isError ? (
            <p role="alert" className="mt-4 text-sm">{preview.error.message}</p>
          ) : preview.data && <>
            <a href={`/api/courses/${activeCourse.id}/materials/${source.id}/file`} download
              className="mt-3 inline-flex items-center gap-2 text-sm text-accent">
              <Download className="size-4" /> Download original
            </a>
            <p className="mt-4 whitespace-pre-wrap break-words text-sm leading-relaxed">{preview.data.text}</p>
            {preview.data.truncated && <p className="mt-3 text-xs">Preview shortened. Download the original for the full text.</p>}
          </>}
        </div>
      ) : <>
      <div className="px-4 py-3">
        <input type="file" ref={fileInputRef} multiple className="hidden" accept=".pdf,.txt,.md,image/png,image/jpeg,image/webp"
          onChange={(event) => {
            void uploadFiles(Array.from(event.target.files ?? []));
            event.target.value = "";
          }} />
        <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading}
          className={`flex w-full flex-col items-center justify-center gap-2 rounded-control border border-dashed px-3 py-4 text-sm transition-colors disabled:opacity-70 ${dragOver ? "border-accent bg-[var(--accent-soft)]" : "border-line hover:bg-background"}`}>
          <Upload aria-hidden className="size-5 text-accent" />
          <span className="font-medium">{progress ? `Uploading ${progress.current} of ${progress.total}?` : dragOver ? "Drop files to add" : "Drop files or browse"}</span>
          {!progress && <span className="text-xs text-neutral-600 dark:text-neutral-300">PDF, TXT, Markdown, or images</span>}
        </button>
        {progress && <p role="status" className="sr-only">Uploading file {progress.current} of {progress.total}</p>}
        {failures?.courseId === activeCourse.id && failures.messages.length > 0 && (
          <ul aria-label="Upload errors" className="mt-3 max-h-32 space-y-1 overflow-y-auto break-words text-xs text-red-700 dark:text-red-300">
            {failures.messages.map((error, index) => <li key={index}>{error}</li>)}
          </ul>
        )}
      </div>
      {readySelection.length > 0 && <div className="space-y-2 px-4 pb-3">
        <button type="button" className="study-action w-full" onClick={() => onDiagram({ material_ids: readySelection })}>
          Diagram from {readySelection.length === 1 ? "source" : `${readySelection.length} sources`}
        </button>
        <button type="button" className="study-secondary w-full" onClick={() => onPractice({ material_ids: readySelection })}>
          Create study items
        </button>
      </div>}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 text-sm">
        {isLoading ? <p role="status">Loading materials?</p> : isError ? (
          <button type="button" className="underline" onClick={() => refetch()}>Could not load materials. Retry</button>
        ) : materials.length === 0 ? <p className="text-neutral-600 dark:text-neutral-300">Add your first source to study alongside your notes.</p> : (
          <ul className="divide-y divide-[var(--line)]">
            {materials.map((item) => (
              <li key={item.id} className="flex items-center gap-2 py-3">
                {item.processing_status === "completed" && (
                  <input type="checkbox" className="accent-[var(--accent)]" aria-label={`Select ${item.name} for creation`}
                    checked={selected.includes(item.id)} disabled={selected.length >= 12 && !selected.includes(item.id)}
                    onChange={(event) => setSelected((previous) => event.target.checked ? [...previous, item.id] : previous.filter((id) => id !== item.id))} />
                )}
                <FileText aria-hidden className="size-4 shrink-0 text-neutral-500" />
                <div className="min-w-0 flex-1">
                  <button type="button" disabled={item.processing_status !== "completed"}
                    onClick={() => setSource(item)} className="block max-w-full truncate text-left enabled:hover:underline" title={item.name}>{item.name}</button>
                  <p className="text-xs text-neutral-600 dark:text-neutral-300">
                    {{ queued: "Queued", extracting: "Extracting text", indexing: "Indexing text", embedding: "Creating embeddings", completed: "Ready", failed: "Failed" }[item.processing_status] ?? item.processing_status}
                    {" · "}{item.file_size < 1024 ? `${item.file_size} B` : `${(item.file_size / 1024).toFixed(0)} KB`}
                  </p>
                  {item.processing_status === "failed" && <>
                    <p className="mt-1 break-words text-xs text-red-700 dark:text-red-300">{item.processing_error}</p>
                    <button type="button" disabled={retryMutation.isPending} onClick={() => retryMutation.mutate(item.id)}
                      className="mt-1 text-xs text-accent underline">Retry processing</button>
                  </>}
                </div>
                <button type="button" aria-label={`Delete ${item.name}`} onClick={() => deleteMutation.mutate(item.id)}
                  disabled={deleteMutation.isPending} className="rounded-control p-1.5 hover:bg-black/5 hover:text-red-600 dark:hover:bg-white/10">
                  <Trash2 className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      </>}
    </aside>
  );
}
