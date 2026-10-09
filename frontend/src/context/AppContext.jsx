import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AppContext = createContext(null);

const DEFAULT_SETTINGS = {
  theme: 'theme-cyber',
  defaultQuality: '1080p',
  defaultAudioFormat: 'mp3',
  preferredContainer: 'mp4',
  incognitoMode: false,
  autoDownloadBrowser: true,
};

export function AppProvider({ children }) {
  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('nexaload_theme') || 'theme-cyber';
  });

  // Settings state
  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('nexaload_settings');
      return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  // Navigation
  const [activeTab, setActiveTab] = useState('downloader');

  // Backend status
  const [serverStatus, setServerStatus] = useState('checking');

  // Download state
  const [activeTasks, setActiveTasks] = useState([]);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Toast notifications
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 5);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Update theme on body
  useEffect(() => {
    document.body.classList.remove('theme-cyber', 'theme-slate', 'theme-oled');
    document.body.classList.add(theme);
    localStorage.setItem('nexaload_theme', theme);
  }, [theme]);

  // Update settings in localStorage
  useEffect(() => {
    localStorage.setItem('nexaload_settings', JSON.stringify(settings));
  }, [settings]);

  // Check server health on load & interval
  const verifyServer = useCallback(async () => {
    try {
      const res = await api.checkHealth();
      setServerStatus(res.status === 'online' ? 'online' : 'offline');
    } catch {
      setServerStatus('offline');
    }
  }, []);

  useEffect(() => {
    verifyServer();
    const timer = setInterval(verifyServer, 15000);
    return () => clearInterval(timer);
  }, [verifyServer]);

  // Fetch download history
  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await api.getHistory();
      setHistory(data);
    } catch (err) {
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Start new download task
  const addDownloadTask = useCallback(async (downloadOptions) => {
    try {
      const res = await api.startDownload(downloadOptions);
      const taskId = res.task_id;
      
      const newTask = {
        task_id: taskId,
        url: downloadOptions.url,
        title: downloadOptions.title || 'Media',
        thumbnail: downloadOptions.thumbnail,
        resolution: downloadOptions.quality,
        format_type: downloadOptions.format_type,
        container: downloadOptions.container,
        status: 'queued',
        percent: 0,
        speed_str: null,
        eta_str: null,
        download_url: null,
        error: null,
      };

      setActiveTasks((prev) => [newTask, ...prev]);
      addToast(`Download started: ${newTask.title.slice(0, 35)}...`, 'info');
      return taskId;
    } catch (err) {
      addToast(err.message || 'Failed to start download', 'error');
      throw err;
    }
  }, [addToast]);

  // Poll active tasks for progress
  useEffect(() => {
    const hasPending = activeTasks.some(
      (t) => t.status === 'queued' || t.status === 'downloading' || t.status === 'merging' || t.status === 'converting'
    );
    if (!hasPending) return;

    const interval = setInterval(async () => {
      const updatedList = await Promise.all(
        activeTasks.map(async (task) => {
          if (task.status === 'finished' || task.status === 'error') {
            return task;
          }
          try {
            const progress = await api.getProgress(task.task_id);
            if (progress.status === 'finished') {
              addToast(`Download ready: ${progress.title?.slice(0, 35) || 'File'}`, 'success');
              loadHistory();
            } else if (progress.status === 'error') {
              addToast(`Download failed: ${progress.error?.slice(0, 60) || 'Unknown error'}`, 'error');
            }
            return { ...task, ...progress };
          } catch {
            return task;
          }
        })
      );
      setActiveTasks(updatedList);
    }, 750);

    return () => clearInterval(interval);
  }, [activeTasks, addToast, loadHistory]);

  const clearCompletedTasks = useCallback(() => {
    setActiveTasks((prev) => prev.filter((t) => t.status !== 'finished' && t.status !== 'error'));
  }, []);

  const removeSingleTask = useCallback((taskId) => {
    setActiveTasks((prev) => prev.filter((t) => t.task_id !== taskId));
  }, []);

  return (
    <AppContext.Provider
      value={{
        theme,
        setTheme,
        settings,
        setSettings,
        activeTab,
        setActiveTab,
        serverStatus,
        activeTasks,
        addDownloadTask,
        clearCompletedTasks,
        removeSingleTask,
        history,
        historyLoading,
        loadHistory,
        toasts,
        addToast,
        removeToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}
