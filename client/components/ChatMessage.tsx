import React, { useMemo, useState } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy, Terminal, FileText, Download } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import "katex/dist/katex.min.css";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// 1. TEXT PRE-PROCESSING (Updated for Naked LaTeX)
// ============================================================================

function preprocessContent(content: string): string {
  if (!content) return "";

  let processed = content;

  // 1. Remove LLM training artifacts
  processed = processed
    .replace(/^###?\s*(Instruction|Response|User Context|Input|Output):\s*/gim, "")
    .replace(/\n###?\s*(Instruction|Response|User Context|Input|Output):\s*/gi, "\n")
    .replace(/<\|?(im_start|im_end|endoftext|pad|eos|bos)\|?>/gi, "");

  // 2. FIX INLINE CODE BLOCKS
  // Convert code blocks with only a single short term to inline code
  
  // Case A: ```int``` or ``` int ``` (no newlines)
  processed = processed.replace(/```\s*([^`\n]+?)\s*```/g, "`$1`");
  
  // Case B: ```\nint\n``` or ```\n float \n``` (with newlines but single word)
  processed = processed.replace(/```\s*\n\s*(\w{1,20})\s*\n\s*```/g, "`$1`");
  
  // Case C: ```text\nint\n``` - with language identifier but single word content
  // Common for types like int, float, double, string, bool, etc.
  processed = processed.replace(/```(?:text|plaintext|txt)?\s*\n\s*(\w{1,20})\s*\n\s*```/gi, "`$1`");
  
  // Case D: Handle any remaining single-word code blocks (aggressive cleanup)
  processed = processed.replace(/```[a-z]*\s*\n?\s*(-?\d+\.?\d*|\w{1,20})\s*\n?\s*```/gi, "`$1`");
  
  // Trim whitespace INSIDE inline code backticks (` int ` -> `int`)
  processed = processed.replace(/`\s+([^`\n]+?)\s+`/g, "`$1`");
  processed = processed.replace(/`\s+([^`\n]+?)`/g, "`$1`");
  processed = processed.replace(/`([^`\n]+?)\s+`/g, "`$1`");

  // 3. DETECT & WRAP NAKED LATEX
  processed = processed.replace(
    /(^|\n)(?![ \t]*```)(?![ \t]*\$\$)([^`\n$]*\s=\s[^`\n$]*(?:\\frac|\\times|\\cdot|\\text|\\sqrt|\^)[^`\n$]*)(?=$|\n)/g,
    "$1$$$2$$"
  );

  // 4. CLEANUP DIRTY TABLES
  processed = processed.replace(/<\/?(td|tr|th|table|thead|tbody)>/gi, "");

  // 5. Fix table separator rows
  processed = fixTableSeparators(processed);

  // 6. Ensure proper spacing around tables
  processed = processed.replace(/([^\n])\n(\|[^\n]+\|)\n(\|[\s:\-]+\|)/g, "$1\n\n$2\n$3");
  processed = processed.replace(/(\|[^\n]+\|)\n([^\n|])/g, "$1\n\n$2");

  // 7. Ensure newlines before/after REMAINING code blocks (multi-line ones)
  processed = processed.replace(/([^\n])```/g, "$1\n```");
  processed = processed.replace(/```([^\n])(?!\w)/g, "```\n$1");

  // 8. Ensure newlines before headers
  processed = processed.replace(/([^\n])\n(#{1,6}\s)/g, "$1\n\n$2");

  // 9. Normalize MathJax delimiters
  processed = processed
    .replace(/\\\[/g, "$$")
    .replace(/\\\]/g, "$$")
    .replace(/\\\(/g, "$")
    .replace(/\\\)/g, "$");

  return processed.trim();
}

/**
 * Fix malformed table separator rows.
 */
function fixTableSeparators(text: string): string {
  const lines = text.split("\n");
  const result: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const prevLine = lines[i - 1];

    const isValidSeparator = /^\|(\s*:?-{1,}:?\s*\|)+\s*$/.test(line.trim());
    
    const isMalformedSeparator =
      !isValidSeparator &&
      line.includes("|") &&
      line.includes("-") &&
      !/[a-zA-Z0-9]/.test(line) && 
      prevLine &&
      prevLine.includes("|");

    if (isMalformedSeparator) {
      const headerCols = (prevLine.match(/\|/g) || []).length;

      if (headerCols > 1) {
        const alignMatches = line.match(/(:)?-+(:)?/g) || [];
        let separator = "|";

        for (let j = 0; j < headerCols - 1; j++) {
          const align = alignMatches[j] || "---";
          const hasLeft = align.startsWith(":");
          const hasRight = align.endsWith(":");
          separator += ` ${hasLeft ? ":" : ""}---${hasRight ? ":" : ""} |`;
        }

        result.push(separator);
        continue;
      }
    }

    result.push(line);
  }

  return result.join("\n");
}

// ============================================================================
// 2. SUB-COMPONENTS
// ============================================================================

const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1.5 rounded-md hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-all"
    >
      {copied ? (
        <Check className="w-4 h-4 text-green-500" />
      ) : (
        <Copy className="w-4 h-4" />
      )}
    </button>
  );
};

const CodeBlock = ({ inline, className, children }: any) => {
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : "text";
  const codeString = String(children).replace(/\n$/, "");

  if (inline) {
    return (
      <code className="px-1.5 py-0.5 mx-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-orange-600 dark:text-orange-400 font-mono text-sm border border-slate-200 dark:border-slate-700/50">
        {children}
      </code>
    );
  }

  return (
    <div className="my-5 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 bg-[#1e1e1e] shadow-sm group">
      <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-white/5">
        <div className="flex items-center gap-2">
          {language === "bash" || language === "shell" ? (
            <Terminal className="w-3.5 h-3.5 text-green-400" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-blue-400" />
          )}
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
            {language}
          </span>
        </div>
        <CopyButton text={codeString} />
      </div>
      <div className="overflow-x-auto">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: "1.25rem",
            background: "transparent",
            fontSize: "0.85rem",
            lineHeight: "1.6",
          }}
          wrapLines={false}
        >
          {codeString}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};


// ============================================================================
// 3. MARKDOWN COMPONENT MAPPING
// ============================================================================

const MarkdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold mt-8 mb-4 border-b border-slate-200 dark:border-slate-700 pb-2 text-slate-900 dark:text-slate-100">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xl font-bold mt-6 mb-3 text-slate-800 dark:text-slate-100">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-semibold mt-4 mb-2 text-slate-800 dark:text-slate-200">
      {children}
    </h3>
  ),
  p: ({ children }) => (
    <div className="mb-4 leading-7 text-slate-600 dark:text-slate-300">
      {children}
    </div>
  ),
  ul: ({ children }) => (
    <ul className="my-3 pl-6 list-disc space-y-1.5 marker:text-orange-500 text-slate-600 dark:text-slate-300">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="my-3 pl-6 list-decimal space-y-1.5 text-slate-600 dark:text-slate-300">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="pl-1">{children}</li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-4 pl-4 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-500/10 py-2 rounded-r italic text-slate-700 dark:text-slate-300">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300 underline underline-offset-2 transition-colors"
    >
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="my-6 w-full overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse bg-white dark:bg-slate-800/50">
          {children}
        </table>
      </div>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700">
      {children}
    </thead>
  ),
  tbody: ({ children }) => (
    <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
      {children}
    </tbody>
  ),
  tr: ({ children }) => (
    <tr className="hover:bg-slate-50/80 dark:hover:bg-slate-700/30 transition-colors">
      {children}
    </tr>
  ),
  th: ({ children }) => (
    <th className="px-4 py-3 whitespace-nowrap text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-3 align-top text-slate-600 dark:text-slate-300 leading-relaxed border-l border-transparent first:border-l-0">
      {children}
    </td>
  ),
  img: ({ src, alt }) => (
    <img
      src={src}
      alt={alt}
      className="max-w-full h-auto rounded-lg border border-slate-200 dark:border-slate-700 my-4 shadow-sm"
      loading="lazy"
    />
  ),
  code: CodeBlock,
};

// ============================================================================
// 4. MEMOIZED RENDERER
// ============================================================================

const katexOptions = { throwOnError: false, strict: false };

const AIContentRenderer = React.memo(
  ({ content }: { content: string }) => {
    const cleanedContent = useMemo(() => preprocessContent(content), [content]);

    return (
      <div className="ai-response-content prose prose-slate dark:prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, [rehypeKatex, katexOptions]]}
          components={MarkdownComponents}
        >
          {cleanedContent}
        </ReactMarkdown>
      </div>
    );
  },
  (prev, next) => prev.content === next.content
);

AIContentRenderer.displayName = "AIContentRenderer";

// ============================================================================
// 5. MAIN EXPORT
// ============================================================================

interface TestAccuracyInfo {
  is_test_question: boolean;
  accuracy: number;
  expected_response?: string;
}

interface ChatMessageProps {
  id?: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
  attachments?: { name: string; type: string }[];
  testAccuracy?: TestAccuracyInfo;
}

// Accuracy Badge Component
const AccuracyBadge = ({ accuracy }: { accuracy: number }) => {
  const getAccuracyColor = (acc: number) => {
    if (acc >= 80) return "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800";
    if (acc >= 60) return "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800";
    return "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800";
  };

  const getAccuracyLabel = (acc: number) => {
    if (acc >= 80) return "Excellent";
    if (acc >= 60) return "Good";
    if (acc >= 40) return "Fair";
    return "Needs Improvement";
  };

  return (
    <div className={cn(
      "mt-4 pt-3 border-t border-slate-200 dark:border-slate-700"
    )}>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-slate-500 dark:text-slate-400">Test Accuracy:</span>
        <span className={cn(
          "px-2 py-0.5 rounded-full border font-medium",
          getAccuracyColor(accuracy)
        )}>
          {accuracy.toFixed(1)}% - {getAccuracyLabel(accuracy)}
        </span>
      </div>
    </div>
  );
};

export default function ChatMessage({
  text,
  isAI,
  timestamp,
  attachments,
  testAccuracy,
}: ChatMessageProps) {
  return (
    <div
      className={cn(
        "flex gap-4 w-full mb-6",
        isAI ? "justify-start" : "justify-end"
      )}
    >
      {isAI && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shrink-0 shadow-md ring-2 ring-white dark:ring-slate-900">
          <span className="text-white font-bold text-xs">AI</span>
        </div>
      )}

      <div
        className={cn(
          "relative px-5 py-4 shadow-sm max-w-[85%] md:max-w-[75%]",
          isAI
            ? "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-700"
            : "bg-orange-600 text-white rounded-2xl rounded-tr-sm"
        )}
      >
        {/* Attachments */}
        {attachments && attachments.length > 0 && (
          <div className="flex gap-2 mb-3 pb-3 border-b border-white/20">
            {attachments.map((file, i) => (
              <div
                key={i}
                className="flex items-center gap-2 px-3 py-1 bg-black/10 rounded text-xs"
              >
                <Download className="w-3 h-3" /> {file.name}
              </div>
            ))}
          </div>
        )}

        {/* Message Content */}
        {isAI ? (
          <div className="min-w-0 overflow-hidden text-sm md:text-base">
            <AIContentRenderer content={text} />
          </div>
        ) : (
          <div className="whitespace-pre-wrap leading-relaxed text-sm md:text-base">{text}</div>
        )}

        {/* Test Accuracy Badge */}
        {isAI && testAccuracy?.is_test_question && (
          <AccuracyBadge accuracy={testAccuracy.accuracy} />
        )}

        {/* Timestamp */}
        {timestamp && (
          <div className={cn(
            "text-[10px] mt-2 text-right",
            isAI ? "text-slate-400" : "text-orange-100/70"
          )}>
            {timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        )}
      </div>
    </div>
  );
}