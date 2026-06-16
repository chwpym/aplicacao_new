import { SearchSection } from "../components/Home/SearchSection";
import { FilterSectionTable } from "../components/HomeTable/FilterSectionTable";
import { DataTableTable } from "../components/HomeTable/DataTableTable";
import { useCatalogTable } from "../hooks/useCatalogTable";

const HomeTable = () => {
  const {
    partId,
    setPartId,
    loading,
    results,
    provedores,
    selectedProvedor,
    setSelectedProvedor,
    agrupar,
    setAgrupar,
    visibleFields,
    setVisibleFields,
    saveCurrentAsDefault,
    restoreDefault,
    uniqueReferences,
    displayResults,
    paginatedResults,
    filterText,
    setFilterText,
    currentPage,
    setCurrentPage,
    totalPages,
    handleSearch,
    getFieldLabel,
    copyToClipboard,
    clearResults,
    downloadAllImages,
    cancelSearch,
  } = useCatalogTable();

  return (
    <div className="space-y-6 pb-20">
      <div className="bg-primary/10 border border-primary/20 text-primary px-4 py-3 rounded-2xl text-xs font-semibold flex items-center justify-between">
        <span>🛠️ Você está visualizando a página de teste isolada do recurso <strong>Cópia de Tabela Inteligente</strong>.</span>
        <span className="text-[10px] uppercase font-bold bg-primary text-white px-2 py-0.5 rounded-lg shadow-sm">Ambiente de Teste</span>
      </div>

      <SearchSection
        partId={partId}
        setPartId={setPartId}
        selectedProvedor={selectedProvedor}
        setSelectedProvedor={setSelectedProvedor}
        provedores={provedores}
        loading={loading}
        handleSearch={handleSearch}
        cancelSearch={cancelSearch}
      />
      
      <FilterSectionTable
        visibleFields={visibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={agrupar}
        setAgrupar={setAgrupar}
        getFieldLabel={getFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
      />
      
      <DataTableTable
        results={results}
        displayResults={displayResults}
        paginatedResults={paginatedResults}
        filterText={filterText}
        setFilterText={setFilterText}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        totalPages={totalPages}
        visibleFields={visibleFields}
        loading={loading}
        uniqueReferences={uniqueReferences}
        getFieldLabel={getFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
        partId={partId}
      />
    </div>
  );
};

export default HomeTable;
