import React from "react";
import { Copy, Check, Trash2 } from "lucide-react";

interface FilterSectionProps {
  visibleFields: any;
  setVisibleFields: (val: any) => void;
  agrupar: boolean;
  setAgrupar: React.Dispatch<React.SetStateAction<boolean>>;
  getFieldLabel: (field: string) => string;
  copyToClipboard: (mode: "completa" | "intermediaria" | "agrupada") => void;
  clearResults: () => void;
}

export const FilterSection: React.FC<FilterSectionProps> = ({
  visibleFields,
  setVisibleFields,
  agrupar,
  setAgrupar,
  getFieldLabel,
  copyToClipboard,
  clearResults,
}) => {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center gap-6 pt-4 border-t border-slate-100 dark:border-slate-800 mt-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">
          Exibir:
        </span>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {Object.keys(visibleFields).map((field) => {
            return (
              <label
                key={field}
                className="flex items-center gap-2 cursor-pointer group whitespace-nowrap"
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={visibleFields[field as keyof typeof visibleFields]}
                  onChange={() =>
                    setVisibleFields((prev: any) => ({
                      ...prev,
                      [field]: !prev[field as keyof typeof visibleFields],
                    }))
                  }
                />
                <div
                  className={`w-4 h-4 rounded border transition-all flex items-center justify-center ${visibleFields[field as keyof typeof visibleFields] ? "bg-primary border-primary" : "border-slate-300 dark:border-slate-600"}`}
                >
                  {visibleFields[field as keyof typeof visibleFields] && (
                    <Check size={10} className="text-white" />
                  )}
                </div>
                <span className="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors capitalize">
                  {getFieldLabel(field)}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 lg:ml-auto">
        <div className="flex items-center gap-4 lg:border-l lg:border-slate-200 lg:dark:border-slate-800 lg:pl-4">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              className="sr-only"
              checked={agrupar}
              onChange={() => setAgrupar((prev) => !prev)}
            />
            <div
              className={`w-8 h-4 rounded-full transition-all relative ${agrupar ? "bg-primary" : "bg-slate-300 dark:bg-slate-700"}`}
            >
              <div
                className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${agrupar ? "left-[18px]" : "left-0.5"}`}
              />
            </div>
            <span className="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors uppercase whitespace-nowrap">
              Agrupar
            </span>
          </label>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => copyToClipboard("completa")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-900 transition-all text-[10px] font-bold flex items-center gap-1.5"
            title="Completa: Marca, Modelo, Motor, Config, Ano"
          >
            <Copy size={10} /> COMPL.
          </button>
          <button
            type="button"
            onClick={() => copyToClipboard("intermediaria")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-900 transition-all text-[10px] font-bold flex items-center gap-1.5"
            title="Interm: Marca, Veículo, Config, Ano (por range)"
          >
            <Copy size={10} /> INTERM.
          </button>
          <button
            type="button"
            onClick={() => copyToClipboard("agrupada")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-900 transition-all text-[10px] font-bold flex items-center gap-1.5"
            title="Agrupada: Marca, Veículo, Range Total de Anos"
          >
            <Copy size={10} /> AGRUP.
          </button>
        </div>

        <button
          type="button"
          onClick={clearResults}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/30 hover:shadow-red-600/50 transition-all text-[10px] font-bold uppercase tracking-widest"
          title="Limpar todos os resultados da busca"
        >
          <Trash2 size={12} fill="white" />
          Limpar
        </button>
      </div>
    </div>
  );
};
