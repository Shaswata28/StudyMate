"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api, type DiagramOrigin, type PracticeContent, type PracticeItem, type PracticeKind } from "@/lib/api";

const field = "mt-1 block w-full rounded-control border border-line bg-background p-2";

export default function PracticeStudio({ courseId, origin, close }: {
  courseId: string; origin?: DiagramOrigin; close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cache = useQueryClient();
  const key = ["practice", courseId];
  const list = useQuery({ queryKey: key, queryFn: () => api.listPractice(courseId) });
  const [kind, setKind] = useState<PracticeKind>("flashcard");
  const [topic, setTopic] = useState("");
  const [creating, setCreating] = useState(Boolean(origin));
  const [active, setActive] = useState<number>();
  const [revealed, setRevealed] = useState(false);
  const [grade, setGrade] = useState<boolean>();
  const [edit, setEdit] = useState<PracticeContent>();
  const [choiceText, setChoiceText] = useState("");
  const item = list.data?.find((entry) => entry.id === active);

  useEffect(() => { dialog.current?.showModal(); }, []);

  function store(item: PracticeItem) {
    cache.setQueryData<PracticeItem[]>(key, (previous = []) =>
      [...previous.filter((entry) => entry.id !== item.id), item].sort((a, b) => a.due_at - b.due_at || a.id - b.id));
  }

  const review = useMutation({
    mutationFn: (value: { recalled: boolean } | { choice: string }) => api.reviewPractice(courseId, item!, value),
    onSuccess: (result) => {
      store(result.item);
      setGrade(result.correct);
      setRevealed(true);
      void cache.invalidateQueries({ queryKey: ["study"] });
    },
    onError: () => void list.refetch(),
  });
  const update = useMutation({
    mutationFn: () => api.editPractice(courseId, item!, {
      ...edit!, choices: item?.kind === "quiz" ? choiceText.split("\n").map((value) => value.trim()).filter(Boolean) : [],
    }),
    onSuccess: (saved) => { store(saved); setEdit(undefined); },
    onError: () => void list.refetch(),
  });
  const generate = useMutation({
    mutationFn: () => api.createPractice(courseId, origin!, kind, topic),
    onSuccess: async (items) => {
      await cache.invalidateQueries({ queryKey: key });
      void cache.invalidateQueries({ queryKey: ["study"] });
      setCreating(false);
      select(items[0].id);
    },
  });

  function select(id?: number) {
    setActive(id);
    setRevealed(false);
    setGrade(undefined);
    setEdit(undefined);
    review.reset();
    update.reset();
  }

  const busy = update.isPending || review.isPending;
  const error = generate.error || review.error || update.error;
  return (
    <dialog ref={dialog} onClose={close} aria-labelledby="practice-title"
      className="fixed inset-0 m-auto max-h-[90vh] w-[min(44rem,calc(100%-2rem))] overflow-auto rounded-panel border border-line bg-surface p-5 text-foreground shadow-xl backdrop:bg-black/45 sm:p-7">
      <header className="flex items-center justify-between gap-3">
        <h2 id="practice-title" className="font-display text-3xl">Study tools</h2>
        <button type="button" className="study-secondary" aria-label="Close study tools" onClick={close}><X className="size-4" /></button>
      </header>
      {creating ? (
        <form className="mt-5 space-y-4" onSubmit={(event) => { event.preventDefault(); generate.mutate(); }}>
          <label className="block text-sm">Study format
            <select className={field} value={kind} disabled={generate.isPending} onChange={(event) => setKind(event.target.value as PracticeKind)}>
              <option value="flashcard">Flashcards</option><option value="quiz">Multiple-choice quiz</option>
            </select>
          </label>
          <label className="block text-sm">Topic
            <input className={field} value={topic} placeholder="Optional focus" maxLength={4000} disabled={generate.isPending}
              onChange={(event) => setTopic(event.target.value)} />
          </label>
          <button type="submit" className="study-action" disabled={generate.isPending}>{generate.isPending ? "Preparing study items…" : "Generate"}</button>
        </form>
      ) : item ? (
        <div className="mt-5 space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" className="study-secondary" disabled={busy} onClick={() => select()}>All study items</button>
            {!edit && <button type="button" className="study-secondary" disabled={busy} onClick={() => {
              setEdit({ question: item.question, answer: item.answer, explanation: item.explanation, choices: item.choices });
              setChoiceText(item.choices.join("\n"));
            }}>Edit item</button>}
          </div>
          {edit ? (
            <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); update.mutate(); }}>
              {(["question", "answer", "explanation"] as const).map((name) => (
                <label key={name} className="block text-sm capitalize">{name}
                  <textarea className={field} required value={edit[name]} disabled={busy} maxLength={{ question: 300, answer: 400, explanation: 650 }[name]}
                    onChange={(event) => setEdit({ ...edit, [name]: event.target.value })} />
                </label>
              ))}
              {item.kind === "quiz" && <label className="block text-sm">Choices, one per line
                <textarea className={field} required value={choiceText} disabled={busy} onChange={(event) => setChoiceText(event.target.value)} />
              </label>}
              <div className="flex gap-2">
                <button type="submit" className="study-action" disabled={busy}>Save item</button>
                <button type="button" className="study-secondary" disabled={busy} onClick={() => { setEdit(undefined); update.reset(); }}>Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <h3 className="break-words font-display text-2xl">{item.question}</h3>
              {item.kind === "quiz" && grade === undefined && <div className="grid gap-2">
                {item.choices.map((choice) => <button key={choice} type="button" className="study-secondary justify-start text-left"
                  disabled={busy} onClick={() => review.mutate({ choice })}>{choice}</button>)}
              </div>}
              {item.kind === "flashcard" && !revealed && <button type="button" className="study-action" onClick={() => setRevealed(true)}>Show answer</button>}
              {revealed && <div className="space-y-2 rounded-control border border-line bg-background p-4 text-sm">
                {grade !== undefined && <p role="status" className="font-medium">{grade ? "Correct" : "Review again"}</p>}
                <p className="font-semibold">{item.answer}</p>
                <p className="whitespace-pre-wrap">{item.explanation}</p>
                <details open={grade === false}>
                  <summary className="cursor-pointer font-medium text-accent">{item.evidence.source.name}{item.evidence.source.page ? ` · p. ${item.evidence.source.page}` : ""}</summary>
                  <blockquote className="mt-2 whitespace-pre-wrap break-words border-l border-line pl-3">{item.evidence.text}</blockquote>
                </details>
              </div>}
              {item.kind === "flashcard" && revealed && grade === undefined && <div className="flex flex-wrap gap-2">
                <button type="button" className="study-secondary" disabled={busy} onClick={() => review.mutate({ recalled: false })}>Again</button>
                <button type="button" className="study-action" disabled={busy} onClick={() => review.mutate({ recalled: true })}>Remembered</button>
              </div>}
              {grade !== undefined && <p className="text-sm">Next review {new Date(item.due_at * 1000).toLocaleString()}</p>}
            </>
          )}
        </div>
      ) : (
        <div className="mt-5 space-y-2">
          {list.isPending ? <p role="status">Loading study items…</p> : list.isError ? (
            <button type="button" className="study-secondary" onClick={() => void list.refetch()}>Could not load study items. Retry</button>
          ) : !list.data.length ? <p>Select course sources to create flashcards or a quiz.</p> : list.data.map((entry) => (
            <button type="button" key={entry.id} className="study-secondary w-full flex-col items-start text-left" onClick={() => select(entry.id)}>
              <span>{entry.question}</span>
              <span className="text-xs font-normal text-neutral-600 dark:text-neutral-300">
                {entry.kind === "flashcard" ? "Flashcard" : "Quiz"} · {entry.due_at * 1000 <= Date.now() ? "Due now" : new Date(entry.due_at * 1000).toLocaleString()}
              </span>
            </button>
          ))}
        </div>
      )}
      {error && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{error.message}</p>}
    </dialog>
  );
}
