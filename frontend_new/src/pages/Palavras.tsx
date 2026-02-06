import { useState, useEffect } from 'react';
import { Trash2, Plus, Tag, X } from 'lucide-react';
import { configApi } from '../services/api';

const Palavras = () => {
    const [palavras, setPalavras] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedField, setSelectedField] = useState('todos');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newWord, setNewWord] = useState('');
    const [newWordField, setNewWordField] = useState('modelo');

    const campos = [
        { id: 'todos', label: 'Todos os Campos' },
        { id: 'marca', label: 'Marca' },
        { id: 'veiculo', label: 'Veículo' },
        { id: 'modelo', label: 'Modelo' },
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
        fetchPalavras();
    }, []);

    const fetchPalavras = async () => {
        try {
            const response = await configApi.getPalavras();
            setPalavras(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newWord.trim()) return;

        try {
            await configApi.createPalavra({
                palavra: newWord.trim(),
                campo: newWordField
            });
            setNewWord('');
            setIsModalOpen(false);
            fetchPalavras();
        } catch (error) {
            console.error(error);
            alert('Erro ao adicionar palavra');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Tem certeza que deseja remover este termo?')) return;
        try {
            await configApi.deletePalavra(id);
            fetchPalavras();
        } catch (error) {
            console.error(error);
            alert('Erro ao remover palavra');
        }
    };

    const filteredPalavras = selectedField === 'todos'
        ? palavras
        : palavras.filter(p => p.campo === selectedField);

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">Filtros de Limpeza</h1>
                    <p className="text-slate-500 text-sm">Remova termos indesejados automaticamente dos resultados.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary hover:bg-primary-hover text-white px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all"
                >
                    <Plus size={20} /> Adicionar Termo
                </button>
            </div>

            <div className="flex flex-wrap gap-2">
                {campos.map(campo => (
                    <button
                        key={campo.id}
                        onClick={() => setSelectedField(campo.id)}
                        className={`px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-all ${selectedField === campo.id
                            ? 'bg-primary text-white'
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
                ) : filteredPalavras.length === 0 ? (
                    <div className="col-span-full py-10 text-center text-slate-400">Nenhum termo cadastrado para este filtro.</div>
                ) : (
                    filteredPalavras.map((p) => (
                        <div key={p.id} className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 p-4 rounded-xl flex items-center justify-between group">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg text-slate-400 group-hover:text-primary transition-colors">
                                    <Tag size={18} />
                                </div>
                                <div>
                                    <div className="font-bold">{p.palavra}</div>
                                    <div className="text-[10px] uppercase font-bold text-slate-400">Campo: {p.campo}</div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(p.id)}
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
                            <h2 className="text-xl font-bold">Novo Termo de Limpeza</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X size={24} /></button>
                        </div>

                        <form onSubmit={handleAdd} className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Campo Alvo</label>
                                <select
                                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20"
                                    value={newWordField}
                                    onChange={(e) => setNewWordField(e.target.value)}
                                >
                                    {campos.filter(c => c.id !== 'todos').map(c => (
                                        <option key={c.id} value={c.id}>{c.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Palavra ou Frase</label>
                                <input
                                    autoFocus
                                    type="text"
                                    placeholder="Ex: SOHC L4"
                                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20"
                                    value={newWord}
                                    onChange={(e) => setNewWord(e.target.value)}
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2.5 bg-slate-100 dark:bg-slate-800 rounded-xl font-semibold text-slate-600 dark:text-slate-400"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-all shadow-lg shadow-primary/20"
                                >
                                    Salvar Termo
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Palavras;
