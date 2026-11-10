import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterSection } from './FilterSection';

describe('FilterSection (Home Principal) Component', () => {
  const defaultVisibleFields = {
    marca: true,
    codigo: true,
    produto: true,
    ano: false,
  };

  const mockGetFieldLabel = (field: string) => {
    const labels: Record<string, string> = {
      marca: 'Marca',
      codigo: 'Código',
      produto: 'Produto',
      ano: 'Ano',
    };
    return labels[field] || field;
  };

  it('renders visible field toggles with correct labels', () => {
    const setVisibleFields = vi.fn();
    const setAgrupar = vi.fn();
    const copyToClipboard = vi.fn();
    const clearResults = vi.fn();
    const saveCurrentAsDefault = vi.fn();
    const restoreDefault = vi.fn();
    const setSelectedCodigo = vi.fn();

    render(
      <FilterSection
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
        uniqueCodigos={[]}
        selectedCodigo=""
        setSelectedCodigo={setSelectedCodigo}
      />
    );

    expect(screen.getByText('Marca')).toBeInTheDocument();
    expect(screen.getByText('Código')).toBeInTheDocument();
    expect(screen.getByText('Produto')).toBeInTheDocument();
    expect(screen.getByText('Ano')).toBeInTheDocument();
  });

  it('triggers clearResults callback on clicking clear button', () => {
    const setVisibleFields = vi.fn();
    const setAgrupar = vi.fn();
    const copyToClipboard = vi.fn();
    const clearResults = vi.fn();
    const saveCurrentAsDefault = vi.fn();
    const restoreDefault = vi.fn();
    const setSelectedCodigo = vi.fn();

    render(
      <FilterSection
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
        uniqueCodigos={[]}
        selectedCodigo=""
        setSelectedCodigo={setSelectedCodigo}
      />
    );

    const clearButton = screen.getByTitle('Limpar todos os resultados da busca');
    fireEvent.click(clearButton);

    expect(clearResults).toHaveBeenCalledTimes(1);
  });

  it('toggles agrupar state on click', () => {
    const setVisibleFields = vi.fn();
    const setAgrupar = vi.fn();
    const copyToClipboard = vi.fn();
    const clearResults = vi.fn();
    const saveCurrentAsDefault = vi.fn();
    const restoreDefault = vi.fn();
    const setSelectedCodigo = vi.fn();

    render(
      <FilterSection
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
        uniqueCodigos={[]}
        selectedCodigo=""
        setSelectedCodigo={setSelectedCodigo}
      />
    );

    const agruparButton = screen.getByText('Agrupar');
    fireEvent.click(agruparButton);

    expect(setAgrupar).toHaveBeenCalledTimes(1);
  });
});
