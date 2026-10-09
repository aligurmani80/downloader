import React from 'react';
import { 
  Loader2, 
  ArrowDownCircle, 
  Cpu, 
  SearchCheck, 
  CheckCircle2, 
  Radio, 
  ShieldCheck, 
  Zap 
} from 'lucide-react';

export default function DownloadProgress({ job }) {
  if (!job) return null;

  const progress = Math.min(Math.max(job.progress || job.percent || 0, 0), 100);
  const status = job.status || 'pending';
  const phaseMsg = job.phase_message || job.message || 'Processing media streams...';

  // Determine stage status
  const getStageStatus = (stageIdx) => {
    if (status === 'completed') return 'completed';
    if (status === 'verifying') {
      if (stageIdx <= 4) return 'completed';
      if (stageIdx === 5) return 'active';
    }
    if (status === 'merging') {
      if (stageIdx <= 3) return 'completed';
      if (stageIdx === 4) return 'active';
      return 'pending';
    }
    if (status === 'downloading') {
      if (stageIdx === 1) return 'completed';
      if (progress < 50) {
        if (stageIdx === 2) return 'active';
      } else {
        if (stageIdx === 2) return 'completed';
        if (stageIdx === 3) return 'active';
      }
      return 'pending';
    }
    if (status === 'analyzing') {
      if (stageIdx === 1) return 'active';
      return 'pending';
    }
    return 'pending';
  };

  const steps = [
    { id: 1, label: 'Resolving 8K/4K Streams', icon: Radio },
    { id: 2, label: 'Downloading Video Stream', icon: ArrowDownCircle },
    { id: 3, label: 'Downloading Audio Stream', icon: ArrowDownCircle },
    { id: 4, label: 'FFmpeg Lossless Muxing', icon: Cpu },
    { id: 5, label: 'FFprobe Stream Verification', icon: ShieldCheck },
  ];

  return (
    <div className="w-full bg-slate-900/95 border border-indigo-500/30 rounded-3xl p-6 md:p-8 shadow-2xl backdrop-blur-2xl relative overflow-hidden animate-in fade-in duration-300 text-slate-100">
      
      {/* Background Glow */}
      <div className="absolute -top-24 -right-24 w-60 h-60 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">Downloading & Processing</h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase">
                {status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{phaseMsg}</p>
          </div>
        </div>

        {/* Speed, ETA & Size Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {job.speed_str && job.speed_str !== '--' && (
            <span className="px-3 py-1 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono text-indigo-300 font-semibold flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>{job.speed_str}</span>
            </span>
          )}
          {job.eta_str && job.eta_str !== '--' && (
            <span className="px-3 py-1 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-300 font-semibold">
              ⏳ ETA: {job.eta_str}
            </span>
          )}
        </div>
      </div>

      {/* Main Progress Bar */}
      <div className="mt-6">
        <div className="flex justify-between items-center text-xs font-semibold text-slate-400 mb-2">
          <span>Overall Pipeline Progress</span>
          <div className="flex items-center gap-2">
            {job.downloaded_str && job.total_str && (
              <span className="text-slate-400 font-mono text-xs">
                {job.downloaded_str} / {job.total_str}
              </span>
            )}
            <span className="text-indigo-400 font-mono font-bold text-sm">
              {progress.toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="w-full h-4 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800 shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-red-600 via-indigo-500 to-purple-500 rounded-full transition-all duration-300 shadow-lg shadow-indigo-500/40 relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full" />
          </div>
        </div>
      </div>

      {/* 5-Stage Stepper */}
      <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
        {steps.map((step) => {
          const sStatus = getStageStatus(step.id);
          const Icon = step.icon;
          return (
            <div
              key={step.id}
              className={`p-3 rounded-2xl border transition-all flex flex-col justify-between ${
                sStatus === 'completed'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : sStatus === 'active'
                  ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-200 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-400/30'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-4 h-4 ${sStatus === 'active' ? 'animate-pulse text-indigo-400' : ''}`} />
                {sStatus === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              </div>
              <span className="text-[11px] font-semibold leading-tight">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
