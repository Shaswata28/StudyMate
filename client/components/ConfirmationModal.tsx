import { AlertTriangle, X } from "lucide-react";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "warning";
}

export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Delete",
  cancelText = "Cancel",
  variant = "danger",
}: ConfirmationModalProps) {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
    } else if (e.key === "Enter") {
      handleConfirm();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onKeyDown={handleKeyPress}>
      {/* Backdrop with blur */}
      <div
        className="absolute inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm transition-colors"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[500px] mx-4 bg-white dark:bg-slate-800 rounded-[20px] sm:rounded-[30px] border-2 border-black dark:border-white shadow-2xl p-6 sm:p-8 message-enter">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 sm:top-6 sm:right-6 hover:opacity-70 transition-opacity btn-micro"
          aria-label="Close modal"
        >
          <X className="w-6 h-6 sm:w-8 sm:h-8 text-black dark:text-white" strokeWidth={2} />
        </button>

        {/* Icon */}
        <div className="flex justify-center mb-4">
          <div
            className={`p-3 rounded-full ${
              variant === "danger"
                ? "bg-red-100 dark:bg-red-950/30"
                : "bg-orange-100 dark:bg-orange-950/30"
            }`}
          >
            <AlertTriangle
              className={`w-8 h-8 sm:w-10 sm:h-10 ${
                variant === "danger"
                  ? "text-red-600 dark:text-red-400"
                  : "text-orange-600 dark:text-orange-400"
              }`}
              strokeWidth={2}
            />
          </div>
        </div>

        {/* Title */}
        <h2 className="font-audiowide text-lg sm:text-xl tracking-[1.8px] sm:tracking-[2px] text-black dark:text-white text-center mb-3">
          {title}
        </h2>

        {/* Message */}
        <p className="font-roboto text-sm sm:text-base text-gray-700 dark:text-gray-300 text-center mb-6 sm:mb-8 px-2">
          {message}
        </p>

        {/* Action Buttons */}
        <div className="flex gap-3 sm:gap-4">
          <button
            onClick={onClose}
            className="flex-1 px-4 sm:px-6 py-2.5 sm:py-3 bg-gray-100 dark:bg-slate-700 text-black dark:text-white font-audiowide text-xs sm:text-sm tracking-[1.2px] sm:tracking-[1.3px] rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 transition-all duration-200 btn-micro"
          >
            {cancelText}
          </button>
          <button
            onClick={handleConfirm}
            className={`flex-1 px-4 sm:px-6 py-2.5 sm:py-3 font-audiowide text-xs sm:text-sm tracking-[1.2px] sm:tracking-[1.3px] rounded-lg transition-all duration-200 btn-micro ${
              variant === "danger"
                ? "bg-red-600 dark:bg-red-500 text-white hover:bg-red-700 dark:hover:bg-red-600"
                : "bg-orange-600 dark:bg-orange-500 text-white hover:bg-orange-700 dark:hover:bg-orange-600"
            }`}
            autoFocus
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
