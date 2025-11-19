import { Plus, Send, Loader } from "lucide-react";
import { useState, useRef } from "react";

interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  isLoading?: boolean;
}

export default function ChatInput({ onSend, onFileUpload, isLoading = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  return (
    <div className="w-full max-w-[609px] mx-auto">
      <div className="relative flex items-center bg-studymate-gray dark:bg-slate-800 rounded-[26px] shadow-lg h-[52px] px-4 transition-all duration-200 border border-transparent dark:border-slate-700 hover:shadow-xl">
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
          className="flex-shrink-0 mr-3 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Attach file"
          aria-busy={isUploading}
        >
          {isUploading ? (
            <Loader className="w-[26px] h-[26px] text-studymate-black dark:text-white animate-spin" strokeWidth={3} />
          ) : (
            <Plus className="w-[26px] h-[26px] text-studymate-black dark:text-white" strokeWidth={3} />
          )}
        </button>

        {/* Input Field */}
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask anything"
          disabled={isLoading}
          className="flex-1 bg-transparent outline-none font-audiowide text-xl text-studymate-darkgray dark:text-gray-300 placeholder:text-studymate-darkgray dark:placeholder:text-gray-500 tracking-[2px] disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          aria-label="Message input"
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          className="flex-shrink-0 ml-3 transition-all duration-200 btn-micro disabled:opacity-50 disabled:cursor-not-allowed"
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
