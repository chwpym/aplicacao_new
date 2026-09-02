import React, { useState } from "react";
import {
  Search, Database, Settings, Hash, FlaskConical,
  Trash2, Car, Download, HelpCircle, SlidersHorizontal,
  Moon, Check, Copy, ChevronDown, LayoutDashboard
} from "lucide-react";

// ─── PALETAS MODO LIGHT COM DIFERENTES CONTRASTES ────────────────────────────
const PALETAS = [
  {
    id: "inversao-tecnica",
    nome: "🔄 Inversão Técnica",
    desc: "Inverte a lógica: Fundo claro (#F8FAFC) e cards/tabelas em cinza-escuro denso (#E2E8F0) com sidebar cinza (#EEF2F6).",
    primary: "#0f52ba", // Azul cobalto
    primaryHover: "#0a3d8f",
    accent: "#00b4d8",
    bg: "#FFFFFF",       // Fundo ultra claro
    surface: "#E4E9F2",  // Cards e tabelas em cinza estruturado
    sidebarBg: "#F0F4F8", // Sidebar cinza claro
    border: "#CCD4E0",
    textBody: "#1F2937",
    textMuted: "#4B5563",
    rowHover: "#D6DFEB",
    rowSelected: "#C8D5E8",
    shadowCard: "none",
  },
  {
    id: "premium-saas",
    nome: "✨ Premium SaaS (Padrão)",
    desc: "Lógica tradicional: Fundo levemente acinzentado (#F5F7FB) com cards e sidebar brancos (#FFFFFF).",
    primary: "#0f52ba",
    primaryHover: "#0a3d8f",
    accent: "#00b4d8",
    bg: "#F5F7FB",
    surface: "#FFFFFF",
    sidebarBg: "#FFFFFF",
    border: "#E4E9F2",
    textBody: "#1F2937",
    textMuted: "#64748b",
    rowHover: "#F2F5FC",
    rowSelected: "#ECE8FF",
    shadowCard: "0 4px 18px rgba(15,23,42,.04)",
  },
  {
    id: "cinza-suave",
    nome: "🔵 Cinza Suave (Clássico)",
    desc: "Fundo #e8ecf0 com cards e tabelas brancas.",
    primary: "#0f52ba",
    primaryHover: "#0a3d8f",
    accent: "#00b4d8",
    bg: "#e8ecf0",
    surface: "#ffffff",
    sidebarBg: "#ffffff",
    border: "#d1d9e0",
    textBody: "#0f172a",
    textMuted: "#64748b",
    rowHover: "#f0f4fa",
    rowSelected: "#dbeafe",
    shadowCard: "none",
  }
];

// ─── APP PREVIEW COMPONENTE ──────────────────────────────────────────────────
const AppPreview: React.FC<{ paleta: typeof PALETAS[0] }> = ({ paleta }) => {
  const navItems = [
    { name: "WORKSPACE", icon: Search, active: true },
    { name: "PROVEDORES", icon: Database },
    { name: "SIGLAS", icon: Hash },
    { name: "PLAYGROUND", icon: FlaskConical },
    { name: "LIMPEZA", icon: Trash2 },
    { name: "BIBLIOTECA", icon: Car },
    { name: "CONFIGURAÇÕES", icon: SlidersHorizontal },
    { name: "BACKUP", icon: Download },
    { name: "AJUDA", icon: HelpCircle },
  ];

  const stats = [
    { label: "Buscas Hoje", value: "142", color: paleta.primary },
    { label: "Provedores", value: "24", color: "#22C55E" },
    { label: "Em Andamento", value: "7", color: "#F59E0B" },
    { label: "Erros", value: "2", color: "#EF4444" },
  ];

  return (
    <div
      className="rounded-2xl overflow-hidden flex transition-all duration-300 animate-in fade-in"
      style={{
        height: 500,
        border: `1px solid ${paleta.border}`,
        boxShadow: paleta.shadowCard,
        fontFamily: "Inter, system-ui, sans-serif"
      }}
    >
      {/* ── SIDEBAR ── */}
      <div
        className="w-52 flex flex-col shrink-0 border-r"
        style={{ background: paleta.sidebarBg, borderColor: paleta.border }}
      >
        {/* Logo */}
        <div className="p-4 pb-3">
          <div className="flex items-center gap-2.5 mb-5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center text-white"
              style={{
                background: paleta.primary,
              }}
            >
              <Settings size={15} />
            </div>
            <div>
              <div className="text-[12px] font-black leading-none" style={{ color: paleta.textBody }}>
                Catálogo V4
              </div>
              <div className="text-[8px] uppercase tracking-widest mt-0.5" style={{ color: paleta.textMuted }}>
                Gerenciador de Peças
              </div>
            </div>
          </div>

          {/* Nav Label */}
          <div className="text-[8px] uppercase tracking-widest px-2 pb-1.5" style={{ color: paleta.textMuted }}>
            Navegação
          </div>

          {/* Nav Items */}
          <div className="space-y-0.5">
            {navItems.map((item) => (
              <div
                key={item.name}
                className="flex items-center gap-2 px-2.5 py-2 rounded-lg transition-all cursor-pointer"
                style={{
                  background: item.active ? paleta.primary : "transparent",
                  color: item.active ? "white" : paleta.textMuted,
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                }}
              >
                <item.icon size={11} />
                {item.name}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-auto p-4 pt-3" style={{ borderTop: `1px solid ${paleta.border}` }}>
          <div className="flex items-center gap-2 mb-2.5">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0"
              style={{ background: `${paleta.primary}15`, color: paleta.primary }}
            >
              AC
            </div>
            <div>
              <div className="text-[10px] font-bold" style={{ color: paleta.textBody }}>
                Estoque Original
              </div>
              <div className="text-[8px] uppercase tracking-wide" style={{ color: paleta.textMuted }}>
                Administrador
              </div>
            </div>
          </div>

          {/* Toggle tema */}
          <div
            className="flex items-center justify-between px-2 py-1.5 rounded-lg"
            style={{
              background: paleta.bg,
              fontSize: 9,
              fontWeight: 700,
              color: paleta.textMuted,
            }}
          >
            <div className="flex items-center gap-1.5">
              <Moon size={10} />
              Tema Escuro
            </div>
            <div className="w-6 h-3 rounded-full" style={{ background: "#d1d5db" }} />
          </div>
        </div>
      </div>

      {/* ── CONTENT ── */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: paleta.bg }}>
        {/* Top bar */}
        <div
          className="px-5 py-3 flex items-center justify-between shrink-0 border-b"
          style={{ background: paleta.sidebarBg, borderColor: paleta.border }}
        >
          <div className="flex items-center gap-1.5">
            <LayoutDashboard size={12} style={{ color: paleta.textMuted }} />
            <span className="text-[10px] font-bold" style={{ color: paleta.textBody }}>Workspace</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold"
              style={{ background: `${paleta.primary}15`, color: paleta.primary }}
            >
              AC
            </div>
            <span className="text-[9px] font-bold" style={{ color: paleta.textBody }}>Estoque Original</span>
          </div>
        </div>

        <div className="flex-1 overflow-hidden p-4 flex flex-col gap-3">
          {/* Stats cards */}
          <div className="grid grid-cols-4 gap-2 shrink-0">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl p-3 border transition-all duration-300"
                style={{
                  background: paleta.surface,
                  borderColor: paleta.border,
                  boxShadow: paleta.shadowCard,
                }}
              >
                <div className="text-[8px] font-bold uppercase tracking-wide mb-1" style={{ color: paleta.textMuted }}>
                  {stat.label}
                </div>
                <div className="text-lg font-black leading-none" style={{ color: stat.color }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Search bar */}
          <div
            className="rounded-xl p-3 flex gap-2 shrink-0 border transition-all duration-300"
            style={{
              background: paleta.surface,
              borderColor: paleta.border,
              boxShadow: paleta.shadowCard,
            }}
          >
            <div
              className="flex-1 flex items-center gap-2 rounded-lg px-3 py-2 border bg-white"
              style={{ borderColor: paleta.border, fontSize: 10, color: paleta.textMuted }}
            >
              <Search size={11} />
              Digite o código da peça...
            </div>
            <div
              className="flex items-center gap-1 px-3 py-2 rounded-lg border bg-white"
              style={{ borderColor: paleta.border, fontSize: 10, color: paleta.textMuted }}
            >
              Todos os Provedores <ChevronDown size={10} />
            </div>
            <div
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg font-bold text-white cursor-pointer"
              style={{
                background: paleta.primary,
                fontSize: 10,
              }}
            >
              <Search size={11} />
              Pesquisar
            </div>
          </div>

          {/* Table */}
          <div
            className="flex-1 rounded-xl overflow-hidden border transition-all duration-300"
            style={{
              borderColor: paleta.border,
              background: paleta.surface,
              boxShadow: paleta.shadowCard,
            }}
          >
            {/* Header tabela */}
            <div
              className="flex items-center px-4 py-2 border-b"
              style={{ background: paleta.bg, borderColor: paleta.border, fontSize: 8, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: paleta.textMuted }}
            >
              <span className="w-32">Marca Peça</span>
              <span className="w-28">Montadora</span>
              <span className="w-24">Veículo</span>
              <span className="w-20">Motor</span>
              <span className="flex-1">Ano</span>
              <span className="w-16 text-right">Ações</span>
            </div>

            {/* Linhas */}
            {[
              { marca: "SAMPEL", mont: "TOYOTA", vei: "Corolla", motor: "2.0", ano: "2020-24", selected: true },
              { marca: "TSA", mont: "HONDA", vei: "Civic", motor: "1.5T", ano: "2018-22", hover: true },
              { marca: "VICTOR REINZ", mont: "GM", vei: "Onix", motor: "1.0T", ano: "2019-23" },
              { marca: "SCHAEFFLER", mont: "VW", vei: "Polo", motor: "1.0", ano: "2020-24" },
            ].map((row, i) => {
              let rowBg = paleta.surface;
              if (row.selected) rowBg = paleta.rowSelected;
              else if (row.hover) rowBg = paleta.rowHover;

              return (
                <div
                  key={i}
                  className="flex items-center px-4 py-2 border-b"
                  style={{
                    fontSize: 9,
                    borderColor: paleta.border,
                    background: rowBg,
                    borderLeft: row.selected ? `4px solid ${paleta.primary}` : "none",
                  }}
                >
                  <span className="w-32 font-bold" style={{ color: paleta.textBody }}>{row.marca}</span>
                  <span className="w-28" style={{ color: paleta.textMuted }}>{row.mont}</span>
                  <span className="w-24" style={{ color: paleta.textMuted }}>{row.vei}</span>
                  <span className="w-20" style={{ color: paleta.textMuted }}>{row.motor}</span>
                  <span className="flex-1" style={{ color: paleta.textMuted }}>{row.ano}</span>
                  <div className="w-16 flex justify-end gap-1">
                    <div className="w-5 h-5 rounded flex items-center justify-center" style={{ background: `${paleta.primary}18` }}>
                      <Check size={9} color={paleta.primary} />
                    </div>
                    <div className="w-5 h-5 rounded flex items-center justify-center" style={{ background: "#fee2e2" }}>
                      <Copy size={9} color="#ef4444" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── PÁGINA PRINCIPAL ─────────────────────────────────────────────────────────
const DesignPreview: React.FC = () => {
  const [paletaId, setPaletaId] = useState("premium-saas");
  const paleta = PALETAS.find((p) => p.id === paletaId)!;

  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = [
      `/* Modificações para o index.css */`,
      `--color-background-light:  ${paleta.bg};`,
      `--color-surface-light:     ${paleta.surface};`,
    ].join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100">
          🎨 Laboratório de Design — Comparador de Estruturas
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Experimente a nova estrutura reversa (Fundo claro e tabelas/cards mais escuros), ideal para um design mais focado e técnico.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_2fr] gap-8">
        {/* ── CONTROLES ── */}
        <div className="space-y-6">
          <div>
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
              Escolha uma Opção para Testar
            </h2>
            <div className="space-y-3">
              {PALETAS.map((p) => {
                const selected = paletaId === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => setPaletaId(p.id)}
                    className="w-full flex items-start gap-3 p-3.5 rounded-xl border-2 transition-all text-left bg-white text-slate-900"
                    style={{
                      borderColor: selected ? p.primary : "#e2e8f0",
                      boxShadow: selected ? `0 0 0 3px ${p.primary}25` : "none",
                    }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white"
                      style={{ background: p.primary }}
                    >
                      <Check size={14} className={selected ? "opacity-100" : "opacity-0"} />
                    </div>
                    <div className="flex-1">
                      <span className="text-xs font-black block">{p.nome}</span>
                      <p className="text-[10px] text-slate-500 mt-0.5">{p.desc}</p>
                      
                      <div className="flex gap-1.5 mt-2">
                        <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded border">
                          Fundo: {p.bg}
                        </span>
                        <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded border">
                          Cards/Mesa: {p.surface}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* CTA para aplicação */}
          <div
            className="rounded-2xl p-4 border bg-white text-slate-900"
            style={{ borderColor: paleta.border }}
          >
            <p className="text-[11px] font-bold" style={{ color: paleta.primary }}>
              Configuração Ativa no Preview:
            </p>
            <p className="text-xs mt-1 font-semibold">
              {paleta.nome}
            </p>
            <button
              onClick={handleCopy}
              className="mt-3 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold text-white transition-all"
              style={{
                background: paleta.primary,
              }}
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              {copied ? "Copiado!" : "Copiar Valores"}
            </button>
          </div>
        </div>

        {/* ── PREVIEW ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Visualização da Interface (com botões Azuis)
            </h2>
            <span className="text-[10px] text-slate-400 font-mono">
              Fundo: {paleta.bg} | Cards/Mesa: {paleta.surface}
            </span>
          </div>
          <AppPreview paleta={paleta} />
        </div>
      </div>
    </div>
  );
};

export default DesignPreview;
