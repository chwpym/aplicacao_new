import { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Car, ChevronRight, Database, RefreshCw, CheckCircle2 } from 'lucide-react';
import { configApi } from '../services/api';
import { toast } from '../utils/toast';
import ConfirmModal from '../components/ConfirmModal';

const Automakers = () => {
    const [catalog, setCatalog] = useState<Record<string, string[]>>({});
    const [brands, setBrands] = useState<string[]>([]);
    const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [newModel, setNewModel] = useState('');
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const [modelToDelete, setModelToDelete] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const response = await configApi.getAutomakersInfo();
            setCatalog(response.data.catalog || {});
            const sortedBrands = (response.data.brands || []).sort();
            setBrands(sortedBrands);
        } catch (error) {
            console.error("Erro ao carregar dados:", error);
            toast.error("Erro ao carregar catálogo de montadoras.");
        } finally {
            setLoading(false);
        }
    };

    const handleAddModel = async () => {
        if (!selectedBrand || !newModel.trim()) return;
        
        const modelUpper = newModel.trim().toUpperCase();
        setActionLoading(true);
        try {
            await configApi.addModel(selectedBrand, modelUpper);
            setNewModel('');
            toast.success(`Modelo ${modelUpper} adicionado com sucesso!`);
            await loadData(); // Recarrega para mostrar o novo modelo
        } catch (error) {
            console.error("Erro ao adicionar modelo:", error);
            toast.error("Erro ao adicionar modelo. Verifique a conexão.");
        } finally {
            setActionLoading(false);
        }
    };

    const handleDeleteModel = async () => {
        if (!selectedBrand || !modelToDelete) return;
        
        setActionLoading(true);
        try {
            await configApi.deleteModel(selectedBrand, modelToDelete);
            toast.success(`Modelo ${modelToDelete} removido com sucesso.`);
            setModelToDelete(null);
            await loadData();
        } catch (error) {
            console.error("Erro ao remover modelo:", error);
            toast.error("Erro ao remover modelo.");
        } finally {
            setActionLoading(false);
        }
    };

    const filteredBrands = brands.filter(b => b.toLowerCase().includes(searchTerm.toLowerCase()));
    const currentModels = selectedBrand ? catalog[selectedBrand] || [] : [];

    return (
        <div className="flex flex-col h-[calc(100vh-120px)] space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <ConfirmModal 
                isOpen={isConfirmOpen}
                title="Excluir Modelo?"
                message={`Deseja realmente remover o modelo ${modelToDelete} da marca ${selectedBrand}? Esta ação não pode ser desfeita.`}
                confirmText="Excluir"
                cancelText="Manter"
                type="danger"
                onConfirm={handleDeleteModel}
                onCancel={() => {
                    setIsConfirmOpen(false);
                    setModelToDelete(null);
                }}
            />
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Car className="text-primary" /> Biblioteca de Carros
                    </h1>
                    <p className="text-slate-500 text-sm">Gerencie o mapeamento de modelos e marcas do seu sistema.</p>
                </div>
                <div className="flex items-center gap-3 bg-white dark:bg-slate-900 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="px-4 py-2 text-xs font-bold text-slate-500 border-r border-slate-100 dark:border-slate-800">
                        Total de Marcas: <span className="text-primary">{brands.length}</span>
                    </div>
                    <button 
                        onClick={loadData}
                        className="p-2 text-slate-400 hover:text-primary transition-all rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800"
                        title="Recarregar dados"
                    >
                        <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            <div className="flex flex-1 gap-6 overflow-hidden">
                {/* Lista de Marcas (Lateral) */}
                <div className="w-72 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                    <div className="p-4 border-b border-slate-100 dark:border-slate-800">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                            <input 
                                type="text"
                                placeholder="Buscar marca..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border-none rounded-xl text-sm focus:ring-2 focus:ring-primary/20 transition-all font-medium"
                            />
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                        {loading && brands.length === 0 ? (
                            <div className="flex justify-center py-10">
                                <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
                            </div>
                        ) : filteredBrands.length > 0 ? (
                            filteredBrands.map(brand => (
                                <button
                                    key={brand}
                                    onClick={() => setSelectedBrand(brand)}
                                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                                        selectedBrand === brand 
                                        ? 'bg-primary text-white shadow-lg shadow-primary/20 scale-[1.02]' 
                                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                                    }`}
                                >
                                    {brand}
                                    <ChevronRight size={14} className={selectedBrand === brand ? 'opacity-100' : 'opacity-0'} />
                                </button>
                            ))
                        ) : (
                            <div className="text-center py-10 text-slate-400 text-xs font-medium">Nenhuma marca encontrada</div>
                        )}
                    </div>
                </div>

                {/* Conteúdo (Modelos) */}
                <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-sm">
                    {selectedBrand ? (
                        <div className="flex flex-col h-full">
                            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-50/50 dark:bg-slate-800/30">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary font-black text-xl shadow-inner">
                                        {selectedBrand[0]}
                                    </div>
                                    <div>
                                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em]">Montadora Selecionada</span>
                                        <h2 className="text-2xl font-black text-slate-800 dark:text-slate-100 leading-tight">{selectedBrand}</h2>
                                    </div>
                                </div>
                                <div className="flex gap-2 w-full sm:w-auto">
                                    <div className="relative flex-1 sm:flex-none">
                                        <input 
                                            type="text"
                                            placeholder="Adicionar modelo (Ex: COURIER ROCAM)"
                                            value={newModel}
                                            onChange={(e) => setNewModel(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleAddModel()}
                                            className="pl-4 pr-12 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm w-full sm:w-80 focus:ring-4 focus:ring-primary/10 transition-all font-bold shadow-inner"
                                        />
                                        <button 
                                            onClick={handleAddModel}
                                            disabled={actionLoading || !newModel.trim()}
                                            className="absolute right-1.5 top-1/2 -translate-y-1/2 p-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-all shadow-md shadow-primary/20 disabled:opacity-50"
                                        >
                                            {actionLoading ? <RefreshCw size={18} className="animate-spin" /> : <Plus size={18} />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="flex-1 p-8 overflow-y-auto custom-scrollbar bg-slate-50/20 dark:bg-slate-900/50">
                                {currentModels.length > 0 ? (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                        {currentModels.map(model => (
                                            <div 
                                                key={model}
                                                className="p-4 rounded-2xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between group hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
                                            >
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0" />
                                                    <span className="font-bold text-slate-700 dark:text-slate-300 truncate text-sm uppercase">{model}</span>
                                                </div>
                                                <button 
                                                    onClick={() => {
                                                        setModelToDelete(model);
                                                        setIsConfirmOpen(true);
                                                    }}
                                                    className="opacity-0 group-hover:opacity-100 p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all"
                                                    title="Remover modelo"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4 opacity-60">
                                        <div className="p-8 bg-slate-100 dark:bg-slate-800 rounded-full border-4 border-white dark:border-slate-900 shadow-xl">
                                            <Database size={40} />
                                        </div>
                                        <div className="text-center">
                                            <h3 className="font-bold text-lg text-slate-600 dark:text-slate-400">Nenhum modelo cadastrado</h3>
                                            <p className="text-sm">Adicione o primeiro modelo para a marca {selectedBrand} no campo acima.</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-6">
                            <div className="relative">
                                <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                                <div className="relative p-10 bg-white dark:bg-slate-800 rounded-[3rem] border-4 border-slate-50 dark:border-slate-700 shadow-2xl">
                                    <Car size={64} className="text-primary animate-bounce-slow" />
                                </div>
                            </div>
                            <div className="text-center max-w-xs">
                                <h3 className="font-black text-xl text-slate-800 dark:text-slate-100">Controle de Catálogo</h3>
                                <p className="text-sm font-medium mt-2 leading-relaxed">Selecione uma montadora na lista lateral para gerenciar, adicionar ou corrigir modelos.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Automakers;
