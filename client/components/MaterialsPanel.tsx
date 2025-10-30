import { Folder, FileText, Download } from "lucide-react";

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
  const getFileIcon = (type: string) => {
    if (type.includes("pdf")) return "📄";
    if (type.includes("image")) return "🖼️";
    if (type.includes("video")) return "🎥";
    if (type.includes("word")) return "📝";
    return "📋";
  };

  return (
    <div className="flex-shrink-0 border-t border-black/10 bg-white">
      {/* Materials Header - Aligned with Course Title */}
      <button
        onClick={onToggle}
        className="w-full px-4 md:px-8 lg:px-12 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        aria-label={isOpen ? "Hide materials" : "Show materials"}
      >
        <div className="flex items-center gap-3">
          <Folder className="w-6 h-6 text-studymate-black" strokeWidth={2} />
          <span className="font-audiowide text-[18px] tracking-[1.8px] text-black">
            Materials
          </span>
          {files.length > 0 && (
            <span className="font-audiowide text-sm text-[#666] ml-2">
              ({files.length})
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? "rotate-180" : ""}`}
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
        <div className="px-4 md:px-8 lg:px-12 py-4 bg-gray-50 border-t border-black/10">
          {files.length === 0 ? (
            <p className="font-audiowide text-sm text-gray-500">
              No materials uploaded yet
            </p>
          ) : (
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-black/10 hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-lg flex-shrink-0">
                      {getFileIcon(file.type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-audiowide text-sm text-black truncate">
                        {file.name}
                      </p>
                      <p className="font-roboto text-xs text-gray-500">
                        {file.type.split("/")[1] || "file"}
                      </p>
                    </div>
                  </div>
                  <button
                    className="ml-2 p-2 opacity-0 group-hover:opacity-100 hover:bg-gray-100 rounded transition-all flex-shrink-0"
                    aria-label={`Download ${file.name}`}
                  >
                    <Download className="w-4 h-4 text-studymate-black" strokeWidth={2} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
