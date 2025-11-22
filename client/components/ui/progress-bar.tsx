import { cn } from "@/lib/utils";

interface ProgressBarProps {
  progress: number;
  total: number;
  animated?: boolean;
  showLabel?: boolean;
  variant?: "default" | "brand";
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "h-1",
  md: "h-2",
  lg: "h-3",
};

export function ProgressBar({
  progress,
  total,
  animated = true,
  showLabel = false,
  variant = "default",
  size = "md",
}: ProgressBarProps) {
  const percentage = (progress / total) * 100;

  return (
    <div className="w-full">
      {/* Progress bar container */}
      <div
        className={cn(
          "w-full rounded-full overflow-hidden bg-gray-200 dark:bg-slate-700",
          sizeClasses[size]
        )}
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`Progress: ${progress} of ${total}`}
      >
        {/* Progress fill */}
        <div
          className={cn(
            "h-full transition-all duration-500 ease-out rounded-full",
            variant === "brand"
              ? "bg-gradient-to-r from-studymate-orange to-studymate-green"
              : "bg-blue-500",
            animated && "animate-progress-fill"
          )}
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>

      {/* Progress label */}
      {showLabel && (
        <p className="text-center mt-2 font-audiowide text-sm text-gray-600 dark:text-gray-400">
          Question {progress} of {total}
        </p>
      )}

      {/* Step indicators */}
      <div className="flex gap-1 mt-3">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "flex-1 h-1 rounded-full transition-all duration-300",
              i < progress
                ? "bg-studymate-orange dark:bg-studymate-green"
                : i === progress
                ? "bg-studymate-orange/50 dark:bg-studymate-green/50 animate-pulse"
                : "bg-gray-300 dark:bg-slate-700"
            )}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}

interface LinearProgressProps {
  value: number;
  max?: number;
  className?: string;
  animated?: boolean;
}

export function LinearProgress({
  value,
  max = 100,
  className,
  animated = true,
}: LinearProgressProps) {
  const percentage = (value / max) * 100;

  return (
    <div
      className={cn(
        "w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-slate-700",
        className
      )}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <div
        className={cn(
          "h-full rounded-full bg-studymate-orange transition-all duration-500 ease-out",
          animated && "shadow-lg"
        )}
        style={{
          width: `${percentage}%`,
        }}
      />
    </div>
  );
}
