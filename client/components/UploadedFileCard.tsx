import { FileText, Image as ImageIcon } from "lucide-react";

interface UploadedFileCardProps {
  name: string;
  type: string;
}

export default function UploadedFileCard({ name, type }: UploadedFileCardProps) {
  const isPDF = type === "application/pdf" || name.toLowerCase().endsWith(".pdf");
  const isImage = type.startsWith("image/") || 
    name.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/);

  return (
    <div className="w-full max-w-[193px] h-[61px] rounded-[14px] border border-black bg-transparent flex items-center gap-3 px-3">
      {/* Icon */}
      {isPDF ? (
        <FileText className="w-10 h-9 text-studymate-black flex-shrink-0" strokeWidth={3} />
      ) : isImage ? (
        <ImageIcon className="w-10 h-9 text-studymate-black flex-shrink-0" strokeWidth={3} />
      ) : (
        <FileText className="w-10 h-9 text-studymate-black flex-shrink-0" strokeWidth={3} />
      )}

      {/* File Info */}
      <div className="flex flex-col overflow-hidden">
        <span className="font-audiowide text-base tracking-[1.6px] text-black truncate">
          {name}
        </span>
        <span className="font-audiowide text-[11px] tracking-[1.1px] text-black uppercase">
          {isPDF ? "PDF" : isImage ? "IMAGE" : "FILE"}
        </span>
      </div>
    </div>
  );
}
