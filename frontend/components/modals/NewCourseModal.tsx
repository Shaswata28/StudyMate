"use client";

import { useState } from "react";
import { useStore, SubjectProfile } from "@/store/useStore";
import { X, Check } from "lucide-react";

const COLORS = ["#879478", "#BA826E", "#BB9A56", "#7892A8", "#9A86A8", "#A58F77"];

export default function NewCourseModal({
  onCreateCourse,
}: {
  onCreateCourse: (name: string, color: string, subject: SubjectProfile) => Promise<any>;
}) {
  const { isNewCourseOpen, setIsNewCourseOpen } = useStore();
  const [name, setName] = useState("");
  const [subject, setSubject] = useState<SubjectProfile>("general");
  const [selectedColor, setSelectedColor] = useState(COLORS[0]);
  const [isLoading, setIsLoading] = useState(false);

  if (!isNewCourseOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setIsLoading(true);
      await onCreateCourse(name.trim(), selectedColor, subject);
      setName("");
      setSubject("general");
      setIsNewCourseOpen(false);
    } catch {
      // The workspace reports the request error.
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md p-6 rounded-panel bg-white dark:bg-slate-900 border border-black/10 dark:border-white/10 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-sans text-lg text-black dark:text-white">Create New Course</h3>
          <button
            onClick={() => setIsNewCourseOpen(false)}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-sans mb-2 text-gray-700 dark:text-gray-300">
              Course Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Distributed Systems, Organic Chemistry"
              autoFocus
              required
              className="w-full h-11 rounded-control border border-black/20 dark:border-white/20 bg-gray-50 dark:bg-slate-800 px-4 text-sm text-black dark:text-white focus:outline-none focus:ring-2 focus:ring-[#FEAE01]"
            />
          </div>

          <label className="block space-y-2 text-sm">
            <span>Subject profile</span>
            <select
              className="w-full rounded-control border bg-white p-3 dark:bg-slate-800"
              value={subject}
              onChange={(event) => setSubject(event.target.value as SubjectProfile)}
            >
              <option value="general">General</option>
              <option value="stem">Math, physics, engineering &amp; code</option>
              <option value="life_sciences">Chemistry &amp; biology</option>
              <option value="humanities">Arts &amp; humanities</option>
            </select>
          </label>

          <div>
            <label className="block text-xs font-sans mb-2 text-gray-700 dark:text-gray-300">
              Badge Color
            </label>
            <div className="flex items-center gap-3">
              {COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  aria-label={c}
                  aria-pressed={selectedColor === c}
                  onClick={() => setSelectedColor(c)}
                  className="w-8 h-8 rounded-full flex items-center justify-center transition-transform hover:scale-110"
                  style={{ backgroundColor: c }}
                >
                  {selectedColor === c && <Check className="w-4 h-4 text-white drop-shadow" />}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3">
            <button
              type="button"
              onClick={() => setIsNewCourseOpen(false)}
              className="px-5 h-10 rounded-control border border-black/10 dark:border-white/10 text-xs font-sans hover:bg-gray-50 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !name.trim()}
              className="px-6 h-10 rounded-control bg-black dark:bg-white text-white dark:text-black text-xs font-sans hover:opacity-90 disabled:opacity-50 btn-micro"
            >
              {isLoading ? "Creating..." : "Create Course"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
