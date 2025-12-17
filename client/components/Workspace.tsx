import ChatInput from "./ChatInput";
import ChatContainer from "./ChatContainer";
import UploadedFileCard from "./UploadedFileCard";

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
  isLoadingResponse?: boolean;
  isLoadingChatHistory?: boolean;
  isLoadingMaterials?: boolean;
  chatHistoryError?: string | null;
  materialsError?: string | null;
  onRetryChatHistory?: () => void;
  onRetryMaterials?: () => void;
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
  isLoadingResponse = false,
  isLoadingChatHistory = false,
  isLoadingMaterials = false,
  chatHistoryError = null,
  materialsError = null,
  onRetryChatHistory,
  onRetryMaterials,
}: WorkspaceProps) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-slate-950">
      {/* Main Content Area - Messages and Files */}
      <div className="flex-1 overflow-hidden flex flex-col px-4 md:px-6 lg:px-8 py-4 md:py-6">
        {/* Loading State for Chat History */}
        {isLoadingChatHistory && messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-studymate-black dark:border-white mx-auto mb-4"></div>
              <p className="font-audiowide text-[14px] tracking-[1.4px] text-black/60 dark:text-white/60">
                Loading chat history...
              </p>
            </div>
          </div>
        )}

        {/* Error State for Chat History */}
        {chatHistoryError && !isLoadingChatHistory && messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md px-4">
              <p className="font-roboto text-[14px] text-red-600 dark:text-red-400 mb-4">
                {chatHistoryError}
              </p>
              {onRetryChatHistory && (
                <button
                  onClick={onRetryChatHistory}
                  className="px-6 py-3 bg-studymate-black dark:bg-white text-white dark:text-black font-audiowide text-[13px] tracking-[1.3px] rounded hover:shadow-lg transition-all duration-200"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        )}

        {/* Chat Container - Only show if not loading and no error, or if there are messages */}
        {(!isLoadingChatHistory || messages.length > 0) && !chatHistoryError && (
          <ChatContainer messages={messages} isLoading={isLoadingResponse} />
        )}
      </div>

      {/* Chat Input Section */}
      <div className="border-t border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950 px-4 md:px-6 lg:px-8 py-4 md:py-5 flex-shrink-0">
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
