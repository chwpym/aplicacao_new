type ToastType = 'success' | 'error';

interface ToastEventDetail {
    message: string;
    type: ToastType;
}

export const toast = {
    show: (message: string, type: ToastType = 'success') => {
        const event = new CustomEvent('app-toast', { 
            detail: { message, type } 
        });
        window.dispatchEvent(event);
    },
    success: (message: string) => toast.show(message, 'success'),
    error: (message: string) => toast.show(message, 'error')
};
