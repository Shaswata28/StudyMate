"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import type { CourseSource } from "@/lib/api";
import { playKokoro } from "@/lib/playKokoro";
import { isMermaidDiagram } from "@/lib/renderDiagram";
import ChatDiagram from "./ChatDiagram";
import { findEnglishVoice, getVoiceMode } from "@/lib/systemVoice";
import { toast } from "sonner";
import { Bookmark, Workflow, Layers, Check, Copy, Volume2, VolumeX } from "lucide-react";

export interface MessageProps {
  id: string;
  role: "user" | "model" | "assistant";
  content: string;
  timestamp?: string;
  turnId?: number;
  bookmarked?: boolean;
  sources?: CourseSource[];

}

export default function MessageBubble({ message, reveal, onRevealComplete, onOpenSource, onBookmark, onDiagram, onPractice }: {
  message: MessageProps;
  reveal: boolean;
  onRevealComplete: () => void;
  onOpenSource?: (source: CourseSource) => void;
  onPractice?: (id: number) => void;
  onDiagram?: (id: number) => void;
  onBookmark?: (id: number, saved: boolean) => void;
}) {
  const isUser = message.role === "user";
  const router = useRouter();
  const stopSpeech = useRef<(() => void) | null>(null);
  useEffect(() => () => stopSpeech.current?.(), []);
  const [copied, setCopied] = useState(false);

  const [speaking, setSpeaking] = useState(false);
  const [preparingSpeech, setPreparingSpeech] = useState(false);
  const response = useRef<HTMLDivElement>(null);
  const onComplete = useRef(onRevealComplete);
  onComplete.current = onRevealComplete;

  useLayoutEffect(() => {
    const element = response.current;
    if (!reveal || !element) return;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches || !element.animate) {
      onComplete.current();
      return;
    }

    const height = element.scrollHeight;
    const lines = Math.max(1, Math.round(height / 28));
    const animation = element.animate(
      [{ maxHeight: "0px", overflow: "hidden" }, { maxHeight: `${height}px`, overflow: "hidden" }],
      { duration: Math.min(1600, Math.max(120, lines * 34)), easing: `steps(${lines}, end)` },
    );
    animation.onfinish = () => onComplete.current();
    return () => animation.cancel();
  }, [reveal]);

  const toggleSpeech = async () => {
    if (stopSpeech.current) {
      stopSpeech.current();
      stopSpeech.current = null;
      setSpeaking(false);
      setPreparingSpeech(false);
      return;
    }
    const engine = window.speechSynthesis;
    const plainText = message.content
      .replace(/```[\s\S]*?```/g, " Code block. ")
      .replace(/\$\$[\s\S]*?\$\$|\$[^$\n]+\$/g, " formula ")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[#*`]/g, "")
      .trim();
    if (!plainText) return;
    const controller = new AbortController();
    stopSpeech.current = () => controller.abort();
    setSpeaking(true);
    const finish = () => {
      if (!controller.signal.aborted) {
        stopSpeech.current = null;
        setSpeaking(false);
        setPreparingSpeech(false);
      }
    };

    try {
      const mode = getVoiceMode();
      if (mode === "kokoro") {
        setPreparingSpeech(true);
        await playKokoro(plainText, controller.signal, () => setPreparingSpeech(false));
        finish();
        return;
      }
      if (engine && engine.getVoices().length === 0) {
        await new Promise<void>((resolve) => {
          const done = () => {
            window.clearTimeout(timer);
            engine.removeEventListener("voiceschanged", done);
            resolve();
          };
          const timer = window.setTimeout(done, 700);
          engine.addEventListener("voiceschanged", done, { once: true });
        });
      }
      if (controller.signal.aborted) return;
      const voice = findEnglishVoice(engine, mode);
      if (!engine || !voice) {
        toast.error(mode === "chrome"
          ? "This browser does not offer an online Google English voice. Check Voice setup."
          : "No local English voice is available. Check Voice setup for other options.", {
          action: { label: "Voice setup", onClick: () => router.push("/settings?section=read-aloud") },
        });
        finish();
        return;
      }
      const speech = new SpeechSynthesisUtterance(plainText);
      speech.voice = voice;
      speech.onend = finish;
      speech.onerror = () => {
        if (!controller.signal.aborted) toast.error(mode === "chrome"
          ? "Could not play the Chrome voice. Check your connection or switch to a system voice."
          : "Could not play this system voice.");
        finish();
      };
      stopSpeech.current = () => { controller.abort(); engine.cancel(); };
      engine.cancel();
      engine.speak(speech);
    } catch (error) {
      if (controller.signal.aborted) return;
      toast.error(error instanceof Error ? error.message : "Could not read this answer aloud.", {
        action: { label: "Local setup", onClick: () => router.push("/settings?section=read-aloud") },
      });
      finish();
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="study-enter my-6 flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-panel border border-line bg-surface px-4 py-3 text-sm leading-relaxed sm:max-w-[75%] sm:text-base">
          {message.content}
        </p>
      </div>
    );
  }

  const markdown = message.content.replace(/\[Source (\d+)\](?!\()/gi, (citation, index: string) =>
    message.sources?.[Number(index) - 1] ? `[Source ${index}](#study-source-${index})` : citation,
  );
  const containsDiagram = /^\s*(?:`{3,}|~{3,})[ \t]*(?:mermaid\b|\r?\n[ \t]*(?:flowchart|graph|sequenceDiagram)\b)/im.test(markdown);

  return (
    <article className="my-7 min-w-0" aria-label="StudyMate reply">
      <div ref={response} className="tutor-response min-w-0 break-words text-[1.02rem] leading-[1.75]">
        <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}
          components={{
            pre: ({ node, children, ...props }) => {
              const block = node?.children[0];
              if (block?.type === "element" && block.tagName === "code") {
                const languages = block.properties.className;
                const code = block.children.map((child) => child.type === "text" ? child.value : "").join("");
                if ((Array.isArray(languages) && languages.includes("language-mermaid")) || (!languages && isMermaidDiagram(code))) {
                  return <ChatDiagram key={code} code={code} turnId={message.turnId} />;
                }
              }
              return <pre {...props}>{children}</pre>;
            },
            img: ({ alt }) => alt ? <span>{alt}</span> : null,
            a: ({ href, children }) => {
              const marker = href?.match(/^#study-source-(\d+)$/);
              const source = marker && message.sources?.[Number(marker[1]) - 1];
              return source && onOpenSource ? (
                <button type="button" className="source-citation" title={source.name} onClick={() => onOpenSource(source)}>
                  {children}
                </button>
              ) : <a href={href}>{children}</a>;
            },
          }}>
          {markdown}
        </ReactMarkdown>
      </div>
      <div className={`mt-3 flex items-center gap-3 text-xs text-neutral-600 dark:text-neutral-300 ${reveal ? "invisible" : ""}`}>
            <button
              onClick={toggleSpeech}
              className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 flex items-center gap-1"
              title={speaking ? "Stop reading" : "Read answer aloud"}
            >
              {speaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              <span className="text-[10px]">{preparingSpeech ? "Preparing audio..." : speaking ? "Stop" : "Read aloud"}</span>
            </button>
            {message.turnId !== undefined && onDiagram && !containsDiagram && (
              <button type="button" onClick={() => onDiagram(message.turnId!)}
                className="flex items-center gap-1 rounded p-1 hover:bg-black/5 dark:hover:bg-white/5">
                <Workflow className="size-3.5" /> Diagram
              </button>
            )}
            {message.turnId !== undefined && onPractice && Boolean(message.sources?.length) && (
              <button type="button" onClick={() => onPractice(message.turnId!)}
                className="flex items-center gap-1 rounded p-1 hover:bg-black/5 dark:hover:bg-white/5">
                <Layers className="size-3.5" /> Study items
              </button>
            )}
            {message.turnId !== undefined && onBookmark && (
              <button type="button" aria-pressed={Boolean(message.bookmarked)} onClick={() => onBookmark(message.turnId!, !message.bookmarked)}
                className="flex items-center gap-1 rounded px-1 py-1 hover:bg-black/5 dark:hover:bg-white/5">
                <Bookmark className={`size-3.5 ${message.bookmarked ? "fill-current text-accent" : ""}`} />
                {message.bookmarked ? "Saved" : "Save"}
              </button>
            )}
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors flex items-center gap-1"
              title="Copy answer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              <span className="text-[10px]">{copied ? "Copied" : "Copy"}</span>
            </button>
      </div>
    </article>
  );
}
