import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterSectionTable } from './FilterSectionTable';

describe('FilterSectionTable Component', () => {
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

    render(
      <FilterSectionTable
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
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

    render(
      <FilterSectionTable
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
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

    render(
      <FilterSectionTable
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
      />
    );

    const agruparButton = screen.getByText('Agrupar');
    fireEvent.click(agruparButton);

    expect(setAgrupar).toHaveBeenCalledTimes(1);
  });

  it('triggers copy callbacks for all copy buttons', () => {
    const setVisibleFields = vi.fn();
    const setAgrupar = vi.fn();
    const copyToClipboard = vi.fn();
    const clearResults = vi.fn();
    const saveCurrentAsDefault = vi.fn();
    const restoreDefault = vi.fn();

    render(
      <FilterSectionTable
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
      />
    );

    fireEvent.click(screen.getByText('COMPL.'));
    expect(copyToClipboard).toHaveBeenCalledWith('completa');

    fireEvent.click(screen.getByText('INTERM.'));
    expect(copyToClipboard).toHaveBeenCalledWith('intermediaria');

    fireEvent.click(screen.getByText('AGRUP.'));
    expect(copyToClipboard).toHaveBeenCalledWith('agrupada');
  });

  it('triggers save and restore default preferences', () => {
    const setVisibleFields = vi.fn();
    const setAgrupar = vi.fn();
    const copyToClipboard = vi.fn();
    const clearResults = vi.fn();
    const saveCurrentAsDefault = vi.fn();
    const restoreDefault = vi.fn();

    render(
      <FilterSectionTable
        visibleFields={defaultVisibleFields}
        setVisibleFields={setVisibleFields}
        agrupar={false}
        setAgrupar={setAgrupar}
        getFieldLabel={mockGetFieldLabel}
        copyToClipboard={copyToClipboard}
        clearResults={clearResults}
        saveCurrentAsDefault={saveCurrentAsDefault}
        restoreDefault={restoreDefault}
      />
    );

    fireEvent.click(screen.getByTitle('Salvar estas colunas como meu Padrão de Fábrica'));
    expect(saveCurrentAsDefault).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTitle('Restaurar meu Padrão de Fábrica'));
    expect(restoreDefault).toHaveBeenCalledTimes(1);
  });
});
