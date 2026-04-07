import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, FileText, Ruler, Weight, Tag, Settings, Loader2, AlertCircle } from 'lucide-react';
import { searchApi } from '../../services/api';

interface FichaTecnicaModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: any | null;
  partId?: string;
}

const getFriendlyLabel = (key: string): string => {
  const dictionary: Record<string, string> = {
    diametro_externo: "Diâmetro Externo",
    "Diâmetro Externo": "Diâmetro Externo",
    diametro_interno: "Diâmetro Interno",
    altura: "Altura",
    "Altura": "Altura",
    rosca: "Rosca",
    "Rosca": "Rosca",
    comprimento: "Comprimento",
    largura: "Largura",
    espessura: "Espessura",
    peso: "Peso",
    material: "Material",
    observacao: "Observação Técnica",
    valvula_anti_retorno: "Válvula Anti-Retorno",
    "Anti Retorno": "Anti Retorno",
    valvula_alivio: "Válvula de Alívio",
    "By Pass": "By Pass",
    furos: "Quantidade de Furos",
    referencia: "Cód. Fabricante",
    "Tipo de Filtro": "Tipo de Filtro"
  };

  const cleanKey = key.toLowerCase();
  if (dictionary[key]) return dictionary[key];
  if (dictionary[cleanKey]) return dictionary[cleanKey];
  
  return key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
};

const getIcon = (key: string) => {
  const k = key.toLowerCase();
  if (k.includes('diametro') || k.includes('altura') || k.includes('comprimento') || k.includes('largura')) return <Ruler size={14} />;
  if (k.includes('peso')) return <Weight size={14} />;
  if (k.includes('material')) return <Settings size={14} />;
  return <Tag size={14} />;
};

export const FichaTecnicaModal: React.FC<FichaTecnicaModalProps> = ({ isOpen, onClose, item, partId }) => {
  const [fichaData, setFichaData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !item) {
        setFichaData(null);
        setError(null);
        return;
    }

    // Se já temos os dados no item (raro para Wega agora), usamos direto
    if (item.ficha_tecnica && Object.keys(item.ficha_tecnica).length > 0) {
      setFichaData(item.ficha_tecnica);
      return;
    }

    // Caso contrário, buscamos no backend (On-Demand)
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        // IMPORTANTE: Precisamos do provider_id correto que vem do backend (Wega é 34)
        const providerId = item.provider_id || item.providerId || (item.provedor === "WEGA" ? 34 : 1);
        
        // Use o código do item, id_peca ou, como último recurso, o termo da busca global (partId)
        const codigoBusca = item.codigo || item.id_peca || partId;
        
        if (!codigoBusca || codigoBusca.includes('/') || (typeof codigoBusca === 'string' && codigoBusca.includes('details'))) {
           console.warn("Código de busca inválido ou ausente:", codigoBusca);
           setError("Não foi possível identificar o código deste produto para busca técnica.");
           setLoading(false);
           return;
        }

        const res = await searchApi.getDetalhesPeca(codigoBusca, providerId);
        
        if (res.data && res.data.ficha_tecnica && Object.keys(res.data.ficha_tecnica).length > 0) {
          setFichaData(res.data.ficha_tecnica);
        } else {
          setError("Não foram encontrados dados técnicos detalhados para este item.");
        }
      } catch (err) {
        console.error("Erro ao carregar ficha técnica:", err);
        setError("Falha ao conectar com o servidor para buscar dados técnicos.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [isOpen, item, partId]);

  if (!isOpen || !item) return null;

  return createPortal(
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white dark:bg-slate-900 w-full max-w-xl rounded-3xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden border border-slate-200 dark:border-slate-800 animate-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 leading-tight">
                Ficha Técnica: <span className="text-primary">{item.codigo || partId || ""}</span>
              </h2>
              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                {item.marca} • {item.veiculo}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2.5 rounded-2xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 transition-all border border-transparent hover:border-slate-300 dark:hover:border-slate-600"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto custom-scrollbar bg-white dark:bg-slate-900 min-h-[200px] flex flex-col">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 py-12">
              <Loader2 size={40} className="text-primary animate-spin" />
              <div className="text-center">
                <p className="font-bold text-slate-700 dark:text-slate-200">Buscando Especificações...</p>
                <p className="text-xs text-slate-400 mt-1">Conectando ao catálogo da {item.provedor}</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 py-12 px-8 text-center">
              <div className="h-12 w-12 rounded-full bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center text-amber-500">
                <AlertCircle size={28} />
              </div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400 leading-relaxed">
                {error}
              </p>
            </div>
          ) : fichaData ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(fichaData).map(([key, value], idx) => (
                <div key={idx} className="flex items-start gap-4 p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800 hover:border-primary/20 transition-colors group">
                  <div className="mt-1 h-7 w-7 rounded-lg bg-white dark:bg-slate-800 flex items-center justify-center text-slate-400 group-hover:text-primary transition-colors border border-slate-200 dark:border-slate-700">
                      {getIcon(key)}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{getFriendlyLabel(key)}</span>
                    <span className="text-sm font-bold text-slate-700 dark:text-slate-200 mt-0.5">{value || '---'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50/50 dark:bg-slate-800/20 border-t border-slate-100 dark:border-slate-800 flex justify-end">
          <button 
            onClick={onClose}
            className="px-6 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold rounded-xl hover:opacity-90 transition-all"
          >
            Fechar
          </button>
        </div>

      </div>
    </div>,
    document.body
  );
};
