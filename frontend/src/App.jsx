import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import UrlInput from './components/UrlInput';
import MediaCard from './components/MediaCard';
import DownloadProgress from './components/DownloadProgress';
import CompletedCard from './components/CompletedCard';
import ErrorBanner from './components/ErrorBanner';
import Footer from './components/Footer';
import { 
  Film, 
  Music, 
  ShieldCheck, 
  Zap, 
  Tv, 
  Layers, 
  CheckCircle, 
  HardDrive, 
  Sparkles,
  Cpu
} from 'lucide-react';

const API_BASE = typeof window !== 'undefined' && window.location.port === '5173' 
  ? '/api' 
  : (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? 'http://127.0.0.1:8000/api' 
      : '/api');

export default function App() {
  const [url, setUrl] = useState('');
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [mediaInfo, setMediaInfo] = useState(null);
  const [error, setError] = useState(null);
  const [currentJob, setCurrentJob] = useState(null);
  const [serverStatus, setServerStatus] = useState({ healthy: false });

  const pollIntervalRef = useRef(null);

  // Check backend health on load
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'healthy') {
          setServerStatus({ healthy: true, ...data });
        }
      })
      .catch((err) => {
        console.warn('Backend connection error:', err);
        setServerStatus({ healthy: false });
      });

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleFetchInfo = async (inputUrl) => {
    setError(null);
    setLoadingInfo(true);
    setMediaInfo(null);
    setCurrentJob(null);

    try {
      const response = await fetch(`${API_BASE}/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: inputUrl })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to extract media information.');
      }

      setMediaInfo(data.data || data);
    } catch (err) {
      setError(err.message || 'An error occurred while inspecting video formats.');
    } finally {
      setLoadingInfo(false);
    }
  };

  const startPolling = (jobId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/progress/${jobId}`);
        if (!response.ok) return;

        const jobData = await response.json();
        setCurrentJob(jobData);

        if (jobData.status === 'completed' || jobData.status === 'failed' || jobData.status === 'cancelled') {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          if (jobData.status === 'failed') {
            setError(jobData.error_message || jobData.error || 'Download failed during stream processing.');
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 600);
  };

  const handleStartDownload = async (options) => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: options.url,
          height: options.height,
          quality: options.quality,
          format_type: options.format_type,
          preferred_codec: options.preferred_codec,
          container: options.container
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Could not initiate download.');
      }

      const taskId = data.task_id || data.job_id;
      setCurrentJob({
        task_id: taskId,
        job_id: taskId,
        status: 'pending',
        progress: 0,
        phase_message: 'Download job queued on server...',
        format_type: options.format_type,
        options: options
      });

      startPolling(taskId);
    } catch (err) {
      setError(err.message || 'Failed to start download.');
    }
  };

  const handleReset = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setUrl('');
    setMediaInfo(null);
    setCurrentJob(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#08080c] text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar serverStatus={serverStatus} />

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 md:py-12 flex flex-col items-center">
        
        {/* Hero Header */}
        <div className="text-center max-w-3xl mx-auto mb-8 md:mb-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-600/10 border border-red-500/30 text-red-400 text-xs font-bold mb-4 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-red-400" />
            <span>Master Quality 8K FUHD & 4K UHD Downloader</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight leading-tight">
            Next-Gen 8K Video Downloader
          </h1>

          <p className="mt-3 text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
            Detect actual available resolutions from 144p to 8K (7680×4320). Full support for AV1, VP9, HEVC, and H.264 streams with lossless FFmpeg muxing and FFprobe stream verification.
          </p>
        </div>

        {/* URL Input Form */}
        <div className="w-full max-w-3xl mb-8">
          <UrlInput
            url={url}
            setUrl={setUrl}
            onFetch={handleFetchInfo}
            loading={loadingInfo}
            onClear={() => {
              setUrl('');
              setError(null);
            }}
          />
        </div>

        {/* Error Alert */}
        {error && (
          <div className="w-full max-w-3xl mb-8">
            <ErrorBanner message={error} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Media Preview & Options Card */}
        {mediaInfo && !currentJob && (
          <div className="w-full max-w-3xl mb-8 animate-in fade-in duration-300">
            <MediaCard
              mediaInfo={mediaInfo}
              onStartDownload={handleStartDownload}
              isDownloading={Boolean(currentJob && currentJob.status !== 'completed')}
            />
          </div>
        )}

        {/* Progress Display */}
        {currentJob && currentJob.status !== 'completed' && currentJob.status !== 'failed' && (
          <div className="w-full max-w-3xl mb-8 animate-in fade-in duration-300">
            <DownloadProgress job={currentJob} />
          </div>
        )}

        {/* Completed & Verified Card */}
        {currentJob && currentJob.status === 'completed' && (
          <div className="w-full max-w-3xl mb-8 animate-in zoom-in-95 duration-300">
            <CompletedCard job={currentJob} onReset={handleReset} />
          </div>
        )}

        {/* Features & Reliability Showcase */}
        {!mediaInfo && !currentJob && (
          <section className="w-full max-w-4xl mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center mb-3">
                <Tv className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">Full 144p to 8K Support</h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Detects real formats dynamically. Downloads up to 7680×4320 60FPS HDR without artificial resolution caps.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-3">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">AV1 & VP9 Modern Codecs</h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Never restricts 8K to legacy H.264. Automatically captures native AV1 & VP9 master streams with zero re-encoding loss.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">FFprobe Stream Verification</h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Every video is checked with FFprobe. Guarantees a playable video stream and audio stream—audio-only delivery is strictly prohibited.
              </p>
            </div>

          </section>
        )}

      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
