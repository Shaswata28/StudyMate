"use client";

import Link from "next/link";
import { CircleUserRound, BookOpen, FlaskConical, Grid2X2, LibraryBig, Plus, Search, SquareFunction, Trash2 } from "lucide-react";
import { useStore, type Course } from "@/store/useStore";

const subjectIcons = {
  general: BookOpen,
  stem: SquareFunction,
  life_sciences: FlaskConical,
  humanities: LibraryBig,
};
const navButton = "flex w-full items-center gap-3 rounded-control px-3 py-2.5 text-left text-sm transition-colors hover:bg-black/5 dark:hover:bg-white/10";

export default function Sidebar({ courses, profileName, avatar, onSelectCourse, onDeleteCourse }: {
  courses: Course[];
  profileName: string;
  avatar?: string | null;
  onSelectCourse: (course: Course) => void;
  onDeleteCourse: (courseId: string) => void;
}) {
  const { activeCourse, setActiveCourse, setIsNewCourseOpen, setIsSearchOpen } = useStore();

  return (
    <aside aria-label="Course navigation" className="flex h-full w-[min(18rem,85vw)] shrink-0 flex-col border-r border-line bg-surface">
      <div className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-line px-4">
        <span className="font-display text-[1.7rem] leading-none tracking-tight">StudyMate</span>
      </div>
      <nav aria-label="Study tools" className="space-y-1 p-3">
        <button type="button" onClick={() => setActiveCourse(null)} aria-current={!activeCourse ? "page" : undefined}
          className={`${navButton} ${!activeCourse ? "bg-[var(--accent-soft)]" : ""}`}>
          <Grid2X2 aria-hidden className="size-[18px] shrink-0" /> Study overview
        </button>
        <button type="button" onClick={() => setIsNewCourseOpen(true)} className={navButton}>
          <Plus aria-hidden className="size-[18px] shrink-0" /> New course
        </button>
        <button type="button" onClick={() => setIsSearchOpen(true)} className={navButton}>
          <Search aria-hidden className="size-[18px] shrink-0" /> Search courses
        </button>
      </nav>
      <nav aria-label="My courses" className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
        <h2 className="mb-2 px-3 text-xs font-medium text-neutral-600 dark:text-neutral-300">My courses</h2>
        <ul className="space-y-1">
          {courses.map((course) => {
            const Icon = subjectIcons[course.subject_profile] ?? BookOpen;
            const selected = activeCourse?.id === course.id;
            return (
              <li key={course.id} className={`group flex items-center gap-1 rounded-control ${selected ? "bg-[var(--accent-soft)]" : ""}`}>
                <button type="button" onClick={() => onSelectCourse(course)} aria-current={selected ? "page" : undefined}
                  className={`${navButton} min-w-0 flex-1 ${selected ? "font-semibold" : ""}`}>
                  <Icon aria-hidden className="size-[18px] shrink-0" style={{ color: course.color }} />
                  <span className="truncate" title={course.name}>{course.name}</span>
                </button>
                <button type="button" onClick={() => onDeleteCourse(course.id)}
                  aria-label={`Delete ${course.name}`} title={`Delete ${course.name}`}
                  className="mr-1 shrink-0 rounded-control p-2 opacity-70 hover:bg-black/5 hover:text-red-700 focus-visible:opacity-100 dark:hover:bg-white/10 dark:hover:text-red-300">
                  <Trash2 className="size-4" />
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="shrink-0 border-t border-line p-3">
        <Link href="/settings" className={navButton} aria-label={`Settings for ${profileName}`}>
          {avatar ? <img src={avatar} alt="" className="size-7 shrink-0 rounded-full object-cover" />
            : <CircleUserRound aria-hidden className="size-7 shrink-0 text-accent" />}
          <span className="truncate">{profileName}</span>
        </Link>
      </div>
    </aside>
  );
}
