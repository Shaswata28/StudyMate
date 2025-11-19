import { toast as sonnerToast } from "sonner";

export const toast = {
  success: (message: string, description?: string) => {
    return sonnerToast.success(message, {
      description,
      duration: 4000,
    });
  },

  error: (message: string, description?: string) => {
    return sonnerToast.error(message, {
      description,
      duration: 4000,
    });
  },

  loading: (message: string) => {
    return sonnerToast.loading(message);
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string;
    }
  ) => {
    return sonnerToast.promise(promise, messages, {
      duration: 4000,
    });
  },

  info: (message: string, description?: string) => {
    return sonnerToast(message, {
      description,
      duration: 4000,
    });
  },

  warning: (message: string, description?: string) => {
    return sonnerToast(message, {
      description,
      duration: 4000,
    });
  },

  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId);
  },
};

// Export Sonner toast directly for advanced usage
export { sonnerToast };
