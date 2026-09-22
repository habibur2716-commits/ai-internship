import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import DocumentUpload from './components/DocumentUpload';
import Chat from './components/Chat';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4 md:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center bg-slate-800 p-4 rounded-xl border border-slate-700">
          <h1 className="text-xl font-bold text-indigo-400">RAG AI Assistant Dashboard</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-medium text-sm transition"
          >
            Logout
          </button>
        </div>

        {/* Document Upload Section */}
        <DocumentUpload />

        {/* Chat Section */}
        <Chat />
      </div>
    </div>
  );
}