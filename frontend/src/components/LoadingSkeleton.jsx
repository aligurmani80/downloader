import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSkeleton() {
  return (
    <div 
      className="w-full glass-panel rounded-2xl p-5 sm:p-7 shadow-xl animate-pulse space-y-6"
      role="status" 
      aria-live="polite"
      aria-label="Analyzing media streams"
    >
      <div className="flex items-center gap-3 text-cyan-400 text-sm font-medium">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Extracting streams, codecs, and available resolutions...</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Thumbnail skeleton */}
        <div className="md:col-span-5 aspect-video bg-slate-800/60 rounded-xl relative overflow-hidden border border-white/5">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-[shimmer_2s_infinite]" />
        </div>

        {/* Video metadata skeleton */}
        <div className="md:col-span-7 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="h-6 bg-slate-800/80 rounded-lg w-4/5" />
            <div className="h-4 bg-slate-800/60 rounded-md w-3/5" />
            <div className="flex items-center gap-2 pt-2">
              <div className="h-6 w-20 bg-slate-800/80 rounded-full" />
              <div className="h-6 w-24 bg-slate-800/80 rounded-full" />
              <div className="h-6 w-16 bg-slate-800/80 rounded-full" />
            </div>
          </div>

          <div className="h-10 bg-slate-800/50 rounded-xl w-full" />
        </div>
      </div>

      {/* Quality pills skeleton */}
      <div className="space-y-3 pt-2">
        <div className="h-4 bg-slate-800/60 rounded w-44" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-slate-800/40 border border-white/5 rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}
