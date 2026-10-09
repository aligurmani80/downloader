import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  Download, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FolderOpen, 
  RotateCcw, 
  X, 
  Film, 
  Music, 
  ExternalLink,
  HardDrive
} from 'lucide-react';
import { api } from '../services/api';

export default function DownloadProgressCard({ task, onRetry }) {
  const { removeSingleTask, addToast } = useApp();

  const isDownloading = task.status === 'downloading';
  const isMerging = task.status === 'merging';
  const isConverting = task.status === 'converting';
  const isQueued = task.status === 'queued';
  const isFinished = task.status === 'finished';
  const isError = task.status === 'error';

  const handleOpenFolder = async () => {
    try {
      await api.openFolder();
      addToast('Opened downloads directory', 'info');
    } catch {
      addToast('Failed to open folder on system', 'error');
    }
  };

  const handleBrowserSave = () => {
    if (task.download_url) {
      // Trigger native browser download
      const link = document.createElement('a');
      link.href = task.download_url;
      link.download = task.filename || 'media';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast('Browser file download initiated', 'success');
    }
  };

  const getStatusLabel = () => {
    if (isQueued) return 'Queued in pipeline...';
    if (isDownloading) return `Downloading stream (${task.percent}%)`;
    if (isMerging) return 'Merging audio and video tracks (FFmpeg)...';
    if (isConverting) return 'Converting audio format (FFmpeg)...';
    if (isFinished) return 'Download Complete!';
    if (isError) return 'Download Failed';
    return 'Processing...';
  };

  return (
    <div className={`w-full glass-panel rounded-2xl p-4 sm:p-5 shadow-xl border transition-all duration-300 ${
      isFinished
        ? 'border-emerald-500/40 shadow-emerald-950/20'
        : isError
        ? 'border-rose-500/40 shadow-rose-950/20'
        : 'border-purple-500/30'
    }`}>
      <div className="flex items-start gap-4">
        {/* Media Thumbnail or Type Icon */}
        <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl bg-slate-900 border border-white/10 overflow-hidden shrink-0 relative flex items-center justify-center">
          {task.thumbnail ? (
            <img
              src={task.thumbnail}
              alt={task.title}
              className="w-full h-full object-cover"
            />
          ) : task.format_type === 'audio' ? (
            <Music className="w-8 h-8 text-cyan-400" />
          ) : (
            <Film className="w-8 h-8 text-purple-400" />
          )}

          {/* Status Badge Overlay */}
          <div className="absolute top-1 right-1">
            {isFinished && (
              <span className="p-1 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </span>
            )}
            {isError && (
              <span className="p-1 rounded-full bg-rose-500 text-white flex items-center justify-center shadow">
                <AlertCircle className="w-3.5 h-3.5" />
              </span>
            )}
            {(isDownloading || isMerging || isConverting || isQueued) && (
              <span className="p-1 rounded-full bg-purple-500 text-white flex items-center justify-center shadow">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              </span>
            )}
          </div>
        </div>

        {/* Content & Metrics */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white truncate max-w-sm sm:max-w-md">
                {task.title}
              </h3>
              <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                <span className="font-semibold text-cyan-400 uppercase">
                  {task.ext || (task.format_type === 'audio' ? 'MP3' : 'MP4')}
                </span>
                {task.resolution && (
                  <>
                    <span>•</span>
                    <span>{task.resolution}</span>
                  </>
                )}
                {task.filename && (
                  <>
                    <span>•</span>
                    <span className="truncate max-w-[140px] text-slate-400">{task.filename}</span>
                  </>
                )}
              </div>
            </div>

            <button
              onClick={() => removeSingleTask(task.task_id)}
              className="p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Progress Bar (Active states) */}
          {!isFinished && !isError && (
            <div className="space-y-1.5">
              <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-white/5 relative">
                <div
                  className="h-full gradient-brand rounded-full transition-all duration-300 relative"
                  style={{ width: `${Math.min(task.percent || 5, 100)}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </div>
              </div>

              {/* Progress stats */}
              <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                <span className="flex items-center gap-1.5 text-purple-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                  {getStatusLabel()}
                </span>

                <div className="flex items-center gap-3">
                  {task.speed_str && <span>{task.speed_str}</span>}
                  {task.eta_str && <span>ETA {task.eta_str}</span>}
                  <span className="font-bold text-slate-200">{task.percent}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Success State Actions */}
          {isFinished && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mr-2">
                <CheckCircle2 className="w-4 h-4" /> Ready for playback
              </span>

              <button
                onClick={handleBrowserSave}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30 transition-all cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save to Device</span>
              </button>

              <button
                onClick={handleOpenFolder}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 transition-colors cursor-pointer"
              >
                <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
                <span>Open in Folder</span>
              </button>
            </div>
          )}

          {/* Error State */}
          {isError && (
            <div className="space-y-2 pt-1">
              <p className="text-xs text-rose-300 bg-rose-950/40 p-2.5 rounded-lg border border-rose-500/20">
                {task.error || 'An unexpected error occurred during download.'}
              </p>
              {onRetry && (
                <button
                  onClick={() => onRetry(task)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Retry Download</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
