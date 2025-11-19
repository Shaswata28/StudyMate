import { cn } from "@/lib/utils";

interface SkeletonLoaderProps {
  type?: "text" | "avatar" | "card" | "button" | "lines";
  count?: number;
  className?: string;
  animated?: boolean;
}

export function SkeletonLoader({
  type = "text",
  count = 1,
  className,
  animated = true,
}: SkeletonLoaderProps) {
  const animationClass = animated ? "animate-pulse" : "";

  if (type === "avatar") {
    return (
      <div
        className={cn(
          "rounded-full bg-muted",
          animationClass,
          "w-12 h-12",
          className
        )}
      />
    );
  }

  if (type === "button") {
    return (
      <div
        className={cn(
          "rounded-lg bg-muted",
          animationClass,
          "h-10 w-32",
          className
        )}
      />
    );
  }

  if (type === "card") {
    return (
      <div className={cn("space-y-3", className)}>
        <div className={cn("h-32 bg-muted rounded-lg", animationClass)} />
        <div className="space-y-2">
          <div className={cn("h-4 bg-muted rounded w-3/4", animationClass)} />
          <div className={cn("h-4 bg-muted rounded w-1/2", animationClass)} />
        </div>
      </div>
    );
  }

  if (type === "lines") {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-4 bg-muted rounded",
              animationClass,
              i === count - 1 ? "w-1/2" : "w-full"
            )}
          />
        ))}
      </div>
    );
  }

  // default text skeleton
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-4 bg-muted rounded",
            animationClass,
            i === count - 1 ? "w-3/4" : "w-full"
          )}
        />
      ))}
    </div>
  );
}

export function SkeletonFileCard() {
  return (
    <div className="w-full max-w-[193px] h-[61px] rounded-[14px] border border-muted bg-muted animate-pulse" />
  );
}

export function SkeletonMessageBubble() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="w-8 h-8 rounded-full bg-muted animate-pulse flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
        <div className="h-4 bg-muted rounded w-1/2 animate-pulse" />
      </div>
    </div>
  );
}
