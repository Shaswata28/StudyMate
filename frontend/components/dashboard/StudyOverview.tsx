"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ArrowUpRight, BookOpen, FileText, MessageCircle, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { type Course, useStore } from "@/store/useStore";

const subjects: Record<Course["subject_profile"], string> = {
  general: "General",
  stem: "STEM",
  life_sciences: "Chemistry & biology",
  humanities: "Arts & humanities",
};

export default function StudyOverview({ name, courses, coursesPending, onResume, onReview }: {
  name: string;
  courses: Course[];
  coursesPending: boolean;
  onReview: (courseId: string) => void;
  onResume: (course: Course) => void;
}) {
  const { data, isError, refetch } = useQuery({ queryKey: ["study"], queryFn: api.getStudy });
  const setIsNewCourseOpen = useStore((state) => state.setIsNewCourseOpen);
  const latest = data?.recent[0];
  const lastCourse = courses.find((course) => course.id === latest?.course_id);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <main className="study-enter min-h-0 flex-1 overflow-y-auto px-5 py-8 sm:px-8 lg:px-12 lg:py-12">
      <div className="mx-auto max-w-5xl space-y-10">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            <h1 className="break-words font-display text-5xl leading-none tracking-tight md:text-6xl">{greeting}, {name}.</h1>
            <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-300">
              {lastCourse ? "Pick up where you left off, or open a course below." : "Open a course to study, or make space for something new."}
            </p>
          </div>
          <button type="button" onClick={() => setIsNewCourseOpen(true)} className="study-action">
            <Plus className="size-4" aria-hidden /> New course
          </button>
        </header>

        <dl aria-label="Study summary" className="grid grid-cols-3 divide-x divide-[var(--line)] rounded-panel border border-line bg-surface">
          {([
            [BookOpen, "Courses", coursesPending ? undefined : courses.length],
            [MessageCircle, "Questions", data?.turns],
            [FileText, "Materials", data?.materials],
          ] as const).map(([Icon, label, count]) => (
            <div key={label} className="min-w-0 px-3 py-4 sm:px-5">
              <dt className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-300 sm:text-sm">
                <Icon aria-hidden className="hidden size-4 shrink-0 text-accent sm:block" /> {label}
              </dt>
              <dd className="mt-2 font-display text-4xl leading-none">{count ?? "—"}</dd>
            </div>
          ))}
        </dl>

        <section aria-labelledby="due-heading">
          <h2 id="due-heading" className="font-display text-3xl">Flashcards due today</h2>
          <p className="mt-2 text-sm">{data?.due_flashcards ?? "?"} due</p>
          {Boolean(data?.due_courses.length) && <ul className="mt-3 flex flex-wrap gap-2">
            {data?.due_courses.map(({ course_id, count }) => {
              const course = courses.find((item) => item.id === course_id);
              return course && <li key={course_id}><button type="button" className="study-secondary" onClick={() => onReview(course_id)}>
                {course.name} · {count}
              </button></li>;
            })}
          </ul>}
        </section>
        {latest && lastCourse && (
          <section aria-labelledby="resume-heading">
            <h2 id="resume-heading" className="mb-3 font-display text-3xl">Continue studying</h2>
            <button type="button" onClick={() => onResume(lastCourse)}
              className="flex w-full items-center justify-between gap-4 rounded-panel border border-line bg-[var(--accent-soft)] px-5 py-4 text-left transition-colors hover:border-accent sm:px-6 sm:py-5">
              <span className="min-w-0 space-y-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-accent">
                  <span className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: lastCourse.color }} /> {lastCourse.name}
                </span>
                <span className="line-clamp-2 break-words text-base leading-snug sm:text-lg">{latest.question}</span>
              </span>
              <span className="flex shrink-0 items-center gap-2 text-sm font-medium text-accent">
                <span className="hidden sm:inline">Resume chat</span><ArrowRight aria-hidden className="size-5" />
              </span>
            </button>
          </section>
        )}

        <section aria-labelledby="courses-heading">
          <h2 id="courses-heading" className="font-display text-3xl">Your courses</h2>
          {coursesPending ? <p role="status" className="mt-3 text-sm">Loading courses…</p> : courses.length === 0 ? (
            <div className="mt-3 rounded-panel border border-dashed border-line bg-surface px-5 py-6">
              <p className="text-sm">Create a course to start a chat and keep its materials together.</p>
              <button type="button" onClick={() => setIsNewCourseOpen(true)} className="study-secondary mt-4">Create your first course</button>
            </div>
          ) : (
            <ul className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {courses.map((course) => (
                <li key={course.id}>
                  <button type="button" onClick={() => onResume(course)}
                    className="group flex h-full min-h-28 w-full flex-col items-start rounded-panel border border-line bg-surface p-4 text-left transition-colors hover:border-accent">
                    <span className="flex w-full items-center justify-between gap-3">
                      <BookOpen aria-hidden className="size-5" style={{ color: course.color }} />
                      <ArrowUpRight aria-hidden className="size-4 shrink-0 text-accent" />
                    </span>
                    <span className="mt-3 max-w-full break-words text-base font-semibold leading-snug">{course.name}</span>
                    <span className="mt-1 text-xs text-neutral-600 dark:text-neutral-300">{subjects[course.subject_profile] ?? subjects.general}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="recent-heading">
          <h2 id="recent-heading" className="font-display text-3xl">Recent questions</h2>
          {isError ? <button type="button" className="mt-3 text-sm text-accent underline" onClick={() => refetch()}>Could not load recent activity. Retry</button>
            : !data ? <p role="status" className="mt-3 text-sm">Loading recent activity…</p>
            : data.recent.length === 0 ? <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-300">Questions will appear here after your first chat.</p>
            : (
              <ul className="mt-3 divide-y divide-[var(--line)] rounded-panel border border-line bg-surface px-3 sm:px-4">
                {data.recent.map((turn) => {
                  const course = courses.find((item) => item.id === turn.course_id);
                  return (
                    <li key={turn.id}>
                      <button type="button" disabled={!course} onClick={() => course && onResume(course)}
                        className="flex w-full items-center gap-3 rounded-control px-2 py-3.5 text-left transition-colors hover:bg-background disabled:opacity-60">
                        <MessageCircle aria-hidden className="size-4 shrink-0 text-accent" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-medium">{turn.question}</span>
                          <span className="mt-1 block truncate text-xs text-neutral-600 dark:text-neutral-300">{turn.course} · {new Date(turn.created_at).toLocaleDateString()}</span>
                        </span>
                        <ArrowUpRight aria-hidden className="size-4 shrink-0 text-accent" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
        </section>
      </div>
    </main>
  );
}
