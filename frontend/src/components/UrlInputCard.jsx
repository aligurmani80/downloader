import React, { useState, useEffect } from 'react';
import { 
  Link2, 
  Search, 
  Clipboard, 
  X, 
  Video, 
  Music, 
  Sparkles,
  Loader2,
  Check
} from 'lucide-react';

export default function UrlInputCard({ onAnalyze, isLoading, initialUrl = '' }) {
  const [url, setUrl] = useState(initialUrl);
  const [targetType, setTargetType] = useState('video'); // 'video' | 'audio'
  const [pasted, setPasted] = useState(false);

  useEffect(() => {
    if (initialUrl) setUrl(initialUrl);
  }, [initialUrl]);

  // Platform identification logic
  const getPlatformInfo = (inputUrl) => {
    if (!inputUrl) return null;
    const lower = inputUrl.toLowerCase();
    if (lower.includes('youtube.com') || lower.includes('youtu.be')) {
      return { name: 'YouTube', color: 'bg-red-500/20 text-red-300 border-red-500/30', type: 'youtube' };
    }
    if (lower.includes('tiktok.com')) {
      return { name: 'TikTok', color: 'bg-pink-500/20 text-pink-300 border-pink-500/30', type: 'tiktok' };
    }
    if (lower.includes('instagram.com') || lower.includes('instagr.am')) {
      return { name: 'Instagram', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30', type: 'instagram' };
    }
    if (lower.includes('twitter.com') || lower.includes('x.com')) {
      return { name: 'X / Twitter', color: 'bg-sky-500/20 text-sky-300 border-sky-500/30', type: 'twitter' };
    }
    if (lower.includes('facebook.com') || lower.includes('fb.watch')) {
      return { name: 'Facebook', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30', type: 'facebook' };
    }
    if (lower.includes('reddit.com')) {
      return { name: 'Reddit', color: 'bg-orange-500/20 text-orange-300 border-orange-500/30', type: 'reddit' };
    }
    if (lower.includes('vimeo.com')) {
      return { name: 'Vimeo', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30', type: 'vimeo' };
    }
    if (lower.startsWith('http://') || lower.startsWith('https://')) {
      return { name: 'Web Media', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30', type: 'web' };
    }
    return null;
  };

  const detectedPlatform = getPlatformInfo(url);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        setPasted(true);
        setTimeout(() => setPasted(false), 2000);
      }
    } catch {
      // Clipboard read permission might not be granted in some browser setups
    }
  };

  const handleClear = () => {
    setUrl('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim() || isLoading) return;
    onAnalyze(url.trim(), targetType);
  };

  return (
    <div className="w-full glass-panel rounded-2xl p-4 sm:p-6 shadow-2xl relative overflow-hidden transition-all duration-300">
      {/* Decorative ambient gradients */}
      <div className="gradient-glow -top-16 -left-16 w-56 h-56 bg-purple-600/30" />
      <div className="gradient-glow -bottom-16 -right-16 w-56 h-56 bg-cyan-600/30" />

      {/* Mode selection tabs */}
      <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-white/5">
        <div className="flex items-center p-1 bg-slate-900/90 rounded-xl border border-white/5">
          <button
            type="button"
            onClick={() => setTargetType('video')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              targetType === 'video'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Video & Audio</span>
          </button>
          <button
            type="button"
            onClick={() => setTargetType('audio')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              targetType === 'audio'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Music className="w-4 h-4" />
            <span>Audio Only (MP3)</span>
          </button>
        </div>

        {/* Live Platform Badge */}
        {detectedPlatform && (
          <div className={`hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${detectedPlatform.color} animate-in fade-in`}>
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            <span>{detectedPlatform.name} Detected</span>
          </div>
        )}
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Link2 className="w-5 h-5" />
          </div>

          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste TikTok, Instagram, YouTube or any video link..."
            disabled={isLoading}
            aria-label="Video or audio URL input"
            className="w-full glass-input rounded-xl py-3.5 pl-11 pr-24 text-sm sm:text-base font-normal placeholder:text-slate-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />

          <div className="absolute inset-y-0 right-2 flex items-center gap-1">
            {url && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                title="Clear input"
                aria-label="Clear URL"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <button
              type="button"
              onClick={handlePaste}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded-lg border border-white/10 transition-colors"
              title="Paste from clipboard"
            >
              {pasted ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Clipboard className="w-3.5 h-3.5 text-slate-400" />}
              <span>{pasted ? 'Pasted' : 'Paste'}</span>
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={!url.trim() || isLoading}
          className="gradient-brand text-white font-semibold px-6 py-3.5 rounded-xl shadow-lg shadow-purple-600/30 hover:shadow-purple-600/50 hover:brightness-110 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:shadow-none transition-all flex items-center justify-center gap-2 min-w-[140px]"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-cyan-200" />
              <span>Analyze URL</span>
            </>
          )}
        </button>
      </form>

      {/* Mobile detected badge */}
      {detectedPlatform && (
        <div className="sm:hidden mt-3 flex items-center gap-1.5 text-xs font-medium text-slate-300">
          <span className={`px-2 py-0.5 rounded-md border text-[11px] font-semibold ${detectedPlatform.color}`}>
            {detectedPlatform.name}
          </span>
          <span>link detected</span>
        </div>
      )}

      {/* Supported Platforms chips */}
      <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
        <span className="font-medium text-slate-400">Supported Platforms:</span>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900/60 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-red-500" /> YouTube
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900/60 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-pink-500" /> TikTok
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900/60 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 to-amber-500" /> Instagram
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900/60 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-sky-400" /> X / Twitter
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900/60 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-blue-600" /> Facebook
          </span>
        </div>
      </div>
    </div>
  );
}
