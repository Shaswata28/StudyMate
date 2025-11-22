import { FileText, Image as ImageIcon, Download, X } from "lucide-react";

interface UploadedFileCardProps {
  name: string;
  type: string;
  onRemove?: () => void;
  onDownload?: () => void;
}

export default function UploadedFileCard({
  name,
  type,
  onRemove,
  onDownload,
}: UploadedFileCardProps) {
  const isPDF = type === "application/pdf" || name.toLowerCase().endsWith(".pdf");
  const isImage = type.startsWith("image/") ||
    name.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);

  return (
    <div className="w-full max-w-[193px] h-[61px] rounded-[14px] border-2 border-black dark:border-white bg-transparent dark:bg-slate-800 flex items-center gap-3 px-3 hover:shadow-lg dark:hover:shadow-lg hover:scale-105 transition-all duration-200 message-enter group">
      {/* Icon */}
      {isPDF ? (
        <FileText className="w-10 h-9 text-studymate-black dark:text-white flex-shrink-0" strokeWidth={3} />
      ) : isImage ? (
        <ImageIcon className="w-10 h-9 text-studymate-black dark:text-white flex-shrink-0" strokeWidth={3} />
      ) : (
        <FileText className="w-10 h-9 text-studymate-black dark:text-white flex-shrink-0" strokeWidth={3} />
      )}

      {/* File Info */}
      <div className="flex flex-col overflow-hidden flex-1">
        <span className="font-audiowide text-base tracking-[1.6px] text-black dark:text-white truncate">
          {name}
        </span>
        <span className="font-audiowide text-[11px] tracking-[1.1px] text-black dark:text-gray-300 uppercase">
          {isPDF ? "PDF" : isImage ? "IMAGE" : "FILE"}
        </span>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex-shrink-0">
        {onDownload && (
          <button
            onClick={onDownload}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-slate-700 rounded transition-colors btn-micro"
            aria-label={`Download ${name}`}
            title="Download"
          >
            <Download className="w-4 h-4 text-studymate-black dark:text-white" strokeWidth={2} />
          </button>
        )}
        {onRemove && (
          <button
            onClick={onRemove}
            className="p-1.5 hover:bg-red-100 dark:hover:bg-red-950/30 rounded transition-colors btn-micro"
            aria-label={`Remove ${name}`}
            title="Remove"
          >
            <X className="w-4 h-4 text-red-600 dark:text-red-400" strokeWidth={2} />
          </button>
        )}
      </div>
    </div>
  );
}
