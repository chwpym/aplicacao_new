import { useState, useEffect } from 'react';
import { Plus, Trash2, Search, X, Tag } from 'lucide-react';
import { configApi } from '../services/api';

const Siglas = () => {
    const [siglas, setSiglas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedField, setSelectedField] = useState('todos');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newNome, setNewNome] = useState('');
    const [newSigla, setNewSigla] = useState('');
    const [newCampo, setNewCampo] = useState('marca');

    const campos = [
        { id: 'todos', label: 'Todos os Campos' },
        { id: 'marca', label: 'Marca Peça' },
        { id: 'veiculo', label: 'Montadora' },
        { id: 'modelo', label: 'Veículo' },
        { id: 'versao', label: 'Modelo' },
        { id: 'motor', label: 'Motor' },
        { id: 'configuracao_motor', label: 'Combustível' },
        { id: 'ano', label: 'Ano' },
        { id: 'imagem', label: 'Imagens' },
        { id: 'referencias', label: 'Referências' },
        { id: 'observacao', label: 'Observações' },
        { id: 'posicao', label: 'Posição' },
        { id: 'lado', label: 'Lado' },
        { id: 'direcao', label: 'Direção' },
        { id: 'sistema_freio', label: 'Sistema Freio' },
        { id: 'restricao', label: 'Restrição' },
        { id: 'apenas', label: 'Apenas' },
    ];

    useEffect(() => {
        fetchSiglas();
    }, []);

    const fetchSiglas = async () => {
        try {
            const response = await configApi.getSiglas();
            setSiglas(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newNome.trim() || !newSigla.trim()) return;

        try {
            await configApi.createSigla({
                nome_completo: newNome.trim().toUpperCase(),
                abreviacao: newSigla.trim().toUpperCase(),
                campo: newCampo
            });
            setNewNome('');
            setNewSigla('');
            setIsModalOpen(false);
            fetchSiglas();
        } catch (error) {
            console.error(error);
            alert('Erro ao adicionar sigla');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Tem certeza que deseja remover esta sigla?')) return;
        try {
            await configApi.deleteSigla(id);
            fetchSiglas();
        } catch (error) {
            console.error(error);
            alert('Erro ao remover sigla');
        }
    };

    const getFieldLabel = (field: string) => {
        const found = campos.find(c => c.id === field);
        return found ? found.label : field;
    };

    const filteredSiglas = siglas.filter(s => {
        const matchesField = selectedField === 'todos' || s.campo === selectedField;
        const matchesSearch = 
            s.nome_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
            s.abreviacao.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesField && matchesSearch;
    });

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">Dicionário de Siglas</h1>
                    <p className="text-slate-500 text-sm">Converta nomes longos em abreviações padrão por coluna.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary hover:bg-primary-hover text-white px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-primary/20"
                >
                    <Plus size={20} /> Nova Sigla
                </button>
            </div>

            <div className="relative">
                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-400">
                    <Search size={18} />
                </div>
                <input
                    type="text"
                    placeholder="Pesquisar sigla ou nome original..."
                    className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 transition-all font-medium"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            <div className="flex flex-wrap gap-2 overflow-x-auto pb-2 custom-scrollbar">
                {campos.map(campo => (
                    <button
                        key={campo.id}
                        onClick={() => setSelectedField(campo.id)}
                        className={`px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-all ${selectedField === campo.id
                            ? 'bg-primary text-white shadow-md shadow-primary/20'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700'
                            }`}
                    >
                        {campo.label}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {loading ? (
                    <div className="col-span-full py-10 text-center text-slate-400">Carregando...</div>
                ) : filteredSiglas.length === 0 ? (
                    <div className="col-span-full py-10 text-center text-slate-400">Nenhuma sigla encontrada para este filtro.</div>
                ) : (
                    filteredSiglas.map((s) => (
                        <div key={s.id} className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 p-4 rounded-xl flex items-center justify-between group hover:shadow-lg transition-all border-l-4 border-l-primary">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg text-primary">
                                    <Tag size={18} />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold text-lg">{s.nome_completo}</span>
                                        <span className="text-slate-300">→</span>
                                        <span className="bg-primary text-white px-2 py-0.5 rounded text-xs font-black shadow-sm">
                                            {s.abreviacao}
                                        </span>
                                    </div>
                                    <div className="text-[10px] uppercase font-bold text-slate-400 mt-1">
                                        CAMPO: <span className="text-primary/60">{getFieldLabel(s.campo)}</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(s.id)}
                                className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Modal de Adição */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-surface-light dark:bg-surface-dark w-full max-w-md rounded-2xl shadow-2xl p-6 border border-slate-200 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold">Nova Sigla</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors"><X size={24} /></button>
                        </div>

                        <form onSubmit={handleAdd} className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Coluna Aplicada</label>
                                <select 
                                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 appearance-none transition-all cursor-pointer"
                                    value={newCampo}
                                    onChange={(e) => setNewCampo(e.target.value)}
                                >
                                    {campos.filter(c => c.id !== 'todos').map(c => (
                                        <option key={c.id} value={c.id}>{c.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Nome Original</label>
                                    <input
                                        autoFocus
                                        type="text"
                                        placeholder="Ex: VOLKSWAGEN"
                                        className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 transition-all font-bold"
                                        value={newNome}
                                        onChange={(e) => setNewNome(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Sigla (Abreviação)</label>
                                    <input
                                        type="text"
                                        placeholder="Ex: VW"
                                        className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20 transition-all font-bold text-primary"
                                        value={newSigla}
                                        onChange={(e) => setNewSigla(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2.5 bg-slate-100 dark:bg-slate-800 rounded-xl font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-all shadow-lg shadow-primary/20"
                                >
                                    Salvar Sigla
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Siglas;
