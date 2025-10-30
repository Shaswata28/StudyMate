import { Plus, Send } from "lucide-react";
import { useState, useRef } from "react";

interface ChatInputProps {
  onSend?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
}

export default function ChatInput({ onSend, onFileUpload }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim()) {
      onSend?.(message);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload?.(Array.from(files));
      e.target.value = ""; // Reset input
    }
  };

  return (
    <div className="w-full max-w-[609px] mx-auto">
      <div className="relative flex items-center bg-studymate-gray rounded-[26px] shadow-lg h-[52px] px-4">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload files"
        />

        {/* Plus Icon */}
        <button
          onClick={handleFileClick}
          className="flex-shrink-0 mr-3 hover:opacity-70 transition-opacity"
          aria-label="Attach file"
        >
          <Plus className="w-[26px] h-[26px] text-studymate-black" strokeWidth={3} />
        </button>

        {/* Input */}
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask anything"
          className="flex-1 bg-transparent outline-none font-audiowide text-xl text-studymate-darkgray placeholder:text-studymate-darkgray tracking-[2px]"
        />

        {/* Send Icon */}
        <button
          onClick={handleSend}
          className="flex-shrink-0 ml-3 hover:opacity-70 transition-opacity"
          aria-label="Send message"
        >
          <Send className="w-6 h-6 text-studymate-black" strokeWidth={3} />
        </button>
      </div>
    </div>
  );
}
