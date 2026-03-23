
import { 
    BookOpen, 
    FlaskConical, 
    Globe, 
    Search, 
    Database, 
    Settings2,
    ArrowLeft
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ManualProvedores = () => {
    const navigate = useNavigate();

    return (
        <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in duration-500 pb-20">
            {/* Header com botão de voltar */}
            <div className="space-y-6">
                <button 
                    onClick={() => navigate('/ajuda')}
                    className="flex items-center gap-2 text-slate-500 hover:text-primary transition-colors font-bold text-sm"
                >
                    <ArrowLeft size={16} /> Voltar para Ajuda
                </button>
                
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-3xl p-10 shadow-sm relative overflow-hidden group">
                    <div className="absolute -right-20 -top-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-all duration-700"></div>
                    <div className="relative z-10 space-y-4">
                        <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-xs font-black uppercase tracking-widest">
                            <BookOpen size={16} /> Manual Oficial
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black tracking-tight text-slate-900 dark:text-white">
                            Gerenciando <span className="text-primary">Provedores</span>
                        </h1>
                        <p className="text-slate-500 max-w-2xl text-lg leading-relaxed">
                            Aprenda a criar, editar e testar qualquer provedor novo diretamente pelo Frontend, sem escrever uma linha de código Python. 
                        </p>
                        <div className="pt-2">
                            <button 
                                onClick={() => navigate('/documentacao')}
                                className="bg-primary hover:bg-primary-hover text-white font-black text-xs uppercase tracking-widest px-5 py-3 rounded-xl shadow-lg shadow-primary/20 flex items-center gap-2 animate-bounce"
                            >
                                <BookOpen size={16} /> Ver Documentação Completa (Avançado)
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* O Fluxo de Trabalho (Playground) */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                    <FlaskConical size={28} className="text-amber-500" />
                    <h2 className="text-2xl font-black tracking-tight">O Fluxo de Trabalho Seguro</h2>
                </div>
                <div className="bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/10 rounded-2xl p-6 sm:p-8">
                    <p className="text-amber-800 dark:text-amber-200 font-bold mb-6 text-lg">
                        Nunca salve um provedor direto no banco sem testar.
                    </p>
                    <ul className="space-y-4">
                        <li className="flex gap-4 items-start">
                            <div className="flex-shrink-0 w-8 h-8 bg-amber-200 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center font-black">1</div>
                            <p className="pt-1 text-slate-700 dark:text-slate-300">Acesse o menu <strong>Provedores</strong> e clique em <strong>Novo Provedor</strong>.</p>
                        </li>
                        <li className="flex gap-4 items-start">
                            <div className="flex-shrink-0 w-8 h-8 bg-amber-200 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center font-black">2</div>
                            <p className="pt-1 text-slate-700 dark:text-slate-300">Preencha os dados básicos (Nome, URL, Cabeçalhos). Ao invés de Salvar, clique em <strong className="text-amber-600 dark:text-amber-400">Testar no Playground</strong>.</p>
                        </li>
                        <li className="flex gap-4 items-start">
                            <div className="flex-shrink-0 w-8 h-8 bg-amber-200 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center font-black">3</div>
                            <p className="pt-1 text-slate-700 dark:text-slate-300">No Playground, digite um código de teste (ex: <code className="bg-white dark:bg-slate-900 px-2 rounded text-primary">1904</code>) e clique em TESTAR. Se a tabela carregar corretamente, retorne e salve!</p>
                        </li>
                    </ul>
                </div>
            </div>

            {/* Como Mapear: GraphQL */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                    <Globe size={28} className="text-blue-500" />
                    <h2 className="text-2xl font-black tracking-tight">Provedores GraphQL (Ex: Fraga)</h2>
                </div>
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                        A tecnologia GraphQL (padrão dos catálogos Fraga) é a mais fácil pois a estrutura de dados é sempre a mesma.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                            <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500 mb-2">Tipo de API</h4>
                            <p className="font-black text-slate-700 dark:text-slate-200">GraphQL Fraga</p>
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                            <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500 mb-2">URL Base</h4>
                            <code className="text-xs text-primary bg-primary/10 px-2 py-1 rounded">https://bff.catalogofraga.com.br/gateway/graphql</code>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500">Cabeçalhos JSON (Obrigatório)</h4>
                        <p className="text-sm text-slate-500">
                            A Fraga bloqueia robôs. Para liberar, você precisa "fingir" que é a página web deles enviando a Origem.
                        </p>
                        <pre className="p-4 bg-slate-900 text-emerald-400 font-mono text-sm rounded-xl overflow-x-auto">
{`{
  "Origin": "https://indisa.catalogofraga.com.br",
  "Referer": "https://indisa.catalogofraga.com.br/"
}`}
                        </pre>
                    </div>
                </div>
            </div>

            {/* Como Mapear: REST API */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                    <Search size={28} className="text-emerald-500" />
                    <h2 className="text-2xl font-black tracking-tight">Provedores REST / ERP (Ex: Nakata, Viemar)</h2>
                </div>
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                        Sua missão é ensinar ao nosso Painel qual é a "palavra inglesa" (ou chave) do JSON que o cliente devolve.
                    </p>
                    <div className="space-y-2">
                        <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500">URL Base com Parâmetro</h4>
                        <code className="text-xs text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-3 py-2 rounded-lg block">https://www.catalogonakata.com.br/detalhe/{"{id}"}</code>
                    </div>
                    <div className="space-y-2">
                        <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500">Lógica do FieldManager</h4>
                        <p className="text-sm text-slate-500">
                            Na aba "Mapeamento", insira a chave exata do JSON equivalente:
                        </p>
                        <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs">
                            <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                <span className="text-slate-400">container:</span> <strong className="text-emerald-600 dark:text-emerald-400">Obj.DetailApl</strong>
                                <span className="text-slate-400 text-[10px] hidden md:inline">Onde fica a lista principal?</span>
                            </div>
                            <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                <span className="text-slate-400">marca:</span> <strong className="text-emerald-600 dark:text-emerald-400">Montadora</strong>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-slate-400">veiculo:</span> <strong className="text-emerald-600 dark:text-emerald-400">Modelo</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Como Mapear: Scraper */}
            <div className="space-y-6">
                <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                    <Database size={28} className="text-rose-500" />
                    <h2 className="text-2xl font-black tracking-tight">Robô Scraper (Ex: DS)</h2>
                </div>
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                        O Scraper lê o site como um Humano. Nós usamos <strong>Seletores CSS</strong> para capturar as caixinhas na tela (o botão Inspecionar/F12 é seu melhor amigo).
                    </p>
                    <div className="space-y-2">
                        <h4 className="font-bold text-xs uppercase tracking-widest text-slate-500">Lógica CSS no FieldManager</h4>
                        <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs">
                            <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                <span className="text-slate-400">container:</span> <strong className="text-rose-500">.jq-apps tr</strong>
                                <span className="text-slate-400 text-[10px] hidden md:inline">A linha que agrupa a tabela</span>
                            </div>
                            <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                <span className="text-slate-400">veiculo:</span> <strong className="text-rose-500">td.modelo</strong>
                                <span className="text-slate-400 text-[10px] hidden md:inline">A coluna do nome do carro</span>
                            </div>
                            <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                <span className="text-slate-400">configuracao_motor:</span> <strong className="text-rose-500">td.complemento</strong>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-slate-400">imagem:</span> <strong className="text-rose-500">.pgwSlider img</strong>
                                <span className="text-slate-400 text-[10px] hidden md:inline">A tag de foto do produto</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Dica de Renomear Colunas */}
            <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 sm:p-8 flex items-start gap-4">
                <Settings2 size={32} className="text-primary mt-1 shrink-0" />
                <div>
                    <h3 className="text-lg font-black tracking-tight text-primary mb-2">Dica Pro: Renomeação Visual</h3>
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm">
                        No <strong>FieldManager</strong> você pode renomear os cabeçalhos das tabelas (ex: mudar "Configuracao Motor" para "Combustível"). Ao fazer isso, você força a Tabela final do sistema a exibir a nomenclatura customizada <strong>exclusivamente</strong> quando aquele Provedor for acionado!
                    </p>
                </div>
            </div>

        </div>
    );
};

export default ManualProvedores;
