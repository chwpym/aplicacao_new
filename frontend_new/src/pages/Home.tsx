
import { SearchSection } from "../components/Home/SearchSection";
import { FilterSection } from "../components/Home/FilterSection";
import { DataTable } from "../components/Home/DataTable";
import { useCatalog } from "../hooks/useCatalog";

const Home = () => {
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
  } = useCatalog();

  return (
    <div className="space-y-6 pb-20">
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
