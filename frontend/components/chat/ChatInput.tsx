"use client";

import { toast } from "sonner";
import { useState, useRef } from "react";
import RecordingStatus from "./RecordingStatus";
import { ArrowUp, FileText, Mic, Paperclip, Square, Trash2, X } from "lucide-react";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface ChatInputProps {
  onSendMessage: (text: string, files?: File[]) => Promise<boolean>;
  isLoading: boolean;
  onTyping: () => void;
  disabled?: boolean;
  visionEnabled: boolean;
  whisperAvailable: boolean;
}

export default function ChatInput({ onSendMessage, isLoading, onTyping, disabled, visionEnabled, whisperAvailable }: ChatInputProps) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { isRecording, isTranscribing, recordingStream, preview, startRecording, finishRecording, discardRecording } = useVoiceRecorder((transcript) => {
    setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
  }, whisperAvailable);

  const submit = async (draft: string) => {
    if (!draft.trim() && files.length === 0) return;
    const sent = await onSendMessage(draft.trim() || "Explain the attached material.", files);
    if (sent) {
      setText("");
      setFiles([]);
    }
  };

  const handleSend = () => {
    if (isLoading || disabled || isTranscribing) return;
    if (isRecording) {
      finishRecording((transcript) => {
        const draft = [text.trim(), transcript].filter(Boolean).join(" ").slice(0, 4000);
        setText(draft);
        void submit(draft);
      });
      return;
    }
    void submit(text);
  };

  const voiceActive = isRecording || isTranscribing;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const file = e.target.files[0];
      if (file?.type.startsWith("image/") && visionEnabled && file.size > 6_000_000) {
        toast.error("Direct chat images are limited to 6 MB. Upload larger images in Materials.");
      } else {
        setFiles(file ? [file] : []);
      }
      e.target.value = "";
    }
  };

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const icon = "composer-button hover:bg-background disabled:opacity-40";

  return (
    <div className="shrink-0 bg-background px-4 pb-4 pt-2 sm:px-8 sm:pb-6">
      <div className="chat-composer mx-auto max-w-3xl rounded-panel border border-line bg-surface p-2">
        {files.map((file, index) => (
          <div key={file.name} className="mx-2 mt-2 inline-flex max-w-[calc(100%-1rem)] items-center gap-2 rounded-control border border-line px-2 py-1 text-xs">
            <FileText aria-hidden className="size-3.5 shrink-0 text-accent" />
            <span className="truncate" title={file.name}>{file.name}</span>
            <button type="button" onClick={() => removeFile(index)} disabled={isLoading || voiceActive}
              className="rounded p-1 hover:bg-background disabled:opacity-50" aria-label={`Remove ${file.name}`}>
              <X className="size-3.5" />
            </button>
          </div>
        ))}
        <div className="flex min-h-14 items-center gap-2 px-2">
          {voiceActive && <RecordingStatus recording={isRecording} stream={recordingStream} />}
          <textarea
            aria-label="Study question"
            value={voiceActive && preview ? [text.trim(), preview].filter(Boolean).join(" ") : text}
            readOnly={voiceActive}
            onChange={(event) => {
              setText(event.target.value);
              if (event.target.value.length > 0) onTyping();
            }}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            placeholder={isRecording ? "Speak your question?" : isTranscribing ? "Preparing your transcript?" : "Ask a study question?"}
            rows={2}
            maxLength={4000}
            className="min-h-12 min-w-0 flex-1 resize-none bg-transparent py-2 text-sm leading-relaxed outline-none"
          />
        </div>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden"
              accept=".pdf,.txt,.md,image/png,image/jpeg,image/webp" />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={disabled || isLoading || voiceActive}
              className={icon} title="Attach a file" aria-label="Attach a file">
              <Paperclip className="size-[18px]" />
            </button>
            <button type="button" onClick={() => void startRecording()} disabled={disabled || isLoading || voiceActive}
              className={icon} aria-label="Voice input" title="Voice input">
              <Mic className="size-[18px]" />
            </button>
          </div>
          <div className="flex items-center gap-1">
            {voiceActive && (
              <button type="button" onClick={discardRecording} title="Discard recording" aria-label="Discard recording" className={icon}>
                <Trash2 className="size-4" />
              </button>
            )}
            {isRecording && (
              <button type="button" onClick={() => finishRecording()} title="Stop and keep transcript"
                aria-label="Stop recording and keep transcript" className={icon}>
                <Square className="size-4" />
              </button>
            )}
            <button type="button" onClick={handleSend} aria-label={isRecording ? "Send voice message" : "Send message"}
              disabled={(!isRecording && !text.trim() && files.length === 0) || isLoading || disabled || isTranscribing}
              className="composer-button bg-accent text-on-accent hover:opacity-90 disabled:opacity-35">
              <ArrowUp className="size-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
