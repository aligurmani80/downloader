import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  DownloadCloud, 
  History, 
  Settings, 
  Sparkles, 
  Activity,
  FolderOpen
} from 'lucide-react';
import { api } from '../services/api';

export default function Navbar() {
  const { activeTab, setActiveTab, serverStatus, history, addToast } = useApp();

  const handleOpenDownloadsFolder = async () => {
    try {
      await api.openFolder();
      addToast('Opened downloads folder in Explorer', 'info');
    } catch {
      addToast('Could not open folder on system', 'error');
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-slate-950/70 border-b border-white/10 transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <button
          onClick={() => setActiveTab('downloader')}
          className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-400 rounded-lg p-1"
        >
          <div className="relative w-10 h-10 rounded-xl gradient-brand flex items-center justify-center shadow-lg shadow-purple-500/20 group-hover:scale-105 transition-transform duration-200">
            <DownloadCloud className="w-5 h-5 text-white" />
            <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-white font-sans">
                Nexa<span className="text-cyan-400">Load</span>
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Universal Media Engine</p>
          </div>
        </button>

        {/* Center Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2 bg-slate-900/80 p-1 rounded-xl border border-white/5" aria-label="Main Navigation">
          <button
            onClick={() => setActiveTab('downloader')}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'downloader'
                ? 'bg-purple-600/90 text-white shadow-md shadow-purple-600/20'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <DownloadCloud className="w-4 h-4" />
            <span>Downloader</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all relative ${
              activeTab === 'history'
                ? 'bg-purple-600/90 text-white shadow-md shadow-purple-600/20'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <History className="w-4 h-4" />
            <span>History</span>
            {history.length > 0 && (
              <span className="ml-0.5 px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {history.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'settings'
                ? 'bg-purple-600/90 text-white shadow-md shadow-purple-600/20'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Settings</span>
          </button>
        </nav>

        {/* Right Action: Open folder & Server status */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenDownloadsFolder}
            title="Open Downloads Folder"
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-white/10 transition-colors"
          >
            <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Downloads</span>
          </button>

          <div
            title={`Backend Status: ${serverStatus}`}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900/80 border border-white/10 text-xs"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                serverStatus === 'online'
                  ? 'bg-emerald-400 animate-pulse ring-2 ring-emerald-400/30'
                  : 'bg-amber-400'
              }`}
            />
            <span className="text-[11px] font-medium text-slate-300 hidden sm:inline">
              {serverStatus === 'online' ? 'Online' : 'Engine...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
