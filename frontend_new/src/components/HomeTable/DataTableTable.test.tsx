import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTableTable } from './DataTableTable';

describe('DataTableTable Component', () => {
  const defaultVisibleFields = {
    marca: true,
    codigo: true,
    produto: true,
    modelo: true,
    motor: true,
    ano: true,
    combustivel: true,
    complemento: true,
    ficha_tecnica: true,
  };

  const mockGetFieldLabel = (field: string) => field.toUpperCase();

  const sampleResults = [
    {
      id: 1,
      marca: 'BOSCH',
      codigo: '0986BF0501',
      produto: 'Filtro de Óleo',
      modelo: 'Gol 1.0',
      motor: 'EA111',
      ano: '2008-2014',
      combustivel: 'Flex',
      complemento: '',
      ficha_tecnica: { Altura: '100mm' },
    },
  ];

  it('renders empty state when there are no results', () => {
    const setFilterText = vi.fn();
    const setCurrentPage = vi.fn();
    const copyToClipboard = vi.fn();
    const downloadAllImages = vi.fn();

    render(
      <DataTableTable
        results={[]}
        displayResults={[]}
        paginatedResults={[]}
        filterText=""
        setFilterText={setFilterText}
        currentPage={1}
        setCurrentPage={setCurrentPage}
        totalPages={0}
        visibleFields={defaultVisibleFields}
        loading={false}
        uniqueReferences={{}}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
        partId=""
      />
    );

    expect(screen.getAllByText(/Nenhum produto encontrado/).length).toBeGreaterThan(0);
  });

  it('renders table rows when results are provided', () => {
    const setFilterText = vi.fn();
    const setCurrentPage = vi.fn();
    const copyToClipboard = vi.fn();
    const downloadAllImages = vi.fn();

    render(
      <DataTableTable
        results={sampleResults}
        displayResults={sampleResults}
        paginatedResults={sampleResults}
        filterText=""
        setFilterText={setFilterText}
        currentPage={1}
        setCurrentPage={setCurrentPage}
        totalPages={1}
        visibleFields={defaultVisibleFields}
        loading={false}
        uniqueReferences={{}}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
        partId="0986BF0501"
      />
    );

    expect(screen.getAllByText('BOSCH').length).toBeGreaterThan(0);
    expect(screen.getAllByText('0986BF0501').length).toBeGreaterThan(0);
  });

  it('calls setFilterText when user types in search input', () => {
    const setFilterText = vi.fn();
    const setCurrentPage = vi.fn();
    const copyToClipboard = vi.fn();
    const downloadAllImages = vi.fn();

    render(
      <DataTableTable
        results={sampleResults}
        displayResults={sampleResults}
        paginatedResults={sampleResults}
        filterText=""
        setFilterText={setFilterText}
        currentPage={1}
        setCurrentPage={setCurrentPage}
        totalPages={1}
        visibleFields={defaultVisibleFields}
        loading={false}
        uniqueReferences={{}}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
        partId="0986BF0501"
      />
    );

    const input = screen.getByPlaceholderText('Filtrar nesta página...');
    fireEvent.change(input, { target: { value: 'Gol' } });

    expect(setFilterText).toHaveBeenCalledWith('Gol');
    expect(setCurrentPage).toHaveBeenCalledWith(1);
  });

  it('opens export menu when clicking Export button', () => {
    const setFilterText = vi.fn();
    const setCurrentPage = vi.fn();
    const copyToClipboard = vi.fn();
    const downloadAllImages = vi.fn();

    render(
      <DataTableTable
        results={sampleResults}
        displayResults={sampleResults}
        paginatedResults={sampleResults}
        filterText=""
        setFilterText={setFilterText}
        currentPage={1}
        setCurrentPage={setCurrentPage}
        totalPages={1}
        visibleFields={defaultVisibleFields}
        loading={false}
        uniqueReferences={{}}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        downloadAllImages={downloadAllImages}
        partId="0986BF0501"
      />
    );

    const exportButton = screen.getByText('Exportar / Salvar');
    fireEvent.click(exportButton);

    expect(screen.getByText('Excel')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('Layout Certtus')).toBeInTheDocument();
  });
});
