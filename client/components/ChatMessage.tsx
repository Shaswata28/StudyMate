import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css"; // <--- CRITICAL: Imports the math styling

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
  return (
    <div
      className={`flex gap-4 mb-4 message-enter ${
        isAI ? "justify-start" : "justify-end"
      }`}
    >
      {isAI && (
        <div className="w-8 h-8 rounded-full bg-studymate-orange flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">AI</span>
        </div>
      )}

      <div
        className={`rounded-lg px-4 py-3 message-enter ${
          isAI
            ? "flex-1 bg-gray-100 dark:bg-slate-800 text-black dark:text-white rounded-tl-none"
            : "max-w-[75%] bg-studymate-black dark:bg-studymate-black text-white rounded-tr-none"
        }`}
        style={{ fontFamily: "'Exo 2', sans-serif" }}
      >
        {/* Attachments (User only) */}
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

        {isAI ? (
          /* AI Message: Render Markdown + Math + Tables */
          <div className="prose prose-sm dark:prose-invert max-w-none break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]} // Added remarkMath
              rehypePlugins={[rehypeKatex]}           // Added rehypeKatex
              components={{
                // Custom Code Block Styling
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <div className="my-3 rounded-lg overflow-hidden bg-slate-900 dark:bg-slate-950">
                      <div className="px-3 py-1 bg-slate-800 dark:bg-slate-900 text-xs text-gray-400 font-mono">
                        {match[1]}
                      </div>
                      <pre className="p-3 overflow-x-auto m-0">
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </pre>
                    </div>
                  ) : (
                    <code
                      className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-studymate-orange"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                // Custom Table Styling
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-4 rounded-lg border border-border">
                    <table className="min-w-full divide-y divide-border" {...props} />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th className="bg-muted px-4 py-2 text-left font-bold" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="px-4 py-2 border-t border-border" {...props} />
                ),
                // Custom Link Styling
                a: ({ node, ...props }) => (
                  <a 
                    className="text-studymate-orange hover:underline font-medium" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    {...props} 
                  />
                ),
                // Style Math Elements (Optional Customization)
                // This targets the span created by KaTeX for inline math
                span: ({ node, className, children, ...props }) => {
                  if (className?.includes('katex')) {
                    return <span className={className} {...props}>{children}</span>;
                  }
                  return <span className={className} {...props}>{children}</span>;
                }
              }}
            >
              {text}
            </ReactMarkdown>
          </div>
        ) : (
          /* User Message: Simple Text (Preserve whitespace) */
          <div className="text-base md:text-lg leading-relaxed whitespace-pre-wrap break-words">
            {text}
          </div>
        )}

        {timestamp && (
          <p
            className={`text-xs mt-2 ${
              isAI
                ? "text-gray-500 dark:text-gray-400"
                : "text-gray-200 dark:text-gray-300"
            }`}
          >
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