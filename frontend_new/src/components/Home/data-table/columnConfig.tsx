import React from "react";
import { Image, Zap, ExternalLink } from "lucide-react";

export interface ColumnConfigItem {
  id: string;
  getHeader: () => string;
  render: (res: any) => React.ReactNode;
}

interface ColumnConfigParams {
  getFieldLabel: (field: string) => string;
  handleOpenGallery: (res: any) => void;
  handleOpenFicha: (res: any) => void;
  proxyImageUrl: (url: string) => string;
}

export const buildColumnConfig = ({
  getFieldLabel,
  handleOpenGallery,
  handleOpenFicha,
  proxyImageUrl,
}: ColumnConfigParams): ColumnConfigItem[] => [
  {
    id: "marca",
    getHeader: () => getFieldLabel("marca"),
    render: (res: any) => (
      <td className="px-4 py-2 font-semibold text-primary uppercase whitespace-nowrap">
        {res.marca || res.provedor || "---"}
      </td>
    ),
  },
  {
    id: "codigo",
    getHeader: () => getFieldLabel("codigo"),
    render: (res: any) => (
      <td className="px-4 py-2 font-mono text-xs font-bold text-slate-700 dark:text-slate-200 whitespace-nowrap">
        {res.codigo || "---"}
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
      <td className="px-4 py-2 font-bold text-slate-600 dark:text-slate-200 whitespace-nowrap">
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
      <td className="px-4 py-2 text-center font-mono bg-slate-50/50 dark:bg-slate-900/20 whitespace-nowrap">
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
    id: "imagem",
    getHeader: () => getFieldLabel("imagem"),
    render: (res: any) => {
      const imgUrl = res.imagens && res.imagens.length > 0 ? res.imagens[0] : res.imagem;
      if (!imgUrl) return <td className="px-4 py-2 text-center text-slate-300">---</td>;
      return (
        <td className="px-4 py-2 text-center">
          <button
            onClick={() => handleOpenGallery(res)}
            className="inline-flex w-10 h-10 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 bg-white items-center justify-center hover:scale-105 transition-transform aspect-square"
            title="Ver imagem na galeria"
          >
            <img
              src={proxyImageUrl(imgUrl)}
              alt={res.codigo || "Peça"}
              loading="lazy"
              decoding="async"
              width={40}
              height={40}
              className="w-full h-full object-contain"
            />
          </button>
        </td>
      );
    },
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
      <td className="px-4 py-2 font-black text-primary uppercase text-[10px] whitespace-nowrap">
        {res.apenas ? `★ ${res.apenas}` : "---"}
      </td>
    ),
  },
  {
    id: "referencias",
    getHeader: () => getFieldLabel("referencias"),
    render: (res: any) => {
      if (!res.referencias) return <td className="px-6 py-4 text-slate-300">---</td>;

      const parts = res.referencias.split(/\s*(?:\||,|;|\n)\s*/).filter((p: string) => !!p.trim());
      const cleanedRefs = parts.map((p: string) => {
        const firstColonIdx = p.indexOf(":");
        if (firstColonIdx === -1) return p.trim();

        const brand = p.slice(0, firstColonIdx).trim().toUpperCase()
          .replace(/\s+ORIGINAL$/g, "")
          .replace(/^ORIGINAL\s+/g, "");
        const code = p.slice(firstColonIdx + 1).trim();

        return `${brand}: ${code}`;
      });

      return (
        <td className="px-4 py-4 min-w-[150px]">
          <div className="text-[10px] text-slate-500 max-w-[200px] leading-relaxed">
            {cleanedRefs.map((ref: string, idx: number) => (
              <div key={idx} className="whitespace-nowrap">{ref}</div>
            ))}
          </div>
        </td>
      );
    },
  },
  {
    id: "ficha_tecnica",
    getHeader: () => getFieldLabel("ficha_tecnica"),
    render: (res: any) => {
      if (!res.ficha_tecnica || Object.keys(res.ficha_tecnica).length === 0) 
        return <td className="px-6 py-4 text-slate-300">---</td>;

      return (
        <td className="px-4 py-4 min-w-[180px]">
          <div className="flex flex-col gap-1">
            {Object.entries(res.ficha_tecnica).map(([label, value]: [string, any], idx: number) => (
              <div key={idx} className="flex items-center gap-1.5 text-[10px] leading-tight">
                <span className="font-bold text-slate-500 uppercase shrink-0">{label}:</span>
                <span className="text-primary font-medium uppercase">{String(value)}</span>
              </div>
            ))}
          </div>
        </td>
      );
    },
  },
  {
    id: "acoes",
    getHeader: () => "Ações",
    render: (res: any) => (
      <td className="px-4 py-2">
        <div className="flex items-center gap-1.5 justify-center">
          <button
            onClick={() => handleOpenGallery(res)}
            disabled={!res.imagem && (!res.imagens || res.imagens.length === 0)}
            className={`
              p-2 rounded-lg transition-all flex items-center justify-center
              ${(!res.imagem && (!res.imagens || res.imagens.length === 0))
                ? 'text-slate-200 cursor-not-allowed'
                : 'bg-primary/5 text-primary hover:bg-primary/10 hover:scale-110 active:scale-95'}
            `}
            title="Ver Galeria de Imagens"
          >
            <Image size={18} />
          </button>

          <button
            onClick={() => handleOpenFicha(res)}
            className="p-2 bg-amber-500/5 text-amber-600 hover:bg-amber-500/10 hover:scale-110 active:scale-95 rounded-lg transition-all flex items-center justify-center"
            title="Ver Ficha Técnica"
          >
            <Zap size={18} />
          </button>

          {res.url && (
            <a
              href={res.url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 bg-slate-100 text-slate-500 hover:bg-slate-200 rounded-lg transition-all flex items-center justify-center"
              title="Ver no site original"
            >
              <ExternalLink size={16} />
            </a>
          )}
        </div>
      </td>
    ),
  },
];
