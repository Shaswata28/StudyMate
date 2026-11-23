"use client";

import { useState } from "react";
import { useStore, Course } from "@/store/useStore";
import { X, Search } from "lucide-react";

export default function SearchCourseModal({
  courses,
  onSelectCourse,
}: {
  courses: Course[];
  onSelectCourse: (course: Course) => void;
}) {
  const { isSearchOpen, setIsSearchOpen } = useStore();
  const [query, setQuery] = useState("");

  if (!isSearchOpen) return null;

  const filtered = courses.filter((c) =>
    c.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md p-6 rounded-panel bg-white dark:bg-slate-900 border border-black/10 dark:border-white/10 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-sans text-base text-black dark:text-white">Search Courses</h3>
          <button
            onClick={() => setIsSearchOpen(false)}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type to filter courses..."
            autoFocus
            className="w-full h-10 rounded-control border border-black/20 dark:border-white/20 bg-gray-50 dark:bg-slate-800 px-3 pl-10 text-xs text-black dark:text-white focus:outline-none focus:ring-2 focus:ring-[#FEAE01]"
          />
        </div>

        <div className="max-h-60 overflow-y-auto space-y-1">
          {filtered.length === 0 ? (
            <p className="text-center text-xs text-gray-400 py-4">No matching courses found</p>
          ) : (
            filtered.map((c) => (
              <div
                key={c.id}
                onClick={() => {
                  onSelectCourse(c);
                  setIsSearchOpen(false);
                }}
                className="flex items-center gap-3 p-2.5 rounded-control hover:bg-gray-100 dark:hover:bg-slate-800 cursor-pointer text-xs"
              >
                <span
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: c.color || "#FEAE01" }}
                />
                <span className="font-sans font-medium text-black dark:text-white truncate">
                  {c.name}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

