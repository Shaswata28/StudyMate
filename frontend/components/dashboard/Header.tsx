"use client";

import { useStore } from "@/store/useStore";
import { Bookmark, PanelLeft, FolderOpen } from "lucide-react";

const control = "shrink-0 rounded-control p-2 hover:bg-black/5 dark:hover:bg-white/10";

export default function Header({ coursesVisible, materialsVisible, savedOpen, toggleCourses, toggleMaterials, toggleSaved }: {
  coursesVisible: boolean; materialsVisible: boolean; savedOpen: boolean;
  toggleCourses: () => void; toggleMaterials: () => void; toggleSaved: () => void;
}) {
  const { activeCourse } = useStore();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-line bg-background px-3 sm:px-5">
      <div className="flex min-w-0 items-center gap-2">
        <button type="button" onClick={toggleCourses} aria-expanded={coursesVisible}
          title="Toggle courses" aria-label="Toggle courses" className={control}>
          <PanelLeft className="size-4" />
        </button>
        {activeCourse && <span className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: activeCourse.color }} />}
        <span className="truncate text-sm font-medium">{activeCourse?.name ?? "Study overview"}</span>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {activeCourse && <>
          <button type="button" onClick={toggleSaved} aria-pressed={savedOpen} title={savedOpen ? "Back to chat" : "Saved answers"} aria-label={savedOpen ? "Back to chat" : "Saved answers"} className={control}>
            <Bookmark className="size-4" />
          </button>
          <button type="button" onClick={toggleMaterials} aria-expanded={materialsVisible}
            title="Study materials" aria-label="Toggle course materials" className={control}>
            <FolderOpen className="size-4" />
          </button>
        </>}
      </div>
    </header>
  );
}
