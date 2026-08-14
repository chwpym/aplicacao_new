import React from 'react';
import { AlertCircle, X, Info, AlertTriangle } from 'lucide-react';

interface AlertModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    onClose: () => void;
    buttonText?: string;
    type?: 'warning' | 'danger' | 'info';
}

const AlertModal: React.FC<AlertModalProps> = ({
    isOpen,
    title,
    message,
    onClose,
    buttonText = 'Entendi',
    type = 'warning'
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

    const Icon = type === 'warning' ? AlertTriangle : type === 'danger' ? AlertCircle : Info;

    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 animate-in fade-in duration-200">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" 
                onClick={onClose}
            />
            
            {/* Modal */}
            <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-8">
                    <div className="flex items-start justify-between mb-6">
                        <div className={`p-3 rounded-2xl border ${colors[type]}`}>
                            <Icon size={28} />
                        </div>
                        <button 
                            onClick={onClose}
                            className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <h3 className="text-xl font-black text-slate-800 dark:text-white mb-2">
                        {title}
                    </h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed font-medium whitespace-pre-wrap">
                        {message}
                    </p>

                    <div className="flex mt-8">
                        <button
                            onClick={onClose}
                            className={`flex-1 px-6 py-3 rounded-2xl font-bold text-white shadow-lg transition-all ${btnColors[type]}`}
                        >
                            {buttonText}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AlertModal;
