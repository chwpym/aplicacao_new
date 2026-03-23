import React, { useState } from "react";
import { Copy, FileDown, Loader2, Info } from "lucide-react";
import { FichaTecnicaModal } from "./FichaTecnicaModal";

interface DataTableProps {
  results: any[];
  displayResults: any[];
  visibleFields: any;
  loading: boolean;
  uniqueReferences: any;
  getFieldLabel: (field: string) => string;
  copyToClipboard: (mode: "completa" | "intermediaria" | "agrupada") => void;
  downloadAllImages: () => void;
}

export const DataTable: React.FC<DataTableProps> = ({
  results,
  displayResults,
  visibleFields,
  loading,
  uniqueReferences,
  getFieldLabel,
  copyToClipboard,
  downloadAllImages,
}) => {
  const [fichaModalOpen, setFichaModalOpen] = useState(false);
  const [selectedFicha, setSelectedFicha] = useState<any>(null);

  const handleOpenFicha = (ficha: any) => {
    setSelectedFicha(ficha);
    setFichaModalOpen(true);
  };

  const COLUMN_CONFIG = [
    {
      id: "marca",
      getHeader: () => getFieldLabel("marca"),
      render: (res: any) => (
        <td className="px-6 py-2 font-semibold text-primary uppercase">
          {res.marca}
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
        <td className="px-6 py-2 font-bold text-slate-600 dark:text-slate-200">
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
        <td className="px-6 py-2 text-center font-mono bg-slate-50/50 dark:bg-slate-900/20">
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
        <td className="px-6 py-2 font-black text-primary uppercase text-[10px]">
          {res.apenas ? `★ ${res.apenas}` : "---"}
        </td>
      ),
    },
    {
      id: "referencias",
      getHeader: () => getFieldLabel("referencias"),
      render: (res: any) => (
        <td className="px-6 py-4">
          <div
            className="text-[10px] text-slate-500 max-w-xs truncate"
            title={res.referencias}
          >
            {res.referencias || "---"}
          </div>
        </td>
      ),
    },
    {
      id: "imagem",
      getHeader: () => getFieldLabel("imagem"),
      render: (res: any) => (
        <td className="px-6 py-4">
          <div className="flex flex-wrap gap-2">
            {res.imagens && res.imagens.length > 0 ? (
              res.imagens.map((imgUrl: string, i: number) => (
                <div key={i} className="group relative">
                  <div className="h-10 w-10 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-white flex items-center justify-center p-1">
                    <img
                      src={imgUrl}
                      alt={`Peça ${i + 1}`}
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                  <div className="absolute -top-2 -right-2 hidden group-hover:flex gap-1">
                    <a
                      href={imgUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-primary text-white p-1 rounded-full"
                    >
                      <FileDown size={10} />
                    </a>
                  </div>
                </div>
              ))
            ) : res.imagem ? (
              <div className="group relative">
                <div className="h-10 w-10 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-white flex items-center justify-center p-1">
                  <img
                    src={res.imagem}
                    alt="Peça"
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
                <div className="absolute -top-2 -right-2 hidden group-hover:flex">
                  <a
                    href={res.imagem}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-primary text-white p-1 rounded-full"
                  >
                    <FileDown size={10} />
                  </a>
                </div>
              </div>
            ) : (
              <div className="h-10 w-10 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                <div className="opacity-20 text-[9px] font-bold">N/A</div>
              </div>
            )}
          </div>
        </td>
      ),
    },
    {
      id: "ficha_tecnica",
      getHeader: () => getFieldLabel("ficha_tecnica"),
      render: (res: any) => (
        <td className="px-6 py-2">
          {res.ficha_tecnica ? (
            <button
              onClick={() => handleOpenFicha(res.ficha_tecnica)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded-md transition-colors text-[10px] font-bold uppercase mx-auto"
              title="Ver Ficha Técnica"
            >
              <Info size={14} /> Ficha
            </button>
          ) : (
            <div className="text-center text-slate-300">---</div>
          )}
        </td>
      ),
    },
  ];

  return (
    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden mt-6">
      <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h2 className="font-bold text-lg">
            Resultados ({displayResults.length})
          </h2>
          {Object.keys(uniqueReferences).length > 0 && (
            <div className="flex flex-wrap gap-2 items-center bg-primary/5 border border-primary/10 rounded-lg px-3 py-1.5">
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
          )}
        </div>
        <div className="flex gap-2">
          {results.length > 0 && (
            <button
              onClick={downloadAllImages}
              disabled={loading}
              className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-orange-500/10 text-orange-600 hover:bg-orange-500/20 transition-all border border-orange-500/20 disabled:opacity-50"
              title="Baixa todas as imagens no formato .zip"
            >
              {loading ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <FileDown size={14} />
              )}
              Salvar Todas
            </button>
          )}
          <button
            onClick={() => copyToClipboard("completa")}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20"
          >
            <Copy size={14} /> Copiar Tudo
          </button>
        </div>
      </div>

      <div className="md:block hidden overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
            <tr>
              {COLUMN_CONFIG.filter(
                (col) => visibleFields[col.id as keyof typeof visibleFields],
              ).map((col) => (
                <th key={col.id} className="px-6 py-2">
                  {col.getHeader()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-white/5">
            {displayResults.length === 0 ? (
              <tr>
                <td
                  colSpan={12}
                  className="px-6 py-12 text-center text-slate-400 italic"
                >
                  {loading
                    ? "Consultando provedores..."
                    : "Nenhum resultado para exibir."}
                </td>
              </tr>
            ) : (
              displayResults.map((res, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-slate-50/50 dark:hover:bg-primary/5 transition-colors text-[11px] group"
                >
                  {COLUMN_CONFIG.filter(
                    (col) => visibleFields[col.id as keyof typeof visibleFields],
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
          <div className="px-6 py-12 text-center text-slate-400 italic">
            {loading
              ? "Consultando provedores..."
              : "Nenhum resultado para exibir."}
          </div>
        ) : (
          displayResults.map((res, idx) => (
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

              {visibleFields.imagem && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {res.imagens && res.imagens.length > 0
                    ? res.imagens.map((imgUrl: string, i: number) => (
                        <a
                          key={i}
                          href={imgUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="h-14 w-14 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-white p-1"
                        >
                          <img
                            src={imgUrl}
                            alt={`Peça ${i + 1}`}
                            className="h-full w-full object-contain"
                          />
                        </a>
                      ))
                    : res.imagem && (
                        <a
                          href={res.imagem}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="h-14 w-14 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-white p-1"
                        >
                          <img
                            src={res.imagem}
                            alt="Peça"
                            className="h-full w-full object-contain"
                          />
                        </a>
                      )}
                </div>
              )}
              
              {visibleFields.ficha_tecnica && res.ficha_tecnica && (
                <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                  <button 
                    onClick={() => handleOpenFicha(res.ficha_tecnica)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary/10 text-primary hover:bg-primary/20 rounded-lg transition-colors text-xs font-bold uppercase"
                  >
                    <Info size={16} /> Ficha Técnica
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <FichaTecnicaModal 
        isOpen={fichaModalOpen} 
        onClose={() => setFichaModalOpen(false)} 
        data={selectedFicha} 
      />
    </div>
  );
};
