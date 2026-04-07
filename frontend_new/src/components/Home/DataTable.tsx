import React, { useState } from "react";
import { Copy, FileDown, Loader2, FileSpreadsheet, FileText } from "lucide-react";
import { FichaTecnicaModal } from "./FichaTecnicaModal";
import { ImageGalleryModal } from "./ImageGalleryModal";
import { exportToExcel, exportToPdf } from "../../utils/exportUtils";
import { Image, Zap, ExternalLink } from "lucide-react";

interface DataTableProps {
  results: any[];
  displayResults: any[];
  paginatedResults: any[];
  filterText: string;
  setFilterText: (val: string) => void;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  totalPages: number;
  visibleFields: any;
  loading: boolean;
  uniqueReferences: any;
  getFieldLabel: (field: string) => string;
  copyToClipboard: (mode: "completa" | "intermediaria" | "agrupada") => void;
  downloadAllImages: () => void;
  partId: string;
}

export const DataTable: React.FC<DataTableProps> = ({
  results,
  displayResults,
  paginatedResults,
  filterText,
  setFilterText,
  currentPage,
  setCurrentPage,
  totalPages,
  visibleFields,
  loading,
  uniqueReferences,
  getFieldLabel,
  copyToClipboard,
  downloadAllImages,
  partId,
}) => {
  const [fichaModalOpen, setFichaModalOpen] = useState(false);
  const [selectedFicha, setSelectedFicha] = useState<any>(null);
  
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryImages, setGalleryImages] = useState<string[]>([]);
  const [galleryTitle, setGalleryTitle] = useState("");

  // Fecha modais se an an busca for limpa
  React.useEffect(() => {
    if (results.length === 0) {
      setFichaModalOpen(false);
      setGalleryOpen(false);
    }
  }, [results.length]);

  const handleOpenFicha = (res: any) => {
    setSelectedFicha(res);
    setFichaModalOpen(true);
  };

  const handleOpenGallery = (res: any) => {
    const imgs = res.imagens && res.imagens.length > 0 
      ? res.imagens 
      : (res.imagem ? [res.imagem] : []);
    
    if (imgs.length === 0) return;
    
    setGalleryImages(imgs);
    setGalleryTitle(`${res.marca} - ${res.veiculo} ${res.modelo}`);
    setGalleryOpen(true);
  };

  const COLUMN_CONFIG = [
    {
      id: "marca",
      getHeader: () => getFieldLabel("marca"),
      render: (res: any) => (
        <td className="px-4 py-2 font-semibold text-primary uppercase whitespace-nowrap">
          {res.marca || res.provedor || "---"}
        </td>
      ),
    },
    {
      id: "veiculo",
      getHeader: () => getFieldLabel("veiculo"),
      render: (res: any) => (
        <td className="px-6 py-2 text-xs font-medium">{res.veiculo}</td>
      ),
    },
    {
      id: "modelo",
      getHeader: () => getFieldLabel("modelo"),
      render: (res: any) => <td className="px-6 py-2 text-xs">{res.modelo}</td>,
    },
    {
      id: "versao",
      getHeader: () => getFieldLabel("versao"),
      render: (res: any) => (
        <td className="px-6 py-2 text-xs text-slate-400 italic font-medium">
          {res.versao || "---"}
        </td>
      ),
    },
    {
      id: "motor",
      getHeader: () => getFieldLabel("motor"),
      render: (res: any) => (
        <td className="px-4 py-2 font-bold text-slate-600 dark:text-slate-200 whitespace-nowrap">
          {res.motor}
        </td>
      ),
    },
    {
      id: "configuracao_motor",
      getHeader: () => getFieldLabel("configuracao_motor"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">
            {res.configuracao_motor || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "combustivel",
      getHeader: () => getFieldLabel("combustivel"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">
            {res.combustivel || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "ano",
      getHeader: () => getFieldLabel("ano"),
      render: (res: any) => (
        <td className="px-4 py-2 text-center font-mono bg-slate-50/50 dark:bg-slate-900/20 whitespace-nowrap">
          {res.ano_inicio || res.ano_fim ? (
            <div className="flex items-center justify-center gap-1">
              <span>{res.ano_inicio || ""}</span>
              <span className="text-slate-300">...</span>
              <span>{res.ano_fim || ""}</span>
            </div>
          ) : (
            "---"
          )}
        </td>
      ),
    },
    {
      id: "observacao",
      getHeader: () => getFieldLabel("observacao"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500">{res.observacao || "---"}</div>
        </td>
      ),
    },
    {
      id: "posicao",
      getHeader: () => getFieldLabel("posicao"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">
            {res.posicao || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "lado",
      getHeader: () => getFieldLabel("lado"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">{res.lado || "---"}</div>
        </td>
      ),
    },
    {
      id: "direcao",
      getHeader: () => getFieldLabel("direcao"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">
            {res.direcao || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "sistema_freio",
      getHeader: () => getFieldLabel("sistema_freio"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-500 uppercase">
            {res.sistema_freio || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "restricao",
      getHeader: () => getFieldLabel("restricao"),
      render: (res: any) => (
        <td className="px-6 py-2">
          <div className="text-slate-400 italic text-[10px]">
            {res.restricao || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "apenas",
      getHeader: () => getFieldLabel("apenas"),
      render: (res: any) => (
        <td className="px-4 py-2 font-black text-primary uppercase text-[10px] whitespace-nowrap">
          {res.apenas ? `★ ${res.apenas}` : "---"}
        </td>
      ),
    },
    {
      id: "referencias",
      getHeader: () => getFieldLabel("referencias"),
      render: (res: any) => {
        if (!res.referencias) return <td className="px-6 py-4 text-slate-300">---</td>;
        
        // Parser para display: Quebra por separadores e limpa
        const parts = res.referencias.split(/\s*(?:\||,|;|\n)\s*/).filter((p: string) => !!p.trim());
        const cleanedRefs = parts.map((p: string) => {
          const pair = p.split(/\s*(?::|-)\s*/);
          if (pair.length < 2) return p.trim();
          const brand = pair[0].trim().toUpperCase().replace(/\s+ORIGINAL$/g, "").replace(/^ORIGINAL\s+/g, "");
          const code = pair.slice(1).join(":").trim();
          return `${brand}: ${code}`;
        });

        return (
          <td className="px-4 py-4 min-w-[150px]">
            <div className="text-[10px] text-slate-500 max-w-[200px] leading-relaxed">
              {cleanedRefs.map((ref: string, idx: number) => (
                <div key={idx} className="whitespace-nowrap">{ref}</div>
              ))}
            </div>
          </td>
        );
      },
    },
    {
      id: "acoes",
      getHeader: () => "Ações",
      render: (res: any) => (
        <td className="px-4 py-2">
          <div className="flex items-center gap-1.5 justify-center">
            {/* Botão de Galeria de Imagens */}
            <button
              onClick={() => handleOpenGallery(res)}
              disabled={!res.imagem && (!res.imagens || res.imagens.length === 0)}
              className={`
                p-2 rounded-lg transition-all flex items-center justify-center
                ${(!res.imagem && (!res.imagens || res.imagens.length === 0)) 
                  ? 'text-slate-200 cursor-not-allowed' 
                  : 'bg-primary/5 text-primary hover:bg-primary/10 hover:scale-110 active:scale-95'}
              `}
              title="Ver Galeria de Imagens"
            >
              <Image size={18} />
            </button>

            {/* Botão de Ficha Técnica On-Demand */}
            <button
              onClick={() => handleOpenFicha(res)}
              className="p-2 bg-amber-500/5 text-amber-600 hover:bg-amber-500/10 hover:scale-110 active:scale-95 rounded-lg transition-all flex items-center justify-center"
              title="Ver Ficha Técnica"
            >
              <Zap size={18} />
            </button>
            
            {/* Link Externo (Opcional se houver raw_response com link) */}
            {res.url && (
               <a 
                href={res.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-2 bg-slate-100 text-slate-500 hover:bg-slate-200 rounded-lg transition-all flex items-center justify-center"
                title="Ver no site original"
               >
                 <ExternalLink size={16} />
               </a>
            )}
          </div>
        </td>
      ),
    },
  ];

  const handleExportExcel = () => {
    exportToExcel(displayResults, visibleFields, getFieldLabel, partId);
  };

  const handleExportPdf = () => {
    exportToPdf(displayResults, results, visibleFields, uniqueReferences, partId, COLUMN_CONFIG);
  };

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-800/50 rounded-2xl shadow-xl shadow-slate-100/50 dark:shadow-none overflow-hidden mt-6 transition-all">
      <div className="border-b border-slate-100 dark:border-slate-800">
        {/* Linha 1: Título + Filtro + Botões */}
        <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-col md:flex-row md:items-center gap-4 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-lg whitespace-nowrap">
                Resultados {partId ? `para ${partId}` : ""} ({displayResults.length})
              </h2>
            </div>

            {/* 🔍 FILTRO RÁPIDO */}
            {results.length > 0 && (
              <div className="flex-1 relative max-w-xs">
                <input
                  type="text"
                  placeholder="Filtrar nesta página..."
                  value={filterText}
                  onChange={(e) => {
                    setFilterText(e.target.value);
                    setCurrentPage(1); // Reseta para pág 1 ao filtrar
                  }}
                  className="w-full pl-3 pr-10 py-1.5 border border-slate-200 dark:border-slate-800 rounded-xl text-xs bg-slate-50/50 dark:bg-slate-900 focus:ring-1 focus:ring-primary outline-none transition-all"
                />
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            {results.length > 0 && (
              <button
                onClick={downloadAllImages}
                disabled={loading}
                className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-orange-500/10 text-orange-600 hover:bg-orange-500/20 transition-all border border-orange-500/20 disabled:opacity-50"
                title="Baixa todas as imagens no formato .zip"
              >
                {loading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <FileDown size={14} />
                )}
                Salvar Todas
              </button>
            )}
            <button
              onClick={() => copyToClipboard("completa")}
              className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20"
            >
              <Copy size={14} /> Copiar Tudo
            </button>

            {displayResults.length > 0 && (
              <>
                <button
                  onClick={handleExportExcel}
                  className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-green-500/10 text-green-600 hover:bg-green-500/20 transition-all border border-green-500/10"
                  title="Exportar para Excel"
                >
                  <FileSpreadsheet size={14} /> Excel
                </button>

                <button
                  onClick={handleExportPdf}
                  className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-red-500/10 text-red-600 hover:bg-red-500/20 transition-all border border-red-500/10"
                  title="Exportar para PDF"
                >
                  <FileText size={14} /> PDF
                </button>
              </>
            )}
          </div>
        </div>

        {/* Linha 2: Referências Cruzadas (Se houver) */}
        {Object.keys(uniqueReferences).length > 0 && (
          <div className="px-4 pb-4">
            <div className="flex flex-wrap gap-x-4 gap-y-1.5 items-center bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/50 rounded-xl px-3 py-2 text-xs w-full max-h-32 overflow-y-auto custom-scrollbar">
              <span className="text-[10px] font-black text-primary uppercase">
                Original:
              </span>
              {Object.entries(uniqueReferences).map(
                ([brand, codes]: [string, any]) => (
                  <div key={brand} className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">
                      {brand}
                    </span>
                    <span className="text-[10px] font-mono font-medium text-slate-700 dark:text-slate-300">
                      {Array.from(codes as Set<string>)
                        .sort()
                        .join(" - ")}
                    </span>
                  </div>
                ),
              )}
            </div>
          </div>
        )}
      </div>

      {/* Desktop Table View */}
      <div className="md:block hidden overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse table-auto">
          <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
            <tr>
              {COLUMN_CONFIG.filter(
                (col) => col.id === "acoes" || visibleFields[col.id as keyof typeof visibleFields]
              ).map((col) => (
                <th key={col.id} className="px-6 py-4 font-black">
                  {col.getHeader()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
            {displayResults.length === 0 ? (
              loading ? (
                // SKELETON LOADING
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {COLUMN_CONFIG.filter(
                      (col) => col.id === "acoes" || visibleFields[col.id as keyof typeof visibleFields]
                    ).map((col) => (
                      <td key={col.id} className="px-4 py-4">
                        <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded-lg w-full"></div>
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={12} className="px-6 py-12 text-center text-slate-400 italic">
                    Nenhum resultado para exibir.
                  </td>
                </tr>
              )
            ) : (
              paginatedResults.map((res, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-slate-50/50 dark:hover:bg-primary/5 transition-colors text-[11px] group"
                >
                  {COLUMN_CONFIG.filter(
                    (col) => col.id === "acoes" || visibleFields[col.id as keyof typeof visibleFields]
                  ).map((col) => (
                    <React.Fragment key={col.id}>
                      {col.render(res)}
                    </React.Fragment>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden block divide-y divide-slate-100 dark:divide-slate-800">
        {displayResults.length === 0 ? (
          loading ? (
            // MOBILE SKELETON LOADING
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="p-4 space-y-3 animate-pulse border-b border-slate-100 dark:border-slate-800">
                <div className="flex justify-between">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
                </div>
                <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
                <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center text-slate-400 italic">
              Nenhum resultado para exibir.
            </div>
          )
        ) : (
          paginatedResults.map((res, idx) => (
            <div
              key={idx}
              className="p-4 space-y-3 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black bg-primary/10 text-primary px-1.5 py-0.5 rounded uppercase">
                      {res.marca}
                    </span>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      {res.veiculo}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                    {res.modelo} • {res.motor}
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

              {/* Botões de Ação Mobile */}
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
          ))
        )}
      </div>

      {/* 🧭 PAGINAÇÃO FOOTER */}
      {displayResults.length > 0 && (
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-4 bg-slate-50/50 dark:bg-slate-900/10">
          <div className="text-xs text-slate-500">
             Mostrando <span className="font-bold text-slate-700 dark:text-slate-200">{paginatedResults.length}</span> de <span className="font-bold">{displayResults.length}</span> itens
          </div>
          <div className="flex items-center gap-2">
             <button 
               onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
               disabled={currentPage === 1}
               className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
             >
               &lt; Anterior
             </button>
             <span className="text-xs font-medium text-slate-500">
               Página <span className="font-bold text-slate-900 dark:text-white">{currentPage}</span> de {totalPages}
             </span>
             <button 
               onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
               disabled={currentPage === totalPages}
               className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
             >
               Próxima &gt;
             </button>
          </div>
        </div>
      )}

      <FichaTecnicaModal 
        isOpen={fichaModalOpen} 
        onClose={() => setFichaModalOpen(false)} 
        item={selectedFicha} 
        partId={partId}
      />

      <ImageGalleryModal
        isOpen={galleryOpen}
        onClose={() => setGalleryOpen(false)}
        images={galleryImages}
        title={galleryTitle}
      />
    </div>
  );
};
