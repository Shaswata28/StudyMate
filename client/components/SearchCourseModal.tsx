import { X, Search } from "lucide-react";
import { useState, useMemo } from "react";

interface Course {
  id: string;
  name: string;
  color: string;
  active?: boolean;
}

interface SearchCourseModalProps {
  isOpen: boolean;
  onClose: () => void;
  courses: Course[];
  onCourseSelect: (courseId: string) => void;
}

export default function SearchCourseModal({
  isOpen,
  onClose,
  courses,
  onCourseSelect,
}: SearchCourseModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCourses = useMemo(() => {
    if (!searchQuery.trim()) return courses;
    return courses.filter((course) =>
      course.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery, courses]);

  const handleCourseClick = (courseId: string) => {
    onCourseSelect(courseId);
    setSearchQuery("");
    onClose();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
      setSearchQuery("");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur */}
      <div
        className="absolute inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm transition-colors"
        onClick={() => {
          onClose();
          setSearchQuery("");
        }}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[639px] mx-4 bg-white dark:bg-slate-800 rounded-[34px] border-2 border-black dark:border-white shadow-2xl p-8 md:p-10 message-enter">
        {/* Close Button */}
        <button
          onClick={() => {
            onClose();
            setSearchQuery("");
          }}
          className="absolute top-6 right-6 hover:opacity-70 transition-opacity btn-micro"
          aria-label="Close modal"
        >
          <X className="w-9 h-9 text-studymate-black dark:text-white" strokeWidth={3} />
        </button>

        {/* Title */}
        <h2 className="font-audiowide text-2xl tracking-[2.4px] text-black dark:text-white mb-6">
          Search Course
        </h2>

        {/* Search Input */}
        <div className="mb-8 relative">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-studymate-darkgray dark:text-gray-400 pointer-events-none" strokeWidth={2} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Search by course name..."
              className="w-full h-[48px] pl-12 pr-4 rounded-xl bg-studymate-gray dark:bg-slate-700 shadow-md font-audiowide text-[14px] tracking-[1.4px] text-studymate-darkgray dark:text-white placeholder:text-studymate-darkgray dark:placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-studymate-orange dark:focus:ring-studymate-green transition-colors"
              autoFocus
            />
          </div>
        </div>

        {/* Course Results */}
        <div className="mb-4">
          {filteredCourses.length === 0 ? (
            <div className="py-12 text-center">
              <p className="font-audiowide text-[14px] tracking-[1.4px] text-studymate-darkgray dark:text-gray-400">
                {searchQuery.trim() ? "No courses found" : "Start typing to search..."}
              </p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[350px] overflow-y-auto">
              {filteredCourses.map((course) => (
                <button
                  key={course.id}
                  onClick={() => handleCourseClick(course.id)}
                  className="w-full flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left border border-black/10 dark:border-slate-600"
                >
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: course.color }}
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="font-audiowide text-[14px] tracking-[1.4px] text-black dark:text-white block">
                      {course.name}
                    </span>
                  </div>
                  {course.active && (
                    <span className="text-xs font-audiowide tracking-[0.8px] px-2 py-1 rounded bg-studymate-orange dark:bg-studymate-green text-black dark:text-black">
                      Current
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer Info */}
        {courses.length > 0 && (
          <div className="text-center">
            <p className="font-roboto text-[12px] tracking-[0.6px] text-studymate-darkgray dark:text-gray-400">
              Total courses: <span className="font-bold">{courses.length}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
