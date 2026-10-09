import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { 
  Settings, 
  Palette, 
  Sliders, 
  Shield, 
  Folder, 
  Check, 
  HardDrive, 
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import { api } from '../services/api';

export default function SettingsView() {
  const { 
    theme, 
    setTheme, 
    settings, 
    setSettings, 
    serverStatus, 
    loadHistory, 
    addToast 
  } = useApp();

  const [systemInfo, setSystemInfo] = useState(null);

  useEffect(() => {
    api.checkHealth().then((info) => setSystemInfo(info)).catch(() => {});
  }, []);

  const handleUpdate = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    addToast('Preferences saved', 'info');
  };

  const handleOpenFolder = async () => {
    try {
      await api.openFolder();
      addToast('Opened downloads folder', 'info');
    } catch {
      addToast('Failed to open downloads folder', 'error');
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Clear all downloaded history? Files on your hard drive will remain intact.')) return;
    try {
      await api.clearHistory();
      await loadHistory();
      addToast('History cleared', 'success');
    } catch {
      addToast('Failed to clear history', 'error');
    }
  };

  return (
    <div className="w-full space-y-6 max-w-4xl mx-auto animate-in fade-in duration-300">
      <div className="glass-panel rounded-2xl p-4 sm:p-6">
        <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-purple-400" />
          <span>Application Settings</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Customize interface themes, default output qualities, and media preferences.
        </p>
      </div>

      {/* Theme selection card */}
      <div className="glass-panel rounded-2xl p-5 sm:p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Palette className="w-4 h-4 text-cyan-400" />
          <span>Appearance & Visual Theme</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Cyber Dark */}
          <button
            type="button"
            onClick={() => setTheme('theme-cyber')}
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer relative ${
              theme === 'theme-cyber'
                ? 'bg-purple-600/20 border-purple-500 ring-2 ring-purple-500/30 text-white'
                : 'bg-slate-900/60 border-white/5 text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-white">Cyber Dark</span>
              {theme === 'theme-cyber' && <Check className="w-4 h-4 text-purple-400" />}
            </div>
            <p className="text-xs text-slate-400">
              Deep obsidian with neon violet and electric cyan accents.
            </p>
          </button>

          {/* Midnight Slate */}
          <button
            type="button"
            onClick={() => setTheme('theme-slate')}
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer relative ${
              theme === 'theme-slate'
                ? 'bg-blue-600/20 border-blue-500 ring-2 ring-blue-500/30 text-white'
                : 'bg-slate-900/60 border-white/5 text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-white">Midnight Slate</span>
              {theme === 'theme-slate' && <Check className="w-4 h-4 text-blue-400" />}
            </div>
            <p className="text-xs text-slate-400">
              Rich midnight navy with crisp blue and cool silver borders.
            </p>
          </button>

          {/* OLED Black */}
          <button
            type="button"
            onClick={() => setTheme('theme-oled')}
            className={`p-4 rounded-xl border text-left transition-all cursor-pointer relative ${
              theme === 'theme-oled'
                ? 'bg-zinc-800/60 border-purple-400 ring-2 ring-purple-400/30 text-white'
                : 'bg-slate-900/60 border-white/5 text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-white">OLED Black</span>
              {theme === 'theme-oled' && <Check className="w-4 h-4 text-purple-400" />}
            </div>
            <p className="text-xs text-slate-400">
              True #000000 black background for maximum contrast and battery savings.
            </p>
          </button>
        </div>
      </div>

      {/* Media & Quality Preferences */}
      <div className="glass-panel rounded-2xl p-5 sm:p-6 space-y-5">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span>Default Quality & Formats</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Default Video Quality */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Default Video Quality
            </label>
            <select
              value={settings.defaultQuality}
              onChange={(e) => handleUpdate('defaultQuality', e.target.value)}
              className="w-full glass-input rounded-xl px-3 py-2.5 text-xs text-slate-200 border border-white/10 focus:outline-none focus:border-purple-500"
            >
              <option value="best">Best Available (Auto Max Resolution)</option>
              <option value="1080p">1080p Full HD (Recommended)</option>
              <option value="720p">720p HD (Balanced Speed/Size)</option>
              <option value="480p">480p Standard Definition</option>
            </select>
          </div>

          {/* Default Audio Format */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Default Audio Format
            </label>
            <select
              value={settings.defaultAudioFormat}
              onChange={(e) => handleUpdate('defaultAudioFormat', e.target.value)}
              className="w-full glass-input rounded-xl px-3 py-2.5 text-xs text-slate-200 border border-white/10 focus:outline-none focus:border-cyan-500"
            >
              <option value="mp3">MP3 - 320 kbps (High Fidelity)</option>
              <option value="m4a">M4A - AAC (Apple Native)</option>
              <option value="wav">WAV - Uncompressed Lossless</option>
              <option value="opus">Opus - Efficient Voice & Music</option>
            </select>
          </div>

          {/* Preferred Video Container */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Preferred Video Container
            </label>
            <select
              value={settings.preferredContainer}
              onChange={(e) => handleUpdate('preferredContainer', e.target.value)}
              className="w-full glass-input rounded-xl px-3 py-2.5 text-xs text-slate-200 border border-white/10 focus:outline-none focus:border-purple-500"
            >
              <option value="mp4">MP4 (H.264/AAC - Universal Compatibility)</option>
              <option value="webm">WebM (VP9/Opus - High Efficiency)</option>
              <option value="mkv">MKV (Matroska - Multi-Track)</option>
            </select>
          </div>

          {/* Auto Browser Save Toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <div>
              <div className="text-xs font-semibold text-white">Browser Auto-Save</div>
              <div className="text-[11px] text-slate-400">Trigger browser download when ready</div>
            </div>
            <input
              type="checkbox"
              checked={settings.autoDownloadBrowser}
              onChange={(e) => handleUpdate('autoDownloadBrowser', e.target.checked)}
              className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500 bg-slate-800 border-white/10"
            />
          </div>
        </div>
      </div>

      {/* Privacy & Storage Preferences */}
      <div className="glass-panel rounded-2xl p-5 sm:p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>Privacy & Local Storage</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-white/5">
          <div>
            <div className="text-xs font-semibold text-white">Incognito Session</div>
            <div className="text-[11px] text-slate-400">Do not persist downloaded records to history</div>
          </div>
          <input
            type="checkbox"
            checked={settings.incognitoMode}
            onChange={(e) => handleUpdate('incognitoMode', e.target.checked)}
            className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500 bg-slate-800 border-white/10"
          />
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-slate-400">
            Storage folder: <code className="text-cyan-300 font-mono text-[11px]">{systemInfo?.downloads_dir || 'downloads/'}</code>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleOpenFolder}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 transition-colors cursor-pointer"
            >
              <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span>Open Folder</span>
            </button>
            <button
              type="button"
              onClick={handleClearHistory}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition-colors cursor-pointer"
            >
              <span>Clear History Data</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
