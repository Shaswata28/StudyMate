import { Plus, Send, Loader } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  isLoading?: boolean;
}

export default function ChatInput({ onSend, onFileUpload, isLoading = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 100)}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSend?.(message);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileClick = () => {
    if (!isLoading && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      onFileUpload?.(Array.from(files));
      e.target.value = "";
      // Reset uploading state after a delay
      setTimeout(() => setIsUploading(false), 1000);
    }
  };

  // Determine text size based on message length
  const getTextSizeClass = () => {
    if (message.length > 200) return "text-base";
    if (message.length > 100) return "text-lg";
    return "text-xl";
  };

  return (
    <div className="w-full max-w-[609px] mx-auto">
      <div className="relative flex items-end bg-studymate-gray dark:bg-slate-800 rounded-[26px] shadow-lg min-h-[52px] px-4 py-3 transition-all duration-200 border border-transparent dark:border-slate-700 hover:shadow-xl">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload files"
          disabled={isLoading || isUploading}
        />

        {/* Plus Icon - File Upload Button */}
        <button
          onClick={handleFileClick}
          disabled={isLoading || isUploading}
          className="flex-shrink-0 mr-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Attach file"
          aria-busy={isUploading}
        >
          {isUploading ? (
            <Loader className="w-[26px] h-[26px] text-studymate-black dark:text-white animate-spin" strokeWidth={3} />
          ) : (
            <Plus className="w-[26px] h-[26px] text-studymate-black dark:text-white" strokeWidth={3} />
          )}
        </button>

        {/* Textarea Field */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Ask anything"
          disabled={isLoading}
          rows={1}
          className={`flex-1 bg-transparent outline-none ${getTextSizeClass()} text-studymate-darkgray dark:text-gray-300 placeholder:text-studymate-darkgray dark:placeholder:text-gray-500 tracking-[2px] disabled:opacity-50 disabled:cursor-not-allowed transition-all resize-none overflow-y-auto max-h-[100px] leading-relaxed scrollbar-thin scrollbar-thumb-studymate-darkgray dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-studymate-black dark:hover:scrollbar-thumb-gray-500`}
          style={{ fontFamily: "'Exo 2', sans-serif" }}
          aria-label="Message input"
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          className="flex-shrink-0 ml-3 mb-1 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Send message"
          aria-busy={isLoading}
        >
          {isLoading ? (
            <Loader className="w-6 h-6 text-studymate-black dark:text-white animate-spin" strokeWidth={3} />
          ) : (
            <Send className="w-6 h-6 text-studymate-black dark:text-white" strokeWidth={3} />
          )}
        </button>
      </div>
    </div>
  );
}
