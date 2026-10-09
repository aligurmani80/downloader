// API service for NexaLoad

const BASE_URL = '/api';

export const api = {
  async checkHealth() {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (!res.ok) throw new Error('Health check failed');
      return await res.json();
    } catch (err) {
      console.warn('Backend offline or unreachable', err);
      return { status: 'offline' };
    }
  },

  async analyzeUrl(url) {
    const res = await fetch(`${BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to analyze URL');
    }
    return data;
  },

  async startDownload({ url, format_type, quality, format_id, container, title, thumbnail }) {
    const res = await fetch(`${BASE_URL}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        format_type,
        quality,
        format_id,
        container,
        title,
        thumbnail,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to initiate download');
    }
    return data;
  },

  async getProgress(taskId) {
    const res = await fetch(`${BASE_URL}/progress/${taskId}`);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to fetch task progress');
    }
    return await res.json();
  },

  async getHistory() {
    const res = await fetch(`${BASE_URL}/history`);
    if (!res.ok) throw new Error('Failed to load history');
    return await res.json();
  },

  async deleteHistoryItem(itemId) {
    const res = await fetch(`${BASE_URL}/history/${itemId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete history item');
    return await res.json();
  },

  async clearHistory() {
    const res = await fetch(`${BASE_URL}/history/clear`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to clear history');
    return await res.json();
  },

  async openFolder() {
    const res = await fetch(`${BASE_URL}/downloads/open-folder`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to open downloads folder');
    return await res.json();
  },
};
