import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { configApi } from '../services/api';
import {
  Settings,
  Search,
  Hash,
  Trash2,
  Database,
  Moon,
  Sun,
  FlaskConical,
  Menu,
  X,
  HelpCircle,
  Download,
  SlidersHorizontal,
  Car
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme');
      if (saved) return saved === 'dark';
      return document.documentElement.classList.contains('dark');
    }
    return false;
  });

  const location = useLocation();

  const [isBackingUp, setIsBackingUp] = useState(false);
  const [notification, setNotification] = useState<{ message: string, type: 'success' | 'error' } | null>(null);

  const handleBackup = async () => {
    if (isBackingUp) return;
    setIsBackingUp(true);
    try {
      const resp = await configApi.exportBackup();
      setNotification({ message: resp.data.message, type: 'success' });
    } catch (error) {
      setNotification({ message: "Falha ao realizar backup.", type: 'error' });
    } finally {
      setIsBackingUp(false);
      // Remove notificação após 5 segundos
      setTimeout(() => setNotification(null), 5000);
    }
  };

  React.useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  const [systemStatus, setSystemStatus] = useState<'healthy' | 'warning' | 'critical' | 'offline'>('offline');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const resp = await configApi.getHealth();
        setSystemStatus(resp.data.overall);
      } catch (error) {
        setSystemStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 600000); // 10 minutos
    return () => clearInterval(interval);
  }, []);

  // Listener para Toasts Globais
  useEffect(() => {
    const handleToast = (e: any) => {
      const { message, type } = e.detail;
      setNotification({ message, type });
      // Auto-hide após 5 segundos
      setTimeout(() => setNotification(null), 5000);
    };

    window.addEventListener('app-toast', handleToast);
    return () => window.removeEventListener('app-toast', handleToast);
  }, []);

  const getStatusColor = () => {
    switch (systemStatus) {
      case 'healthy': return 'bg-emerald-500 shadow-emerald-500/50';
      case 'warning': return 'bg-amber-500 shadow-amber-500/50';
      case 'critical': return 'bg-rose-500 shadow-rose-500/50';
      default: return 'bg-slate-400';
    }
  };

  const navItems = [
    { name: 'Workspace', path: '/', icon: <Search size={20} /> },
    { name: 'Provedores', path: '/provedores', icon: <Database size={20} /> },
    { name: 'Siglas', path: '/siglas', icon: <Hash size={20} /> },
    { name: 'Playground', path: '/playground', icon: <FlaskConical size={20} /> },
    { name: 'Limpeza', path: '/palavras', icon: <Trash2 size={20} /> },
    { name: 'Biblioteca', path: '/automakers', icon: <Car size={20} /> },
    { name: 'Configurações', path: '/configuracoes', icon: <SlidersHorizontal size={20} /> },
    { name: 'Backup', path: '#', icon: <Download size={20} />, action: 'backup' },
    { name: 'Ajuda', path: '/ajuda', icon: <HelpCircle size={20} /> },
  ];

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className={`min-h-screen bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 flex flex-col md:flex-row transition-colors duration-200`}>
      {/* Notificação Customizada */}
      {notification && (
        <div className="fixed top-6 right-6 z-[100] animate-in fade-in slide-in-from-right-8 duration-300">
          <div className={`
            px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-md border flex items-center gap-4 min-w-[320px] max-w-[500px]
            ${notification.type === 'success' 
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' 
              : 'bg-rose-500/10 border-rose-500/20 text-rose-500'}
          `}>
            <div className={`p-2 rounded-xl ${notification.type === 'success' ? 'bg-emerald-500/20' : 'bg-rose-500/20'}`}>
              {notification.type === 'success' ? <Download size={20} /> : <X size={20} />}
            </div>
            <div className="flex-1 flex flex-col gap-0.5">
              <span className="font-black text-xs uppercase tracking-wider">
                {notification.type === 'success' ? 'Backup Concluído' : 'Erro no Sistema'}
              </span>
              <p className="text-[11px] font-bold opacity-90 break-all leading-relaxed">
                {notification.message}
              </p>
            </div>
            <button 
              onClick={() => setNotification(null)}
              className="p-1 hover:bg-black/5 rounded-lg transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Mobile Header */}
      <header className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="bg-primary p-1.5 rounded-lg">
            <Settings className="text-white" size={20} />
          </div>
          <h1 className="text-lg font-bold tracking-tight">Catalogo V4</h1>
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Mobile Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={() => setIsMobileMenuOpen(false)}>
          <div
            className="absolute left-0 top-0 bottom-0 w-64 bg-surface-light dark:bg-surface-dark p-6 shadow-xl animate-in slide-in-from-left duration-300"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex flex-col h-full uppercase">
              <div className="flex items-center gap-3 mb-8">
                <div className="bg-primary p-2 rounded-xl">
                  <Settings className="text-white" size={24} />
                </div>
                <span className="font-bold text-lg">Menu</span>
              </div>

              <nav className="flex flex-col gap-2">
                {navItems.map((item) => (
                  item.action === 'backup' ? (
                    <button
                      key={item.name}
                      onClick={handleBackup}
                      disabled={isBackingUp}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 w-full text-left uppercase font-bold`}
                    >
                      {item.icon}
                      <span>{isBackingUp ? 'Processando...' : item.name}</span>
                    </button>
                  ) : (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${location.pathname === item.path
                        ? 'bg-primary text-white shadow-lg shadow-primary/20 font-bold'
                        : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500'
                        }`}
                    >
                      {item.icon}
                      <span>{item.name}</span>
                    </Link>
                  )
                ))}
              </nav>

              <div className="mt-auto pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-4">
                <button
                  onClick={toggleTheme}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition-all font-bold"
                >
                  {isDark ? <Sun size={20} /> : <Moon size={20} />}
                  <span>{isDark ? 'Modo Claro' : 'Modo Escuro'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-surface-light dark:bg-surface-dark border-r border-slate-200 dark:border-slate-800 h-screen sticky top-0 shrink-0">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-primary p-2 rounded-xl shadow-lg shadow-primary/30">
              <Settings className="text-white" size={24} />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight leading-none">Catalogo V4</h1>
                <div 
                  className={`w-2 h-2 rounded-full ${getStatusColor()} shadow-[0_0_8px] transition-all duration-500`}
                  title={`Status da API FIPE: ${systemStatus.toUpperCase()}`}
                />
              </div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Gerenciador de Peças</span>
            </div>
          </div>

          <nav className="flex flex-col gap-1.5 uppercase tracking-wider text-[11px] font-bold">
            <span className="text-slate-400 px-4 py-2 mb-1">Navegação</span>
            {navItems.map((item) => (
              item.action === 'backup' ? (
                <button
                  key={item.name}
                  onClick={handleBackup}
                  disabled={isBackingUp}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-500 w-full text-left uppercase font-bold ${isBackingUp ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {item.icon}
                  <span>{isBackingUp ? 'Processando...' : item.name}</span>
                </button>
              ) : (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${location.pathname === item.path
                    ? 'bg-primary text-white shadow-lg shadow-primary/25 translate-x-1'
                    : 'hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-500'
                    }`}
                >
                  {item.icon}
                  <span>{item.name}</span>
                </Link>
              )
            ))}
          </nav>
        </div>

        <div className="mt-auto p-6 space-y-4">
          <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3 mb-1">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary text-xs shrink-0">
                AC
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-xs font-bold truncate">Estoque Original</span>
                <span className="text-[9px] text-slate-400 font-bold uppercase">Administrador</span>
              </div>
            </div>
          </div>

          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-500 transition-all font-bold text-xs border border-transparent hover:border-slate-200 dark:hover:border-slate-800"
          >
            <div className="flex items-center gap-3">
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
              <span>{isDark ? 'Tema Claro' : 'Tema Escuro'}</span>
            </div>
            <div className={`w-8 h-4 rounded-full p-1 transition-colors ${isDark ? 'bg-primary' : 'bg-slate-300'}`}>
              <div className={`w-2 h-2 rounded-full bg-white transition-transform ${isDark ? 'translate-x-4' : ''}`} />
            </div>
          </button>

          <div className="text-[9px] text-slate-400 text-center font-bold uppercase tracking-widest pt-2">
            v4.0.0-react | 2024
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 overflow-auto p-4 md:p-8 max-w-[1600px] mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
