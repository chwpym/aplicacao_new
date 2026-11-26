import React, { useState, useRef, useEffect } from "react";
import {
  Copy,
  FileDown,
  Loader2,
  FileSpreadsheet,
  FileText,
  ShoppingBag,
  ChevronDown,
  Settings,
  Printer,
  Image,
} from "lucide-react";

interface TableToolbarProps {
  results: any[];
  displayResults: any[];
  partId: string;
  filterText: string;
  setFilterText: (val: string) => void;
  setCurrentPage: (page: number) => void;
  loading: boolean;
  handleExportExcel: () => void;
  handleExportPdf: () => void;
  handleExportCerttus: () => void;
  downloadAllImages: () => void;
  copyToClipboard: (
    mode: "completa" | "intermediaria" | "agrupada" | "tabela" | "tabela_limpa" | "tabela_tabulada" | "etiqueta" | "excel" | "similares",
    erpFont?: string,
    erpFontSize?: number,
    hideDashesRow?: boolean
  ) => void;
  actualErpFont: string;
  erpFontSize: number;
  setErpFontSize: (size: number) => void;
  fontOption: string;
  setFontOption: (opt: string) => void;
  customFont: string;
  setCustomFont: (font: string) => void;
  hideDashesRow: boolean;
  onOpenMlModal: (cleanMode: boolean) => void;
}

export const TableToolbar: React.FC<TableToolbarProps> = ({
  results,
  displayResults,
  partId,
  filterText,
  setFilterText,
  setCurrentPage,
  loading,
  handleExportExcel,
  handleExportPdf,
  handleExportCerttus,
  downloadAllImages,
  copyToClipboard,
  actualErpFont,
  erpFontSize,
  setErpFontSize,
  fontOption,
  setFontOption,
  customFont,
  setCustomFont,
  hideDashesRow,
  onOpenMlModal,
}) => {
  const [exportOpen, setExportOpen] = useState(false);
  const [copyOpen, setCopyOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [mlMenuOpen, setMlMenuOpen] = useState(false);

  const exportRef = useRef<HTMLDivElement>(null);
  const copyRef = useRef<HTMLDivElement>(null);
  const mlMenuRef = useRef<HTMLDivElement>(null);

  // Fecha menus com Escape ou clique fora
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setExportOpen(false);
        setCopyOpen(false);
        setMlMenuOpen(false);
        setSettingsOpen(false);
      }
    };
    const handleClickOutside = (event: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(event.target as Node)) setExportOpen(false);
      if (copyRef.current && !copyRef.current.contains(event.target as Node)) setCopyOpen(false);
      if (mlMenuRef.current && !mlMenuRef.current.contains(event.target as Node)) setMlMenuOpen(false);
    };
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <>
      <div className="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Título + Filtro de busca rápida */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
          <div className="flex items-center gap-2">
            <h2 className="font-bold text-lg whitespace-nowrap">
              Resultados {partId ? `para ${partId}` : ""} ({displayResults.length})
            </h2>
          </div>

          {results.length > 0 && (
            <div className="flex-1 relative max-w-xs">
              <input
                type="text"
                placeholder="Filtrar nesta página..."
                value={filterText}
                onChange={(e) => {
                  setFilterText(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-3 pr-10 py-1.5 border border-slate-200 dark:border-slate-800 rounded-xl text-xs bg-slate-50/50 dark:bg-slate-900 focus:ring-1 focus:ring-primary outline-none transition-all"
              />
            </div>
          )}
        </div>

        {/* Dropdowns e Ações */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 w-full lg:w-auto mt-4 lg:mt-0">
          {results.length > 0 && (
            <div className="flex w-full sm:w-auto items-center gap-2">
              {/* 📥 EXPORTAR DROPDOWN */}
              <div className="relative w-full sm:w-auto" ref={exportRef}>
                <button
                  onClick={() => {
                    setExportOpen(!exportOpen);
                    setCopyOpen(false);
                    setMlMenuOpen(false);
                  }}
                  aria-expanded={exportOpen}
                  aria-haspopup="true"
                  className="flex items-center justify-between gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 transition-all border border-slate-500/20 dark:text-slate-400 w-full sm:w-auto"
                >
                  <div className="flex items-center gap-2">
                    <FileDown size={14} /> Exportar / Salvar
                  </div>
                  <ChevronDown
                    size={14}
                    className={`transition-transform ${exportOpen ? "rotate-180" : ""}`}
                  />
                </button>

                {exportOpen && (
                  <div className="absolute top-full right-0 mt-2 w-full sm:w-48 bg-white dark:bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-1.5 z-50 flex flex-col gap-1">
                    <button
                      onClick={() => {
                        handleExportExcel();
                        setExportOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <FileSpreadsheet size={14} className="text-green-600" /> Excel
                    </button>
                    <button
                      onClick={() => {
                        handleExportPdf();
                        setExportOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <FileText size={14} className="text-red-600" /> PDF
                    </button>
                    <button
                      onClick={() => {
                        handleExportCerttus();
                        setExportOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <FileSpreadsheet size={14} className="text-cyan-600" /> Layout Certtus
                    </button>
                    <button
                      onClick={() => {
                        downloadAllImages();
                        setExportOpen(false);
                      }}
                      disabled={loading}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 disabled:opacity-50 transition-colors"
                    >
                      {loading ? (
                        <Loader2 size={14} className="animate-spin text-orange-600" />
                      ) : (
                        <Image size={14} className="text-orange-600" />
                      )}{" "}
                      Imagens ZIP
                    </button>
                  </div>
                )}
              </div>

              {/* 📋 COPIAR DROPDOWN */}
              <div className="relative w-full sm:w-auto" ref={copyRef}>
                <button
                  onClick={() => {
                    setCopyOpen(!copyOpen);
                    setExportOpen(false);
                    setMlMenuOpen(false);
                  }}
                  aria-expanded={copyOpen}
                  aria-haspopup="true"
                  className="flex items-center justify-between gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 transition-all border border-slate-500/20 dark:text-slate-400 w-full sm:w-auto"
                >
                  <div className="flex items-center gap-2">
                    <Copy size={14} /> Copiar Grades
                  </div>
                  <ChevronDown
                    size={14}
                    className={`transition-transform ${copyOpen ? "rotate-180" : ""}`}
                  />
                </button>

                {copyOpen && (
                  <div className="absolute top-full right-0 mt-2 w-full sm:w-56 bg-white dark:bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-1.5 z-50 flex flex-col gap-1">
                    <button
                      onClick={() => {
                        copyToClipboard("tabela", actualErpFont, erpFontSize, hideDashesRow);
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <Copy size={14} className="text-slate-500" /> Grade WhatsApp
                    </button>
                    <button
                      onClick={() => {
                        copyToClipboard("tabela_limpa", actualErpFont, erpFontSize, hideDashesRow);
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <Copy size={14} className="text-emerald-600" /> Tabela ERP (Limpa)
                    </button>
                    <button
                      onClick={() => {
                        copyToClipboard("tabela_tabulada", actualErpFont, erpFontSize, hideDashesRow);
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <Copy size={14} className="text-amber-600" /> Tabulado ERP
                    </button>
                    <div className="h-px bg-slate-200 dark:bg-slate-700/50 my-1"></div>
                    <button
                      onClick={() => {
                        copyToClipboard("excel", actualErpFont, erpFontSize, hideDashesRow);
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <FileSpreadsheet size={14} className="text-green-600" /> Excel / Word (HTML)
                    </button>
                    <button
                      onClick={() => {
                        copyToClipboard("similares");
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <Copy size={14} className="text-blue-600" /> Apenas Similares
                    </button>
                    <div className="h-px bg-slate-200 dark:bg-slate-700/50 my-1"></div>
                    <button
                      onClick={() => {
                        copyToClipboard("etiqueta");
                        setCopyOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <Printer size={14} className="text-purple-600" /> Etiqueta (ZPL)
                    </button>
                  </div>
                )}
              </div>

              {/* ⚙️ CONFIGURAÇÕES DE FONTE ERP */}
              <button
                onClick={() => setSettingsOpen(!settingsOpen)}
                className={`flex items-center justify-center p-2.5 rounded-xl transition-all border ${
                  settingsOpen
                    ? "bg-slate-800/80 text-white border-slate-800/50"
                    : "bg-slate-500/10 text-slate-600 hover:bg-slate-500/20 border-slate-500/20 dark:text-slate-400"
                }`}
                title="Ajustes avançados de Fonte ERP"
              >
                <Settings
                  size={16}
                  className={`transition-transform duration-500 ${settingsOpen ? "rotate-90" : ""}`}
                />
              </button>
            </div>
          )}

          {/* 🛒 AÇÕES PRINCIPAIS */}
          {displayResults.length > 0 && (
            <div className="flex w-full sm:w-auto items-center gap-2 pl-0 lg:pl-2 lg:border-l lg:border-slate-200/50 dark:lg:border-slate-700/50">
              <button
                onClick={() => copyToClipboard("completa")}
                className="flex flex-1 items-center justify-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20 whitespace-nowrap"
              >
                <Copy size={14} /> Copiar Tudo
              </button>
              <div className="relative flex-1" ref={mlMenuRef}>
                <button
                  onClick={() => {
                    setMlMenuOpen(!mlMenuOpen);
                    setExportOpen(false);
                    setCopyOpen(false);
                  }}
                  aria-expanded={mlMenuOpen}
                  aria-haspopup="true"
                  className="flex w-full items-center justify-between gap-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500/20 transition-all border border-yellow-500/20 whitespace-nowrap"
                >
                  <div className="flex items-center gap-2">
                    <ShoppingBag size={14} /> Anúncio ML
                  </div>
                  <ChevronDown
                    size={14}
                    className={`transition-transform ${mlMenuOpen ? "rotate-180" : ""}`}
                  />
                </button>

                {mlMenuOpen && (
                  <div className="absolute top-full right-0 mt-2 w-full sm:w-56 bg-white dark:bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-1.5 z-50 flex flex-col gap-1">
                    <button
                      onClick={() => {
                        onOpenMlModal(false);
                        setMlMenuOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <ShoppingBag size={14} className="text-yellow-600" /> ML (Com Ícones)
                    </button>
                    <button
                      onClick={() => {
                        onOpenMlModal(true);
                        setMlMenuOpen(false);
                      }}
                      className="flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg text-left text-slate-700 dark:text-slate-300 transition-colors"
                    >
                      <FileText size={14} className="text-emerald-600" /> ERP (Texto Limpo)
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* PAINEL DE AJUSTE DE FONTE PARA ERP */}
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

            {fontOption === "custom" && (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  placeholder="Ex: Trebuchet MS"
                  value={customFont}
                  onChange={(e) => setCustomFont(e.target.value)}
                  className="text-xs border border-slate-200 dark:border-slate-800 rounded-lg px-2 py-1 bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-200 focus:ring-1 focus:ring-primary outline-none w-36"
                  title="Digite o nome exato da fonte instalada no seu Windows"
                />
              </div>
            )}

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
    </>
  );
};
