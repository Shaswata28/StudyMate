import { X, Folder, Download, Grid3x3, List } from "lucide-react";
import { useState } from "react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
}

interface MaterialsModalProps {
  isOpen: boolean;
  onClose: () => void;
  files: UploadedFile[];
}

export default function MaterialsModal({ isOpen, onClose, files }: MaterialsModalProps) {
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm transition-colors"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[639px] mx-4 bg-white dark:bg-slate-800 rounded-[20px] sm:rounded-[30px] border-2 border-black dark:border-white shadow-2xl p-6 sm:p-8 message-enter max-h-[80vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 hover:opacity-70 transition-opacity btn-micro"
          aria-label="Close modal"
        >
          <X className="w-6 h-6 sm:w-8 sm:h-8 text-black dark:text-white" strokeWidth={2} />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Folder className="w-6 h-6 sm:w-8 sm:h-8 text-studymate-orange dark:text-studymate-green flex-shrink-0" strokeWidth={2} />
          <h2 className="font-audiowide text-xl sm:text-2xl tracking-[1.8px] sm:tracking-[2.4px] text-black dark:text-white">
            Materials
          </h2>
          {files.length > 0 && (
            <span className="font-audiowide text-sm sm:text-base text-[#666] dark:text-gray-400 ml-2">
              ({files.length})
            </span>
          )}
        </div>

        {files.length === 0 ? (
          <div className="py-12 text-center">
            <Folder className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600 mb-4" strokeWidth={1} />
            <p className="font-audiowide text-sm sm:text-base tracking-[0.8px] text-gray-500 dark:text-gray-400">
              No materials uploaded yet
            </p>
            <p className="font-roboto text-xs sm:text-sm text-gray-400 dark:text-gray-500 mt-2">
              Upload files using the attachment button in the chat input
            </p>
          </div>
        ) : (
          <>
            {/* Search and View Toggle */}
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center gap-3">
              <input
                type="text"
                placeholder="Search materials..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-3 sm:px-4 py-2 rounded-lg border-2 border-black/20 dark:border-slate-600 bg-white dark:bg-slate-700 text-black dark:text-white font-audiowide text-xs sm:text-sm tracking-[0.5px] focus:outline-none focus:ring-2 focus:ring-studymate-orange dark:focus:ring-studymate-green transition-all"
                aria-label="Search materials"
              />
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => setViewMode("list")}
                  className={`p-2 sm:p-2.5 rounded-lg transition-all duration-200 ${
                    viewMode === "list"
                      ? "bg-studymate-orange dark:bg-studymate-green text-black dark:text-black"
                      : "bg-gray-100 dark:bg-slate-700 text-black dark:text-white hover:bg-gray-200 dark:hover:bg-slate-600"
                  }`}
                  aria-label="List view"
                  aria-pressed={viewMode === "list"}
                >
                  <List className="w-4 h-4 sm:w-5 sm:h-5" strokeWidth={2} />
                </button>
                <button
                  onClick={() => setViewMode("grid")}
                  className={`p-2 sm:p-2.5 rounded-lg transition-all duration-200 ${
                    viewMode === "grid"
                      ? "bg-studymate-orange dark:bg-studymate-green text-black dark:text-black"
                      : "bg-gray-100 dark:bg-slate-700 text-black dark:text-white hover:bg-gray-200 dark:hover:bg-slate-600"
                  }`}
                  aria-label="Grid view"
                  aria-pressed={viewMode === "grid"}
                >
                  <Grid3x3 className="w-4 h-4 sm:w-5 sm:h-5" strokeWidth={2} />
                </button>
              </div>
            </div>

            {/* Files Display */}
            {viewMode === "list" ? (
              <div className="space-y-3">
                {filteredFiles.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
                    No materials match your search
                  </p>
                ) : (
                  filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-slate-700 rounded-lg border border-black/10 dark:border-slate-600 hover:shadow-md dark:hover:shadow-lg transition-all duration-200 group message-enter"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-lg sm:text-xl flex-shrink-0">
                          {getFileIcon(file.type)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="font-audiowide text-xs sm:text-sm tracking-[0.5px] text-black dark:text-white truncate">
                            {file.name}
                          </p>
                          <p className="font-roboto text-xs text-gray-500 dark:text-gray-400">
                            {file.type.split("/")[1] || "file"}
                          </p>
                        </div>
                      </div>
                      <button
                        className="ml-2 p-2 opacity-0 group-hover:opacity-100 hover:bg-white dark:hover:bg-slate-600 rounded transition-all duration-200 flex-shrink-0 btn-micro"
                        aria-label={`Download ${file.name}`}
                      >
                        <Download className="w-4 h-4 sm:w-5 sm:h-5 text-studymate-orange dark:text-studymate-green" strokeWidth={2} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {filteredFiles.length === 0 ? (
                  <p className="col-span-full text-sm text-gray-500 dark:text-gray-400 text-center py-8">
                    No materials match your search
                  </p>
                ) : (
                  filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      className="p-3 sm:p-4 bg-gray-50 dark:bg-slate-700 rounded-lg border border-black/10 dark:border-slate-600 hover:shadow-md dark:hover:shadow-lg transition-all duration-200 group cursor-pointer message-enter"
                    >
                      <div className="text-2xl sm:text-3xl mb-2">{getFileIcon(file.type)}</div>
                      <p className="font-audiowide text-xs tracking-[0.3px] text-black dark:text-white truncate mb-1">
                        {file.name}
                      </p>
                      <div className="flex items-center justify-between">
                        <p className="font-roboto text-xs text-gray-500 dark:text-gray-400">
                          {file.type.split("/")[1] || "file"}
                        </p>
                        <button
                          className="p-1 opacity-0 group-hover:opacity-100 hover:bg-white dark:hover:bg-slate-600 rounded transition-all duration-200 btn-micro"
                          aria-label={`Download ${file.name}`}
                        >
                          <Download className="w-3 h-3 sm:w-4 sm:h-4 text-studymate-orange dark:text-studymate-green" strokeWidth={2} />
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
    </div>
  );
}
