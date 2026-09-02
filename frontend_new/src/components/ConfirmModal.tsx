import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
    confirmText?: string;
    cancelText?: string;
    type?: 'warning' | 'danger' | 'info';
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    title,
    message,
    onConfirm,
    onCancel,
    confirmText = 'Confirmar',
    cancelText = 'Cancelar',
    type = 'info'
}) => {
    if (!isOpen) return null;

    const colors = {
        warning: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
        danger: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
        info: 'text-primary bg-primary/10 border-primary/20'
    };

    const btnColors = {
        warning: 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/20',
        danger: 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/20',
        info: 'bg-primary hover:bg-primary-hover shadow-primary/20'
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-in fade-in duration-200">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" 
                onClick={onCancel}
            />
            
            {/* Modal */}
            <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-8">
                    <div className="flex items-start justify-between mb-6">
                        <div className={`p-3 rounded-2xl border ${colors[type]}`}>
                            <AlertCircle size={28} />
                        </div>
                        <button 
                            onClick={onCancel}
                            className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <h3 className="text-xl font-black text-slate-800 dark:text-white mb-2">
                        {title}
                    </h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed font-medium">
                        {message}
                    </p>

                    <div className="flex gap-3 mt-8">
                        <button
                            onClick={onCancel}
                            className="flex-1 px-6 py-3 rounded-2xl font-bold text-slate-500 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
                        >
                            {cancelText}
                        </button>
                        <button
                            onClick={() => {
                                onConfirm();
                                onCancel();
                            }}
                            className={`flex-1 px-6 py-3 rounded-2xl font-bold text-white shadow-lg transition-all ${btnColors[type]}`}
                        >
                            {confirmText}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConfirmModal;
