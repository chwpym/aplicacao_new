import { useState, useEffect } from 'react';
import { Save, RotateCcw, Eye, EyeOff, Database, RefreshCw } from 'lucide-react';
import { configApi } from '../services/api';
import { toast } from '../utils/toast';
import ConfirmModal from '../components/ConfirmModal';
import { ConfiguracoesImagens } from '../components/ConfiguracoesImagens';

const PREF_KEY = 'colunas_visiveis';

const allFields = [
    { id: 'marca', label: 'Marca Peça' },
    { id: 'codigo', label: 'Cód. Peça' },
    { id: 'veiculo', label: 'Montadora' },
    { id: 'modelo', label: 'Veículo' },
    { id: 'versao', label: 'Modelo' },
    { id: 'motor', label: 'Motor' },
    { id: 'configuracao_motor', label: 'Config. Motor' },
    { id: 'combustivel', label: 'Combustível' },
    { id: 'ano', label: 'Ano' },
    { id: 'imagem', label: 'Imagens' },
    { id: 'referencias', label: 'Referências OE' },
    { id: 'observacao', label: 'Observações' },
    { id: 'posicao', label: 'Posição' },
    { id: 'lado', label: 'Lado' },
    { id: 'direcao', label: 'Direção' },
    { id: 'sistema_freio', label: 'Sistema Freio' },
    { id: 'restricao', label: 'Restrição' },
    { id: 'apenas', label: 'Apenas' },
    { id: 'ficha_tecnica', label: 'Ficha Técnica' },
];

const factoryDefaults: Record<string, boolean> = {
    marca: true, codigo: false, veiculo: true, modelo: true, versao: true,
    motor: true, configuracao_motor: true, combustivel: true, ano: true,
    imagem: false, referencias: false, observacao: false, posicao: false,
    lado: false, direcao: false, sistema_freio: false, restricao: false,
    apenas: false, ficha_tecnica: true,
};

const Configuracoes = () => {
    const [fields, setFields] = useState<Record<string, boolean>>({});
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [automakerInfo, setAutomakerInfo] = useState<any>(null);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'grade' | 'imagens' | 'manutencao'>('grade');

    useEffect(() => {
        loadPreferences();
        loadAutomakerInfo();
    }, []);

    const loadAutomakerInfo = async () => {
        try {
            const response = await configApi.getAutomakersInfo();
            setAutomakerInfo(response.data);
        } catch (error) {
            console.error("Erro ao carregar info de montadoras:", error);
        }
    };

    const handleSyncFipe = async () => {
        setSyncing(true);
        try {
            const response = await configApi.syncFipe();
            toast.success(response.data.message || "Sincronização iniciada com sucesso!");
            // Polling simples: busca info novamente após 5 segundos para ver se já mudou algo
            setTimeout(loadAutomakerInfo, 5000);
        } catch (error) {
            console.error("Erro ao sincronizar FIPE:", error);
            toast.error("Falha ao iniciar sincronização. Tente novamente mais tarde.");
        } finally {
            setSyncing(false);
        }
    };

    const loadPreferences = async () => {
        setLoading(true);
        try {
            const response = await configApi.getPreferencias(PREF_KEY);
            if (response.data && response.data.valor) {
                setFields({ ...factoryDefaults, ...JSON.parse(response.data.valor) });
            } else {
                // Tenta fallback do localStorage antigo para migração suave
                const raw = localStorage.getItem('visibleFieldsDefault');
                if (raw) setFields({ ...factoryDefaults, ...JSON.parse(raw) });
                else setFields({ ...factoryDefaults });
            }
        } catch (error) {
            console.error("Erro ao carregar preferências:", error);
            toast.error("Erro ao carregar suas preferências padrão.");
            setFields({ ...factoryDefaults });
        } finally {
            setLoading(false);
        }
    };

    const toggle = (id: string) => {
        setSaved(false);
        setFields(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleSave = async () => {
        try {
            await configApi.savePreferencias(PREF_KEY, fields);
            // Também salva no localStorage para garantir carregamento instantâneo no useCatalog
            localStorage.setItem('visibleFieldsDefault', JSON.stringify(fields));
            setSaved(true);
            toast.success("Suas preferências padrão foram salvas!");
            setTimeout(() => setSaved(false), 3000);
        } catch (error) {
            console.error("Erro ao salvar preferências:", error);
            toast.error("Erro ao salvar preferências no banco de dados.");
        }
    };

    const handleReset = () => {
        setFields({ ...factoryDefaults });
        setSaved(false);
    };

    const handleSelectAll = () => {
        const all: Record<string, boolean> = {};
        allFields.forEach(f => { all[f.id] = true; });
        setFields(all);
        setSaved(false);
    };

    const handleDeselectAll = () => {
        const none: Record<string, boolean> = {};
        allFields.forEach(f => { none[f.id] = false; });
        setFields(none);
        setSaved(false);
    };

    const activeCount = Object.values(fields).filter(Boolean).length;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <ConfirmModal 
                isOpen={isConfirmOpen}
                title="Sincronizar com FIPE?"
                message="Isso buscará novos modelos e marcas na API oficial. O processo ocorre em segundo plano e pode levar alguns minutos."
                confirmText="Sincronizar Agora"
                cancelText="Agora não"
                type="warning"
                onConfirm={handleSyncFipe}
                onCancel={() => setIsConfirmOpen(false)}
            />

            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">Configurações</h1>
                    <p className="text-slate-500 text-sm">Defina o seu <span className="text-primary font-bold">Padrão de Fábrica</span> e preferências do sistema.</p>
                </div>
            </div>

            {/* Custom Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-px">
                <button
                    onClick={() => setActiveTab('grade')}
                    className={`px-4 py-2 font-bold text-sm border-b-2 transition-colors ${activeTab === 'grade' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                >
                    Grade e Colunas
                </button>
                <button
                    onClick={() => setActiveTab('imagens')}
                    className={`px-4 py-2 font-bold text-sm border-b-2 transition-colors ${activeTab === 'imagens' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                >
                    Processamento de Imagens
                </button>
                <button
                    onClick={() => setActiveTab('manutencao')}
                    className={`px-4 py-2 font-bold text-sm border-b-2 transition-colors ${activeTab === 'manutencao' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                >
                    Manutenção (FIPE)
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'grade' && (
                <div className="space-y-6 animate-in fade-in duration-300">
                    <div className="flex items-center justify-end gap-3 mb-4">
                        <button
                            onClick={handleReset}
                            className="px-4 py-2 rounded-xl font-semibold flex items-center gap-2 transition-all bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 text-sm"
                        >
                            <RotateCcw size={16} /> Restaurar Padrão
                        </button>
                        <button
                            onClick={handleSave}
                            className={`px-6 py-2 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg text-sm ${saved
                                ? 'bg-emerald-500 text-white shadow-emerald-500/20'
                                : 'bg-primary hover:bg-primary-hover text-white shadow-primary/20'
                                }`}
                        >
                            <Save size={16} /> {saved ? 'Padrão Salvo!' : 'Salvar Padrão'}
                        </button>
                    </div>

                    {/* Info bar */}
                    <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-900/50 rounded-xl px-5 py-3 border border-slate-200 dark:border-slate-800">
                        <span className="text-sm font-semibold text-slate-500">
                            <span className="text-primary font-black">{activeCount}</span> de {allFields.length} colunas ativas no seu padrão
                        </span>
                        <div className="flex gap-2">
                            <button
                                onClick={handleSelectAll}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-primary/10 text-primary hover:bg-primary/20 transition-all"
                            >
                                <Eye size={14} /> Marcar Tudo
                            </button>
                            <button
                                onClick={handleDeselectAll}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-200 dark:bg-slate-800 text-slate-500 hover:bg-slate-300 dark:hover:bg-slate-700 transition-all"
                            >
                                <EyeOff size={14} /> Desmarcar Tudo
                            </button>
                        </div>
                    </div>

                    {/* Grid de toggles */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {allFields.map(f => {
                            const isActive = !!fields[f.id];
                            return (
                                <button
                                    key={f.id}
                                    onClick={() => toggle(f.id)}
                                    className={`flex items-center justify-between p-4 rounded-xl border-2 transition-all duration-200 group cursor-pointer ${isActive
                                        ? 'border-primary bg-primary/5 dark:bg-primary/10 shadow-md shadow-primary/10'
                                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700'
                                        }`}
                                >
                                    <span className={`font-bold text-sm ${isActive ? 'text-primary' : 'text-slate-400'}`}>
                                        {f.label}
                                    </span>
                                    <div className={`w-10 h-5 rounded-full p-0.5 transition-colors ${isActive ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}>
                                        <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${isActive ? 'translate-x-5' : ''}`} />
                                    </div>
                                </button>
                            );
                        })}
                    </div>

                    {/* Nota */}
                    <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 text-amber-800 dark:text-amber-200 text-xs font-medium leading-relaxed">
                        <span className="font-bold">Dica:</span> Ao salvar aqui, você define o seu padrão fixo. Na tela de busca, você pode desmarcar colunas para uma pesquisa específica sem medo, pois ao recarregar a página, o sistema voltará para este padrão salvo no banco de dados.
                    </div>
                </div>
            )}

            {activeTab === 'imagens' && (
                <div className="space-y-6 animate-in fade-in duration-300 pt-2">
                    <ConfiguracoesImagens />
                </div>
            )}

            {activeTab === 'manutencao' && (
                <div className="space-y-6 animate-in fade-in duration-300 pt-2">
                    <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <Database size={20} className="text-primary" /> Manutenção do Sistema
                    </h2>
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                        <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                            <div className="space-y-1">
                                <h3 className="font-bold text-slate-800 dark:text-slate-100">Catálogo Mestre (FIPE)</h3>
                                <p className="text-sm text-slate-500">
                                    Sincronize marcas e modelos para garantir o reconhecimento automático de montadoras.
                                </p>
                                <div className="flex gap-4 pt-2">
                                    <div className="text-xs">
                                        <span className="text-slate-400">Modelos:</span> <span className="font-bold text-primary">{automakerInfo?.count || 0}</span>
                                    </div>
                                    <div className="text-xs">
                                        <span className="text-slate-400">Atualização:</span> <span className="font-bold text-slate-500">{automakerInfo?.last_update ? new Date(automakerInfo.last_update).toLocaleDateString() : 'Nunca'}</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsConfirmOpen(true)}
                                disabled={syncing}
                                className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold transition-all whitespace-nowrap shadow-lg ${
                                    syncing 
                                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed shadow-none' 
                                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-500/20'
                                }`}
                            >
                                <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
                                {syncing ? 'Sincronizando...' : 'Sincronizar Agora'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Configuracoes;

