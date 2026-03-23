import React from "react";
import { Search, Loader2 } from "lucide-react";

interface SearchSectionProps {
  partId: string;
  setPartId: (val: string) => void;
  selectedProvedor: number | "";
  setSelectedProvedor: (val: number | "") => void;
  provedores: any[];
  loading: boolean;
  handleSearch: (e: React.FormEvent) => void;
}

export const SearchSection: React.FC<SearchSectionProps> = ({
  partId,
  setPartId,
  selectedProvedor,
  setSelectedProvedor,
  provedores,
  loading,
  handleSearch,
}) => {
  return (
    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={20} />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-3 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              placeholder="Digite o código da peça..."
              value={partId}
              onChange={(e) => setPartId(e.target.value)}
            />
          </div>

          <div className="w-full md:w-64">
            <select
              value={selectedProvedor}
              onChange={(e) => setSelectedProvedor(Number(e.target.value))}
              className="w-full h-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary transition-all"
            >
              <option value="">Todos os Provedores</option>
              {provedores.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 md:w-auto w-full"
          >
            {loading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <Search size={20} />
            )}
            {loading ? "Buscando..." : "Pesquisar"}
          </button>
        </div>
      </form>
    </div>
  );
};
