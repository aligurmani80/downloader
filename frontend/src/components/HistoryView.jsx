import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { 
  History, 
  Trash2, 
  Download, 
  FolderOpen, 
  ExternalLink, 
  RotateCcw, 
  Calendar, 
  HardDrive, 
  Film, 
  Music, 
  AlertCircle, 
  CheckCircle2,
  FileCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function HistoryView({ onRedownloadUrl }) {
  const { history, historyLoading, loadHistory, addToast } = useApp();
  const [filter, setFilter] = useState('all'); // 'all' | 'video' | 'audio'

  const handleOpenFolder = async () => {
    try {
      await api.openFolder();
      addToast('Opened downloads folder', 'info');
    } catch {
      addToast('Failed to open downloads folder', 'error');
    }
  };

  const handleDeleteItem = async (itemId) => {
    try {
      await api.deleteHistoryItem(itemId);
      await loadHistory();
      addToast('Removed from history', 'info');
    } catch {
      addToast('Failed to remove item', 'error');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear your entire download history?')) {
      return;
    }
    try {
      await api.clearHistory();
      await loadHistory();
      addToast('History cleared', 'info');
    } catch {
      addToast('Failed to clear history', 'error');
    }
  };

  const filteredHistory = history.filter((item) => {
    if (filter === 'video') return item.format_type === 'video';
    if (filter === 'audio') return item.format_type === 'audio';
    return true;
  });

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-300">
      {/* Header bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-white">Download History</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
              {history.length} {history.length === 1 ? 'file' : 'files'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track past downloads and access saved files directly on your local machine.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={handleOpenFolder}
            className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-white/10 transition-colors"
          >
            <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Open Folder</span>
          </button>

          {history.length > 0 && (
            <button
              onClick={handleClearAll}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      {history.length > 0 && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === 'all'
                ? 'bg-purple-600 text-white'
                : 'bg-slate-900/60 text-slate-400 hover:text-white'
            }`}
          >
            All Downloads ({history.length})
          </button>
          <button
            onClick={() => setFilter('video')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === 'video'
                ? 'bg-purple-600 text-white'
                : 'bg-slate-900/60 text-slate-400 hover:text-white'
            }`}
          >
            Videos ({history.filter((i) => i.format_type === 'video').length})
          </button>
          <button
            onClick={() => setFilter('audio')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === 'audio'
                ? 'bg-cyan-600 text-white'
                : 'bg-slate-900/60 text-slate-400 hover:text-white'
            }`}
          >
            Audio Tracks ({history.filter((i) => i.format_type === 'audio').length})
          </button>
        </div>
      )}

      {/* History Items List */}
      {filteredHistory.length > 0 ? (
        <div className="space-y-3">
          {filteredHistory.map((item) => (
            <div
              key={item.id}
              className="glass-panel glass-panel-hover rounded-xl p-4 border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              {/* Media Thumbnail & Details */}
              <div className="flex items-center gap-3.5 min-w-0 flex-1">
                <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-lg bg-slate-900 border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
                  {item.thumbnail ? (
                    <img
                      src={item.thumbnail}
                      alt={item.title}
                      className="w-full h-full object-cover"
                    />
                  ) : item.format_type === 'audio' ? (
                    <Music className="w-6 h-6 text-cyan-400" />
                  ) : (
                    <Film className="w-6 h-6 text-purple-400" />
                  )}
                </div>

                <div className="min-w-0 flex-1 space-y-1">
                  <h3 className="text-sm font-bold text-white truncate max-w-sm sm:max-w-lg">
                    {item.title}
                  </h3>
                  
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span className="font-semibold text-cyan-400 uppercase">
                      {item.ext}
                    </span>
                    {item.resolution && (
                      <>
                        <span>•</span>
                        <span>{item.resolution}</span>
                      </>
                    )}
                    {item.filesize_str && (
                      <>
                        <span>•</span>
                        <span>{item.filesize_str}</span>
                      </>
                    )}
                    <span>•</span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <Calendar className="w-3 h-3" />
                      {item.download_date}
                    </span>
                  </div>

                  {/* Real file availability status */}
                  <div className="pt-0.5">
                    {item.is_available ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" /> Ready on disk
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                        <AlertCircle className="w-3 h-3" /> File removed or moved
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 w-full sm:w-auto justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-white/5">
                {item.is_available ? (
                  <a
                    href={item.download_url}
                    download={item.filename}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white shadow transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Save</span>
                  </a>
                ) : (
                  onRedownloadUrl && item.url && (
                    <button
                      onClick={() => onRedownloadUrl(item.url)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Download Again</span>
                    </button>
                  )
                )}

                <button
                  onClick={() => handleDeleteItem(item.id)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Remove from history"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty history */
        <div className="glass-panel rounded-2xl p-10 text-center space-y-3 border border-white/5">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mx-auto">
            <History className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white">No Downloads in History</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Videos or audio files you download will appear here with instant access and file management.
          </p>
        </div>
      )}
    </div>
  );
}
