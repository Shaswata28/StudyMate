import { useMemo } from "react";

interface ChatMessageProps {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
  attachments?: { name: string; type: string }[];
}

export default function ChatMessage({
  text,
  isAI,
  timestamp,
  attachments,
}: ChatMessageProps) {
  const formattedContent = useMemo(() => {
    if (!isAI) return text;

    // Simple markdown parsing for code blocks
    let content = text;

    // Parse code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts: (React.ReactNode | string)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push(parseInlineMarkdown(content.substring(lastIndex, match.index)));
      }

      // Add code block
      const language = match[1] || "plaintext";
      const code = match[2];
      parts.push(
        <div key={`code-${match.index}`} className="my-3 rounded-lg overflow-hidden bg-slate-900 dark:bg-slate-950">
          <div className="px-3 py-1 bg-slate-800 dark:bg-slate-900 text-xs text-gray-400 font-mono">
            {language}
          </div>
          <pre className="p-3 overflow-x-auto">
            <code className="text-sm text-gray-100 font-mono">{code.trim()}</code>
          </pre>
        </div>
      );
      lastIndex = codeBlockRegex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(parseInlineMarkdown(content.substring(lastIndex)));
    }

    return parts.length > 0 ? parts : parseInlineMarkdown(content);
  }, [text, isAI]);

  return (
    <div
      className={`flex gap-4 mb-4 message-enter ${
        isAI ? "justify-start" : "justify-end"
      }`}
    >
      {isAI && (
        <div className="w-8 h-8 rounded-full bg-studymate-orange dark:bg-studymate-orange flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">AI</span>
        </div>
      )}

      <div
        className={`rounded-lg px-4 py-3 message-enter ${
          isAI
            ? "flex-1 bg-gray-100 dark:bg-slate-800 text-black dark:text-white rounded-tl-none"
            : "max-w-[65%] bg-studymate-black dark:bg-studymate-black text-white rounded-tr-none"
        }`}
        style={{ fontFamily: "'Exo 2', sans-serif" }}
      >
        {/* Show attachments if present (for user messages) */}
        {attachments && attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((file, index) => (
              <div
                key={index}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-audiowide ${
                  isAI
                    ? "bg-gray-200 dark:bg-slate-700 text-black dark:text-white"
                    : "bg-white/20 text-white"
                }`}
              >
                <span>{getFileIcon(file.type)}</span>
                <span className="truncate max-w-[150px]">{file.name}</span>
              </div>
            ))}
          </div>
        )}

        <div className="text-base md:text-lg leading-relaxed whitespace-pre-wrap break-words">
          {formattedContent}
        </div>

        {timestamp && (
          <p className={`text-xs mt-2 ${
            isAI
              ? "text-gray-500 dark:text-gray-400"
              : "text-gray-200 dark:text-gray-300"
          }`}>
            {timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </div>
  );
}

function getFileIcon(type: string): string {
  if (type.includes("pdf")) return "📄";
  if (type.includes("image")) return "🖼️";
  if (type.includes("video")) return "🎥";
  if (type.includes("word")) return "📝";
  return "📋";
}

function parseInlineMarkdown(text: string): React.ReactNode {
  const parts: (React.ReactNode | string)[] = [];
  let lastIndex = 0;

  // Bold text **text**
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    parts.push(
      <strong key={`bold-${match.index}`}>{match[1]}</strong>
    );
    lastIndex = boldRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 1 ? parts : text;
}
