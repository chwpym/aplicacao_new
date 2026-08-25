import React, { useState } from 'react';
import { Printer, Download, RotateCcw, Box, FileText } from 'lucide-react';

export const Etiquetas: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'peca' | 'livre' | 'rotacionada'>('peca');
  
  const [formData, setFormData] = useState({
    titulo: 'ORIGINAL AUTO PECAS',
    codigo: '',
    codigo_secundario: '',
    linha1: '',
    linha2: '',
    linha3: '',
    linha4: '',
    linha5: '',
    esq_linha1: '',
    esq_linha2: '',
    esq_linha3: '',
    esq_linha4: '',
    dir_linha1: '',
    dir_linha2: '',
    dir_linha3: '',
    dir_linha4: ''
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const payload = {
        template: activeTab,
        ...formData,
        rotacionar: activeTab === 'rotacionada'
      };

      const response = await fetch('http://localhost:8000/zpl/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Falha ao gerar ZPL');
      
      const data = await response.json();
      const zplCode = data.zpl;

      // Criar Blob e fazer o Download do arquivo TXT
      const blob = new Blob([zplCode], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `etiqueta_${activeTab}_${Date.now()}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

    } catch (error) {
      console.error(error);
      alert('Erro ao gerar etiqueta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 w-full flex flex-col p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
            <Printer size={24} className="text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Gerador de Etiquetas (ZPL)</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Gere arquivos de impressão térmica direta (.txt)</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700/50 w-max">
          <button
            onClick={() => setActiveTab('peca')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'peca' ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'}`}
          >
            <Box size={16} /> Etiqueta Dupla (Peça)
          </button>
          <button
            onClick={() => setActiveTab('livre')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'livre' ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'}`}
          >
            <FileText size={16} /> Etiqueta Livre
          </button>
          <button
            onClick={() => setActiveTab('rotacionada')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'rotacionada' ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'}`}
          >
            <RotateCcw size={16} /> Especial (Rotacionada)
          </button>
        </div>

        {/* Formulário */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700/50 overflow-hidden">
          <div className="p-6 space-y-4">
            
            {activeTab !== 'rotacionada' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase">Título (Topo)</label>
                  <input type="text" name="titulo" value={formData.titulo} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder="Ex: ORIGINAL AUTO PECAS" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase">Código / Ref</label>
                  <input type="text" name="codigo" value={formData.codigo} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-bold text-purple-600" placeholder="Ex: 015511 MDS" />
                </div>
              </div>
            )}

            {activeTab !== 'rotacionada' ? (
              <>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase">
                    {activeTab === 'peca' ? 'Descrição da Peça (Linha 1)' : 'Linha 1'}
                  </label>
                  <input type="text" name="linha1" value={formData.linha1} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder="Ex: DISCO FREIO DIANTEIRO SOLIDO M" />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase">
                    {activeTab === 'peca' ? 'Complemento (Linha 2)' : 'Linha 2'}
                  </label>
                  <input type="text" name="linha2" value={formData.linha2} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder="Ex: DS D28" />
                </div>

                {activeTab === 'peca' ? (
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-500 uppercase">Aplicações (Linhas 3, 4, 5)</label>
                    <input type="text" name="linha3" value={formData.linha3} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm mb-2" placeholder="Linha 3 (Ex: GM CORSA 10 / 14...)" />
                    <input type="text" name="linha4" value={formData.linha4} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm mb-2" placeholder="Linha 4" />
                    <input type="text" name="linha5" value={formData.linha5} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder="Linha 5" />
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-500 uppercase">Aplicações Livres (Linhas 3, 4, 5)</label>
                    <input type="text" name="linha3" value={formData.linha3} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm mb-2" placeholder="Linha 3" />
                    <input type="text" name="linha4" value={formData.linha4} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm mb-2" placeholder="Linha 4" />
                    <input type="text" name="linha5" value={formData.linha5} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder="Linha 5" />
                  </div>
                )}
              </>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Etiqueta Esquerda */}
                <div className="space-y-4">
                  <h3 className="font-bold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 pb-2">Etiqueta Esquerda</h3>
                  {['esq_linha1', 'esq_linha2', 'esq_linha3', 'esq_linha4'].map((fieldName, i) => (
                    <div key={fieldName} className="space-y-1.5">
                      <label className="text-xs font-semibold text-slate-500 uppercase">Linha {i + 1}</label>
                      <input type="text" name={fieldName} value={(formData as any)[fieldName]} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder={`Texto Linha ${i + 1}`} />
                    </div>
                  ))}
                </div>
                {/* Etiqueta Direita */}
                <div className="space-y-4">
                  <h3 className="font-bold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 pb-2">Etiqueta Direita</h3>
                  {['dir_linha1', 'dir_linha2', 'dir_linha3', 'dir_linha4'].map((fieldName, i) => (
                    <div key={fieldName} className="space-y-1.5">
                      <label className="text-xs font-semibold text-slate-500 uppercase">Linha {i + 1}</label>
                      <input type="text" name={fieldName} value={(formData as any)[fieldName]} onChange={handleChange} className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm" placeholder={`Texto Linha ${i + 1}`} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700/50 flex justify-end">
            <button 
              onClick={handleGenerate}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-medium transition-all shadow-sm shadow-purple-600/20 disabled:opacity-50"
            >
              <Download size={16} /> {loading ? 'Gerando...' : 'Baixar TXT (ZPL)'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
