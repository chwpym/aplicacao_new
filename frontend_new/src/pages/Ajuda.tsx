import React from 'react';
import {
    Search,
    FlaskConical,
    HelpCircle,
    CheckCircle2,
    Info,
    ArrowRight,
    BookOpen
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const GuiaCard = ({ title, icon, children }: { title: string, icon: React.ReactNode, children: React.ReactNode }) => (
    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-3xl p-8 shadow-sm hover:shadow-md transition-all">
        <div className="flex items-center gap-4 mb-6">
            <div className="bg-primary/10 p-3 rounded-2xl text-primary">
                {icon}
            </div>
            <h3 className="text-xl font-bold">{title}</h3>
        </div>
        <div className="space-y-4">
            {children}
        </div>
    </div>
);

const Passo = ({ number, children }: { number: number, children: React.ReactNode }) => (
    <div className="flex gap-4">
        <div className="flex-shrink-0 w-8 h-8 bg-primary/10 border border-primary/20 rounded-xl flex items-center justify-center font-black text-primary text-sm">
            {number}
        </div>
        <div className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed pt-1">
            {children}
        </div>
    </div>
);

const Ajuda = () => {
    const navigate = useNavigate();

    return (
        <div className="max-w-5xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
            {/* Header */}
            <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-xs font-black uppercase tracking-widest">
                    <HelpCircle size={16} /> Central de Ajuda
                </div>
                <h1 className="text-4xl md:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
                    Como utilizar o <span className="text-primary">Gerenciador?</span>
                </h1>
                <p className="text-slate-500 max-w-2xl mx-auto text-lg">
                    Um guia completo para leigos e especialistas, para você dominar todas as ferramentas do sistema.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Básico */}
                <GuiaCard title="Nível Básico: O Dia a Dia" icon={<Search size={28} />}>
                    <p className="text-sm text-slate-500 mb-6 italic">
                        Ideal para quem precisa buscar peças e vender rápido no WhatsApp.
                    </p>
                    <div className="space-y-6">
                        <Passo number={1}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">Busca Rápida</span>: Digite o código da peça (ex: 1904) no Workspace e aperte Enter.
                        </Passo>
                        <Passo number={2}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">Filtros Visuais</span>: Use os seletores (Marca, Ano, Motor) para esconder o que você não quer ver.
                        </Passo>
                        <Passo number={3}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">Copiando para Venda</span>: Habilite o <span className="text-primary font-bold italic">Agrupar Resultados</span> e use o botão <span className="font-bold">Copiar Tudo</span>. O texto já sai pronto e bonitinho!
                        </Passo>
                    </div>
                    <div className="mt-8 p-4 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 rounded-2xl flex items-start gap-3">
                        <CheckCircle2 size={18} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                        <p className="text-[11px] text-emerald-700 dark:text-emerald-400 uppercase font-black tracking-tight">
                            Dica de Ouro: O sistema remove automaticamente marcas repetitivas!
                        </p>
                    </div>
                </GuiaCard>

                {/* Avançado */}
                <GuiaCard title="Nível Mestre: Novos Catálogos" icon={<FlaskConical size={28} />}>
                    <p className="text-sm text-slate-500 mb-6 italic">
                        Para quem quer cadastrar novas marcas e dominar o Playground.
                    </p>
                    <div className="space-y-6">
                        <Passo number={1}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">O Playground</span>: É o seu laboratório. Coloque a URL de um site (ex: indisa.comp.br/pecas/{'{id}'}) e veja se ele "pesca" as informações.
                        </Passo>
                        <Passo number={2}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">Mapeamento</span>: Diga ao sistema onde está a Marca ou o Ano no site usando seletores CSS ou nomes de campos JSON.
                        </Passo>
                        <Passo number={3}>
                            <span className="font-bold text-slate-900 dark:text-slate-100">Salvando</span>: Quando tudo estiver funcionando no Playground, basta clicar no botão de salvar para integrar a nova marca ao Workspace global.
                        </Passo>
                    </div>
                    <div className="mt-8 p-4 bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20 rounded-2xl flex flex-col gap-4">
                        <div className="flex items-start gap-3">
                            <Info size={18} className="text-amber-500 flex-shrink-0 mt-0.5" />
                            <p className="text-[11px] text-amber-700 dark:text-amber-400 uppercase font-black tracking-tight">
                                Lembrete: Leia O Manual Detalhado de Provedores para exemplos práticos!
                            </p>
                        </div>
                        <button 
                            onClick={() => navigate('/manual-provedores')}
                            className="bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400 rounded-xl py-2 px-4 text-xs font-bold flex items-center justify-center gap-2 transition-all w-full md:w-auto"
                        >
                            <BookOpen size={14} /> Ler Manual de Provedores (CRUD)
                        </button>
                    </div>
                </GuiaCard>
            </div>

            {/* Banner Suporte */}
            <div className="bg-slate-900 text-white rounded-[40px] p-10 flex flex-col md:flex-row items-center justify-between gap-8 overflow-hidden relative group">
                <div className="absolute -right-20 -top-20 w-64 h-64 bg-primary/20 rounded-full blur-3xl group-hover:bg-primary/30 transition-all duration-700"></div>

                <div className="space-y-4 relative z-10">
                    <h2 className="text-3xl font-black tracking-tight leading-tight">
                        Ainda com dúvidas ou <br />precisa de um <span className="text-primary italic">Catálogo Complexo?</span>
                    </h2>
                    <p className="text-slate-400 text-sm max-w-md uppercase font-bold tracking-widest">
                        Chame o suporte técnico para integrações via Playwright ou Scrapers protegidos.
                    </p>
                </div>

                <button className="bg-primary hover:bg-primary-hover text-white px-8 py-4 rounded-2xl font-black uppercase tracking-widest text-sm flex items-center gap-3 transition-all transform hover:scale-105 shadow-xl shadow-primary/20 relative z-10">
                    Falar com Suporte <ArrowRight size={20} />
                </button>
            </div>

            <footer className="text-center text-slate-400 text-[10px] uppercase font-bold tracking-[0.2em] pt-10">
                Gerenciador de Peças V4 | Desenvolvido com Antigravity DMA
            </footer>
        </div>
    );
};

export default Ajuda;
