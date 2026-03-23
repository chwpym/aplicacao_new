import React from 'react';
import { X, FileText } from 'lucide-react';

interface FichaTecnicaModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: Record<string, any> | null;
}

export const FichaTecnicaModal: React.FC<FichaTecnicaModalProps> = ({ isOpen, onClose, data }) => {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-surface-dark w-full max-w-lg rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border border-slate-200 dark:border-slate-800 animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText size={16} className="text-primary" />
            </div>
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Ficha Técnica Detalhada
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 dark:text-slate-500 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto custom-scrollbar">
          <div className="space-y-3">
            {Object.entries(data).map(([key, value], idx) => (
               <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                 <span className="text-[10px] font-bold text-slate-500 uppercase mb-1 md:mb-0 mr-4 shrink-0">{key}</span>
                 <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 text-left md:text-right">{value}</span>
               </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
