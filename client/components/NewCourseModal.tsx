import { X, ArrowRightCircle } from "lucide-react";
import { useState } from "react";

interface NewCourseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (courseName: string, color: string) => void;
}

const COURSE_COLORS = [
  { id: "red", hex: "#F14141" },
  { id: "orange", hex: "#FEAE01" },
  { id: "green", hex: "#1FC209" },
  { id: "blue", hex: "#41C8F1" },
  { id: "pink", hex: "#EE50CE" },
];

export default function NewCourseModal({ isOpen, onClose, onSubmit }: NewCourseModalProps) {
  const [courseName, setCourseName] = useState("");
  const [selectedColor, setSelectedColor] = useState(COURSE_COLORS[2].hex); // Default to green

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (courseName.trim()) {
      onSubmit(courseName.trim(), selectedColor);
      setCourseName("");
      setSelectedColor(COURSE_COLORS[2].hex);
      onClose();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSubmit();
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur */}
      <div
        className="absolute inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm transition-colors"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[639px] mx-4 bg-white dark:bg-slate-800 rounded-[34px] border-2 border-black dark:border-white shadow-2xl p-8 md:p-10 message-enter">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 hover:opacity-70 transition-opacity btn-micro"
          aria-label="Close modal"
        >
          <X className="w-9 h-9 text-studymate-black dark:text-white" strokeWidth={3} />
        </button>

        {/* Title */}
        <h2 className="font-audiowide text-2xl tracking-[2.4px] text-black dark:text-white mb-6">
          Add New Course
        </h2>

        {/* Course Name Section */}
        <div className="mb-8">
          <label htmlFor="course-name" className="font-audiowide text-lg tracking-[1.8px] text-black dark:text-white mb-3 block">
            Course name
          </label>
          <input
            id="course-name"
            type="text"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter Course name"
            className="w-full h-[42px] px-4 rounded-xl bg-studymate-gray dark:bg-slate-700 shadow-md font-audiowide text-[13px] tracking-[1.3px] text-studymate-darkgray dark:text-white placeholder:text-studymate-darkgray dark:placeholder:text-gray-400 outline-none focus:ring-2 focus:ring-studymate-orange dark:focus:ring-studymate-green transition-colors"
            autoFocus
          />
        </div>

        {/* Course Color Section */}
        <div className="mb-6">
          <label className="font-audiowide text-lg tracking-[1.8px] text-black dark:text-white mb-4 block">
            Course color
          </label>
          <div className="flex gap-6 md:gap-8 flex-wrap">
            {COURSE_COLORS.map((color) => (
              <button
                key={color.id}
                onClick={() => setSelectedColor(color.hex)}
                className="relative flex-shrink-0 transition-all duration-200 hover:scale-110 btn-micro"
                aria-label={`Select ${color.id} color`}
              >
                <div
                  className="w-12 h-12 rounded-full shadow-md"
                  style={{ backgroundColor: color.hex }}
                />
                {selectedColor === color.hex && (
                  <div
                    className="absolute inset-0 rounded-full border-3 border-black dark:border-white shadow-lg"
                    style={{ margin: "-3px" }}
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          className="absolute bottom-8 right-8 hover:opacity-70 dark:hover:opacity-80 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed btn-micro"
          disabled={!courseName.trim()}
          aria-label="Add course"
        >
          <ArrowRightCircle className="w-9 h-9 text-studymate-black dark:text-white" strokeWidth={3} />
        </button>
      </div>
    </div>
  );
}
