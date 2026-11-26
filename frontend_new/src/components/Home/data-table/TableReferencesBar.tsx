import React from "react";

interface TableReferencesBarProps {
  uniqueReferences: Record<string, any>;
}

export const TableReferencesBar: React.FC<TableReferencesBarProps> = ({ uniqueReferences }) => {
  if (Object.keys(uniqueReferences).length === 0) return null;

  return (
    <div className="px-4 pb-4">
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 items-center bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/50 rounded-xl px-3 py-2 text-xs w-full max-h-32 overflow-y-auto custom-scrollbar">
        <span className="text-[10px] font-black text-primary uppercase">
          Original:
        </span>
        {Object.entries(uniqueReferences).map(([brand, codes]: [string, any]) => (
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
        ))}
      </div>
    </div>
  );
};
