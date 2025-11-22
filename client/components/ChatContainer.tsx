import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";

interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
}

interface ChatContainerProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function ChatContainer({
  messages,
  isLoading = false,
}: ChatContainerProps) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-12">
        <h3 className="font-audiowide text-lg text-black dark:text-white mb-2">
          Start a conversation
        </h3>
        <p className="font-roboto text-sm text-gray-500 dark:text-gray-400 max-w-sm">
          Ask questions about your uploaded materials to get personalized explanations
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex flex-col gap-4 smooth-scroll overflow-y-auto flex-1"
    >
      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          id={message.id}
          text={message.text}
          isAI={message.isAI}
          timestamp={message.timestamp}
        />
      ))}

      {isLoading && (
        <div className="flex gap-4 mb-4 justify-start animate-float-up">
          <div className="w-8 h-8 rounded-full bg-studymate-orange dark:bg-studymate-orange flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <div className="bg-gray-100 dark:bg-slate-800 rounded-lg px-4 py-3 rounded-tl-none">
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-studymate-black dark:bg-white animate-bounce" style={{ animationDelay: "0ms" }} />
              <div className="w-2 h-2 rounded-full bg-studymate-black dark:bg-white animate-bounce" style={{ animationDelay: "150ms" }} />
              <div className="w-2 h-2 rounded-full bg-studymate-black dark:bg-white animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        </div>
      )}

      <div ref={endOfMessagesRef} />
    </div>
  );
}
