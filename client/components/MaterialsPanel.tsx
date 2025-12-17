import { Folder, Download, Grid3x3, List } from "lucide-react";
import { useState } from "react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
}

interface MaterialsPanelProps {
  files: UploadedFile[];
  isOpen: boolean;
  onToggle: () => void;
}

export default function MaterialsPanel({ files, isOpen, onToggle }: MaterialsPanelProps) {
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [searchQuery, setSearchQuery] = useState("");

  const getFileIcon = (type: string) => {
    if (type.includes("pdf")) return "📄";
    if (type.includes("image")) return "🖼️";
    if (type.includes("video")) return "🎥";
    if (type.includes("word")) return "📝";
    return "📋";
  };

  const filteredFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-shrink-0 border-t border-black/10 bg-white dark:bg-slate-950 expand-collapse">
      {/* Materials Header - Aligned with Course Title */}
      <button
        onClick={onToggle}
        className="w-full px-4 md:px-8 lg:px-12 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-900 transition-colors btn-micro"
        aria-label={isOpen ? "Hide materials" : "Show materials"}
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3">
          <Folder className="w-6 h-6 text-studymate-black dark:text-studymate-black" strokeWidth={2} />
          <span className="font-audiowide text-[18px] tracking-[1.8px] text-black dark:text-white">
            Materials
          </span>
          {files.length > 0 && (
            <span className="font-audiowide text-sm text-[#666] dark:text-gray-400 ml-2">
              ({files.length})
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </button>

      {/* Materials List - Expanded View */}
      {isOpen && (
        <div className="animate-expand-collapse px-4 md:px-8 lg:px-12 py-4 bg-gray-50 dark:bg-slate-900 border-t border-black/10 dark:border-slate-700">
          {files.length === 0 ? (
            <p className="font-audiowide text-sm text-gray-500 dark:text-gray-400">
              No materials uploaded yet
            </p>
          ) : (
            <>
              {/* Search and View Toggle */}
              <div className="mb-4 flex items-center gap-3">
                <input
                  type="text"
                  placeholder="Search materials..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg border border-black/10 dark:border-slate-700 bg-white dark:bg-slate-800 text-black dark:text-white font-audiowide text-sm focus:outline-none focus:ring-2 focus:ring-studymate-orange"
                  aria-label="Search materials"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => setViewMode("list")}
                    className={`p-2 rounded transition-colors ${
                      viewMode === "list"
                        ? "bg-studymate-orange text-white"
                        : "bg-white dark:bg-slate-800 text-black dark:text-white hover:bg-gray-100 dark:hover:bg-slate-700"
                    }`}
                    aria-label="List view"
                    aria-pressed={viewMode === "list"}
                  >
                    <List className="w-4 h-4" strokeWidth={2} />
                  </button>
                  <button
                    onClick={() => setViewMode("grid")}
                    className={`p-2 rounded transition-colors ${
                      viewMode === "grid"
                        ? "bg-studymate-orange text-white"
                        : "bg-white dark:bg-slate-800 text-black dark:text-white hover:bg-gray-100 dark:hover:bg-slate-700"
                    }`}
                    aria-label="Grid view"
                    aria-pressed={viewMode === "grid"}
                  >
                    <Grid3x3 className="w-4 h-4" strokeWidth={2} />
                  </button>
                </div>
              </div>

              {/* Files Display */}
              {viewMode === "list" ? (
                <div className="space-y-3 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-studymate-darkgray dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-studymate-black dark:hover:scrollbar-thumb-gray-500">
                  {filteredFiles.length === 0 ? (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      No materials match your search
                    </p>
                  ) : (
                    filteredFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg border border-black/10 dark:border-slate-700 hover:shadow-md dark:hover:shadow-lg transition-all duration-200 group message-enter"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <span className="text-lg flex-shrink-0">
                            {getFileIcon(file.type)}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="font-audiowide text-sm text-black dark:text-white truncate">
                              {file.name}
                            </p>
                            <p className="font-roboto text-xs text-gray-500 dark:text-gray-400">
                              {file.type.split("/")[1] || "file"}
                            </p>
                          </div>
                        </div>
                        <button
                          className="ml-2 p-2 opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-all duration-200 flex-shrink-0 btn-micro"
                          aria-label={`Download ${file.name}`}
                        >
                          <Download className="w-4 h-4 text-studymate-black dark:text-white" strokeWidth={2} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-studymate-darkgray dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-studymate-black dark:hover:scrollbar-thumb-gray-500">
                  {filteredFiles.length === 0 ? (
                    <p className="col-span-full text-sm text-gray-500 dark:text-gray-400">
                      No materials match your search
                    </p>
                  ) : (
                    filteredFiles.map((file) => (
                      <div
                        key={file.id}
                        className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-black/10 dark:border-slate-700 hover:shadow-md dark:hover:shadow-lg transition-all duration-200 group cursor-pointer message-enter"
                      >
                        <div className="text-2xl mb-2">{getFileIcon(file.type)}</div>
                        <p className="font-audiowide text-xs text-black dark:text-white truncate mb-1">
                          {file.name}
                        </p>
                        <div className="flex items-center justify-between">
                          <p className="font-roboto text-xs text-gray-500 dark:text-gray-400">
                            {file.type.split("/")[1] || "file"}
                          </p>
                          <button
                            className="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-all duration-200 btn-micro"
                            aria-label={`Download ${file.name}`}
                          >
                            <Download className="w-3 h-3 text-studymate-black dark:text-white" strokeWidth={2} />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
