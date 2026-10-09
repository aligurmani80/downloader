import React, { useMemo } from 'react';
import { Search, Clipboard, X, Loader2, Play, Music2, Camera, Globe, ArrowRight } from 'lucide-react';

export default function UrlInput({
  url,
  setUrl,
  onFetch,
  loading,
  onClear
}) {
  // Client-side quick platform detection
  const detectedPlatform = useMemo(() => {
    if (!url) return null;
    const lower = url.toLowerCase();
    if (lower.includes('youtube.com') || lower.includes('youtu.be')) {
      return {
        name: 'YouTube',
        color: 'from-red-600 to-rose-600',
        textColor: 'text-red-400',
        bgColor: 'bg-red-500/10 border-red-500/30',
        icon: Play
      };
    }
    if (lower.includes('tiktok.com')) {
      return {
        name: 'TikTok',
        color: 'from-cyan-500 to-pink-500',
        textColor: 'text-cyan-400',
        bgColor: 'bg-cyan-500/10 border-cyan-500/30',
        icon: Music2
      };
    }
    if (lower.includes('instagram.com') || lower.includes('instagr.am')) {
      return {
        name: 'Instagram',
        color: 'from-fuchsia-600 to-pink-600',
        textColor: 'text-pink-400',
        bgColor: 'bg-pink-500/10 border-pink-500/30',
        icon: Camera
      };
    }
    if (lower.startsWith('http://') || lower.startsWith('https://')) {
      return {
        name: 'Web Video',
        color: 'from-blue-600 to-indigo-600',
        textColor: 'text-blue-400',
        bgColor: 'bg-blue-500/10 border-blue-500/30',
        icon: Globe
      };
    }
    return null;
  }, [url]);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
      }
    } catch (err) {
      console.warn('Clipboard access denied:', err);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) {
      onFetch(url.trim());
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex flex-col md:flex-row items-stretch md:items-center bg-slate-900/90 rounded-2xl border-2 border-slate-700/80 focus-within:border-indigo-500 shadow-2xl shadow-indigo-950/40 transition-all p-2 gap-2">
          
          {/* Input field */}
          <div className="flex-1 flex items-center px-3 min-w-0">
            <Search className="w-5 h-5 text-slate-400 mr-3 flex-shrink-0" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube, TikTok, or Instagram video link here..."
              className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm md:text-base outline-none focus:ring-0 py-2.5"
              disabled={loading}
            />

            {/* Clear Button */}
            {url && (
              <button
                type="button"
                onClick={onClear}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                title="Clear input"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Paste Button */}
            <button
              type="button"
              onClick={handlePaste}
              className="ml-1 p-2 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-indigo-500/10 border border-transparent hover:border-indigo-500/30 transition flex items-center gap-1.5 text-xs font-medium"
              title="Paste from clipboard"
            >
              <Clipboard className="w-4 h-4" />
              <span className="hidden sm:inline">Paste</span>
            </button>
          </div>

          {/* Action button */}
          <button
            type="submit"
            disabled={!url.trim() || loading}
            className={`px-6 py-3.5 rounded-xl font-bold text-sm md:text-base text-white flex items-center justify-center gap-2 transition-all shadow-md ${
              !url.trim() || loading
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 active:scale-[0.98] shadow-indigo-500/25'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Fetching Info...</span>
              </>
            ) : (
              <>
                <span>Fetch Media</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Live Detected Platform Pill */}
        {detectedPlatform && (
          <div className="mt-3 flex items-center justify-between px-1">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${detectedPlatform.bgColor}`}>
              <detectedPlatform.icon className={`w-3.5 h-3.5 ${detectedPlatform.textColor}`} />
              <span className="text-slate-300">Detected:</span>
              <span className={`font-bold ${detectedPlatform.textColor}`}>{detectedPlatform.name}</span>
            </div>

            <span className="text-xs text-slate-500">
              Ready to analyze stream formats
            </span>
          </div>
        )}
      </form>
    </div>
  );
}
