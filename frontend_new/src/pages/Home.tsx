import { useEffect } from 'react';
import { SearchSection } from "../components/Home/SearchSection";
import { FilterSection } from "../components/Home/FilterSection";
import { DataTable } from "../components/Home/DataTable";
import { useCatalog } from "../hooks/useCatalog";
import AlertModal from "../components/AlertModal";

const Home = () => {
  const {
    partId,
    setPartId,
    loading,
    results,
    provedores,
    selectedProvedor,
    setSelectedProvedor,
    searchInputRef,
    agrupar,
    setAgrupar,
    visibleFields,
    setVisibleFields,
    saveCurrentAsDefault,
    restoreDefault,
    uniqueCodigos,
    selectedCodigo,
    setSelectedCodigo,
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
    alertConfig,
    setAlertConfig,
  } = useCatalog();

  useEffect(() => {
    if (selectedProvedor) {
      const p = provedores.find(prov => String(prov.id) === String(selectedProvedor));
      if (p) {
        document.title = `Workspace - ${p.nome}`;
        return;
      }
    }
    document.title = "Workspace - Catálogo V4";
  }, [selectedProvedor, provedores]);

  return (
    <div className="space-y-6 pb-20">
      <AlertModal
        isOpen={alertConfig.isOpen}
        title={alertConfig.title}
        message={alertConfig.message}
        type={alertConfig.type}
        onClose={() => setAlertConfig({ ...alertConfig, isOpen: false })}
      />
      <SearchSection
        partId={partId}
        setPartId={setPartId}
        selectedProvedor={selectedProvedor}
        setSelectedProvedor={setSelectedProvedor}
        provedores={provedores}
        loading={loading}
        handleSearch={handleSearch}
        cancelSearch={cancelSearch}
        inputRef={searchInputRef}
      />
      
      <FilterSection
        visibleFields={visibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={agrupar}
        setAgrupar={setAgrupar}
        getFieldLabel={getFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
        uniqueCodigos={uniqueCodigos}
        selectedCodigo={selectedCodigo}
        setSelectedCodigo={setSelectedCodigo}
      />
      
      <DataTable
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

export default Home;
