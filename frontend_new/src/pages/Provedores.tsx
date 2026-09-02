import { useState, useEffect, useMemo } from 'react';
import { Plus, Database, Trash2, Edit2, Shield, Globe, LayoutGrid, List, Search } from 'lucide-react';
import { configApi } from '../services/api';
import ProvedorForm from '../components/ProvedorForm';

const Provedores = () => {
    const [provedores, setProvedores] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingProvedor, setEditingProvedor] = useState<any>(null);
    const [viewMode, setViewMode] = useState<'card' | 'list'>('card');
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState<'nome' | 'tipo'>('nome');
    const [filterStatus, setFilterStatus] = useState<'todos' | 'ativos' | 'inativos'>('todos');

    useEffect(() => {
        fetchProvedores();
    }, []);

    const fetchProvedores = async () => {
        try {
            const response = await configApi.getProvedores();
            setProvedores(response.data);
        } catch (error) {
            console.error('Erro ao carregar provedores:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (data: any) => {
        try {
            const payload = { ...data };
            if (typeof payload.headers === 'object') {
                payload.headers = JSON.stringify(payload.headers);
            }

            if (editingProvedor) {
                await configApi.updateProvedor(editingProvedor.id, payload);
            } else {
                await configApi.createProvedor(payload);
            }
            setIsFormOpen(false);
            setEditingProvedor(null);
            fetchProvedores();
        } catch (error) {
            alert('Erro ao salvar provedor. Verifique os dados.');
        }
    };

    const handleEdit = (prov: any) => {
        setEditingProvedor(prov);
        setIsFormOpen(true);
    };

    const handleDelete = async (id: number, nome: string) => {
        if (window.confirm(`Deseja realmente remover o provedor "${nome}"?`)) {
            try {
                await configApi.deleteProvedor(id);
                fetchProvedores();
            } catch (error) {
                alert('Erro ao excluir');
            }
        }
    };

    const filteredProvedores = useMemo(() => {
        return provedores
            .filter(p => {
                if (filterStatus === 'ativos' && !p.ativo) return false;
                if (filterStatus === 'inativos' && p.ativo) return false;
                return true;
            })
            .filter(p =>
                p.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                p.tipo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (p.url && p.url.toLowerCase().includes(searchTerm.toLowerCase()))
            )
            .sort((a, b) => {
                if (sortBy === 'nome') return a.nome.localeCompare(b.nome);
                return a.tipo.localeCompare(b.tipo);
            });
    }, [provedores, searchTerm, sortBy, filterStatus]);

    return (
        <div className="space-y-6 pb-10">
            {/* Header e Ações */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold">Configuração de Provedores</h1>
                    <p className="text-slate-500 text-sm">Gerencie as fontes de dados para suas pesquisas.</p>
                </div>
                <button
                    onClick={() => { setEditingProvedor(null); setIsFormOpen(true); }}
                    className="bg-primary hover:bg-primary-hover text-white px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-primary/20 shrink-0"
                >
                    <Plus size={20} /> Novo Provedor
                </button>
            </div>

            {/* Barra de Busca e Filtros */}
            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 p-4 rounded-xl shadow-sm flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Buscar por nome, tipo ou URL..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2 w-full md:w-auto">
                    <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-lg">
                        <button
                            onClick={() => setViewMode('card')}
                            className={`p-1.5 rounded-md transition-all ${viewMode === 'card' ? 'bg-white dark:bg-slate-800 shadow-sm text-primary' : 'text-slate-500 hover:text-slate-700'}`}
                            title="Modo Card"
                        >
                            <LayoutGrid size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? 'bg-white dark:bg-slate-800 shadow-sm text-primary' : 'text-slate-500 hover:text-slate-700'}`}
                            title="Modo Lista"
                        >
                            <List size={18} />
                        </button>
                    </div>
                    <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700 mx-1 hidden md:block" />
                    <select
                        className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value as any)}
                    >
                        <option value="todos">Status: Todos</option>
                        <option value="ativos">Status: Ativos</option>
                        <option value="inativos">Status: Inativos</option>
                    </select>
                    <select
                        className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as any)}
                    >
                        <option value="nome">Ordernar: Nome</option>
                        <option value="tipo">Ordernar: Tipo</option>
                    </select>
                </div>
            </div>

            {loading ? (
                <div className="py-20 text-center text-slate-400">Carregando provedores...</div>
            ) : filteredProvedores.length === 0 ? (
                <div className="bg-surface-light dark:bg-surface-dark border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl py-20 text-center text-slate-400">
                    <Search size={40} className="mx-auto mb-4 opacity-10" />
                    <p>Nenhum provedor encontrado para sua busca.</p>
                </div>
            ) : viewMode === 'card' ? (
                /* Modo Card (Grid) */
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredProvedores.map((prov) => (
                        <div key={prov.id} className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all group relative overflow-hidden">
                            <div className="flex justify-between items-start mb-4">
                                <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-xl text-primary">
                                    {prov.tipo === 'graphql' ? <Globe size={24} /> : <Database size={24} />}
                                </div>
                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button onClick={() => handleEdit(prov)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500">
                                        <Edit2 size={16} />
                                    </button>
                                    <button onClick={() => handleDelete(prov.id, prov.nome)} className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-500">
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-1 mb-6">
                                <div className="flex items-center gap-2">
                                    <h3 className="font-bold text-lg">{prov.nome}</h3>
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${prov.ativo ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                                        {prov.ativo ? 'Ativo' : 'Inativo'}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-400 truncate font-mono">{prov.url}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-[11px] font-medium text-slate-500">
                                <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900/50 p-2 rounded-lg">
                                    <Shield size={14} className={prov.login_required ? "text-amber-500" : "text-slate-400"} />
                                    {prov.login_required ? "Login Requerido" : "Acesso Público"}
                                </div>
                                <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900/50 p-2 rounded-lg uppercase">
                                    {prov.tipo}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                /* Modo Lista (Tabela) */
                <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                            <tr>
                                <th className="px-6 py-4">Provedor</th>
                                <th className="px-6 py-4">URL</th>
                                <th className="px-6 py-4">Tipo</th>
                                <th className="px-6 py-4 text-center">Status</th>
                                <th className="px-6 py-4 text-right">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {filteredProvedores.map((prov) => (
                                <tr key={prov.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="text-primary opacity-60">
                                                {prov.tipo === 'graphql' ? <Globe size={18} /> : <Database size={18} />}
                                            </div>
                                            <span className="font-bold text-sm">{prov.nome}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-xs text-slate-400 font-mono block max-w-[300px] truncate">{prov.url}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-1.5 text-xs text-slate-500 uppercase font-medium">
                                            {prov.tipo}
                                            {prov.login_required && <Shield size={12} className="text-amber-500" />}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`text-[9px] px-2 py-0.5 rounded-full font-black uppercase ${prov.ativo ? 'text-emerald-500' : 'text-slate-400'}`}>
                                            ● {prov.ativo ? 'Ativo' : 'Inativo'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => handleEdit(prov)} className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500" title="Editar">
                                                <Edit2 size={14} />
                                            </button>
                                            <button onClick={() => handleDelete(prov.id, prov.nome)} className="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-500" title="Excluir">
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {isFormOpen && (
                <ProvedorForm
                    provedor={editingProvedor}
                    onSave={handleSave}
                    onCancel={() => setIsFormOpen(false)}
                />
            )}
        </div>
    );
};

export default Provedores;
