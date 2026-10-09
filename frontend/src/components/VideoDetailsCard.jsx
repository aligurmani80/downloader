import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Clock, 
  ExternalLink, 
  CheckCircle2, 
  Download, 
  Film, 
  Music, 
  ShieldCheck, 
  Layers, 
  Info,
  Sparkles,
  FileVideo,
  FileAudio
} from 'lucide-react';

export default function VideoDetailsCard({ videoData, onStartDownload, defaultMode = 'video' }) {
  const [downloadMode, setDownloadMode] = useState(defaultMode); // 'video' | 'audio'
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [selectedAudioFormat, setSelectedAudioFormat] = useState(null);
  const [containerOption, setContainerOption] = useState('mp4');

  useEffect(() => {
    setDownloadMode(defaultMode);
  }, [defaultMode]);

  // Set default format selections
  useEffect(() => {
    if (videoData?.video_formats?.length) {
      // Pick best HD resolution by default (e.g., 1080p or 720p or top available)
      const hdOption = videoData.video_formats.find((f) => f.height === 1080) ||
                       videoData.video_formats.find((f) => f.height === 720) ||
                       videoData.video_formats[0];
      setSelectedFormat(hdOption);
    }

    if (videoData?.audio_formats?.length) {
      setSelectedAudioFormat(videoData.audio_formats[0]);
    }
  }, [videoData]);

  if (!videoData) return null;

  const isVideo = downloadMode === 'video';

  const handleDownloadClick = () => {
    if (isVideo && selectedFormat) {
      onStartDownload({
        url: videoData.url,
        format_type: 'video',
        quality: selectedFormat.resolution,
        format_id: selectedFormat.format_id,
        container: containerOption,
        title: videoData.title,
        thumbnail: videoData.thumbnail,
      });
    } else if (!isVideo && selectedAudioFormat) {
      onStartDownload({
        url: videoData.url,
        format_type: 'audio',
        quality: selectedAudioFormat.quality_label,
        format_id: selectedAudioFormat.format_id,
        container: selectedAudioFormat.ext,
        title: videoData.title,
        thumbnail: videoData.thumbnail,
      });
    }
  };

  return (
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-7 shadow-2xl border border-white/10 space-y-6 animate-in fade-in duration-300">
      {/* Top Media Overview Header */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 sm:gap-7 items-start">
        {/* Real Thumbnail with Duration & Platform Badge */}
        <div className="md:col-span-5 relative group rounded-xl overflow-hidden bg-slate-900 border border-white/10 shadow-lg aspect-video flex items-center justify-center">
          {videoData.thumbnail ? (
            <img
              src={videoData.thumbnail}
              alt={videoData.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-2">
              <Film className="w-10 h-10" />
              <span className="text-xs">No preview thumbnail</span>
            </div>
          )}

          {/* Platform Badge */}
          <div className="absolute top-3 left-3 px-2.5 py-1 rounded-md bg-slate-950/80 backdrop-blur-md border border-white/10 text-xs font-semibold text-white flex items-center gap-1.5 shadow">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>{videoData.platform}</span>
          </div>

          {/* Duration Badge */}
          {videoData.duration_str && (
            <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-slate-950/90 backdrop-blur-md border border-white/10 text-xs font-mono font-medium text-slate-200 flex items-center gap-1 shadow">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>{videoData.duration_str}</span>
            </div>
          )}
        </div>

        {/* Video Info Details */}
        <div className="md:col-span-7 flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
              <span className="text-cyan-400 font-semibold">{videoData.uploader}</span>
              {videoData.view_count && (
                <>
                  <span>•</span>
                  <span>{Number(videoData.view_count).toLocaleString()} views</span>
                </>
              )}
            </div>

            <h2 className="text-lg sm:text-xl font-bold text-white leading-snug tracking-tight">
              {videoData.title}
            </h2>

            {videoData.description && (
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {videoData.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2 text-xs text-slate-400 border-t border-white/5">
            <a
              href={videoData.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-slate-300 hover:text-cyan-400 transition-colors"
            >
              <span>Verify original link</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span>•</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Stream verified
            </span>
          </div>
        </div>
      </div>

      {/* Mode Selection: Video vs Audio */}
      <div className="border-t border-white/10 pt-5">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div className="flex items-center p-1 bg-slate-900 rounded-xl border border-white/10">
            <button
              onClick={() => setDownloadMode('video')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                isVideo
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/25'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileVideo className="w-4 h-4" />
              <span>Full Video ({videoData.video_formats?.length || 0} Qualities)</span>
            </button>
            <button
              onClick={() => setDownloadMode('audio')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                !isVideo
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/25'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileAudio className="w-4 h-4" />
              <span>Audio Only (MP3 / M4A)</span>
            </button>
          </div>

          {isVideo && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <label htmlFor="container-select" className="text-slate-300 font-medium">Container:</label>
              <select
                id="container-select"
                value={containerOption}
                onChange={(e) => setContainerOption(e.target.value)}
                className="bg-slate-900 border border-white/10 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400"
              >
                <option value="mp4">MP4 (Recommended Universal)</option>
                <option value="webm">WebM (Modern Web)</option>
                <option value="mkv">MKV (High Definition Matroska)</option>
              </select>
            </div>
          )}
        </div>

        {/* Video Quality Options Grid */}
        {isVideo ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold text-slate-200 uppercase tracking-wider">
                Select Video Quality:
              </span>
              <span>Only qualities available from the host are listed</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {videoData.video_formats.map((fmt) => {
                const isSelected = selectedFormat?.format_id === fmt.format_id;
                const is4K = fmt.height >= 2160;
                const isFullHD = fmt.height === 1080;
                const isHD = fmt.height === 720;

                return (
                  <button
                    key={fmt.format_id}
                    onClick={() => setSelectedFormat(fmt)}
                    className={`relative text-left p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between gap-1.5 ${
                      isSelected
                        ? 'bg-purple-600/20 border-purple-500 ring-2 ring-purple-500/30 text-white shadow-lg shadow-purple-900/30'
                        : 'bg-slate-900/60 border-white/5 hover:border-white/20 text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-base font-extrabold tracking-tight">
                        {fmt.resolution}
                      </span>
                      {isSelected ? (
                        <CheckCircle2 className="w-4 h-4 text-purple-400" />
                      ) : (
                        (is4K || isFullHD) && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                            is4K ? 'bg-amber-500/20 text-amber-300' : 'bg-cyan-500/20 text-cyan-300'
                          }`}>
                            {is4K ? '4K UHD' : '1080p FHD'}
                          </span>
                        )
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-white/5">
                      <span>{fmt.filesize_str || 'Estimated stream'}</span>
                      {fmt.fps && <span>{fmt.fps} fps</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Audio Format Options Grid */
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-semibold text-slate-200 uppercase tracking-wider">
                Select Audio Quality & Format:
              </span>
              <span>Extracted lossless audio track with FFmpeg</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {videoData.audio_formats.map((afmt) => {
                const isSelected = selectedAudioFormat?.format_id === afmt.format_id;
                return (
                  <button
                    key={afmt.format_id}
                    onClick={() => setSelectedAudioFormat(afmt)}
                    className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                      isSelected
                        ? 'bg-cyan-600/20 border-cyan-400 ring-2 ring-cyan-400/30 text-white shadow-lg shadow-cyan-900/30'
                        : 'bg-slate-900/60 border-white/5 hover:border-white/20 text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>
                        <Music className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-white uppercase">
                          {afmt.ext.toUpperCase()}
                        </div>
                        <div className="text-xs text-slate-400">
                          {afmt.quality_label}
                        </div>
                      </div>
                    </div>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Codec & Compatibility Notice */}
        <div className="mt-4 p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-2.5 text-xs text-slate-400">
          <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            {isVideo ? (
              <span>
                <strong className="text-slate-200">Format Compatibility: </strong>
                {containerOption === 'mp4' 
                  ? 'MP4 (H.264/AAC) provides universal compatibility across Windows, Mac, iOS, Android, and all smart TVs.'
                  : containerOption === 'webm'
                  ? 'WebM (VP9/Opus) offers high compression efficiency for web playback.'
                  : 'MKV retains multi-track audio and high-bitrate video streams.'}
              </span>
            ) : (
              <span>
                <strong className="text-slate-200">Audio Notice: </strong>
                Audio is extracted directly from the best available source stream and encoded at selected bitrates using FFmpeg.
              </span>
            )}
          </div>
        </div>

        {/* Primary Download CTA Button */}
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-white/5">
          <div className="text-xs text-slate-400 text-center sm:text-left">
            <span>Ready to download: </span>
            <span className="font-semibold text-white">
              {isVideo 
                ? `${selectedFormat?.resolution || 'Video'} • ${containerOption.toUpperCase()}`
                : `${selectedAudioFormat?.quality_label || 'Audio'} • ${selectedAudioFormat?.ext?.toUpperCase() || 'MP3'}`}
            </span>
          </div>

          <button
            onClick={handleDownloadClick}
            disabled={isVideo ? !selectedFormat : !selectedAudioFormat}
            className="w-full sm:w-auto gradient-brand text-white font-bold px-8 py-3.5 rounded-xl shadow-xl shadow-purple-600/30 hover:shadow-purple-600/50 hover:brightness-110 active:scale-[0.98] disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-sm sm:text-base cursor-pointer"
          >
            <Download className="w-5 h-5 text-cyan-200" />
            <span>Download {isVideo ? 'Video' : 'Audio Track'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
