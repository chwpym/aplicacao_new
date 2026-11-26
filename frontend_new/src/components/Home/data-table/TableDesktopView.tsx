import React from "react";
import { SearchX } from "lucide-react";
import { ColumnConfigItem } from "./columnConfig";

interface TableDesktopViewProps {
  columns: ColumnConfigItem[];
  visibleFields: any;
  displayResults: any[];
  paginatedResults: any[];
  loading: boolean;
  partId: string;
}

export const TableDesktopView: React.FC<TableDesktopViewProps> = ({
  columns,
  visibleFields,
  displayResults,
  paginatedResults,
  loading,
  partId,
}) => {
  const activeColumns = columns.filter(
    (col) => col.id === "acoes" || visibleFields[col.id as keyof typeof visibleFields]
  );

  return (
    <div className="md:block hidden overflow-x-auto custom-scrollbar">
      <table className="w-full text-left border-collapse table-auto relative">
        <thead className="bg-slate-50/95 dark:bg-slate-800/95 text-slate-500 uppercase text-[10px] font-bold tracking-wider sticky top-0 z-10 backdrop-blur-md shadow-sm">
          <tr>
            {activeColumns.map((col) => (
              <th key={col.id} className="px-6 py-4 font-black">
                {col.getHeader()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
          {displayResults.length === 0 ? (
            loading ? (
              // Skeleton Loading
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {activeColumns.map((col) => (
                    <td key={col.id} className="px-4 py-4">
                      <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded-lg w-full"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={Math.max(1, activeColumns.length)} className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 bg-amber-500/10 rounded-2xl flex items-center justify-center">
                      <SearchX size={28} className="text-amber-500" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-600 dark:text-slate-300">
                        Nenhum produto encontrado{partId ? ` para "${partId}"` : "."}
                      </p>
                      <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
                        A busca foi realizada com sucesso no servidor, mas o provedor não retornou resultados.
                        Verifique se o <strong>código está correto</strong> ou tente outro provedor.
                      </p>
                    </div>
                  </div>
                </td>
              </tr>
            )
          ) : (
            paginatedResults.map((res, idx) => (
              <tr
                key={idx}
                className="hover:bg-slate-50/50 dark:hover:bg-primary/5 transition-colors text-[11px] group"
              >
                {activeColumns.map((col) => (
                  <React.Fragment key={col.id}>{col.render(res)}</React.Fragment>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
