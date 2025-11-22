import { cn } from "@/lib/utils";

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg";
  variant?: "default" | "brand";
}

const sizeClasses = {
  sm: "w-4 h-4 border-2",
  md: "w-6 h-6 border-2",
  lg: "w-8 h-8 border-3",
};

export function Spinner({
  size = "md",
  variant = "default",
  className,
  ...props
}: SpinnerProps) {
  return (
    <div
      className={cn(
        "inline-block rounded-full border border-t-transparent animate-spin",
        variant === "brand" ? "border-studymate-black border-t-studymate-orange" : "border-current border-t-transparent",
        sizeClasses[size],
        className
      )}
      {...props}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export function LoadingOverlay({
  isLoading,
  children,
}: {
  isLoading: boolean;
  children: React.ReactNode;
}) {
  if (!isLoading) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      {children}
      <div className="absolute inset-0 bg-white/50 dark:bg-black/50 rounded-lg flex items-center justify-center backdrop-blur-sm">
        <Spinner size="lg" variant="brand" />
      </div>
    </div>
  );
}
