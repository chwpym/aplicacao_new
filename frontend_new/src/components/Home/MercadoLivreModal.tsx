import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Copy, Check, ShoppingBag, FileText, Car, Wrench, SearchX } from "lucide-react";
import { generateMercadoLivreContent, type MercadoLivreContent } from "../../utils/mercadoLivreGenerator";

interface MercadoLivreModalProps {
  isOpen: boolean;
  onClose: () => void;
  displayResults: any[];
  partId: string;
  uniqueReferences?: any;
  cleanMode?: boolean;
}

export const MercadoLivreModal: React.FC<MercadoLivreModalProps> = ({
  isOpen,
  onClose,
  displayResults,
  partId,
  uniqueReferences,
  cleanMode = false,
}) => {
  const emptyState: MercadoLivreContent = {
    titulo: "",
    descricaoResumida: "",
    aplicacoes: "",
    referencias: "",
    palavrasChave: "",
  };

  const [content, setContent] = useState<MercadoLivreContent>(emptyState);
  const [editableContent, setEditableContent] = useState<MercadoLivreContent>(emptyState);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && displayResults.length > 0) {
      const generated = generateMercadoLivreContent(displayResults, partId, uniqueReferences, cleanMode);
      setContent(generated);
      setEditableContent(generated);
    } else if (displayResults.length === 0) {
      setContent(emptyState);
      setEditableContent(emptyState);
    }
  }, [isOpen, displayResults, partId, uniqueReferences, cleanMode]);

  if (!isOpen) return null;

  const handleCopy = async (field: keyof MercadoLivreContent, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Erro ao copiar:", err);
    }
  };

  const handleCopyAll = async () => {
    const fullText = [
      editableContent.titulo,
      "",
      editableContent.descricaoResumida,
      "",
      editableContent.aplicacoes,
      "",
      editableContent.referencias,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(fullText);
      setCopiedField("all");
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Erro ao copiar tudo:", err);
    }
  };

  const handleRegenerate = () => {
    const generated = generateMercadoLivreContent(displayResults, partId, uniqueReferences, cleanMode);
    setContent(generated);
    setEditableContent(generated);
  };

  const sections: { key: keyof MercadoLivreContent; label: string; icon: React.ReactNode; color: string; isTextarea: boolean; rows?: number }[] = [
    {
      key: "titulo",
      label: `Título Otimizado (${editableContent.titulo.length}/70)`,
      icon: <ShoppingBag size={16} />,
      color: editableContent.titulo.length > 70 ? "red" : "emerald",
      isTextarea: false,
    },
    {
      key: "descricaoResumida",
      label: "Descrição Resumida",
      icon: <FileText size={16} />,
      color: "blue",
      isTextarea: true,
      rows: 10,
    },
    {
      key: "aplicacoes",
      label: "Aplicações Detalhadas",
      icon: <Car size={16} />,
      color: "purple",
      isTextarea: true,
      rows: 12,
    },
    {
      key: "referencias",
      label: "Referências / Códigos Equivalentes",
      icon: <Wrench size={16} />,
      color: "yellow",
      isTextarea: true,
      rows: 8,
    },
    {
      key: "palavrasChave",
      label: "Palavras-chave Ocultas (IDX/Tags)",
      icon: <SearchX size={16} />,
      color: "slate",
      isTextarea: true,
      rows: 6,
    },
  ];

  const colorClasses: Record<string, { bg: string; border: string; text: string; badge: string }> = {
    yellow: {
      bg: "bg-yellow-500/5",
      border: "border-yellow-500/20",
      text: "text-yellow-600 dark:text-yellow-400",
      badge: "bg-yellow-500/10 text-yellow-600",
    },
    red: {
      bg: "bg-red-500/5",
      border: "border-red-500/20",
      text: "text-red-600 dark:text-red-400",
      badge: "bg-red-500/10 text-red-600",
    },
    blue: {
      bg: "bg-blue-500/5",
      border: "border-blue-500/20",
      text: "text-blue-600 dark:text-blue-400",
      badge: "bg-blue-500/10 text-blue-600",
    },
    emerald: {
      bg: "bg-emerald-500/5",
      border: "border-emerald-500/20",
      text: "text-emerald-600 dark:text-emerald-400",
      badge: "bg-emerald-500/10 text-emerald-600",
    },
    purple: {
      bg: "bg-purple-500/5",
      border: "border-purple-500/20",
      text: "text-purple-600 dark:text-purple-400",
      badge: "bg-purple-500/10 text-purple-600",
    },
    slate: {
      bg: "bg-slate-500/5",
      border: "border-slate-500/20",
      text: "text-slate-600 dark:text-slate-400",
      badge: "bg-slate-500/10 text-slate-600",
    },
  };

  return createPortal(
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-yellow-500/5 to-amber-500/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 flex items-center justify-center">
              <ShoppingBag size={22} className="text-yellow-600" />
            </div>
            <div>
              <h2 className="font-bold text-lg text-slate-900 dark:text-white">
                {cleanMode ? "Gerador de Anúncio — ERP Limpo" : "Gerador de Anúncio — Mercado Livre"}
              </h2>
              <p className="text-xs text-slate-400">
                Código: <span className="font-mono font-bold text-slate-600 dark:text-slate-300">{partId}</span>
                {" "}• {displayResults.length} aplicações encontradas
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRegenerate}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
              title="Regenerar conteúdo a partir dos resultados"
            >
              ↻ Regenerar
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content - scrollable */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          {sections.map((section) => {
            const colors = colorClasses[section.color];
            const isCopied = copiedField === section.key;

            return (
              <div
                key={section.key}
                className={`rounded-xl border ${colors.border} ${colors.bg} p-4 transition-all`}
              >
                {/* Section Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={colors.text}>{section.icon}</span>
                    <span className={`text-xs font-black uppercase tracking-wider ${colors.text}`}>
                      {section.label}
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopy(section.key, editableContent[section.key])}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      isCopied
                        ? "bg-emerald-500 text-white"
                        : `${colors.badge} hover:opacity-80`
                    }`}
                  >
                    {isCopied ? <Check size={12} /> : <Copy size={12} />}
                    {isCopied ? "Copiado!" : "Copiar"}
                  </button>
                </div>

                {/* Editable Field */}
                {section.isTextarea ? (
                  <textarea
                    value={editableContent[section.key]}
                    onChange={(e) =>
                      setEditableContent((prev) => ({
                        ...prev,
                        [section.key]: e.target.value,
                      }))
                    }
                    rows={section.rows || 8}
                    className="w-full bg-white/80 dark:bg-slate-950/50 border border-slate-200/50 dark:border-slate-800/50 rounded-lg p-3 text-xs text-slate-700 dark:text-slate-300 font-mono leading-relaxed resize-y focus:ring-1 focus:ring-primary outline-none transition-all"
                  />
                ) : (
                  <input
                    type="text"
                    value={editableContent[section.key]}
                    onChange={(e) =>
                      setEditableContent((prev) => ({
                        ...prev,
                        [section.key]: e.target.value,
                      }))
                    }
                    maxLength={70}
                    className={`w-full bg-white/80 dark:bg-slate-950/50 border rounded-lg px-3 py-2.5 text-sm font-bold text-slate-800 dark:text-white focus:ring-1 focus:ring-primary outline-none transition-all ${
                      editableContent.titulo.length > 70
                        ? "border-red-400"
                        : "border-slate-200/50 dark:border-slate-800/50"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
          <p className="text-[10px] text-slate-400 max-w-md">
            💡 Você pode editar o texto antes de copiar. As alterações não são salvas — ao reabrir, o conteúdo é regenerado.
          </p>
          <button
            onClick={handleCopyAll}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all shadow-lg ${
              copiedField === "all"
                ? "bg-emerald-500 text-white shadow-emerald-500/30"
                : "bg-yellow-500 text-white hover:bg-yellow-600 shadow-yellow-500/30 hover:shadow-yellow-500/50"
            }`}
          >
            {copiedField === "all" ? <Check size={14} /> : <Copy size={14} />}
            {copiedField === "all" ? "Tudo Copiado!" : "Copiar Tudo"}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};
