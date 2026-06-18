import React, { useState } from "react";
import { Copy, FileDown, Loader2, FileSpreadsheet, FileText, SearchX, ShoppingBag, ChevronDown, Settings } from "lucide-react";
import { FichaTecnicaModal } from "./FichaTecnicaModal";
import { ImageGalleryModal } from "./ImageGalleryModal";
import { MercadoLivreModal } from "./MercadoLivreModal";
import { exportToExcel, exportToPdf } from "../../utils/exportUtils";
import { exportToCerttus } from "../../utils/certtusExport";
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
  copyToClipboard: (
    mode: "completa" | "intermediaria" | "agrupada" | "tabela" | "tabela_limpa" | "tabela_tabulada",
    erpFont?: string,
    erpFontSize?: number
  ) => void;
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

  const [fontOption, setFontOption] = useState<string>("monospace");
  const [customFont, setCustomFont] = useState<string>("");
  const [erpFontSize, setErpFontSize] = useState<number>(9);
  const [hideDashesRow, setHideDashesRow] = useState<boolean>(true);
  const [mlModalOpen, setMlModalOpen] = useState(false);

  // States para o novo layout Detox
  const [exportOpen, setExportOpen] = useState(false);
  const [copyOpen, setCopyOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const exportRef = React.useRef<HTMLDivElement>(null);
  const copyRef = React.useRef<HTMLDivElement>(null);

  const actualErpFont = fontOption === "custom" ? customFont : fontOption;

  // Fecha modais se a busca for limpa
  React.useEffect(() => {
    if (results.length === 0) {
      setFichaModalOpen(false);
      setGalleryOpen(false);
      setMlModalOpen(false);
      setSettingsOpen(false);
    }
  }, [results.length]);

  // Click outside para fechar os dropdowns
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(event.target as Node)) setExportOpen(false);
      if (copyRef.current && !copyRef.current.contains(event.target as Node)) setCopyOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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
      id: "codigo",
      getHeader: () => getFieldLabel("codigo"),
      render: (res: any) => (
        <td className="px-4 py-2 font-mono text-xs font-bold text-slate-700 dark:text-slate-200 whitespace-nowrap">
          {res.codigo || "---"}
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
          // Separa apenas pelo PRIMEIRO sinal de dois pontos
          const firstColonIdx = p.indexOf(":");
          if (firstColonIdx === -1) return p.trim();

          const brand = p.slice(0, firstColonIdx).trim().toUpperCase()
            .replace(/\s+ORIGINAL$/g, "")
            .replace(/^ORIGINAL\s+/g, "");
          const code = p.slice(firstColonIdx + 1).trim();

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
      id: "ficha_tecnica",
      getHeader: () => getFieldLabel("ficha_tecnica"),
      render: (res: any) => {
        if (!res.ficha_tecnica || Object.keys(res.ficha_tecnica).length === 0) 
          return <td className="px-6 py-4 text-slate-300">---</td>;

        return (
          <td className="px-4 py-4 min-w-[180px]">
            <div className="flex flex-col gap-1">
              {Object.entries(res.ficha_tecnica).map(([label, value]: [string, any], idx: number) => (
                <div key={idx} className="flex items-center gap-1.5 text-[10px] leading-tight">
                  <span className="font-bold text-slate-500 uppercase shrink-0">{label}:</span>
                  <span className="text-primary font-medium uppercase">{String(value)}</span>
                </div>
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

  const handleExportCerttus = () => {
    exportToCerttus(displayResults, partId);
  };

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-800/50 rounded-2xl shadow-xl shadow-slate-100/50 dark:shadow-none overflow-hidden mt-6 transition-all">
      <div className="border-b border-slate-100 dark:border-slate-800">
        {/* Linha 1: Título + Filtro + Botões */}
        <div className="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
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

          <div className="flex flex-col sm:flex-row items-center justify-end gap-3 w-full lg:w-auto mt-4 lg:mt-0">
            {results.length > 0 && (
              <div className="flex w-full sm:w-auto items-center gap-2">
                
                {/* 📥 EXPORTAR DROPDOWN */}
                <div className="relative w-full sm:w-auto" ref={exportRef}>
                  <button 
                    onClick={() => { setExportOpen(!exportOpen); setCopyOpen(false); }}
                    className="flex items-center justify-between gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 transition-all border border-slate-500/20 dark:text-slate-400 w-full sm:w-auto"
                  >
                    <div className="flex items-center gap-2">
                      <FileDown size={14} /> Exportar / Salvar
                    </div>
                    <ChevronDown size={14} className={`transition-transform ${exportOpen ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {exportOpen && (
                    <div className="absolute top-full right-0 mt-2 w-full sm:w-48 bg-white dark:bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-1.5 z-50 flex flex-col gap-1">
                      <button onClick={() => { handleExportExcel(); setExportOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <FileSpreadsheet size={14} className="text-green-600" /> Excel
                      </button>
                      <button onClick={() => { handleExportPdf(); setExportOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <FileText size={14} className="text-red-600" /> PDF
                      </button>
                      <button onClick={() => { handleExportCerttus(); setExportOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <FileSpreadsheet size={14} className="text-cyan-600" /> Layout Certtus
                      </button>
                      <button onClick={() => { downloadAllImages(); setExportOpen(false); }} disabled={loading} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 disabled:opacity-50 transition-colors">
                        {loading ? <Loader2 size={14} className="animate-spin text-orange-600" /> : <Image size={14} className="text-orange-600" />} Imagens ZIP
                      </button>
                    </div>
                  )}
                </div>

                {/* 📋 COPIAR DROPDOWN */}
                <div className="relative w-full sm:w-auto" ref={copyRef}>
                  <button 
                    onClick={() => { setCopyOpen(!copyOpen); setExportOpen(false); }}
                    className="flex items-center justify-between gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 transition-all border border-slate-500/20 dark:text-slate-400 w-full sm:w-auto"
                  >
                    <div className="flex items-center gap-2">
                      <Copy size={14} /> Copiar Grades
                    </div>
                    <ChevronDown size={14} className={`transition-transform ${copyOpen ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {copyOpen && (
                    <div className="absolute top-full right-0 mt-2 w-full sm:w-56 bg-white dark:bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-1.5 z-50 flex flex-col gap-1">
                      <button onClick={() => { copyToClipboard("tabela", actualErpFont, erpFontSize, hideDashesRow); setCopyOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <Copy size={14} className="text-slate-500" /> Grade WhatsApp
                      </button>
                      <button onClick={() => { copyToClipboard("tabela_limpa", actualErpFont, erpFontSize, hideDashesRow); setCopyOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <Copy size={14} className="text-emerald-600" /> Tabela ERP (Limpa)
                      </button>
                      <button onClick={() => { copyToClipboard("tabela_tabulada", actualErpFont, erpFontSize, hideDashesRow); setCopyOpen(false); }} className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors">
                        <Copy size={14} className="text-amber-600" /> Tabulado ERP
                      </button>
                    </div>
                  )}
                </div>

                {/* ⚙️ CONFIGURAÇÕES DE FONTE */}
                <button
                  onClick={() => setSettingsOpen(!settingsOpen)}
                  className={`flex items-center justify-center p-2.5 rounded-xl transition-all border ${settingsOpen ? 'bg-slate-800/80 text-white border-slate-800/50' : 'bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 border-slate-500/20 dark:text-slate-400'}`}
                  title="Ajustes avançados de Fonte ERP"
                >
                  <Settings size={16} className={`transition-transform duration-500 ${settingsOpen ? 'rotate-90' : ''}`} />
                </button>
              </div>
            )}
            
            {/* 🛒 AÇÕES PRINCIPAIS (Destaque) */}
            {displayResults.length > 0 && (
              <div className="flex w-full sm:w-auto items-center gap-2 pl-0 lg:pl-2 lg:border-l lg:border-slate-200/50 dark:lg:border-slate-700/50">
                <button
                  onClick={() => copyToClipboard("completa")}
                  className="flex flex-1 items-center justify-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20 whitespace-nowrap"
                >
                  <Copy size={14} /> Copiar Tudo
                </button>
                <button
                  onClick={() => setMlModalOpen(true)}
                  className="flex flex-1 items-center justify-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500/20 transition-all border border-yellow-500/20 whitespace-nowrap"
                >
                  <ShoppingBag size={14} /> Anúncio ML
                </button>
              </div>
            )}
          </div>
        </div>

        {/* ⚙️ PAINEL DE AJUSTE DE FONTE PARA ERP (CANVAS PROPORCIONAL) */}
        {settingsOpen && results.length > 0 && (
          <div className="mx-4 mb-4 p-3 bg-slate-50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-800/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 transition-all">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-black text-slate-700 dark:text-slate-200 flex items-center gap-1.5 uppercase">
                ⚙️ Ajuste de Alinhamento para a Fonte do ERP
              </span>
              <span className="text-[10px] text-slate-400">
                Se as colunas quebrarem ao colar no seu ERP (fonte proporcional), escolha a fonte exata dele abaixo para compensar os tamanhos.
              </span>
            </div>
            
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              {/* Seletor de Fonte */}
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Fonte:</span>
                <select
                  value={fontOption}
                  onChange={(e) => setFontOption(e.target.value)}
                  className="text-xs border border-slate-200 dark:border-slate-800 rounded-lg px-2 py-1 bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-200 focus:ring-1 focus:ring-primary outline-none cursor-pointer"
                >
                  <option value="monospace">Monospace (Padrão Reto)</option>
                  <option value="Segoe UI">Segoe UI (Windows Moderno)</option>
                  <option value="Tahoma">Tahoma (Delphi / Clássico)</option>
                  <option value="Microsoft Sans Serif">MS Sans Serif (Legacy)</option>
                  <option value="Arial">Arial</option>
                  <option value="Calibri">Calibri</option>
                  <option value="custom">Outra Fonte...</option>
                </select>
              </div>

              {/* Input de Fonte Customizada */}
              {fontOption === "custom" && (
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    placeholder="Ex: Trebuchet MS"
                    value={customFont}
                    onChange={(e) => setCustomFont(e.target.value)}
                    className="text-xs border border-slate-200 dark:border-slate-800 rounded-lg px-2 py-1 bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-200 focus:ring-1 focus:ring-primary outline-none w-36"
                    title="Digite o nome exato da fonte instalada no seu Windows (ex: Trebuchet MS, MS Sans Serif, etc.)"
                  />
                </div>
              )}

              {/* Seletor de Tamanho */}
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Tam (pt):</span>
                <input
                  type="number"
                  min="6"
                  max="20"
                  value={erpFontSize}
                  onChange={(e) => setErpFontSize(Number(e.target.value))}
                  className="text-xs border border-slate-200 dark:border-slate-800 rounded-lg px-2 py-1 bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-200 focus:ring-1 focus:ring-primary outline-none w-14 text-center font-semibold"
                />
              </div>
            </div>
          </div>
        )}

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
        <table className="w-full text-left border-collapse table-auto relative">
          <thead className="bg-slate-50/95 dark:bg-slate-800/95 text-slate-500 uppercase text-[10px] font-bold tracking-wider sticky top-0 z-10 backdrop-blur-md shadow-sm">
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
                  <td colSpan={12} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-14 h-14 bg-amber-500/10 rounded-2xl flex items-center justify-center">
                        <SearchX size={28} className="text-amber-500" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-600 dark:text-slate-300">
                          Nenhum produto encontrado{partId ? ` para "${partId}"` : "."}
                        </p>
                        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
                          A busca foi realizada com sucesso no servidor, mas o provedor não retornou resultados.
                          Verifique se o <strong>código está correto</strong> ou tente outro provedor.
                          Verifique se o <strong>código está correto</strong> ou tente outro provedor.
                        </p>
                      </div>
                    </div>
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
            <div className="px-6 py-12 text-center">
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
                      {Object.entries(res.ficha_tecnica).map(([label, value]: [string, any], idx: number) => (
                        <div key={idx} className="flex items-center gap-1 uppercase">
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
          <div className="flex items-center gap-1.5 md:gap-2">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="px-2 md:px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              title="Primeira Página"
            >
              &lt;&lt;
            </button>
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-2 md:px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              &lt; Ant
            </button>
            <span className="text-xs font-medium text-slate-500 whitespace-nowrap">
              Pág <span className="font-bold text-slate-900 dark:text-white">{currentPage}</span> de {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-2 md:px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Próx &gt;
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-2 md:px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              title="Última Página"
            >
              &gt;&gt;
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

      <MercadoLivreModal
        isOpen={mlModalOpen}
        onClose={() => setMlModalOpen(false)}
        displayResults={results}
        partId={partId}
        uniqueReferences={uniqueReferences}
      />
    </div>
  );
};
