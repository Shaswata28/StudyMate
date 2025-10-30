import ChatInput from "./ChatInput";
import UploadedFileCard from "./UploadedFileCard";
import MaterialsPanel from "./MaterialsPanel";
import { useState } from "react";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
}

interface Message {
  id: string;
  text: string;
  isAI: boolean;
}

interface WorkspaceProps {
  courseName: string;
  courseColor: string;
  subtitle: string;
  uploadedFiles: UploadedFile[];
  messages: Message[];
  onSendMessage?: (message: string) => void;
  onFileUpload?: (files: File[]) => void;
  materialsPanelOpen?: boolean;
  onMaterialsToggle?: () => void;
}

export default function Workspace({
  courseName,
  courseColor,
  subtitle,
  uploadedFiles,
  messages,
  onSendMessage,
  onFileUpload,
  materialsPanelOpen = false,
  onMaterialsToggle,
}: WorkspaceProps) {
  const [isMaterialsOpen, setIsMaterialsOpen] = useState(materialsPanelOpen);

  const handleMaterialsToggle = () => {
    setIsMaterialsOpen(!isMaterialsOpen);
    onMaterialsToggle?.();
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header Section */}
      <div className="border-b border-black/10 bg-white">
        <div className="px-4 md:px-8 lg:px-12 py-6 md:py-8">
          {/* Course Title */}
          <div className="flex items-center gap-3 mb-2">
            <div
              className="w-[19px] h-[19px] rounded-full flex-shrink-0"
              style={{ backgroundColor: courseColor }}
            />
            <h1 className="font-audiowide text-3xl md:text-4xl lg:text-[28px] text-black">
              {courseName}
            </h1>
          </div>

          {/* Subtitle */}
          <p className="font-audiowide text-sm tracking-[1.4px] text-[#201F1F]">
            {subtitle}
          </p>
        </div>

        {/* Materials Panel - Aligned with course title */}
        <MaterialsPanel
          files={uploadedFiles}
          isOpen={isMaterialsOpen}
          onToggle={handleMaterialsToggle}
        />
      </div>

      {/* Main Content Area - Messages and Files */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 lg:px-12 py-6 md:py-8">
        <div className="flex flex-col items-center justify-center gap-6 min-h-full">
          {/* Show uploaded files if any */}
          {uploadedFiles.length > 0 && (
            <div className="flex flex-wrap gap-4 justify-center w-full">
              {uploadedFiles.map((file) => (
                <UploadedFileCard key={file.id} name={file.name} type={file.type} />
              ))}
            </div>
          )}

          {/* Show messages */}
          {messages.length > 0 && (
            <div className="max-w-[750px] w-full space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`font-audiowide text-base tracking-[0.32px] ${
                    message.isAI ? "text-black" : "text-studymate-darkgray"
                  }`}
                >
                  {message.text}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Input */}
      <div className="border-t border-black/10 bg-white px-4 md:px-8 lg:px-12 py-6 md:py-8">
        <ChatInput onSend={onSendMessage} onFileUpload={onFileUpload} />
      </div>
    </div>
  );
}
