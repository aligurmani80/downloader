import React, { useState, useMemo } from 'react';
import { 
  Video, 
  Music, 
  CheckCircle2, 
  Clock, 
  User, 
  Download, 
  Sparkles, 
  ShieldCheck, 
  Zap, 
  Tv, 
  Layers, 
  Info, 
  AlertCircle,
  Eye
} from 'lucide-react';

export default function MediaCard({ mediaInfo, onStartDownload, isDownloading }) {
  const [formatType, setFormatType] = useState('video'); // 'video' | 'audio'
  const [selectedHeight, setSelectedHeight] = useState('best'); // 'best' | number (e.g. 4320, 2160, 1080)
  const [selectedCodec, setSelectedCodec] = useState('auto'); // 'auto' | 'av01' | 'vp9' | 'avc1'
  const [selectedContainer, setSelectedContainer] = useState('mp4'); // 'mp4' | 'mkv'

  if (!mediaInfo) return null;

  const resolutions = mediaInfo.resolutions || [];
  const has8K = mediaInfo.has_8k;
  const has4K = mediaInfo.has_4k;
  const hasHdr = mediaInfo.has_hdr;

  // Selected resolution details
  const currentResolutionObj = useMemo(() => {
    if (selectedHeight === 'best') {
      return resolutions[0] || null;
    }
    return resolutions.find(r => r.height === Number(selectedHeight)) || null;
  }, [selectedHeight, resolutions]);

  // Codec availability for currently selected resolution
  const availableCodecsForCurrentRes = useMemo(() => {
    if (!currentResolutionObj) return ['AV1', 'VP9', 'H.264'];
    return currentResolutionObj.codecs || [];
  }, [currentResolutionObj]);

  const handleDownload = (overrideHeight = null) => {
    const heightToUse = overrideHeight !== null ? overrideHeight : (selectedHeight === 'best' ? null : Number(selectedHeight));
    
    onStartDownload({
      url: mediaInfo.webpage_url,
      format_type: formatType,
      height: heightToUse,
      quality: selectedHeight === 'best' && overrideHeight === null ? 'best' : `${heightToUse}p`,
      preferred_codec: selectedCodec,
      container: selectedContainer
    });
  };

  return (
    <div className="w-full bg-slate-900/95 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl backdrop-blur-2xl relative overflow-hidden transition-all text-slate-100">
      {/* Background Ambient Glow */}
      <div className="absolute -top-32 -right-32 w-80 h-80 bg-red-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header: Video Info and Badges */}
      <div className="flex flex-col lg:flex-row gap-6 relative z-10 pb-6 border-b border-slate-800">
        
        {/* Left: Thumbnail with dynamic 8K / 4K / HDR badges */}
        <div className="w-full lg:w-80 flex-shrink-0">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 shadow-xl group">
            {mediaInfo.thumbnail ? (
              <img
                src={mediaInfo.thumbnail}
                alt={mediaInfo.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-600">
                <Video className="w-16 h-16" />
              </div>
            )}

            {/* Glowing 8K / 4K Badge */}
            {has8K ? (
              <div className="absolute top-2.5 left-2.5 bg-gradient-to-r from-red-600 via-pink-600 to-purple-600 px-3 py-1 rounded-full text-xs font-black text-white shadow-lg shadow-red-500/50 flex items-center gap-1.5 animate-pulse border border-white/20">
                <Sparkles className="w-3.5 h-3.5" />
                <span>8K ULTRA HD</span>
              </div>
            ) : has4K ? (
              <div className="absolute top-2.5 left-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 px-3 py-1 rounded-full text-xs font-black text-white shadow-lg shadow-indigo-500/50 flex items-center gap-1.5 border border-white/20">
                <span>4K ULTRA HD</span>
              </div>
            ) : null}

            {/* HDR Tag */}
            {hasHdr && (
              <div className="absolute top-2.5 right-2.5 bg-amber-500/90 text-slate-950 font-black text-[10px] px-2 py-0.5 rounded-md shadow-md uppercase">
                HDR
              </div>
            )}

            {/* Duration Tag */}
            {mediaInfo.duration_formatted && (
              <div className="absolute bottom-2.5 right-2.5 bg-slate-950/85 backdrop-blur-md px-2.5 py-1 rounded-lg text-xs font-mono font-semibold text-slate-200 border border-slate-800 flex items-center gap-1.5 shadow-md">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span>{mediaInfo.duration_formatted}</span>
              </div>
            )}
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="flex items-center gap-1 truncate max-w-[180px]">
              <User className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
              <span className="truncate">{mediaInfo.channel || 'Video'}</span>
            </span>
            {mediaInfo.view_count && (
              <span className="flex items-center gap-1 text-slate-400">
                <Eye className="w-3.5 h-3.5 text-slate-400" />
                <span>{Number(mediaInfo.view_count).toLocaleString()} views</span>
              </span>
            )}
          </div>
        </div>

        {/* Right: Title and Max Quality Hero Action */}
        <div className="flex-1 flex flex-col justify-between">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-white line-clamp-2 leading-snug">
              {mediaInfo.title}
            </h2>

            {/* Max Resolution Info Strip */}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              <span className="text-slate-400">Max Detected Resolution:</span>
              <span className="px-2.5 py-0.5 rounded-lg bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                {mediaInfo.max_resolution || 'Full HD'}
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400">Available Codecs:</span>
              <div className="flex items-center gap-1">
                {(mediaInfo.all_codecs || ['AV1', 'VP9', 'H.264']).map((c) => (
                  <span key={c} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Hero Download Button: Download Maximum Available Quality */}
          <div className="mt-5 p-4 rounded-2xl bg-gradient-to-r from-slate-950/80 via-slate-900 to-indigo-950/40 border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <Zap className="w-4 h-4 text-amber-400 animate-pulse" />
                <span>1-Click Maximum Quality Preset</span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Download highest detected video stream ({mediaInfo.max_resolution}) + best audio lossless.
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleDownload(null)}
              disabled={isDownloading}
              className="w-full sm:w-auto px-6 py-3 rounded-xl font-extrabold text-sm flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 via-indigo-600 to-purple-600 hover:from-red-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/30 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            >
              <Download className="w-4 h-4" />
              <span>Download Max Quality ({has8K ? '8K' : (has4K ? '4K' : 'HD')})</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Controls Section */}
      <div className="mt-6 space-y-6">
        
        {/* Format Selection (Video vs Audio) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>1. Format Type</span>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-3 max-w-md">
            <button
              type="button"
              onClick={() => setFormatType('video')}
              className={`p-3.5 rounded-2xl flex items-center justify-center gap-2.5 font-bold text-sm transition-all border ${
                formatType === 'video'
                  ? 'bg-indigo-600/25 border-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                  : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Video className={`w-4 h-4 ${formatType === 'video' ? 'text-indigo-400' : ''}`} />
              <span>Video + Audio (144p - 8K)</span>
            </button>

            <button
              type="button"
              onClick={() => setFormatType('audio')}
              className={`p-3.5 rounded-2xl flex items-center justify-center gap-2.5 font-bold text-sm transition-all border ${
                formatType === 'audio'
                  ? 'bg-purple-600/25 border-purple-500 text-white shadow-lg shadow-purple-600/20'
                  : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Music className={`w-4 h-4 ${formatType === 'audio' ? 'text-purple-400' : ''}`} />
              <span>HQ Audio Only (MP3 320k)</span>
            </button>
          </div>
        </div>

        {/* Video Resolutions Selection (Only Available Resolutions!) */}
        {formatType === 'video' && (
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Tv className="w-4 h-4 text-indigo-400" />
                <span>2. Available Resolutions (Detected via yt-dlp)</span>
              </label>
              <span className="text-[11px] text-slate-400">
                {resolutions.length} resolution{resolutions.length === 1 ? '' : 's'} available
              </span>
            </div>

            {/* Resolutions Grid: Shows only resolutions present for this video */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* Best Quality Option */}
              <button
                type="button"
                onClick={() => setSelectedHeight('best')}
                className={`p-3.5 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                  selectedHeight === 'best'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/20 ring-1 ring-indigo-400'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-1.5 font-bold text-sm">
                      <span>Maximum Available</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/30 text-indigo-300 font-semibold uppercase">
                        Auto Best
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 block mt-0.5">
                      Up to {mediaInfo.max_resolution || '8K'}
                    </span>
                  </div>
                  {selectedHeight === 'best' && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                </div>
                <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="text-emerald-400 font-semibold">Highest Bitrate</span>
                  <span>•</span>
                  <span>Lossless Merge</span>
                </div>
              </button>

              {/* Specific Detected Resolutions */}
              {resolutions.map((res) => {
                const isSelected = selectedHeight === res.height.toString();
                const is8K = res.height >= 4320;
                const is4K = res.height >= 2160 && res.height < 4320;
                const is2K = res.height >= 1440 && res.height < 2160;

                return (
                  <button
                    key={res.height}
                    type="button"
                    onClick={() => setSelectedHeight(res.height.toString())}
                    className={`p-3.5 rounded-2xl text-left border transition-all flex flex-col justify-between relative overflow-hidden ${
                      isSelected
                        ? (is8K 
                            ? 'bg-red-950/40 border-red-500 text-white shadow-lg shadow-red-500/20 ring-1 ring-red-400' 
                            : 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/20 ring-1 ring-indigo-400')
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    {/* Top Row: Tag, Tier, Radio */}
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-1.5 font-bold text-sm">
                          <span>{res.res_tag}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-extrabold uppercase ${
                            is8K
                              ? 'bg-red-600/30 text-red-300 border border-red-500/40'
                              : is4K
                              ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
                              : is2K
                              ? 'bg-purple-600/30 text-purple-300'
                              : 'bg-slate-800 text-slate-300'
                          }`}>
                            {res.tier_name}
                          </span>
                        </div>
                        <span className="text-xs text-slate-400 block mt-0.5">
                          {res.width ? `${res.width}×${res.height}` : `${res.height}p`} • {res.fps}fps {res.is_hdr ? '• HDR' : ''}
                        </span>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className={`w-4 h-4 ${is8K ? 'text-red-400' : 'text-indigo-400'}`} />
                      )}
                    </div>

                    {/* Bottom Row: Codecs and File Size */}
                    <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                      <div className="flex items-center gap-1">
                        {res.codecs.map((codec) => (
                          <span
                            key={codec}
                            className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold ${
                              codec === 'AV1'
                                ? 'bg-indigo-900/50 text-indigo-300 border border-indigo-700/50'
                                : codec === 'VP9'
                                ? 'bg-teal-900/50 text-teal-300 border border-teal-700/50'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {codec}
                          </span>
                        ))}
                      </div>
                      <span className="font-mono text-slate-400">{res.filesize_str}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Advanced Settings: Codec & Container (Video only) */}
        {formatType === 'video' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
            
            {/* Codec Preference */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                3. Video Codec Selection
              </label>
              <select
                value={selectedCodec}
                onChange={(e) => setSelectedCodec(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
              >
                <option value="auto">Auto / Best Quality (AV1 / VP9 / H.264)</option>
                <option value="av01">AV1 (Next-Gen 8K Master - Highest Sharpness)</option>
                <option value="vp9">VP9 (Standard 4K/8K YouTube Codec)</option>
                <option value="avc1">H.264 / AVC (Universal Compatibility - ≤1080p)</option>
              </select>
              <p className="text-[11px] text-slate-400 mt-1.5 leading-normal">
                {selectedHeight >= 2160 || selectedHeight === 'best'
                  ? '⚠️ YouTube 8K and 4K streams use AV1 or VP9. H.264 is not provided at 8K/4K.'
                  : 'H.264 provides maximum compatibility with older TVs and players.'}
              </p>
            </div>

            {/* Container Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                4. Output Container
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedContainer('mp4')}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    selectedContainer === 'mp4'
                      ? 'bg-indigo-600/25 border-indigo-500 text-white shadow-sm'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span>MP4 (Universal)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedContainer('mkv')}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    selectedContainer === 'mkv'
                      ? 'bg-purple-600/25 border-purple-500 text-white shadow-sm'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span>MKV (Raw Streams)</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5 leading-normal">
                {selectedContainer === 'mp4'
                  ? 'MP4 muxes video losslessly and pairs AAC stereo audio for seamless playback.'
                  : 'MKV preserves untouched bit-exact AV1/VP9 and Opus streams without alteration.'}
              </p>
            </div>
          </div>
        )}

        {/* Guarantees and Notes Box */}
        <div className="p-4 rounded-2xl bg-slate-950/60 border border-emerald-500/20 flex items-start gap-3 text-xs text-slate-300">
          <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-emerald-300 text-xs">
              Quality Preservation & Stream Verification Guarantee:
            </span>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              • <strong>Lossless Stream Copying:</strong> Merging via FFmpeg uses <code className="text-indigo-300">-c:v copy</code>, ensuring zero re-encoding artifacts or resolution loss.<br />
              • <strong>Playable Video Verification:</strong> Each completed download is inspected by FFprobe. Audio-only delivery is strictly rejected for video requests.
            </p>
          </div>
        </div>

        {/* Primary Download Trigger */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => handleDownload()}
            disabled={isDownloading}
            className={`w-full sm:w-auto px-8 py-4 rounded-2xl font-black text-base flex items-center justify-center gap-3 transition-all shadow-xl ${
              isDownloading
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-gradient-to-r from-red-600 via-indigo-600 to-purple-600 hover:from-red-500 hover:to-purple-500 text-white shadow-indigo-600/30 active:scale-[0.98]'
            }`}
          >
            <Download className="w-5 h-5" />
            <span>
              {isDownloading
                ? 'Processing Download...'
                : formatType === 'video'
                ? `Download ${selectedHeight === 'best' ? (has8K ? '8K Ultra HD' : 'Best Quality') : `${selectedHeight}p`} (${selectedContainer.toUpperCase()})`
                : 'Download HQ MP3 Audio'}
            </span>
          </button>

          <span className="text-xs text-slate-500 text-center sm:text-right">
            Chunked streaming enabled • Safe temporary file cleanup on disk.
          </span>
        </div>
      </div>
    </div>
  );
}
