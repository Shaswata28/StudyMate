import { CheckCircle, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

interface StatusAlertProps {
  type: "success" | "error" | "info" | "warning";
  title: string;
  message?: string;
  onClose?: () => void;
  autoClose?: boolean;
  duration?: number;
  className?: string;
}

export function StatusAlert({
  type,
  title,
  message,
  onClose,
  autoClose = true,
  duration = 5000,
  className,
}: StatusAlertProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onClose?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [autoClose, duration, onClose]);

  if (!isVisible) {
    return null;
  }

  const variants = {
    success: {
      bg: "bg-green-50 dark:bg-green-950/30",
      border: "border-green-200 dark:border-green-800",
      icon: <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />,
      titleColor: "text-green-800 dark:text-green-200",
      messageColor: "text-green-700 dark:text-green-300",
    },
    error: {
      bg: "bg-red-50 dark:bg-red-950/30",
      border: "border-red-200 dark:border-red-800",
      icon: <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />,
      titleColor: "text-red-800 dark:text-red-200",
      messageColor: "text-red-700 dark:text-red-300",
    },
    info: {
      bg: "bg-blue-50 dark:bg-blue-950/30",
      border: "border-blue-200 dark:border-blue-800",
      icon: <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />,
      titleColor: "text-blue-800 dark:text-blue-200",
      messageColor: "text-blue-700 dark:text-blue-300",
    },
    warning: {
      bg: "bg-yellow-50 dark:bg-yellow-950/30",
      border: "border-yellow-200 dark:border-yellow-800",
      icon: <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />,
      titleColor: "text-yellow-800 dark:text-yellow-200",
      messageColor: "text-yellow-700 dark:text-yellow-300",
    },
  };

  const variant = variants[type];

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border px-4 py-3 animate-slide-in-from-top-5 duration-200",
        variant.bg,
        variant.border,
        className
      )}
      role="alert"
    >
      <div className="flex-shrink-0 mt-0.5">{variant.icon}</div>

      <div className="flex-1">
        <h3 className={cn("font-semibold text-sm", variant.titleColor)}>
          {title}
        </h3>
        {message && (
          <p className={cn("text-sm mt-1", variant.messageColor)}>
            {message}
          </p>
        )}
      </div>

      {onClose && (
        <button
          onClick={() => {
            setIsVisible(false);
            onClose();
          }}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          aria-label="Close alert"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export function StatusMessage({
  type,
  title,
  animated = true,
}: {
  type: "success" | "error";
  title: string;
  animated?: boolean;
}) {
  const isSuccess = type === "success";

  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 py-6",
        animated && "message-enter"
      )}
    >
      {isSuccess ? (
        <div className="relative w-16 h-16">
          <svg
            className="w-16 h-16 animate-success-checkmark"
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle
              cx="32"
              cy="32"
              r="30"
              className="text-green-500 dark:text-green-400"
            />
            <path
              d="M20 32l8 8 16-16"
              className="text-green-500 dark:text-green-400"
            />
          </svg>
        </div>
      ) : (
        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-950/30 flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
        </div>
      )}

      <h3 className={cn(
        "font-audiowide text-lg",
        isSuccess
          ? "text-green-600 dark:text-green-400"
          : "text-red-600 dark:text-red-400"
      )}>
        {title}
      </h3>
    </div>
  );
}
