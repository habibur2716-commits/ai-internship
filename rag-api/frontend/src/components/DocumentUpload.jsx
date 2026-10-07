import React, { useState } from 'react';
import API from '../api/axios';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [loadingFile, setLoadingFile] = useState(false);
  const [loadingUrl, setLoadingUrl] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setMessage('');
    setError('');
    setLoadingFile(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await API.post('/documents/upload-pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage('PDF file successfully uploaded and indexed!');
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setLoadingFile(false);
    }
  };

  const handleUrlUpload = async (e) => {
    e.preventDefault();
    if (!url) return;
    setMessage('');
    setError('');
    setLoadingUrl(true);

    try {
      await API.post('/documents/process-url', { url: url.trim() });
      setMessage('URL successfully processed and indexed!');
      setUrl('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to index URL.');
    } finally {
      setLoadingUrl(false);
    }
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-xl p-6 rounded-2xl border border-slate-800/80 shadow-2xl mb-6">
      <h3 className="text-base font-semibold mb-4 text-slate-200 flex items-center gap-2">
        <span className="text-indigo-400">📚</span> Add Knowledge Base Source
      </h3>

      {message && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs p-3 rounded-xl mb-4 flex items-center gap-2">
          <span>✅</span> {message}
        </div>
      )}

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs p-3 rounded-xl mb-4 flex items-center gap-2">
          <span>⚠️</span> {error}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-5">
        {/* PDF Upload */}
        <form onSubmit={handleFileUpload} className="space-y-3 bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
          <label className="block text-xs font-medium text-slate-300">Upload PDF Document</label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/80 file:text-white hover:file:bg-indigo-500 cursor-pointer"
          />
          <button
            type="submit"
            disabled={!file || loadingFile}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 active:scale-98 text-white font-medium rounded-xl text-xs transition shadow-md shadow-indigo-600/20 disabled:opacity-40"
          >
            {loadingFile ? 'Uploading...' : 'Upload PDF'}
          </button>
        </form>

        {/* URL Indexing */}
        <form onSubmit={handleUrlUpload} className="space-y-3 bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
          <label className="block text-xs font-medium text-slate-300">Index Web URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="w-full px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50"
          />
          <button
            type="submit"
            disabled={!url || loadingUrl}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 active:scale-98 text-white font-medium rounded-xl text-xs transition shadow-md shadow-indigo-600/20 disabled:opacity-40"
          >
            {loadingUrl ? 'Indexing...' : 'Index Web Page'}
          </button>
        </form>
      </div>
    </div>
  );
}