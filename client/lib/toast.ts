/**
 * Simple Toast Notification System
 */

type ToastType = 'success' | 'error' | 'info';

interface ToastOptions {
  message: string;
  type: ToastType;
  duration?: number;
}

class ToastService {
  private container: HTMLDivElement | null = null;

  private getContainer(): HTMLDivElement {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'fixed top-4 right-4 z-[10000] flex flex-col gap-2';
      document.body.appendChild(this.container);
    }
    return this.container;
  }

  private show(options: ToastOptions) {
    const { message, type, duration = 3000 } = options;
    const container = this.getContainer();

    const toast = document.createElement('div');
    toast.className = `
      px-4 py-3 rounded-lg shadow-lg
      font-roboto text-[13px]
      transform transition-all duration-300
      translate-x-0 opacity-100
      ${type === 'success' ? 'bg-green-500 text-white' : ''}
      ${type === 'error' ? 'bg-red-500 text-white' : ''}
      ${type === 'info' ? 'bg-blue-500 text-white' : ''}
    `;
    toast.textContent = message;

    container.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    }, 10);

    // Remove after duration
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      toast.style.opacity = '0';
      setTimeout(() => {
        container.removeChild(toast);
      }, 300);
    }, duration);
  }

  success(message: string, duration?: number) {
    this.show({ message, type: 'success', duration });
  }

  error(message: string, duration?: number) {
    this.show({ message, type: 'error', duration });
  }

  info(message: string, duration?: number) {
    this.show({ message, type: 'info', duration });
  }
}

export const toast = new ToastService();
