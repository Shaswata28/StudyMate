import { Folder } from "lucide-react";

interface HeaderProps {
  courseName?: string;
  courseColor?: string;
  uploadedFiles?: any[];
  onMaterialsClick?: () => void;
}

export default function Header({ 
  courseName, 
  courseColor, 
  uploadedFiles = [], 
  onMaterialsClick 
}: HeaderProps) {
  return (
    <header className="h-[70px] px-6 md:px-8 lg:pl-8 lg:pr-12 flex items-center justify-between border-b border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950 transition-colors duration-200">
      <div className="flex items-center gap-4">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[32px] tracking-[3.2px] text-black dark:text-white">
          STUDYMATE
        </h1>
        
        {/* Course Title */}
        {courseName && (
          <div className="flex items-center gap-3 ml-6">
            <div
              className="w-[19px] h-[19px] rounded-full flex-shrink-0"
              style={{ backgroundColor: courseColor }}
            />
            <h2 className="font-audiowide text-lg md:text-xl lg:text-[20px] text-black dark:text-white truncate">
              {courseName}
            </h2>
          </div>
        )}
      </div>

      {/* Materials Button */}
      {onMaterialsClick && (
        <button
          onClick={onMaterialsClick}
          className="p-2 sm:p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-all duration-200 btn-micro relative flex-shrink-0"
          aria-label="View materials"
        >
          <Folder className="w-5 h-5 sm:w-6 sm:h-6 text-studymate-orange dark:text-studymate-green" strokeWidth={2} />
          {uploadedFiles.length > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-studymate-orange dark:bg-studymate-green text-white dark:text-black font-audiowide text-xs rounded-full flex items-center justify-center font-bold">
              {uploadedFiles.length}
            </span>
          )}
        </button>
      )}
    </header>
  );
}
