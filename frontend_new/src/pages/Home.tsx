
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
    uniqueReferences,
    displayResults,
    handleSearch,
    getFieldLabel,
    copyToClipboard,
    clearResults,
    downloadAllImages,
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
      />
      
      <FilterSection
        visibleFields={visibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={agrupar}
        setAgrupar={setAgrupar}
        provedores={provedores}
        selectedProvedor={selectedProvedor}
        getFieldLabel={getFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
      />
      
      <DataTable
        results={results}
        displayResults={displayResults}
        visibleFields={visibleFields}
        loading={loading}
        uniqueReferences={uniqueReferences}
        getFieldLabel={getFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
      />
    </div>
  );
};

export default Home;
