import React from "react";
import { Eye, EyeOff, Settings2 } from "lucide-react";

interface FieldManagerProps {
  mapping: string; // JSON string
  onChange: (newMapping: string) => void;
}

const ALL_FIELDS = [
  { key: "marca", defaultLabel: "Marca" },
  { key: "codigo", defaultLabel: "Cód. Peça" },
  { key: "veiculo", defaultLabel: "Montadora" },
  { key: "modelo", defaultLabel: "Veículo" },
  { key: "versao", defaultLabel: "Modelo / Versão" },
  { key: "motor", defaultLabel: "Motor" },
  { key: "configuracao_motor", defaultLabel: "Config. Motor" },
  { key: "combustivel", defaultLabel: "Combustível" },
  { key: "ano", defaultLabel: "Ano" },
  { key: "referencias", defaultLabel: "Referências" },
  { key: "observacao", defaultLabel: "Observações" },
  { key: "posicao", defaultLabel: "Posição" },
  { key: "lado", defaultLabel: "Lado" },
  { key: "direcao", defaultLabel: "Direção" },
  { key: "sistema_freio", defaultLabel: "Sistema Freio" },
  { key: "restricao", defaultLabel: "Restrição" },
  { key: "apenas", defaultLabel: "Apenas" },
  { key: "imagem", defaultLabel: "Imagens" },
  { key: "ficha_tecnica", defaultLabel: "Ficha Técnica" },
];

const FieldManager: React.FC<FieldManagerProps> = ({ mapping, onChange }) => {
  let currentMap: any = {};
  try {
    currentMap = JSON.parse(mapping || "{}");
  } catch {
    currentMap = {};
  }

  const labels = currentMap.labels || {};
  const visibility = currentMap.visibility || {};

  const handleLabelChange = (key: string, value: string) => {
    const nextMap = { ...currentMap };
    if (!nextMap.labels) nextMap.labels = {};
    nextMap.labels[key] = value;
    onChange(JSON.stringify(nextMap, null, 2));
  };

  const toggleVisibility = (key: string) => {
    const nextMap = { ...currentMap };
    if (!nextMap.visibility) nextMap.visibility = {};
    // Se não tiver nada, assume true (visível) e inverte
    const current = visibility[key] !== undefined ? visibility[key] : true;
    nextMap.visibility[key] = !current;
    onChange(JSON.stringify(nextMap, null, 2));
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-800/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
          <Settings2 size={16} className="text-primary" />
          GERENCIAR COLUNAS DO WORKSPACE
        </div>
        <span className="text-[10px] text-slate-400 font-medium italic">
          Isolado para este provedor
        </span>
      </div>

      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {ALL_FIELDS.map((f) => {
          const isVisible =
            visibility[f.key] !== undefined ? visibility[f.key] : true;
          const customLabel = labels[f.key] || f.defaultLabel;

          return (
            <div
              key={f.key}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${isVisible ? "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-sm" : "bg-slate-50 dark:bg-slate-900/30 border-slate-100 dark:border-slate-800 opacity-60"}`}
            >
              <button
                onClick={() => toggleVisibility(f.key)}
                className={`p-2 rounded-lg transition-colors ${isVisible ? "text-primary bg-primary/5 hover:bg-primary/10" : "text-slate-400 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"}`}
                title={isVisible ? "Ocultar Coluna" : "Mostrar Coluna"}
              >
                {isVisible ? <Eye size={18} /> : <EyeOff size={18} />}
              </button>

              <div className="flex-1 space-y-1">
                <div className="text-[10px] font-black text-slate-400 uppercase flex justify-between">
                  <span>{f.key.replace("_", " ")}</span>
                  {customLabel !== f.defaultLabel && (
                    <span className="text-primary-hover">Editado</span>
                  )}
                </div>
                <input
                  value={customLabel}
                  onChange={(e) => handleLabelChange(f.key, e.target.value)}
                  placeholder={f.defaultLabel}
                  className="w-full bg-transparent border-none p-0 text-sm font-semibold outline-none focus:ring-0 focus:border-none placeholder:text-slate-300"
                  disabled={!isVisible}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="px-5 py-3 bg-slate-100/30 dark:bg-slate-800/20 text-[10px] text-slate-400 text-center">
        Dica: Ocultar colunas não essenciais melhora a performance e a
        visualização no Workspace.
      </div>
    </div>
  );
};

export default FieldManager;
