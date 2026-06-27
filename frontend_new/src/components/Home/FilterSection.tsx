import React from "react";
import { Copy, Check, Trash2, Save, RotateCcw } from "lucide-react";

interface FilterSectionProps {
  visibleFields: any;
  setVisibleFields: (val: any) => void;
  agrupar: boolean;
  setAgrupar: React.Dispatch<React.SetStateAction<boolean>>;
  getFieldLabel: (field: string) => string;
  copyToClipboard: (mode: "completa" | "intermediaria" | "agrupada") => void;
  clearResults: () => void;
  saveCurrentAsDefault: () => void;
  restoreDefault: () => void;
  uniqueCodigos?: string[];
  selectedCodigo?: string;
  setSelectedCodigo?: (val: string) => void;
}

export const FilterSection: React.FC<FilterSectionProps> = ({
  visibleFields,
  setVisibleFields,
  agrupar,
  setAgrupar,
  getFieldLabel,
  copyToClipboard,
  clearResults,
  saveCurrentAsDefault,
  restoreDefault,
  uniqueCodigos = [],
  selectedCodigo = "",
  setSelectedCodigo = () => {},
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
        
        {/* Ações de Preferência */}
        <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-4 ml-2">
          <button
            type="button"
            onClick={saveCurrentAsDefault}
            className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 transition-all"
            title="Salvar estas colunas como meu Padrão de Fábrica"
          >
            <Save size={14} />
          </button>
          <button
            type="button"
            onClick={restoreDefault}
            className="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-primary/5 transition-all"
            title="Restaurar meu Padrão de Fábrica"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      <div className="flex flex-col items-end gap-2 lg:ml-auto w-full lg:w-auto mt-4 lg:mt-0">
        
        {/* PRIMEIRA LINHA: Toggle Agrupar + Limpar */}
        <div className="flex items-center gap-4 justify-end w-full flex-wrap">
          {uniqueCodigos.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase">Peça:</span>
              <select
                value={selectedCodigo}
                onChange={(e) => setSelectedCodigo(e.target.value)}
                className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 outline-none text-slate-700 dark:text-slate-300 font-medium"
              >
                <option value="">Todas</option>
                {uniqueCodigos.map(cod => (
                  <option key={cod} value={cod}>{cod}</option>
                ))}
              </select>
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer group lg:border-l lg:border-slate-200 lg:dark:border-slate-800 lg:pl-4">
            <input
              type="checkbox"
              className="sr-only"
              checked={agrupar}
              onChange={() => setAgrupar((prev) => !prev)}
            />
            <div className={`w-8 h-4 rounded-full transition-all relative ${agrupar ? "bg-primary" : "bg-slate-300 dark:bg-slate-700"}`}>
              <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${agrupar ? "left-[18px]" : "left-0.5"}`} />
            </div>
            <span className="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors uppercase whitespace-nowrap">
              Agrupar
            </span>
          </label>

          <div className="w-px h-5 bg-slate-200 dark:bg-slate-800 shrink-0"></div>

          <button
            type="button"
            onClick={clearResults}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-red-500/10 text-red-600 hover:bg-red-500/20 transition-all border border-red-500/20 text-[10px] font-bold uppercase tracking-widest whitespace-nowrap"
            title="Limpar todos os resultados da busca"
          >
            <Trash2 size={12} />
            Limpar
          </button>
        </div>

        {/* SEGUNDA LINHA: Botões de Cópia Agrupada */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl justify-end w-full sm:w-auto">
          <button
            type="button"
            onClick={() => copyToClipboard("completa")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-700 transition-all text-[10px] font-bold flex items-center gap-1.5 whitespace-nowrap"
            title="Completa: Marca, Modelo, Motor, Config, Ano"
          >
            <Copy size={10} /> COMPL.
          </button>
          <button
            type="button"
            onClick={() => copyToClipboard("intermediaria")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-700 transition-all text-[10px] font-bold flex items-center gap-1.5 whitespace-nowrap"
            title="Interm: Marca, Veículo, Config, Ano (por range)"
          >
            <Copy size={10} /> INTERM.
          </button>
          <button
            type="button"
            onClick={() => copyToClipboard("agrupada")}
            className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-700 transition-all text-[10px] font-bold flex items-center gap-1.5 whitespace-nowrap"
            title="Agrupada: Marca, Veículo, Range Total de Anos"
          >
            <Copy size={10} /> AGRUP.
          </button>
        </div>
      </div>
    </div>
  );
};
