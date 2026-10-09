import React from 'react';
import { ShieldCheck, Video, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-slate-800/80 bg-slate-950/80 py-10 px-4 text-center">
      <div className="max-w-4xl mx-auto flex flex-col items-center gap-4">
        
        {/* Platform Icons */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-slate-400">
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
            🎬 YouTube Videos & Shorts
          </span>
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
            🎵 TikTok Clips & Audio
          </span>
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
            📸 Instagram Reels & Posts
          </span>
        </div>

        {/* Legal Disclaimer */}
        <div className="max-w-2xl text-[11px] text-slate-500 leading-relaxed">
          <p>
            <strong>Permissions & Compliance Notice:</strong> This software is engineered strictly for downloading content that users own, creative commons works, or public content where you have explicit permission to download. The system strictly respects platform access boundaries and does not bypass DRM or authentication mechanisms.
          </p>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-600">
          <span>Engineered with Python FastAPI, yt-dlp, FFmpeg & React</span>
        </div>
      </div>
    </footer>
  );
}
