import React, { useState, useEffect } from 'react';
import { Search, Loader2, Copy, FileDown, Check } from 'lucide-react';
import { searchApi, configApi } from '../services/api';

import JSZip from 'jszip';

const Home = () => {
    const [partId, setPartId] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [provedores, setProvedores] = useState<any[]>([]);
    const [selectedProvedor, setSelectedProvedor] = useState<number | ''>('');
    const [agrupar, setAgrupar] = useState(true);
    const [visibleFields, setVisibleFields] = useState<any>({
        marca: true,
        veiculo: true,
        modelo: true,
        motor: true,
        configuracao_motor: true,
        ano: true,
        imagem: false,
        referencias: false,
        observacao: false,
        posicao: false,
        lado: false,
        direcao: false
    });

    useEffect(() => {
        fetchProvedores();
    }, []);

    const fetchProvedores = async () => {
        try {
            const response = await configApi.getProvedores();
            const ativos = response.data
                .filter((p: any) => p.ativo)
                .sort((a: any, b: any) => a.nome.localeCompare(b.nome));

            setProvedores(ativos);
        } catch (error) {
            console.error('Erro ao buscar provedores:', error);
        }
    };

    const getFieldLabel = (field: string) => {
        if (selectedProvedor) {
            const prov = provedores.find(p => String(p.id) === String(selectedProvedor));
            if (prov) {
                // Tenta extrair do mapeamento JSON
                if (prov.mapeamento) {
                    try {
                        const map = JSON.parse(prov.mapeamento);
                        if (map.labels && map.labels[field]) {
                            return map.labels[field];
                        }
                    } catch { }
                }

                // Fallback específico para DS se o usuário não atualizou o mapeamento no DB
                if (prov.nome.toUpperCase().trim() === 'DS') {
                    if (field === 'configuracao_motor') return 'Combustível';
                    if (field === 'observacao') return 'Observações';
                    if (field === 'imagem') return 'Imagens';
                }
            }
        }

        const defaults: Record<string, string> = {
            marca: 'Marca',
            veiculo: 'Veículo',
            modelo: 'Modelo',
            motor: 'Motor',
            configuracao_motor: 'Combustível', // Mudando default global para Combustível
            ano: 'Ano',
            imagem: 'Imagens',
            referencias: 'Referências',
            observacao: 'Observações',
            posicao: 'Posição',
            lado: 'Lado',
            direcao: 'Direção'
        };

        return defaults[field] || field.replace('_', ' ');
    };

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!partId) return;

        setLoading(true);
        try {
            // Passa apenas o provedor selecionado
            const response = await searchApi.buscarPeca(
                partId,
                selectedProvedor ? [selectedProvedor as number] : undefined,
                agrupar
            );
            const sorted = response.data.sort((a: any, b: any) => {
                if (a.marca !== b.marca) return a.marca.localeCompare(b.marca);
                if (a.veiculo !== b.veiculo) return a.veiculo.localeCompare(b.veiculo);
                return a.modelo.localeCompare(b.modelo);
            });
            setResults(sorted);
        } catch (error) {
            console.error('Erro na busca:', error);
            alert('Erro ao realizar busca. Verifique se o backend está rodando.');
        } finally {
            setLoading(false);
        }
    };

    const formatYearShort = (year: number | string | null | undefined) => {
        if (!year) return '';
        const s = year.toString();
        return s.length >= 4 ? s.substring(2) : s;
    };

    const uniqueReferences = React.useMemo(() => {
        const brands: Record<string, Set<string>> = {};
        results.forEach(res => {
            if (res.referencias) {
                // Tenta split por ' | ' primeiro, depois por outros possíveis separadores
                res.referencias.split(/\s*\|\s*/).forEach((ref: string) => {
                    // Tenta split por ': ' (com espaço) ou ':' (sem espaço)
                    const parts = ref.split(/:\s*/);
                    if (parts.length >= 2) {
                        const brand = parts[0].trim();
                        const code = parts.slice(1).join(':').trim();
                        if (brand && code) {
                            const cleanBrand = brand.toUpperCase().replace(' ORIGINAL', '').replace('ORIGINAL ', '');
                            if (!brands[cleanBrand]) brands[cleanBrand] = new Set();
                            brands[cleanBrand].add(code);
                        }
                    }
                });
            }
        });
        return brands;
    }, [results]);

    const copyToClipboard = (mode: 'completa' | 'intermediaria' | 'agrupada') => {
        if (results.length === 0) return;

        let text = '';

        if (mode === 'completa') {
            const lines = results.map(res => {
                const parts = [];
                if (visibleFields.marca) parts.push(res.marca);
                if (visibleFields.veiculo) parts.push(res.veiculo);
                if (visibleFields.modelo) parts.push(res.modelo);
                if (visibleFields.motor) parts.push(res.motor);
                if (visibleFields.configuracao_motor) parts.push(res.configuracao_motor);
                if (visibleFields.ano) {
                    const anoStr = res.ano_inicio || res.ano_fim
                        ? `${res.ano_inicio || ''}...${res.ano_fim || ''}`
                        : '';
                    if (anoStr) parts.push(anoStr);
                }
                if (visibleFields.referencias) parts.push(res.referencias);
                return parts.join(' ').replace(/\s+/g, ' ').trim();
            }).filter(line => line.length > 0);

            text = Array.from(new Set(lines)).join('\n');
        } else {
            const groups: any = {};
            results.forEach(res => {
                const dynamicKeyParts = [];
                if (visibleFields.marca) dynamicKeyParts.push(res.marca);
                if (visibleFields.veiculo) dynamicKeyParts.push(res.veiculo);
                if (visibleFields.modelo) dynamicKeyParts.push(res.modelo);
                if (visibleFields.motor) dynamicKeyParts.push(res.motor);
                if (visibleFields.configuracao_motor) dynamicKeyParts.push(res.configuracao_motor);

                const key = dynamicKeyParts.join('|') || 'default';

                if (!groups[key]) {
                    groups[key] = {
                        parts: dynamicKeyParts,
                        anos: [],
                        items: [] // Adiciona para armazenar os itens originais para o modo 'agrupada'
                    };
                }
                groups[key].anos.push({ start: res.ano_inicio, end: res.ano_fim });
                groups[key].items.push(res); // Adiciona o item original
            });

            const sortedGroups = Object.values(groups).sort((a: any, b: any) => {
                const brandA = a.parts[0] || '';
                const brandB = b.parts[0] || '';
                if (brandA !== brandB) return brandA.localeCompare(brandB);
                const vehicleA = a.parts[1] || '';
                const vehicleB = b.parts[1] || '';
                return vehicleA.localeCompare(vehicleB);
            });

            if (mode === 'intermediaria') {
                const lines: string[] = [];
                sortedGroups.forEach((g: any) => {
                    const uniqueRanges = new Set<string>();
                    g.anos.forEach((a: any) => {
                        const yearRange = `${formatYearShort(a.start)}...${a.end ? formatYearShort(a.end) : ''}`;
                        uniqueRanges.add(yearRange);
                    });
                    const sortedRanges = Array.from(uniqueRanges).sort();
                    sortedRanges.forEach(range => {
                        lines.push(`${g.parts.join(' ')} ${range}`.replace(/\s+/g, ' ').trim());
                    });
                });
                text = lines.join('\n');
            } else { // mode === 'agrupada'
                const lines = sortedGroups.map((g: any) => {
                    const starts = g.anos.map((a: any) => a.start).filter((a: any) => a !== null && a !== undefined && a !== '');
                    const ends = g.anos.map((a: any) => a.end).filter((a: any) => a !== null && a !== undefined && a !== '');
                    const minStart = starts.length > 0 ? (starts.every((s: any) => !isNaN(Number(s))) ? Math.min(...starts.map(Number)) : starts[0]) : '';
                    const maxEnd = ends.length > 0 ? (ends.every((e: any) => !isNaN(Number(e))) ? Math.max(...ends.map(Number)) : ends[ends.length - 1]) : '';
                    const yearRange = `${formatYearShort(minStart)}${maxEnd ? '...' + formatYearShort(maxEnd) : '...'}`;
                    return `${g.parts.join(' ')} ${yearRange}`.replace(/\s+/g, ' ').trim();
                });
                text = lines.join('\n');
            }
        }

        if (Object.keys(uniqueReferences).length > 0) {
            text += '\n\nORIGINAL:';
            Object.entries(uniqueReferences).forEach(([brand, codes]) => {
                // Remove espaços duplos e garante formatação limpa
                const codesList = Array.from(codes as Set<string>).sort().join(' - ');
                text += `\n${brand}  ${codesList}`;
            });
        }

        navigator.clipboard.writeText(text);
        // Usando toast no futuro, por enquanto alert discreto removido ou mantido
        // alert(`Copiado no modo ${mode.toUpperCase()}!`);
    };

    // Lógica para processar os resultados que serão EXIBIDOS na tela
    const displayResults = React.useMemo(() => {
        if (results.length === 0) return [];

        // Se "Agrupar Resultados" estiver desligado no topo, mostramos tudo individual
        if (!agrupar) return results;

        const groups: any = {};
        results.forEach(res => {
            // Chave baseada apenas no que está visível
            const keyParts = [];
            if (visibleFields.marca) keyParts.push(res.marca);
            if (visibleFields.veiculo) keyParts.push(res.veiculo);
            if (visibleFields.modelo) keyParts.push(res.modelo);
            if (visibleFields.motor) keyParts.push(res.motor);
            if (visibleFields.configuracao_motor) keyParts.push(res.configuracao_motor);

            const key = keyParts.join('|') || 'default';

            if (!groups[key]) {
                groups[key] = {
                    ...res, // Pega os dados base do primeiro item
                    anos: []
                };
            }
            if (res.ano_inicio || res.ano_fim) {
                groups[key].anos.push({ start: res.ano_inicio, end: res.ano_fim });
            }
        });

        // Transforma os grupos em linhas de exibição
        const processed: any[] = [];
        Object.values(groups).forEach((g: any) => {
            // No modo de exibição, vamos manter os ranges de anos organizados (similar ao INTERM)
            const uniqueRanges = new Set<string>();
            g.anos.forEach((a: any) => {
                uniqueRanges.add(`${a.start}...${a.end}`);
            });

            Array.from(uniqueRanges).sort().forEach(range => {
                const [start, end] = range.split('...');
                processed.push({
                    ...g,
                    ano_inicio: start !== 'undefined' && start !== 'null' ? (isNaN(Number(start)) ? start : Number(start)) : null,
                    ano_fim: end !== 'undefined' && end !== 'null' ? (isNaN(Number(end)) ? end : Number(end)) : null
                });
            });

            // Se não tiver anos, adiciona a linha base
            if (g.anos.length === 0) {
                processed.push(g);
            }
        });

        return processed.sort((a, b) => {
            if (a.marca !== b.marca) return a.marca.localeCompare(b.marca);
            if (a.veiculo !== b.veiculo) return a.veiculo.localeCompare(b.veiculo);
            if (a.modelo !== b.modelo) return (a.modelo || '').localeCompare(b.modelo || '');
            return (a.ano_inicio || 0) - (b.ano_inicio || 0);
        });
    }, [results, visibleFields, agrupar]);

    const clearResults = () => {
        setResults([]);
        setPartId('');
    };

    const downloadAllImages = async () => {
        const imagesToDownload: { url: string; name: string }[] = [];
        const seenUrls = new Set<string>();
        
        results.forEach((res) => {
            const allImgs = res.imagens && res.imagens.length > 0 ? res.imagens : (res.image || res.imagem ? [res.image || res.imagem] : []);
            allImgs.forEach((url: string, imgIdx: number) => {
                if (url && url.startsWith('http') && !seenUrls.has(url)) {
                    seenUrls.add(url);
                    // Como as fotos são da PEÇA, usamos o código ou marca para o nome
                    // Extraímos o nome do arquivo da URL original para manter extensões e sufixos (ex: WO-545B.jpg)
                    const urlPath = url.split('/').pop()?.split('?')[0] || `imagem_${imgIdx}.jpg`;
                    const fileName = `${res.marca || 'PECA'}_${urlPath}`.replace(/[^a-z0-9._-]/gi, '_');
                    imagesToDownload.push({ url, name: fileName });
                }
            });
        });

        if (imagesToDownload.length === 0) {
            alert('Nenhuma imagem encontrada para baixar.');
            return;
        }

        setLoading(true);
        const zip = new JSZip();
        
        try {
            const downloadPromises = imagesToDownload.map(async (img) => {
                try {
                    // Usa o proxy do backend para evitar CORS
                    const proxyUrl = `http://localhost:8000/search/proxy/image?url=${encodeURIComponent(img.url)}`;
                    const response = await fetch(proxyUrl);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const blob = await response.blob();
                    zip.file(img.name, blob);
                } catch (err) {
                    console.error(`Falha ao baixar imagem via proxy: ${img.url}`, err);
                }
            });

            await Promise.all(downloadPromises);
            
            const content = await zip.generateAsync({ type: 'blob' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(content);
            link.download = `imagens_${partId || 'busca'}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Erro ao gerar ZIP:', error);
            alert('Erro ao compactar imagens.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 pb-20">
            {/* Search Header */}
            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                <form onSubmit={handleSearch} className="space-y-4">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                <Search size={20} />
                            </div>
                            <input
                                type="text"
                                className="block w-full pl-10 pr-3 py-3 border border-slate-200 dark:border-slate-700 rounded-xl bg-slate-50 dark:bg-slate-900 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                placeholder="Digite o código da peça..."
                                value={partId}
                                onChange={(e) => setPartId(e.target.value)}
                            />
                        </div>

                        <div className="w-full md:w-64">
                            <select
                                value={selectedProvedor}
                                onChange={(e) => setSelectedProvedor(Number(e.target.value))}
                                className="w-full h-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-primary transition-all"
                            >
                                <option value="">Todos os Provedores</option>
                                {provedores.map(p => (
                                    <option key={p.id} value={p.id}>{p.nome}</option>
                                ))}
                            </select>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/20 md:w-auto w-full"
                        >
                            {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                            {loading ? 'Buscando...' : 'Pesquisar'}
                        </button>
                    </div>

                    {/* Filters Row */}
                    <div className="flex flex-col lg:flex-row lg:items-center gap-6 pt-4 border-t border-slate-100 dark:border-slate-800 mt-4">
                        <div className="flex items-center gap-2 overflow-x-auto pb-2 lg:pb-0 no-scrollbar">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">Exibir:</span>
                            <div className="flex items-center gap-4">
                                {Object.keys(visibleFields).map((field) => {
                                    if (selectedProvedor) {
                                        const prov = provedores.find(p => String(p.id) === String(selectedProvedor));
                                        if (prov && prov.mapeamento) {
                                            try {
                                                const map = JSON.parse(prov.mapeamento);
                                                const coreFields = ['marca', 'veiculo', 'modelo', 'motor', 'configuracao_motor', 'ano', 'observacao', 'imagem'];
                                                if (!map[field] && !coreFields.includes(field)) return null;
                                            } catch { }
                                        }
                                    }
                                    return (
                                        <label key={field} className="flex items-center gap-2 cursor-pointer group whitespace-nowrap">
                                            <input
                                                type="checkbox"
                                                className="sr-only"
                                                checked={visibleFields[field as keyof typeof visibleFields]}
                                                onChange={() => setVisibleFields((prev: any) => ({ ...prev, [field]: !prev[field as keyof typeof visibleFields] }))}
                                            />
                                            <div className={`w-4 h-4 rounded border transition-all flex items-center justify-center ${visibleFields[field as keyof typeof visibleFields] ? 'bg-primary border-primary' : 'border-slate-300 dark:border-slate-600'}`}>
                                                {visibleFields[field as keyof typeof visibleFields] && <Check size={10} className="text-white" />}
                                            </div>
                                            <span className="text-xs font-medium text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors capitalize">
                                                {getFieldLabel(field)}
                                            </span>
                                        </label>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-4 lg:ml-auto">
                            <div className="flex items-center gap-4 lg:border-l lg:border-slate-200 lg:dark:border-slate-800 lg:pl-4">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        className="sr-only"
                                        checked={agrupar}
                                        onChange={() => setAgrupar(prev => !prev)}
                                    />
                                    <div className={`w-8 h-4 rounded-full transition-all relative ${agrupar ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}>
                                        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${agrupar ? 'left-[18px]' : 'left-0.5'}`} />
                                    </div>
                                    <span className="text-xs font-bold text-slate-600 dark:text-slate-400 group-hover:text-primary transition-colors uppercase whitespace-nowrap">
                                        Agrupar
                                    </span>
                                </label>
                            </div>

                            <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                                <button
                                    type="button"
                                    onClick={() => copyToClipboard('completa')}
                                    className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-900 transition-all text-[10px] font-bold flex items-center gap-1.5"
                                    title="Completa: Marca, Modelo, Motor, Config, Ano"
                                >
                                    <Copy size={10} /> COMPL.
                                </button>
                                <button
                                    type="button"
                                    onClick={() => copyToClipboard('intermediaria')}
                                    className="px-3 py-1.5 rounded-lg text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-slate-900 transition-all text-[10px] font-bold flex items-center gap-1.5"
                                    title="Interm: Marca, Veículo, Config, Ano (por range)"
                                >
                                    <Copy size={10} /> INTERM.
                                </button>
    </div>
    
    <button
        type="button"
        onClick={clearResults}
        className="text-[10px] font-bold text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest pl-2"
    >
        Limpar
    </button>
</div>
                    </div>
                </form>
            </div>

            {/* Results Section */}
            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <h2 className="font-bold text-lg">Resultados ({displayResults.length})</h2>
                        {Object.keys(uniqueReferences).length > 0 && (
                            <div className="flex flex-wrap gap-2 items-center bg-primary/5 border border-primary/10 rounded-lg px-3 py-1.5">
                                <span className="text-[10px] font-black text-primary uppercase">Original:</span>
                                {Object.entries(uniqueReferences).map(([brand, codes]: [string, any]) => (
                                    <div key={brand} className="flex items-center gap-1.5">
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">{brand}</span>
                                        <span className="text-[10px] font-mono font-medium text-slate-700 dark:text-slate-300">
                                            {Array.from(codes as Set<string>).sort().join(' - ')}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2">
                        {results.length > 0 && (
                            <button
                                onClick={downloadAllImages}
                                disabled={loading}
                                className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-orange-500/10 text-orange-600 hover:bg-orange-500/20 transition-all border border-orange-500/20 disabled:opacity-50"
                                title="Baixa todas as imagens no formato .zip"
                            >
                                {loading ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
                                Salvar Todas
                            </button>
                        )}
                        <button
                            onClick={() => copyToClipboard('completa')}
                            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20"
                        >
                            <Copy size={14} /> Copiar Tudo
                        </button>
                    </div>
                </div>

                <div className="md:block hidden overflow-x-auto custom-scrollbar">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                            <tr>
                                {visibleFields.marca && <th className="px-6 py-4">{getFieldLabel('marca')}</th>}
                                {visibleFields.veiculo && <th className="px-6 py-4">{getFieldLabel('veiculo')}</th>}
                                {visibleFields.modelo && <th className="px-6 py-4">{getFieldLabel('modelo')}</th>}
                                {visibleFields.motor && <th className="px-6 py-4">{getFieldLabel('motor')}</th>}
                                {visibleFields.configuracao_motor && <th className="px-6 py-4">{getFieldLabel('configuracao_motor')}</th>}
                                {visibleFields.ano && <th className="px-6 py-4 text-center">{getFieldLabel('ano')}</th>}
                                {visibleFields.observacao && <th className="px-6 py-4">{getFieldLabel('observacao')}</th>}
                                {visibleFields.posicao && <th className="px-6 py-4">{getFieldLabel('posicao')}</th>}
                                {visibleFields.lado && <th className="px-6 py-4">{getFieldLabel('lado')}</th>}
                                {visibleFields.direcao && <th className="px-6 py-4">{getFieldLabel('direcao')}</th>}
                                {visibleFields.referencias && <th className="px-6 py-4">{getFieldLabel('referencias')}</th>}
                                {visibleFields.imagem && <th className="px-6 py-4">{getFieldLabel('imagem')}</th>}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {displayResults.length === 0 ? (
                                <tr>
                                    <td colSpan={12} className="px-6 py-12 text-center text-slate-400 italic">
                                        {loading ? 'Consultando provedores...' : 'Nenhum resultado para exibir.'}
                                    </td>
                                </tr>
                            ) : (
                                displayResults.map((res, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors text-[11px]">
                                        {visibleFields.marca && (
                                            <td className="px-6 py-4 font-semibold text-primary uppercase">{res.marca}</td>
                                        )}
                                        {visibleFields.veiculo && (
                                            <td className="px-6 py-4 text-xs font-medium">{res.veiculo}</td>
                                        )}
                                        {visibleFields.modelo && (
                                            <td className="px-6 py-4 text-xs">{res.modelo}</td>
                                        )}
                                        {visibleFields.motor && (
                                            <td className="px-6 py-4 font-bold text-slate-600 dark:text-slate-200">
                                                {res.motor}
                                            </td>
                                        )}
                                        {visibleFields.configuracao_motor && (
                                            <td className="px-6 py-4">
                                                <div className="text-slate-500 uppercase">{res.configuracao_motor}</div>
                                            </td>
                                        )}
                                        {visibleFields.ano && (
                                            <td className="px-6 py-4 text-center font-mono bg-slate-50/50 dark:bg-slate-900/20">
                                                {res.ano_inicio || res.ano_fim ? (
                                                    <div className="flex items-center justify-center gap-1">
                                                        <span>{res.ano_inicio || ''}</span>
                                                        <span className="text-slate-300">...</span>
                                                        <span>{res.ano_fim || ''}</span>
                                                    </div>
                                                ) : '---'}
                                            </td>
                                        )}
                                        {visibleFields.observacao && (
                                            <td className="px-6 py-4">
                                                <div className="text-slate-500">{res.observacao || '---'}</div>
                                            </td>
                                        )}
                                        {visibleFields.posicao && (
                                            <td className="px-6 py-4">
                                                <div className="text-slate-500 uppercase">{res.posicao || '---'}</div>
                                            </td>
                                        )}
                                        {visibleFields.lado && (
                                            <td className="px-6 py-4">
                                                <div className="text-slate-500 uppercase">{res.lado || '---'}</div>
                                            </td>
                                        )}
                                        {visibleFields.direcao && (
                                            <td className="px-6 py-4">
                                                <div className="text-slate-500 uppercase">{res.direcao || '---'}</div>
                                            </td>
                                        )}
                                        {visibleFields.referencias && (
                                            <td className="px-6 py-4">
                                                <div className="text-[10px] text-slate-500 max-w-xs truncate" title={res.referencias}>
                                                    {res.referencias || '---'}
                                                </div>
                                            </td>
                                        )}
                                        {visibleFields.imagem && (
                                            <td className="px-6 py-4">
                                                <div className="flex flex-wrap gap-2">
                                                    {(res.imagens && res.imagens.length > 0) ? (
                                                        res.imagens.map((imgUrl: string, i: number) => (
                                                            <div key={i} className="group relative">
                                                                <div className="h-10 w-10 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-white flex items-center justify-center p-1 transition-all group-hover:scale-110 group-hover:shadow-lg">
                                                                    <img src={imgUrl} alt={`Peça ${i + 1}`} className="max-h-full max-w-full object-contain" />
                                                                </div>
                                                                <div className="absolute -top-2 -right-2 hidden group-hover:flex gap-1 animate-in fade-in zoom-in duration-200">
                                                                    <a
                                                                        href={imgUrl}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="bg-primary text-white p-1 rounded-full shadow-md hover:bg-primary-hover transition-colors"
                                                                        title="Abrir imagem original"
                                                                    >
                                                                        <FileDown size={10} />
                                                                    </a>
                                                                </div>
                                                            </div>
                                                        ))
                                                    ) : res.imagem ? (
                                                        <div className="group relative">
                                                            <div className="h-10 w-10 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-white flex items-center justify-center p-1 transition-all group-hover:scale-110 group-hover:shadow-lg">
                                                                <img src={res.imagem} alt="Peça" className="max-h-full max-w-full object-contain" />
                                                            </div>
                                                            <div className="absolute -top-2 -right-2 hidden group-hover:flex animate-in fade-in zoom-in duration-200">
                                                                <a
                                                                    href={res.imagem}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="bg-primary text-white p-1 rounded-full shadow-md hover:bg-primary-hover transition-colors"
                                                                    title="Abrir imagem original"
                                                                >
                                                                    <FileDown size={10} />
                                                                </a>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="h-10 w-10 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                                                            <div className="opacity-20 text-[9px] font-bold">N/A</div>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Mobile Card View */}
                <div className="md:hidden block divide-y divide-slate-100 dark:divide-slate-800">
                    {displayResults.length === 0 ? (
                        <div className="px-6 py-12 text-center text-slate-400 italic">
                            {loading ? 'Consultando provedores...' : 'Nenhum resultado para exibir.'}
                        </div>
                    ) : (
                        displayResults.map((res, idx) => (
                            <div key={idx} className="p-4 space-y-3 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors">
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-black bg-primary/10 text-primary px-1.5 py-0.5 rounded uppercase">
                                                {res.marca}
                                            </span>
                                            <span className="text-sm font-bold text-slate-900 dark:text-white">
                                                {res.veiculo}
                                            </span>
                                        </div>
                                        <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                                            {res.modelo} • {res.motor}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                            {res.ano_inicio || '---'} {res.ano_inicio || res.ano_fim ? '...' : ''} {res.ano_fim || ''}
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px] text-slate-500">
                                    {visibleFields.configuracao_motor && (
                                        <div>
                                            <span className="font-bold text-slate-400 uppercase mr-1">{getFieldLabel('configuracao_motor')}:</span>
                                            <span className="text-slate-700 dark:text-slate-300">{res.configuracao_motor || '---'}</span>
                                        </div>
                                    )}
                                    {visibleFields.posicao && res.posicao && (
                                        <div>
                                            <span className="font-bold text-slate-400 uppercase mr-1">{getFieldLabel('posicao')}:</span>
                                            <span className="text-slate-700 dark:text-slate-300">{res.posicao}</span>
                                        </div>
                                    )}
                                    {visibleFields.observacao && res.observacao && (
                                        <div className="col-span-2">
                                            <span className="font-bold text-slate-400 uppercase mr-1">{getFieldLabel('observacao')}:</span>
                                            <span className="text-slate-700 dark:text-slate-300">{res.observacao}</span>
                                        </div>
                                    )}
                                </div>

                                {visibleFields.imagem && (
                                    <div className="flex flex-wrap gap-2 pt-1">
                                        {(res.imagens && res.imagens.length > 0) ? (
                                            res.imagens.map((imgUrl: string, i: number) => (
                                                <a
                                                    key={i}
                                                    href={imgUrl}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="h-14 w-14 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-white p-1"
                                                >
                                                    <img src={imgUrl} alt={`Peça ${i + 1}`} className="h-full w-full object-contain" />
                                                </a>
                                            ))
                                        ) : res.imagem && (
                                            <a
                                                href={res.imagem}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="h-14 w-14 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-white p-1"
                                            >
                                                <img src={res.imagem} alt="Peça" className="h-full w-full object-contain" />
                                            </a>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Home;
