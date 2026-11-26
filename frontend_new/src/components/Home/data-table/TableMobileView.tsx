import React from "react";
import { SearchX, Image, Zap } from "lucide-react";

interface TableMobileViewProps {
  displayResults: any[];
  paginatedResults: any[];
  visibleFields: any;
  loading: boolean;
  partId: string;
  getFieldLabel: (field: string) => string;
  handleOpenGallery: (res: any) => void;
  handleOpenFicha: (res: any) => void;
  proxyImageUrl: (url: string) => string;
}

export const TableMobileView: React.FC<TableMobileViewProps> = ({
  displayResults,
  paginatedResults,
  visibleFields,
  loading,
  partId,
  getFieldLabel,
  handleOpenGallery,
  handleOpenFicha,
  proxyImageUrl,
}) => {
  if (displayResults.length === 0) {
    if (loading) {
      return (
        <div className="md:hidden block divide-y divide-slate-100 dark:divide-slate-800">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 space-y-3 animate-pulse border-b border-slate-100 dark:border-slate-800">
              <div className="flex justify-between">
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
              </div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="md:hidden block px-6 py-12 text-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 bg-amber-500/10 rounded-2xl flex items-center justify-center">
            <SearchX size={24} className="text-amber-500" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-600 dark:text-slate-300">
              Nenhum produto encontrado{partId ? ` para "${partId}"` : "."}
            </p>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Verifique se o código está correto ou tente outro provedor.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="md:hidden block divide-y divide-slate-100 dark:divide-slate-800">
      {paginatedResults.map((res, idx) => (
        <div
          key={idx}
          className="p-4 space-y-3 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors"
        >
          <div className="flex justify-between items-start gap-2">
            <div className="flex items-start gap-3">
              {visibleFields.imagem && (res.imagem || (res.imagens && res.imagens.length > 0)) && (
                <button
                  onClick={() => handleOpenGallery(res)}
                  className="w-12 h-12 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 bg-white shrink-0 aspect-square flex items-center justify-center"
                  title="Ver imagem na galeria"
                >
                  <img
                    src={proxyImageUrl(res.imagens && res.imagens.length > 0 ? res.imagens[0] : res.imagem)}
                    alt={res.codigo || "Peça"}
                    loading="lazy"
                    decoding="async"
                    width={48}
                    height={48}
                    className="w-full h-full object-contain"
                  />
                </button>
              )}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black bg-primary/10 text-primary px-1.5 py-0.5 rounded uppercase">
                    {res.marca}
                  </span>
                  {visibleFields.codigo && res.codigo && (
                    <span className="text-[10px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 px-1.5 py-0.5 rounded">
                      {res.codigo}
                    </span>
                  )}
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {res.veiculo}
                  </span>
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                  {res.modelo} • {res.motor}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                {res.ano_inicio || "---"}{" "}
                {res.ano_inicio || res.ano_fim ? "..." : ""}{" "}
                {res.ano_fim || ""}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px] text-slate-500">
            {visibleFields.configuracao_motor && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("configuracao_motor")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300">
                  {res.configuracao_motor || "---"}
                </span>
              </div>
            )}
            {visibleFields.combustivel && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("combustivel")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300">
                  {res.combustivel || "---"}
                </span>
              </div>
            )}
            {visibleFields.posicao && res.posicao && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("posicao")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300 uppercase">
                  {res.posicao}
                </span>
              </div>
            )}
            {visibleFields.lado && res.lado && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("lado")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300 uppercase">
                  {res.lado}
                </span>
              </div>
            )}
            {visibleFields.direcao && res.direcao && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("direcao")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300 uppercase">
                  {res.direcao}
                </span>
              </div>
            )}
            {visibleFields.sistema_freio && res.sistema_freio && (
              <div>
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("sistema_freio")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300 uppercase">
                  {res.sistema_freio}
                </span>
              </div>
            )}
            {visibleFields.restricao && res.restricao && (
              <div className="col-span-2">
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("restricao")}:
                </span>
                <span className="text-slate-400 italic">
                  {res.restricao}
                </span>
              </div>
            )}
            {visibleFields.apenas && res.apenas && (
              <div className="col-span-2">
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("apenas")}:
                </span>
                <span className="text-primary font-black uppercase text-[11px]">
                  ★ {res.apenas}
                </span>
              </div>
            )}
            {visibleFields.ficha_tecnica && res.ficha_tecnica && (
              <div className="col-span-2 space-y-1 mt-1 border-t border-slate-50 dark:border-slate-800 pt-1">
                <span className="font-bold text-slate-400 uppercase text-[9px] block">
                  {getFieldLabel("ficha_tecnica")}:
                </span>
                <div className="grid grid-cols-2 gap-1">
                  {Object.entries(res.ficha_tecnica).map(([label, value]: [string, any], subIdx: number) => (
                    <div key={subIdx} className="flex items-center gap-1 uppercase">
                      <span className="text-slate-400 font-bold shrink-0">{label}:</span>
                      <span className="text-primary font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {visibleFields.observacao && res.observacao && (
              <div className="col-span-2">
                <span className="font-bold text-slate-400 uppercase mr-1">
                  {getFieldLabel("observacao")}:
                </span>
                <span className="text-slate-700 dark:text-slate-300">
                  {res.observacao}
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={() => handleOpenGallery(res)}
              disabled={!res.imagem && (!res.imagens || res.imagens.length === 0)}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary/5 text-primary disabled:opacity-30 rounded-lg text-xs font-bold uppercase transition-all"
            >
              <Image size={16} /> Galeria
            </button>
            <button
              onClick={() => handleOpenFicha(res)}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-amber-500/5 text-amber-600 rounded-lg text-xs font-bold uppercase transition-all"
            >
              <Zap size={16} /> Ficha Técnica
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
