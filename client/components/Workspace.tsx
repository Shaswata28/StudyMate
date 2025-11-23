import ChatInput from "./ChatInput";
import ChatContainer from "./ChatContainer";
import UploadedFileCard from "./UploadedFileCard";
import { Folder } from "lucide-react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
}

interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
}

interface WorkspaceProps {
  courseName: string;
  courseColor: string;
  uploadedFiles: UploadedFile[];
  pendingFiles: UploadedFile[];
  messages: Message[];
  onSendMessage?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  onRemovePendingFile?: (fileId: string) => void;
  onMaterialsClick?: () => void;
  isLoadingResponse?: boolean;
}

export default function Workspace({
  courseName,
  courseColor,
  uploadedFiles,
  pendingFiles,
  messages,
  onSendMessage,
  onFileUpload,
  onRemovePendingFile,
  onMaterialsClick,
  isLoadingResponse = false,
}: WorkspaceProps) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-slate-950">
      {/* Header Section */}
      <div className="border-b border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950">
        <div className="px-4 md:px-8 lg:px-12 py-2.5 md:py-3">
          {/* Course Title with Materials Icon */}
          <div className="flex items-center gap-3 justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="w-[19px] h-[19px] rounded-full flex-shrink-0"
                style={{ backgroundColor: courseColor }}
              />
              <h1 className="font-audiowide text-xl sm:text-2xl md:text-3xl lg:text-[24px] text-black dark:text-white truncate">
                {courseName}
              </h1>
            </div>

            {/* Materials Icon Button */}
            <button
              onClick={onMaterialsClick}
              className="p-2 sm:p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-all duration-200 btn-micro relative flex-shrink-0 ml-2"
              aria-label="View materials"
            >
              <Folder className="w-5 h-5 sm:w-6 sm:h-6 text-studymate-orange dark:text-studymate-green" strokeWidth={2} />
              {uploadedFiles.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-studymate-orange dark:bg-studymate-green text-white dark:text-black font-audiowide text-xs rounded-full flex items-center justify-center font-bold">
                  {uploadedFiles.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area - Messages and Files */}
      <div className="flex-1 overflow-hidden flex flex-col px-4 md:px-8 lg:px-12 py-6 md:py-8">
        {/* Chat Container */}
        <ChatContainer messages={messages} isLoading={isLoadingResponse} />
      </div>

      {/* Chat Input Section */}
      <div className="border-t border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950 px-4 md:px-8 lg:px-12 py-6 md:py-8 flex-shrink-0">
        {/* Pending Files Display - Above Chat Input (only show before sending) */}
        {pendingFiles.length > 0 && (
          <div className="flex flex-wrap gap-3 w-full mb-4 max-w-[609px] mx-auto">
            {pendingFiles.slice(-3).map((file) => (
              <UploadedFileCard 
                key={file.id} 
                name={file.name} 
                type={file.type}
                onRemove={() => onRemovePendingFile?.(file.id)}
              />
            ))}
            {pendingFiles.length > 3 && (
              <button
                onClick={onMaterialsClick}
                className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors font-audiowide text-xs tracking-[0.8px] text-studymate-darkgray dark:text-gray-300"
              >
                +{pendingFiles.length - 3} more
              </button>
            )}
          </div>
        )}
        
        <ChatInput onSend={onSendMessage} onFileUpload={onFileUpload} isLoading={isLoadingResponse} />
      </div>
    </div>
  );
}
