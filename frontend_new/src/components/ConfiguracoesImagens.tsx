import React, { useState, useEffect } from 'react';
import { Save, Image as ImageIcon, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { configApi } from '../services/api';
import { toast } from '../utils/toast';

export const ConfiguracoesImagens = () => {
    const [config, setConfig] = useState({
        formato_saida: 'ORIGINAL',
        qualidade: 85,
        max_width: 1024,
        max_height: 1024,
        min_width: 500,
        min_height: 500,
        manter_proporcao: true,
        cor_fundo_jpg: '#FFFFFF'
    });
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        setLoading(true);
        try {
            const response = await configApi.getConfiguracoesImagens();
            if (response.data) {
                setConfig(response.data);
            }
        } catch (error) {
            console.error("Erro ao carregar configurações de imagens:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await configApi.updateConfiguracoesImagens(config);
            toast.success("Configurações de imagem salvas com sucesso!");
        } catch (error) {
            console.error("Erro ao salvar configurações de imagens:", error);
            toast.error("Erro ao salvar as configurações.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-32">
                <Loader2 className="animate-spin text-primary" size={24} />
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-6">
                <h3 className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
                    <ImageIcon size={20} className="text-indigo-600" /> Processamento de Imagens
                </h3>
                <p className="text-sm text-slate-500 mb-6">
                    Configure como o sistema deve processar, comprimir e converter as imagens antes de baixá-las.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Formato */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Formato de Saída
                        </label>
                        <select
                            value={config.formato_saida}
                            onChange={(e) => setConfig({ ...config, formato_saida: e.target.value })}
                            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        >
                            <option value="ORIGINAL">Manter Original (Recomendado)</option>
                            <option value="JPEG">Converter para JPEG</option>
                            <option value="WEBP">Converter para WEBP (Mais leve)</option>
                        </select>
                        <p className="text-xs text-slate-400">
                            Ao converter para JPEG, imagens PNG transparentes receberão fundo sólido.
                        </p>
                    </div>

                    {/* Qualidade */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex justify-between">
                            <span>Qualidade da Compressão</span>
                            <span className="text-indigo-600 font-bold">{config.qualidade}%</span>
                        </label>
                        <input
                            type="range"
                            min="10"
                            max="100"
                            value={config.qualidade}
                            onChange={(e) => setConfig({ ...config, qualidade: parseInt(e.target.value) })}
                            className="w-full accent-indigo-600"
                        />
                        <p className="text-xs text-slate-400">
                            Valores menores geram arquivos mais leves, mas com perda de nitidez (Ideal: 80-90%).
                        </p>
                    </div>

                    {/* Dimensões Máximas */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Dimensões Máximas (Pixels)
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="number"
                                value={config.max_width || ''}
                                onChange={(e) => setConfig({ ...config, max_width: parseInt(e.target.value) || 0 })}
                                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Largura (ex: 1024)"
                            />
                            <span className="text-slate-400 text-xs font-bold">X</span>
                            <input
                                type="number"
                                value={config.max_height || ''}
                                onChange={(e) => setConfig({ ...config, max_height: parseInt(e.target.value) || 0 })}
                                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Altura (ex: 1024)"
                            />
                        </div>
                    </div>

                    {/* Dimensões Mínimas */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Dimensões Mínimas (Pixels)
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="number"
                                value={config.min_width || ''}
                                onChange={(e) => setConfig({ ...config, min_width: parseInt(e.target.value) || 0 })}
                                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Largura (ex: 500)"
                            />
                            <span className="text-slate-400 text-xs font-bold">X</span>
                            <input
                                type="number"
                                value={config.min_height || ''}
                                onChange={(e) => setConfig({ ...config, min_height: parseInt(e.target.value) || 0 })}
                                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                placeholder="Altura (ex: 500)"
                            />
                        </div>
                        <p className="text-xs text-slate-400">
                            (Ex: Mercado Livre exige 500x500. Imagens menores ganharão fundo na cor escolhida).
                        </p>
                    </div>

                    {/* Cor de Fundo */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Cor de Fundo (Apenas JPEG)
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="color"
                                value={config.cor_fundo_jpg}
                                onChange={(e) => setConfig({ ...config, cor_fundo_jpg: e.target.value })}
                                className="w-12 h-10 rounded-lg cursor-pointer border border-slate-200"
                            />
                            <input
                                type="text"
                                value={config.cor_fundo_jpg}
                                onChange={(e) => setConfig({ ...config, cor_fundo_jpg: e.target.value })}
                                className="flex-1 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm uppercase font-mono"
                            />
                        </div>
                    </div>
                </div>

                <div className="mt-8 flex justify-end border-t border-slate-100 dark:border-slate-800 pt-4">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50"
                    >
                        {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                        Salvar Ajustes de Imagem
                    </button>
                </div>
            </div>
        </div>
    );
};
