import { useState, useEffect } from 'react';
import {
    FlaskConical,
    Database,
    Search,
    Code,
    Table,
    Save,
    Play,
    ChevronRight,
    Loader2,
    FileJson,
    Info,
    AlertCircle,
    Check,
    Copy,
    X,
    Settings,
    Package
} from 'lucide-react';
import { searchApi } from '../services/api';

const GRAPHQL_TEMPLATE = `query getProduct($id: String!, $market: MarketType!) {
  product(id: $id, market: $market) {
    id
    partNumber
    crossReferences {
      brand { name }
      partNumber
    }
    vehicles {
      brand
      name
      model
      engineName
      engineConfiguration
      startYear
      endYear
      note
    }
    images {
      imageUrl
    }
  }
}`;

const TEMPLATES = [
    {
        id: 'ds-template',
        nome: 'DS (Scraper)',
        tipo: 'ds',
        url: 'https://www.ds.ind.br/pt/busca-full?q={id}',
        mapeamento: JSON.stringify({
            container: '.jq-apps tr',
            marca: 'td.montadora',
            veiculo: 'td.modelo',
            modelo: 'td.modelo',
            motor: 'td.motor',
            configuracao_motor: 'td.complemento',
            observacao: 'td.observacoes',
            ano_inicio: 'td.ano',
            imagem: '.pgwSlider img',
            referencias: '.jq-codes tr',
            labels: {
                configuracao_motor: 'Combustível',
                observacao: 'Observações'
            }
        }, null, 2)
    },
    {
        id: 'sabo-template',
        nome: 'SABÓ (GraphQL)',
        tipo: 'graphql',
        url: 'https://bff.catalogofraga.com.br/gateway/graphql',
        query: GRAPHQL_TEMPLATE,
        headers: JSON.stringify({
            "Referer": "https://catalogo.sabo.com.br/",
            "Origin": "https://catalogo.sabo.com.br"
        }, null, 2),
        mapeamento: JSON.stringify({
            marca: 'brand',
            veiculo: 'name',
            motor: 'engineName',
            ano_inicio: 'startYear',
            imagem: 'images'
        }, null, 2)
    },
    {
        id: 'ima-template',
        nome: 'IMA (GraphQL)',
        tipo: 'graphql',
        url: 'https://bff.catalogofraga.com.br/gateway/graphql',
        query: GRAPHQL_TEMPLATE,
        headers: JSON.stringify({
            "Referer": "https://catalogoi.com.br/",
            "Origin": "https://catalogoi.com.br"
        }, null, 2),
        mapeamento: JSON.stringify({
            marca: 'brand',
            veiculo: 'name',
            motor: 'engineName',
            ano_inicio: 'startYear',
            imagem: 'images'
        }, null, 2)
    },
    {
        id: 'ampri-template',
        nome: 'AMPRI (GraphQL)',
        tipo: 'graphql',
        url: 'https://bff.catalogofraga.com.br/gateway/graphql',
        query: GRAPHQL_TEMPLATE,
        headers: JSON.stringify({
            "Referer": "https://catalogodepecasampri.com.br/",
            "Origin": "https://catalogodepecasampri.com.br"
        }, null, 2),
        mapeamento: JSON.stringify({
            marca: 'brand',
            veiculo: 'name',
            motor: 'engineName',
            ano_inicio: 'startYear',
            imagem: 'images'
        }, null, 2)
    },
    {
        id: 'generic-scraper',
        nome: 'Generic Scraper Base',
        tipo: 'scraper',
        url: 'https://exemplo.com/busca?q={id}',
        mapeamento: JSON.stringify({
            marca: '.marca',
            veiculo: '.nome',
            motor: '.motor',
            ano_inicio: '.ano',
            imagem: 'img.foto'
        }, null, 2)
    },
    {
        id: 'wega-template',
        nome: 'WEGA (API REST)',
        tipo: 'rest',
        url: 'https://wega.wedigi.com.br/api/v1/produto?cod={id}',
        headers: JSON.stringify({
            "Origin": "https://wegamotors.com",
            "Referer": "https://wegamotors.com/"
        }, null, 2),
        mapeamento: JSON.stringify({
            "container": "Obj.DetailApl",
            "marca": "Montadora",
            "veiculo": "Modelo",
            "modelo": "DescModelo",
            "motor": "Motor",
            "ano_inicio": "Ano",
            "referencias": "root:Obj.DetailConv",
            "ref_marca": "Marca",
            "ref_codigo": "CodigoConcorrente"
        }, null, 2)
    }
];

const Playground = () => {
    const [configs, setConfigs] = useState({
        nome: 'Novo Teste',
        tipo: 'scraper',
        url: '',
        headers: '{}',
        query: '',
        mapeamento: '{}',
        login_required: false,
        username: '',
        password: ''
    });

    const [testId, setTestId] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [viewMode, setViewMode] = useState<'table' | 'json'>('table');
    const [drafts, setDrafts] = useState<any[]>([]);
    const [error, setError] = useState<string | null>(null);

    // Modals visibility
    const [showLibrary, setShowLibrary] = useState(false);
    const [showInstructions, setShowInstructions] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const helperTexts: Record<string, { steps: string[], tips: string[] }> = {
        rest: {
            steps: [
                "Localize a URL da API no portal (Inspeção -> Network -> Fetch/XHR).",
                "Substitua o código da peça na URL por {id}.",
                "Mapeie os campos JSON no campo de mapeamento (ex: brand: 'marca')."
            ],
            tips: [
                "Botão direito -> Inspecionar -> Rede (Network).",
                "Filtre por 'XHR'.",
                "Copie 'Request URL' e veja o 'Preview' para os nomes dos campos."
            ]
        },
        graphql: {
            steps: [
                "Identifique o endpoint de GraphQL (geralmente termina em /graphql).",
                "Copie a Query do painel Network (Payload).",
                "Certifique-se de usar variáveis como $id e $market."
            ],
            tips: [
                "Procure por requisições do tipo 'POST'.",
                "Na aba 'Payload', clique em 'view source' para ver a Query bruta.",
                "Copie Referer e Origin se a API retornar erro de permissão."
            ]
        },
        scraper: {
            steps: [
                "Identifique a URL de busca do site e use {id}.",
                "Use seletores CSS para encontrar o container dos resultados (ex: tr, .item).",
                "Defina seletores para cada campo (ex: td.modelo, .preco)."
            ],
            tips: [
                "Use a tecla F12.",
                "Clique na setinha (Select element) e aponte para o dado no site.",
                "O 'SelectorHub' (extensão) ajuda muito a achar seletores curtos."
            ]
        }
    };

    const currentHelp = helperTexts[configs.tipo] || helperTexts['scraper'];

    useEffect(() => {
        const saved = localStorage.getItem('playground_drafts');
        if (saved) setDrafts(JSON.parse(saved));

        const auto = localStorage.getItem('playground_auto_load');
        if (auto) {
            try {
                const draft = JSON.parse(auto);
                setConfigs(draft);
                localStorage.removeItem('playground_auto_load');
            } catch { }
        }
    }, []);

    const handleLoadTemplate = (tpl: any) => {
        setConfigs({
            ...configs,
            nome: `Teste: ${tpl.nome}`,
            tipo: tpl.tipo,
            url: tpl.url,
            headers: tpl.headers || '{}',
            query: tpl.query || '',
            mapeamento: tpl.mapeamento || '{}'
        });
        setError(null);
        setShowLibrary(false);
    };

    const handleSaveDraft = () => {
        const newDraft = { ...configs, id: Date.now(), date: new Date().toISOString() };
        const nextDrafts = [newDraft, ...drafts].slice(0, 10);
        setDrafts(nextDrafts);
        localStorage.setItem('playground_drafts', JSON.stringify(nextDrafts));
        alert('Rascunho salvo com sucesso!');
    };

    const handleRunTest = async () => {
        if (!testId) {
            setError('Digite um código de peça para testar.');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await searchApi.testarProvedor(testId, configs);
            setResults(response.data);
            if (response.data.length === 0) {
                setError('Nenhum dado extraído. Verifique os seletores ou a URL.');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Erro ao realizar o teste.');
        } finally {
            setLoading(false);
        }
    };

    const getFieldLabel = (field: string) => {
        try {
            const m = JSON.parse(configs.mapeamento);
            if (m.labels && m.labels[field]) return m.labels[field];
        } catch { }

        const defaults: any = {
            marca: 'Marca',
            veiculo: 'Veículo',
            modelo: 'Modelo',
            motor: 'Motor',
            configuracao_motor: 'Combustível',
            ano: 'Ano',
            imagem: 'Imagens',
            referencias: 'Referências',
            observacao: 'Observação'
        };
        return defaults[field] || field;
    };

    // Modal Wrapper Component
    const Modal = ({ isOpen, onClose, title, icon, children }: { isOpen: boolean, onClose: () => void, title: string, icon: any, children: React.ReactNode }) => {
        if (!isOpen) return null;
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200 uppercase">
                <div className="bg-surface-light dark:bg-surface-dark w-full max-w-2xl rounded-[32px] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                    <div className="px-8 py-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0">
                        <div className="flex items-center gap-4">
                            <div className="bg-primary/10 p-2 rounded-xl text-primary">
                                {icon}
                            </div>
                            <h3 className="text-xl font-bold">{title}</h3>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <X size={24} />
                        </button>
                    </div>
                    <div className="p-8 overflow-y-auto custom-scrollbar">
                        {children}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col gap-6 h-[calc(100vh-120px)] animate-in fade-in duration-500">
            {/* Top Toolbar: Compact & Efficient */}
            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-[32px] p-4 md:p-6 shadow-sm flex flex-col gap-6">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <div className="bg-primary p-3 rounded-2xl shadow-lg shadow-primary/30 text-white shrink-0">
                            <FlaskConical size={28} />
                        </div>
                        <div className="flex flex-col">
                            <h2 className="text-xl font-black tracking-tight leading-none">Playground V2</h2>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Laboratório de Testes</p>
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto uppercase">
                        <button
                            onClick={() => setShowLibrary(true)}
                            className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-4 py-2.5 rounded-xl text-xs font-black flex items-center gap-2 transition-all"
                        >
                            <Database size={16} /> Biblioteca
                        </button>
                        <button
                            onClick={() => setShowInstructions(true)}
                            className="bg-amber-100 dark:bg-amber-500/10 hover:bg-amber-200 dark:hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 px-4 py-2.5 rounded-xl text-xs font-black flex items-center gap-2 transition-all"
                        >
                            <Info size={16} /> Como Usar?
                        </button>
                        <button
                            onClick={() => setShowAdvanced(true)}
                            className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2.5 rounded-xl text-xs font-black flex items-center gap-2 transition-all"
                        >
                            <Code size={16} /> Mapeamento
                        </button>
                    </div>
                </div>

                {/* Main Inputs */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                    <div className="md:col-span-2">
                        <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 block">Tipo de API</label>
                        <select
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs font-bold outline-none focus:ring-2 focus:ring-primary/20 appearance-none uppercase"
                            value={configs.tipo}
                            onChange={(e) => setConfigs({ ...configs, tipo: e.target.value })}
                        >
                            <option value="graphql">GraphQL</option>
                            <option value="rest">REST API</option>
                            <option value="scraper">Scraper</option>
                            <option value="ds">Site DS</option>
                        </select>
                    </div>
                    <div className="md:col-span-5">
                        <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 block">URL do Provedor</label>
                        <input
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs font-bold font-mono outline-none focus:ring-2 focus:ring-primary/20"
                            placeholder="https://site.com/pecas/{id}"
                            value={configs.url}
                            onChange={(e) => setConfigs({ ...configs, url: e.target.value })}
                        />
                    </div>
                    <div className="md:col-span-3">
                        <label className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5 block">Código de Teste</label>
                        <input
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs font-black outline-none focus:ring-2 focus:ring-primary/20"
                            placeholder="Ex: 1904"
                            value={testId}
                            onChange={(e) => setTestId(e.target.value)}
                        />
                    </div>
                    <div className="md:col-span-2 flex items-end gap-2">
                        <button
                            onClick={handleRunTest}
                            disabled={loading}
                            className="flex-1 bg-primary text-white h-[42px] rounded-xl font-black text-xs flex items-center justify-center gap-2 hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all disabled:opacity-50"
                        >
                            {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                            TESTAR
                        </button>
                        <button
                            onClick={handleSaveDraft}
                            className="w-[42px] h-[42px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center rounded-xl text-slate-500 transition-all"
                            title="Salvar Rascunho"
                        >
                            <Save size={18} />
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 rounded-2xl p-4 flex items-center gap-3 text-rose-600 dark:text-rose-400 text-xs font-bold animate-in bounce-in duration-300">
                        <AlertCircle size={20} />
                        <span>{error}</span>
                    </div>
                )}
            </div>

            {/* Results Area */}
            <div className="flex-1 bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-[32px] shadow-sm flex flex-col overflow-hidden">
                <div className="px-8 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/30 dark:bg-slate-900/30 shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] border-r border-slate-200 dark:border-slate-800 pr-4 mr-1">
                            Resultados
                        </div>
                        <div className="bg-primary/10 text-primary text-[10px] font-black px-3 py-1 rounded-full uppercase">
                            {results.length} Itens Encontrados
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => {
                                navigator.clipboard.writeText(JSON.stringify(results, null, 2));
                                alert('JSON copiado!');
                            }}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-black transition-all"
                            disabled={results.length === 0}
                        >
                            <Copy size={16} /> JSON
                        </button>
                        <div className="flex bg-slate-200/50 dark:bg-slate-800/50 p-1 rounded-xl">
                            <button
                                onClick={() => setViewMode('table')}
                                className={`p-2 rounded-lg transition-all ${viewMode === 'table' ? 'bg-white dark:bg-slate-700 text-primary shadow-md' : 'text-slate-400 hover:text-slate-600'}`}
                                title="Visualizar em Tabela"
                            >
                                <Table size={18} />
                            </button>
                            <button
                                onClick={() => setViewMode('json')}
                                className={`p-2 rounded-lg transition-all ${viewMode === 'json' ? 'bg-white dark:bg-slate-700 text-primary shadow-md' : 'text-slate-400 hover:text-slate-600'}`}
                                title="Visualizar JSON Bruto"
                            >
                                <FileJson size={18} />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-auto custom-scrollbar">
                    {results.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-slate-700 gap-6">
                            <div className="relative">
                                <Search size={80} className="opacity-20 translate-x-1 translate-y-1" />
                                <FlaskConical size={80} className="opacity-10 absolute inset-0 text-primary" />
                            </div>
                            <div className="text-center font-bold uppercase tracking-widest text-xs opacity-40">
                                Nenhum teste executado ainda.<br />Utilize o botão <span className="text-primary italic">Testar</span> acima.
                            </div>
                        </div>
                    ) : viewMode === 'table' ? (
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-slate-50/80 dark:bg-slate-900/80 text-slate-400 uppercase text-[9px] font-black tracking-widest sticky top-0 z-10 backdrop-blur-md">
                                <tr>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800">{getFieldLabel('marca')}</th>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800">{getFieldLabel('veiculo')}</th>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800">{getFieldLabel('motor')}</th>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800">{getFieldLabel('configuracao_motor')}</th>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800">Ano</th>
                                    <th className="px-8 py-5 border-b border-slate-150 dark:border-slate-800 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {results.map((res: any, i: number) => (
                                    <tr key={i} className="hover:bg-primary/[0.02] transition-colors group">
                                        <td className="px-8 py-4 font-black text-primary text-[10px] uppercase tracking-wider">{res.marca}</td>
                                        <td className="px-8 py-4 text-sm font-bold text-slate-700 dark:text-slate-200">{res.veiculo}</td>
                                        <td className="px-8 py-4 text-xs font-bold text-slate-500 dark:text-slate-400">{res.motor}</td>
                                        <td className="px-8 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-tight">{res.configuracao_motor || '---'}</td>
                                        <td className="px-8 py-4 text-xs font-black font-mono">
                                            {res.ano_inicio || res.ano_fim ? `${res.ano_inicio || ''}..${res.ano_fim || ''}` : '---'}
                                        </td>
                                        <td className="px-8 py-4 flex justify-center">
                                            <span className="bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-tighter">SUCESSO</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <pre className="p-8 text-[11px] font-mono text-emerald-500 dark:text-emerald-400 bg-slate-900 h-full overflow-auto leading-relaxed">
                            {JSON.stringify(results, null, 2)}
                        </pre>
                    )}
                </div>
            </div>

            {/* Modals Implementation */}

            {/* Library Modal: Templates & Drafts */}
            <Modal
                isOpen={showLibrary}
                onClose={() => setShowLibrary(false)}
                title="Biblioteca de Provedores"
                icon={<Database size={20} />}
            >
                <div className="space-y-8 uppercase">
                    <div>
                        <h4 className="text-[10px] font-black text-slate-400 tracking-[0.2em] mb-4">Templates Originais</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {TEMPLATES.map(tpl => (
                                <button
                                    key={tpl.id}
                                    onClick={() => handleLoadTemplate(tpl)}
                                    className="text-left p-4 rounded-2xl border border-slate-100 dark:border-slate-800 hover:border-primary/30 hover:bg-primary/5 transition-all group"
                                >
                                    <div className="text-xs font-black mb-1 flex items-center justify-between">
                                        {tpl.nome}
                                        <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all text-primary" />
                                    </div>
                                    <div className="text-[9px] font-bold text-slate-400">{tpl.tipo.toUpperCase()} • {tpl.url.substring(0, 30)}...</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="text-[10px] font-black text-slate-400 tracking-[0.2em]">Seus Rascunhos Recentes</h4>
                            <button
                                onClick={() => { setDrafts([]); localStorage.removeItem('playground_drafts'); }}
                                className="text-[9px] font-black text-rose-500 hover:underline"
                            >
                                Limpar Tudo
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {drafts.length === 0 ? (
                                <div className="col-span-2 text-center py-10 text-[10px] font-bold text-slate-400 border-2 border-dashed border-slate-100 dark:border-slate-800 rounded-2xl">
                                    Nenhum rascunho salvo ainda.
                                </div>
                            ) : (
                                drafts.map((d: any) => (
                                    <button
                                        key={d.id}
                                        onClick={() => { setConfigs(d); setShowLibrary(false); }}
                                        className="text-left p-4 rounded-2xl border border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-600 transition-all"
                                    >
                                        <div className="text-xs font-black truncate">{d.nome}</div>
                                        <div className="text-[9px] font-bold text-slate-400 mt-1">{new Date(d.date).toLocaleDateString()} • {d.tipo.toUpperCase()}</div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </Modal>

            {/* Instructions Modal */}
            <Modal
                isOpen={showInstructions}
                onClose={() => setShowInstructions(false)}
                title="Manual de Instruções"
                icon={<Info size={20} />}
            >
                <div className="space-y-8 uppercase">
                    <div className="bg-primary/5 dark:bg-primary/10 rounded-2xl p-6 border border-primary/20">
                        <div className="flex items-center gap-3 text-primary mb-6">
                            <Play size={18} />
                            <h4 className="text-sm font-black tracking-widest leading-none">Guia {configs.tipo.toUpperCase()}</h4>
                        </div>
                        <div className="space-y-4">
                            {currentHelp.steps.map((step, idx) => (
                                <div key={idx} className="flex gap-4">
                                    <div className="shrink-0 w-6 h-6 bg-primary text-white text-[10px] font-black rounded-lg flex items-center justify-center">{idx + 1}</div>
                                    <p className="text-xs font-bold leading-relaxed pt-1 text-slate-600 dark:text-slate-400">{step}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <h5 className="text-[10px] font-black text-slate-400 tracking-widest flex items-center gap-2">
                                <Search size={14} /> Dicas Extras
                            </h5>
                            <div className="space-y-3">
                                {currentHelp.tips.map((tip, idx) => (
                                    <div key={idx} className="flex items-start gap-3">
                                        <Check size={14} className="text-emerald-500 mt-0.5 shrink-0" />
                                        <span className="text-[10px] font-bold text-slate-500">{tip}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-800 flex flex-col items-center justify-center text-center gap-3">
                            <Package size={32} className="text-slate-300" />
                            <p className="text-[9px] font-bold text-slate-400 leading-tight">Use F12 e a aba Network para capturar dados em tempo real.</p>
                        </div>
                    </div>
                </div>
            </Modal>

            {/* Advanced Configuration Modal */}
            <Modal
                isOpen={showAdvanced}
                onClose={() => setShowAdvanced(false)}
                title="Mapeamento e Filtros"
                icon={<Code size={20} />}
            >
                <div className="space-y-6">
                    {/* Campos de Mapeamento (Visual) */}
                    {configs.tipo !== 'graphql' && (
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                <span className="flex items-center gap-2"><Database size={14} /> Campos de Mapeamento</span>
                                <span className="text-slate-400/50 italic">Sincronizado com o JSON abaixo</span>
                            </div>
                            <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                                {['container', 'product_link', 'marca', 'veiculo', 'modelo', 'motor', 'configuracao_motor', 'ano_inicio', 'ano_fim', 'imagem', 'image_pattern', 'referencias', 'ref_marca', 'ref_codigo', 'observacao'].map(field => {
                                    const labels: Record<string, string> = {
                                        veiculo: 'Nome do Carro',
                                        modelo: 'Modelo / Versão',
                                        configuracao_motor: 'Combustível / Detalhes',
                                        ano_inicio: 'Ano Inicial',
                                        ano_fim: 'Ano Final',
                                        image_pattern: 'Padrão Imagem ({id})',
                                        product_link: 'Link da Página',
                                        ref_marca: 'Ref: Marca',
                                        ref_codigo: 'Ref: Código'
                                    };
                                    const label = labels[field] || field.toUpperCase().replace('_', ' ');
                                    
                                    let fieldValue = '';
                                    try {
                                        const m = JSON.parse(configs.mapeamento);
                                        fieldValue = m[field] || '';
                                    } catch { }

                                    return (
                                        <div key={field} className="space-y-1">
                                            <label className="text-[9px] font-bold text-slate-500 uppercase">{label}</label>
                                            <input
                                                className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-[10px] outline-none focus:border-primary font-mono transition-all"
                                                placeholder={configs.tipo === 'rest' ? `Atributo: ${field}` : `CSS: .${field}`}
                                                value={fieldValue}
                                                onChange={(e) => {
                                                    const val = e.target.value;
                                                    let currentMap = {};
                                                    try { currentMap = JSON.parse(configs.mapeamento); } catch { }
                                                    const nextMap = { ...currentMap, [field]: val };
                                                    setConfigs({ ...configs, mapeamento: JSON.stringify(nextMap, null, 2) });
                                                }}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center justify-between gap-2">
                            <span className="flex items-center gap-2">
                                {configs.tipo === 'graphql' ? <Code size={14} /> : <Database size={14} />}
                                {configs.tipo === 'graphql' ? 'Query GraphQL' : 'JSON Raw de Mapeamento'}
                            </span>
                            {configs.tipo !== 'graphql' && <span className="text-primary/50 text-[9px] lowercase italic font-normal">Edite aqui para preencher os campos acima</span>}
                        </label>
                        <textarea
                            rows={10}
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl px-5 py-4 text-xs outline-none focus:ring-2 focus:ring-primary/20 font-mono custom-scrollbar"
                            value={configs.tipo === 'graphql' ? configs.query : configs.mapeamento}
                            onChange={(e) => setConfigs({ ...configs, [configs.tipo === 'graphql' ? 'query' : 'mapeamento']: e.target.value })}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                            <Settings size={14} /> Headers JSON (Segurança)
                        </label>
                        <input
                            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-5 py-3 text-xs outline-none focus:ring-2 focus:ring-primary/20 font-mono"
                            placeholder='{"Referer": "https://..."}'
                            value={configs.headers}
                            onChange={(e) => setConfigs({ ...configs, headers: e.target.value })}
                        />
                    </div>

                    <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                        <button
                            onClick={() => setShowAdvanced(false)}
                            className="w-full bg-primary text-white py-4 rounded-2xl font-black uppercase tracking-widest text-xs hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all"
                        >
                            Confirmar Configuração
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default Playground;
