import { useState, useEffect } from 'react';
import { Plus, Trash2, Search, X } from 'lucide-react';
import { configApi } from '../services/api';

const Siglas = () => {
    const [siglas, setSiglas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newNome, setNewNome] = useState('');
    const [newSigla, setNewSigla] = useState('');

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
                abreviacao: newSigla.trim().toUpperCase()
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

    const filteredSiglas = siglas.filter(s =>
        s.nome_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.abreviacao.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">Dicionário de Siglas</h1>
                    <p className="text-slate-500 text-sm">Converta nomes longos de marcas em abreviações padrão.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-primary hover:bg-primary-hover text-white px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all"
                >
                    <Plus size={20} /> Nova Sigla
                </button>
            </div>

            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
                <div className="p-4 border-b border-slate-100 dark:border-slate-800">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Filtrar siglas..."
                            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:ring-2 focus:ring-primary/20"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-slate-50 dark:bg-slate-900/50 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                            <tr>
                                <th className="px-6 py-3">Nome Completo (Original)</th>
                                <th className="px-6 py-3">Abreviação (Sistema)</th>
                                <th className="px-6 py-3 text-right">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {loading ? (
                                <tr><td colSpan={3} className="px-6 py-8 text-center text-slate-400">Carregando...</td></tr>
                            ) : filteredSiglas.length === 0 ? (
                                <tr><td colSpan={3} className="px-6 py-8 text-center text-slate-400">Nenhuma sigla encontrada.</td></tr>
                            ) : (
                                filteredSiglas.map((s) => (
                                    <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                                        <td className="px-6 py-4 font-medium">{s.nome_completo}</td>
                                        <td className="px-6 py-4">
                                            <span className="bg-primary/10 text-primary px-2 py-1 rounded text-sm font-bold">
                                                {s.abreviacao}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => handleDelete(s.id)}
                                                    className="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded text-red-500"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal de Adição */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-surface-light dark:bg-surface-dark w-full max-w-md rounded-2xl shadow-2xl p-6 border border-slate-200 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold">Nova Sigla</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X size={24} /></button>
                        </div>

                        <form onSubmit={handleAdd} className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Nome Completo</label>
                                <input
                                    autoFocus
                                    type="text"
                                    placeholder="Ex: VOLKSWAGEN"
                                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20"
                                    value={newNome}
                                    onChange={(e) => setNewNome(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1.5 uppercase opacity-50">Sigla (Abreviação)</label>
                                <input
                                    type="text"
                                    placeholder="Ex: VW"
                                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary/20"
                                    value={newSigla}
                                    onChange={(e) => setNewSigla(e.target.value)}
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
