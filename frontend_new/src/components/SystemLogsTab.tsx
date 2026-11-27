import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, Trash2, Copy, Search, Terminal, AlertCircle } from 'lucide-react';
import { configApi } from '../services/api';
import { toast } from '../utils/toast';

interface LogRecord {
  timestamp: string;
  level: string;
  category: string;
  message: string;
}

export const SystemLogsTab: React.FC = () => {
  const [logs, setLogs] = useState<LogRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [serverTime, setServerTime] = useState<string>('');
  const logContainerRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const response = await configApi.getSystemLogs({
        limit: 300,
        level: selectedLevel !== 'ALL' ? selectedLevel : undefined,
        search: searchTerm || undefined
      });
      if (response.data && response.data.logs) {
        setLogs(response.data.logs);
        setServerTime(response.data.server_time || '');
      }
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
      if (!silent) toast.error('Não foi possível obter logs do servidor.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedLevel]);

  // Auto-refresh a cada 3 segundos se ativado
  useEffect(() => {
    let interval: any = null;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchLogs(true);
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, selectedLevel, searchTerm]);

  // Rola para o final quando novos logs chegam
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleClear = async () => {
    if (!window.confirm('Deseja limpar os logs do buffer em memória?')) return;
    try {
      await configApi.clearSystemLogs();
      setLogs([]);
      toast.success('Logs limpos com sucesso.');
    } catch (error) {
      toast.error('Erro ao limpar logs.');
    }
  };

  const handleCopy = () => {
    if (logs.length === 0) return;
    const text = logs.map(l => `[${l.timestamp}] [${l.level}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    toast.success('Logs copiados para a área de transferência!');
  };

  const getLevelBadgeClass = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border border-red-500/30';
      case 'WARNING':
        return 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
      case 'DEBUG':
        return 'bg-purple-500/20 text-purple-400 border border-purple-500/30';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Barra de Ações e Filtros */}
      <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 p-4 rounded-xl shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input
            type="text"
            placeholder="Filtrar mensagem de log (ex: METRICS, WEGA, erro, 200 OK)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchLogs()}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:ring-2 focus:ring-primary/50 text-xs transition-all"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto shrink-0 flex-wrap">
          {/* Seletor de Nível */}
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="ALL">Nível: Todos</option>
            <option value="INFO">Apenas INFO</option>
            <option value="WARNING">Apenas AVISOS</option>
            <option value="ERROR">Apenas ERROS</option>
          </select>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
              autoRefresh 
                ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' 
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 border-slate-200 dark:border-slate-700'
            }`}
            title="Atualização automática a cada 3 segundos"
          >
            <RefreshCw size={13} className={autoRefresh ? 'animate-spin' : ''} />
            Auto ({autoRefresh ? 'Ligado' : 'Desligado'})
          </button>

          {/* Atualizar Manual */}
          <button
            onClick={() => fetchLogs()}
            disabled={loading}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors"
            title="Atualizar agora"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>

          {/* Copiar */}
          <button
            onClick={handleCopy}
            disabled={logs.length === 0}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors disabled:opacity-50"
            title="Copiar todos os logs"
          >
            <Copy size={14} />
          </button>

          {/* Limpar */}
          <button
            onClick={handleClear}
            disabled={logs.length === 0}
            className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg border border-red-500/20 transition-colors disabled:opacity-50"
            title="Limpar logs"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Terminal View */}
      <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col font-mono text-xs">
        {/* Terminal Header */}
        <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800/80 flex items-center justify-between text-slate-400 select-none">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80 inline-block" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80 inline-block" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
            <span className="ml-2 font-bold text-[11px] text-slate-300 flex items-center gap-1.5">
              <Terminal size={14} className="text-primary" />
              Terminal de Operações da API (Nuvem / Local)
            </span>
          </div>
          <div className="text-[10px] text-slate-500 flex items-center gap-2">
            {serverTime && <span>Hora no Servidor: {serverTime}</span>}
            <span>• {logs.length} registros</span>
          </div>
        </div>

        {/* Terminal Body */}
        <div 
          ref={logContainerRef}
          className="p-4 space-y-1.5 max-h-[500px] min-h-[300px] overflow-y-auto custom-scrollbar select-text leading-relaxed"
        >
          {loading && logs.length === 0 ? (
            <div className="py-20 text-center text-slate-500 flex flex-col items-center gap-2">
              <RefreshCw size={24} className="animate-spin text-primary" />
              <span>Conectando e lendo logs do servidor...</span>
            </div>
          ) : logs.length === 0 ? (
            <div className="py-20 text-center text-slate-600 flex flex-col items-center gap-2">
              <AlertCircle size={28} className="opacity-30" />
              <span>Nenhum registro de log encontrado para os filtros atuais.</span>
              <span className="text-[11px] text-slate-700">Faça uma busca no Workspace para gerar novos registros.</span>
            </div>
          ) : (
            logs.map((log, index) => {
              const isError = log.level === 'ERROR' || log.level === 'CRITICAL' || log.message.includes('Erro');
              const isMetrics = log.message.includes('[METRICS]') || log.message.includes('resultados');
              const isAudit = log.message.includes('[AUDIT]') || log.message.includes('Iniciando busca');
              
              return (
                <div 
                  key={index} 
                  className={`flex items-start gap-2 py-0.5 px-1.5 rounded hover:bg-slate-900/60 transition-colors ${
                    isError ? 'bg-red-500/5 text-red-300' : isMetrics ? 'text-emerald-300' : isAudit ? 'text-cyan-300' : 'text-slate-300'
                  }`}
                >
                  <span className="text-slate-600 shrink-0 text-[10px] select-none">{log.timestamp.slice(11)}</span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold shrink-0 ${getLevelBadgeClass(log.level)}`}>
                    {log.level}
                  </span>
                  <span className="break-all whitespace-pre-wrap">{log.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
