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
      // Correct endpoint as per backend code: /documents/upload-pdf
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
      // Correct endpoint as per backend code: /documents/process-url
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
    <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-lg mb-6">
      <h3 className="text-xl font-semibold mb-4 text-indigo-400">Add Knowledge Base Source</h3>

      {message && (
        <div className="bg-emerald-500/20 border border-emerald-500 text-emerald-200 text-sm p-3 rounded-lg mb-4">
          {message}
        </div>
      )}

      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-200 text-sm p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* PDF Upload */}
        <form onSubmit={handleFileUpload} className="space-y-3 bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
          <label className="block text-sm font-medium text-slate-300">Upload PDF Document</label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
          />
          <button
            type="submit"
            disabled={!file || loadingFile}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium text-sm transition disabled:opacity-50"
          >
            {loadingFile ? 'Uploading...' : 'Upload PDF'}
          </button>
        </form>

        {/* URL Indexing */}
        <form onSubmit={handleUrlUpload} className="space-y-3 bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
          <label className="block text-sm font-medium text-slate-300">Index Web URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={!url || loadingUrl}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium text-sm transition disabled:opacity-50"
          >
            {loadingUrl ? 'Indexing...' : 'Index Web Page'}
          </button>
        </form>
      </div>
    </div>
  );
}