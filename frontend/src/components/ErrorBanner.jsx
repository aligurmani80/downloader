import React from 'react';
import { AlertTriangle, X, RefreshCw } from 'lucide-react';

export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="w-full bg-rose-950/60 border border-rose-500/40 rounded-2xl p-4 md:p-5 shadow-xl backdrop-blur-md flex items-start justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex-shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-rose-200">Processing Error</h4>
          <p className="text-xs md:text-sm text-rose-300/90 mt-1 leading-relaxed">{message}</p>
          <div className="mt-2 text-[11px] text-rose-400/80">
            Tip: Ensure the video is public, not age-gated, and you have permission to download it.
          </div>
        </div>
      </div>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="p-1 rounded-lg text-rose-400 hover:text-rose-200 hover:bg-rose-900/50 transition flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
