"use client";

import { useLayoutEffect, useRef } from "react";
import MessageBubble, { MessageProps } from "./MessageBubble";
import type { CourseSource } from "@/lib/api";
import { BookOpen, Calculator } from "lucide-react";

interface ChatContainerProps {
  messages: MessageProps[];
  isLoading: boolean;
  newReplyId?: string;
  onRevealComplete: () => void;
  onOpenSource: (source: CourseSource) => void;
  onPractice: (id: number) => void;
  onDiagram: (id: number) => void;
  onBookmark: (id: number, saved: boolean) => void;
  courseName: string;
  onSendExample: (text: string) => void;
}

export default function ChatContainer({
  messages,
  newReplyId,
  onOpenSource,
  onBookmark,
  onDiagram,
  onPractice,
  onRevealComplete,
  isLoading,
  courseName,
  onSendExample,
}: ChatContainerProps) {
  const viewport = useRef<HTMLDivElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const follow = useRef(true);
  const hasMessages = messages.length > 0;

  useLayoutEffect(() => {
    const scroller = viewport.current;
    const inner = content.current;
    if (!scroller || !inner) return;
    const scrollToReply = () => {
      if (follow.current) scroller.scrollTop = scroller.scrollHeight;
    };
    scrollToReply();
    const observer = new ResizeObserver(scrollToReply);
    observer.observe(inner);
    return () => observer.disconnect();
  }, [hasMessages]);

  useLayoutEffect(() => {
    if (isLoading && viewport.current) {
      follow.current = true;
      viewport.current.scrollTop = viewport.current.scrollHeight;
    }
  }, [isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <h3 className="font-sans text-xl text-black dark:text-white mb-2">
          {courseName || "Select a Course"}
        </h3>
        <p className="text-sm text-gray-500 max-w-sm mb-8 font-sans">
          Ask a question or attach course notes to get started.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full text-left">
          <button
            onClick={() => onSendExample("Can you summarize the core concepts in my course materials?")}
            className="p-4 rounded-control border border-black/10 dark:border-white/10 hover:border-black/30 dark:hover:border-white/30 transition-all text-xs flex items-start gap-3 bg-gray-50/50 dark:bg-slate-900/50"
          >
            <BookOpen className="w-4 h-4 text-[#FEAE01] shrink-0 mt-0.5" />
            <div>
              <p className="font-sans mb-1">Summarize Materials</p>
              <p className="text-gray-500">Provide an overview of key topics</p>
            </div>
          </button>

          <button
            onClick={() => onSendExample("Explain this formula step-by-step with LaTeX math.")}
            className="p-4 rounded-control border border-black/10 dark:border-white/10 hover:border-black/30 dark:hover:border-white/30 transition-all text-xs flex items-start gap-3 bg-gray-50/50 dark:bg-slate-900/50"
          >
            <Calculator className="w-4 h-4 text-[#1FC209] shrink-0 mt-0.5" />
            <div>
              <p className="font-sans mb-1">LaTeX Breakdown</p>
              <p className="text-gray-500">Solve & format mathematical equations</p>
            </div>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div ref={viewport} onScroll={(event) => {
      const { scrollHeight, scrollTop, clientHeight } = event.currentTarget;
      follow.current = scrollHeight - scrollTop - clientHeight < 48;
    }} className="min-h-0 flex-1 overflow-y-auto [overflow-anchor:none] px-4 md:px-8 py-6">
      <div ref={content} className="max-w-3xl mx-auto">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} reveal={m.id === newReplyId} onRevealComplete={onRevealComplete} onOpenSource={onOpenSource} onBookmark={onBookmark} onDiagram={onDiagram} onPractice={onPractice} />
        ))}

        {isLoading && (
          <div role="status" className="study-enter my-5 flex items-center gap-3 text-sm text-neutral-600 dark:text-neutral-300">
            <span aria-hidden className="flex items-center gap-1.5 text-[#657354] dark:text-[#b5c0a4]">
              <span className="reply-pulse size-1.5 rounded-full bg-current" />
              <span className="reply-pulse size-1.5 rounded-full bg-current [animation-delay:140ms]" />
              <span className="reply-pulse size-1.5 rounded-full bg-current [animation-delay:280ms]" />
            </span>
            Preparing a reply
          </div>
        )}
      </div>
    </div>
  );
}

