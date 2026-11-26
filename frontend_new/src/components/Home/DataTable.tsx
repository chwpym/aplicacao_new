import React, { useState, useEffect } from "react";
import { FichaTecnicaModal } from "./FichaTecnicaModal";
import { ImageGalleryModal } from "./ImageGalleryModal";
import { MercadoLivreModal } from "./MercadoLivreModal";
import { exportToExcel, exportToPdf } from "../../utils/exportUtils";
import { exportToCerttus } from "../../utils/certtusExport";
import {
  TableToolbar,
  TableReferencesBar,
  TableDesktopView,
  TableMobileView,
  TablePagination,
  buildColumnConfig,
} from "./data-table";

// Helper para URL de proxy de imagem (evita bloqueio de CORS / hotlink)
const proxyImageUrl = (url: string): string => {
  if (!url || !url.startsWith("http")) return url;
  return `http://localhost:8000/search/proxy/image?url=${encodeURIComponent(url)}`;
};

export interface DataTableProps {
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
    mode: "completa" | "intermediaria" | "agrupada" | "tabela" | "tabela_limpa" | "tabela_tabulada" | "etiqueta" | "excel" | "similares",
    erpFont?: string,
    erpFontSize?: number,
    hideDashesRow?: boolean
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
  const [hideDashesRow] = useState<boolean>(true);

  const [mlModalOpen, setMlModalOpen] = useState(false);
  const [mlCleanMode, setMlCleanMode] = useState(false);

  const actualErpFont = fontOption === "custom" ? customFont : fontOption;

  // Fecha modais se a busca for limpa
  useEffect(() => {
    if (results.length === 0) {
      setFichaModalOpen(false);
      setGalleryOpen(false);
      setMlModalOpen(false);
    }
  }, [results.length]);

  const handleOpenFicha = (res: any) => {
    setSelectedFicha(res);
    setFichaModalOpen(true);
  };

  const handleOpenGallery = (res: any) => {
    const imgs =
      res.imagens && res.imagens.length > 0
        ? res.imagens
        : res.imagem
        ? [res.imagem]
        : [];

    if (imgs.length === 0) return;

    setGalleryImages(imgs);
    setGalleryTitle(`${res.marca || res.provedor || "N/A"} - ${res.codigo}`);
    setGalleryOpen(true);
  };

  const columns = buildColumnConfig({
    getFieldLabel,
    handleOpenGallery,
    handleOpenFicha,
    proxyImageUrl,
  });

  const handleExportExcel = () => {
    exportToExcel(displayResults, visibleFields, getFieldLabel, partId);
  };

  const handleExportPdf = () => {
    exportToPdf(displayResults, results, visibleFields, uniqueReferences, partId, columns as any);
  };

  const handleExportCerttus = () => {
    exportToCerttus(displayResults, partId);
  };

  const changePageWithTransition = (newPage: number) => {
    if (typeof document !== "undefined" && "startViewTransition" in document) {
      (document as any).startViewTransition(() => {
        setCurrentPage(newPage);
      });
    } else {
      setCurrentPage(newPage);
    }
  };

  const handleOpenMlModal = (cleanMode: boolean) => {
    setMlCleanMode(cleanMode);
    setMlModalOpen(true);
  };

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-800/50 rounded-2xl shadow-xl shadow-slate-100/50 dark:shadow-none overflow-hidden mt-6">
      <div className="border-b border-slate-100 dark:border-slate-800">
        <TableToolbar
          results={results}
          displayResults={displayResults}
          partId={partId}
          filterText={filterText}
          setFilterText={setFilterText}
          setCurrentPage={setCurrentPage}
          loading={loading}
          handleExportExcel={handleExportExcel}
          handleExportPdf={handleExportPdf}
          handleExportCerttus={handleExportCerttus}
          downloadAllImages={downloadAllImages}
          copyToClipboard={copyToClipboard}
          actualErpFont={actualErpFont}
          erpFontSize={erpFontSize}
          setErpFontSize={setErpFontSize}
          fontOption={fontOption}
          setFontOption={setFontOption}
          customFont={customFont}
          setCustomFont={setCustomFont}
          hideDashesRow={hideDashesRow}
          onOpenMlModal={handleOpenMlModal}
        />

        <TableReferencesBar uniqueReferences={uniqueReferences} />
      </div>

      <TableDesktopView
        columns={columns}
        visibleFields={visibleFields}
        displayResults={displayResults}
        paginatedResults={paginatedResults}
        loading={loading}
        partId={partId}
      />

      <TableMobileView
        displayResults={displayResults}
        paginatedResults={paginatedResults}
        visibleFields={visibleFields}
        loading={loading}
        partId={partId}
        getFieldLabel={getFieldLabel}
        handleOpenGallery={handleOpenGallery}
        handleOpenFicha={handleOpenFicha}
        proxyImageUrl={proxyImageUrl}
      />

      <TablePagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={displayResults.length}
        pageItemsCount={paginatedResults.length}
        onPageChange={changePageWithTransition}
      />

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
        displayResults={displayResults}
        partId={partId}
        uniqueReferences={uniqueReferences}
        cleanMode={mlCleanMode}
      />
    </div>
  );
};
