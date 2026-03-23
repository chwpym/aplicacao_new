import { useState } from 'react';
import { 
    Globe, 
    Search, 
    Database, 
    Settings, 
    Terminal, 
    AlertTriangle, 
    CheckCircle2,
    ArrowLeft,
    Lightbulb
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const SECTIONS = [
    { id: 'fluxo', label: 'Fluxo de Trabalho', icon: <CheckCircle2 size={16} /> },
    { id: 'graphql', label: 'Provedores GraphQL', icon: <Globe size={16} /> },
    { id: 'rest', label: 'Provedores REST API', icon: <Search size={16} /> },
    { id: 'scraper', label: 'Robôs Scraper (HTML)', icon: <Database size={16} /> },
    { id: 'mapeamento', label: 'Field Manager & Labels', icon: <Settings size={16} /> },
    { id: 'debug', label: 'F12 e Diagnóstico', icon: <Terminal size={16} /> },
];

export default function Documentacao() {
    const navigate = useNavigate();
    const [activeSection, setActiveSection] = useState('fluxo');

    const scrollToSection = (id: string) => {
        setActiveSection(id);
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    return (
        <div className="flex flex-col md:flex-row gap-8 max-w-7xl mx-auto items-start animate-in fade-in duration-500 pb-20">
            {/* Sidebar de Navegação */}
            <aside className="w-full md:w-64 shrink-0 bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sticky top-8 flex flex-col gap-2 shadow-sm">
                <button 
                    onClick={() => navigate('/manual-provedores')}
                    className="flex items-center gap-2 text-slate-500 hover:text-primary transition-colors font-bold text-xs uppercase mb-4"
                >
                    <ArrowLeft size={14} /> Manual Simples
                </button>
                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 px-2">Navegação</div>
                <nav className="flex flex-col gap-1">
                    {SECTIONS.map(sec => (
                        <button
                            key={sec.id}
                            onClick={() => scrollToSection(sec.id)}
                            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                                activeSection === sec.id 
                                ? 'bg-primary text-white shadow-lg shadow-primary/25 font-bold translate-x-1' 
                                : 'hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-600 dark:text-slate-400'
                            }`}
                        >
                            {sec.icon}
                            <span>{sec.label}</span>
                        </button>
                    ))}
                </nav>
            </aside>

            {/* Conteúdo Principal */}
            <div className="flex-1 space-y-16">
                
                {/* ID: Fluxo */}
                <section id="fluxo" className="scroll-mt-8 space-y-6">
                    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-3xl p-8 shadow-sm">
                        <div className="inline-flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest mb-4">
                            <CheckCircle2 size={16} /> Boas Práticas
                        </div>
                        <h2 className="text-3xl font-black tracking-tight mb-4">O Fluxo de Trabalho Seguro</h2>
                        <p className="text-slate-500 leading-relaxed mb-6">
                            Adicionar um provedor afeta as buscas globais do sistema. Para garantir que nada quebre para os outros usuários, siga o fluxo abaixo à risca:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800">
                                <h4 className="font-black text-sm text-slate-700 dark:text-slate-200 mb-1">1. Rascunho Inicial</h4>
                                <p className="text-xs text-slate-500">Abra a aba Provedores, crie um novo e preencha a URL e Nome. Não salve ainda.</p>
                            </div>
                            <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800">
                                <h4 className="font-black text-sm text-slate-700 dark:text-slate-200 mb-1">2. Playground</h4>
                                <p className="text-xs text-slate-500">Clique em "Testar no Playground". Ele levará seus dados para uma sandbox segura de testes.</p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ID: GraphQL */}
                <section id="graphql" className="scroll-mt-8 space-y-4">
                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                        <Globe size={24} className="text-blue-500" /> Provedores GraphQL
                    </h2>
                    <p className="text-slate-500 text-sm leading-relaxed">
                         GraphQL é uma linguagem de consulta. A vantagem da rede Fraga (Cofap, Indisa, Sabó) é usar sempre a mesma estrutura.
                    </p>
                    <div className="bg-slate-900 rounded-2xl p-6 text-white space-y-4">
                        <div className="flex justify-between items-center text-xs text-slate-400">
                            <span>Exemplo de Query (GraphQL)</span>
                            <span className="bg-slate-800 px-2 py-1 rounded">Read-only</span>
                        </div>
                        <pre className="text-xs font-mono text-emerald-400 overflow-x-auto leading-relaxed">
{`query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    vehicles {
       brand
       name
       model
       engineName
    }
  }
}`}
                        </pre>
                    </div>
                    <div className="bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/10 rounded-xl p-4 flex gap-3">
                        <AlertTriangle size={20} className="text-amber-500 shrink-0 mt-0.5" />
                        <div>
                            <h5 className="font-black text-amber-800 dark:text-amber-300 text-xs">Cuidado com Bloqueio de CORS</h5>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">Sempre preencha os headers "Origin" e "Referer" com a URL real do catálogo em testes.</p>
                        </div>
                    </div>
                </section>

                {/* ID: REST */}
                <section id="rest" className="scroll-mt-8 space-y-4">
                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                        <Search size={24} className="text-emerald-500" /> Provedores REST API
                    </h2>
                    <p className="text-slate-500 text-sm leading-relaxed">
                        Em APIs REST, a chamada geralmente devolve um JSON simples ao acessar uma URL que contém o ID da peça.
                    </p>
                    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 space-y-4">
                        <div className="space-y-1">
                            <span className="text-[10px] font-black text-slate-400 uppercase">Uso de Variáveis</span>
                            <p className="text-xs text-slate-600">Substitua o código da pesquisa por <code className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-primary font-bold">{"{id}"}</code> em qualquer lugar da URL.</p>
                            <code className="text-xs block bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-3 rounded-xl mt-2">
                                https://api.site.com/produtos/{"{id}"}/aplicacoes
                            </code>
                        </div>
                    </div>
                </section>

                {/* ID: Scraper */}
                <section id="scraper" className="scroll-mt-8 space-y-4">
                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                        <Database size={24} className="text-rose-500" /> Robôs Scraper (HTML)
                    </h2>
                    <p className="text-slate-500 text-sm leading-relaxed">
                        O Scraper faz uma varredura visual. Use os selectores CSS padrão da Web para resgatar os valores das células das linhas (`tr td`).
                    </p>
                    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
                        <ul className="space-y-3">
                            <li className="flex justify-between items-center text-sm border-b border-slate-100 dark:border-slate-800 pb-2">
                                <span className="font-bold text-slate-700 dark:text-slate-300">container:</span>
                                <code className="bg-slate-100 dark:bg-slate-800 p-1 rounded text-rose-500 text-xs">.tabela-corpo tr</code>
                            </li>
                            <li className="flex justify-between items-center text-sm border-b border-slate-100 dark:border-slate-800 pb-2">
                                <span className="font-bold text-slate-700 dark:text-slate-300">marca:</span>
                                <code className="bg-slate-100 dark:bg-slate-800 p-1 rounded text-rose-500 text-xs">td.marca</code>
                            </li>
                        </ul>
                    </div>
                </section>

                {/* ID: Mapeamento */}
                <section id="mapeamento" className="scroll-mt-8 space-y-4">
                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                        <Settings size={24} className="text-violet-500" /> Field Manager & Labels
                    </h2>
                    <p className="text-slate-500 text-sm leading-relaxed">
                        O painel de mapeamento serve para duas coisas: apontar de onde vem o dado e como ele deve se chamar na tela final.
                    </p>
                    <div className="bg-violet-500/5 border border-violet-500/10 rounded-2xl p-6 flex items-start gap-4">
                        <Lightbulb size={24} className="text-violet-500 mt-1 shrink-0" />
                        <div>
                            <h4 className="font-black text-violet-900 dark:text-violet-400 text-sm mb-1">Mapear é diferente de Renomear</h4>
                            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                                A caixa à direita serve para você mudar o nome da Coluna na Grade do Workspace. Se você mapear "veiculo" p/ "Model" do JSON, você pode renomear visualmente no FieldManager para "Meu Carro" e o sistema obedecerá.
                            </p>
                        </div>
                    </div>
                </section>

                {/* ID: Debug */}
                <section id="debug" className="scroll-mt-8 space-y-4">
                    <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                        <Terminal size={24} className="text-slate-500" /> Inspeção (F12) e Diagnóstico
                    </h2>
                    <p className="text-slate-500 text-sm leading-relaxed">
                        Para descobrir o que colocar no Mapeamento ou se a chamada está funcionando, abra o console do navegador.
                    </p>
                    <div className="bg-slate-100 dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800">
                        <ol className="list-decimal list-inside text-xs text-slate-600 dark:text-slate-400 space-y-2 font-semibold">
                            <li>Abra o Chrome no catálogo de origem que você quer copiar.</li>
                            <li>Aperte <kbd className="bg-white dark:bg-slate-800 border rounded px-1 shadow-sm">F12</kbd> e vá na aba **Network (Rede)**.</li>
                            <li>Pesquise pela peça no site deles.</li>
                            <li>Identifique a linha com o nome da Action (ex: Search, Detail) e clique nela.</li>
                            <li>Veja a aba **Response (Resposta)** ou **Preview**. Os nomes dos campos que estão lá devem ser colocados no FieldManager.</li>
                        </ol>
                    </div>
                </section>

            </div>
        </div>
    );
}
