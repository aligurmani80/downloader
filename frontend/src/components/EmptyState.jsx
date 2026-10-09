import React from 'react';
import { 
  Zap, 
  ShieldCheck, 
  Sliders, 
  Sparkles, 
  Film, 
  Music, 
  Flame, 
  CheckCircle2,
  Share2
} from 'lucide-react';

export default function EmptyState({ onSelectPreset }) {
  return (
    <div className="w-full space-y-10 py-6 animate-in fade-in duration-500">
      {/* SaaS Feature Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        <div className="glass-panel glass-panel-hover rounded-2xl p-5 border border-white/10 space-y-3 relative overflow-hidden group">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Zap className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">Ultra-Fast Pipeline</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-threaded stream extraction with direct FFmpeg acceleration for instant downloads without compression loss.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover rounded-2xl p-5 border border-white/10 space-y-3 relative overflow-hidden group">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Sliders className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">Granular Resolutions</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Choose from authentic 144p to 4K UHD and 8K streams. Extracted directly from host manifest data with zero upscaling gimmicks.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover rounded-2xl p-5 border border-white/10 space-y-3 relative overflow-hidden group">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Music className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">Studio Audio Demuxing</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Extract crisp 320 kbps MP3, M4A AAC, or lossless WAV audio tracks directly from videos with metadata preservation.
          </p>
        </div>
      </div>

      {/* 3-Step Guide */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <div className="text-center space-y-1">
          <span className="text-xs font-semibold text-cyan-400 uppercase tracking-widest">
            Simple 3-Step Workflow
          </span>
          <h2 className="text-lg sm:text-xl font-bold text-white">
            How NexaLoad Works
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-xl bg-slate-900/40 border border-white/5">
            <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 font-bold text-sm flex items-center justify-center">
              1
            </div>
            <h4 className="text-sm font-semibold text-white">Copy Any Video URL</h4>
            <p className="text-xs text-slate-400">
              Grab the link from TikTok, Instagram Reels, YouTube, X (Twitter), or Facebook.
            </p>
          </div>

          <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-xl bg-slate-900/40 border border-white/5">
            <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 font-bold text-sm flex items-center justify-center">
              2
            </div>
            <h4 className="text-sm font-semibold text-white">Analyze Stream</h4>
            <p className="text-xs text-slate-400">
              Paste URL above. The backend engine inspects available video and audio streams.
            </p>
          </div>

          <div className="flex flex-col items-center text-center space-y-2 p-4 rounded-xl bg-slate-900/40 border border-white/5">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 font-bold text-sm flex items-center justify-center">
              3
            </div>
            <h4 className="text-sm font-semibold text-white">Download in High Quality</h4>
            <p className="text-xs text-slate-400">
              Pick your exact resolution or audio format, track real-time progress, and save!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
