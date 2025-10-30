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
        className="absolute inset-0 bg-gray-200/5 backdrop-blur-[5px]"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[639px] mx-4 bg-white rounded-[34px] border-2 border-black shadow-2xl p-8 md:p-10">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 hover:opacity-70 transition-opacity"
          aria-label="Close modal"
        >
          <X className="w-9 h-9 text-studymate-black" strokeWidth={3} />
        </button>

        {/* Title */}
        <h2 className="font-audiowide text-2xl tracking-[2.4px] text-black mb-6">
          Add New Course
        </h2>

        {/* Course Name Section */}
        <div className="mb-8">
          <label className="font-audiowide text-lg tracking-[1.8px] text-black mb-3 block">
            Course name
          </label>
          <input
            type="text"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter Course name"
            className="w-full h-[42px] px-4 rounded-xl bg-studymate-gray shadow-md font-audiowide text-[13px] tracking-[1.3px] text-studymate-darkgray placeholder:text-studymate-darkgray outline-none focus:ring-2 focus:ring-black/20"
            autoFocus
          />
        </div>

        {/* Course Color Section */}
        <div className="mb-6">
          <label className="font-audiowide text-lg tracking-[1.8px] text-black mb-4 block">
            Course color
          </label>
          <div className="flex gap-6 md:gap-8 flex-wrap">
            {COURSE_COLORS.map((color) => (
              <button
                key={color.id}
                onClick={() => setSelectedColor(color.hex)}
                className="relative flex-shrink-0 transition-transform hover:scale-110"
                aria-label={`Select ${color.id} color`}
              >
                <div
                  className="w-12 h-12 rounded-full"
                  style={{ backgroundColor: color.hex }}
                />
                {selectedColor === color.hex && (
                  <div
                    className="absolute inset-0 rounded-full border-2 border-black shadow-md"
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
          className="absolute bottom-8 right-8 hover:opacity-70 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed"
          disabled={!courseName.trim()}
          aria-label="Add course"
        >
          <ArrowRightCircle className="w-9 h-9 text-studymate-black" strokeWidth={3} />
        </button>
      </div>
    </div>
  );
}
