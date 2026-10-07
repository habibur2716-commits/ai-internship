import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  
  // 1. Sidebar refresh ke liye trigger state
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // 2. LocalStorage se token nikaalne ke liye state
  const [token, setToken] = useState(localStorage.getItem('access_token') || '');

  // 3. Global Toast Notification State
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg, type = 'info') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      setToken(savedToken);
      setIsAuthenticated(true);
    }
  }, []);

  const handleLoginSuccess = () => {
    const savedToken = localStorage.getItem('access_token');
    setToken(savedToken || '');
    setIsAuthenticated(true);
    showToast('Logged in successfully!', 'success');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken('');
    setIsAuthenticated(false);
    setCurrentSessionId(null);
    showToast('Logged out safely.', 'info');
  };

  // Trigger Function: Chat me question ka answer aate hi trigger hoga
  const handleRefreshSessions = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex h-screen w-screen bg-slate-900 text-white overflow-hidden relative">
      {/* Toast Notification Container */}
      {toastMessage && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl border text-xs font-medium shadow-xl backdrop-blur-md transition-all animate-bounce ${
          toastMessage.type === 'error' 
            ? 'bg-rose-500/20 border-rose-500/40 text-rose-200' 
            : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-200'
        }`}>
          {toastMessage.msg}
        </div>
      )}

      {/* 1. Sidebar Component */}
      <Sidebar
        currentSessionId={currentSessionId}
        onSelectSession={(id) => setCurrentSessionId(id)}
        onNewChat={(id) => setCurrentSessionId(id)}
        token={token}
        onLogout={handleLogout}
        refreshTrigger={refreshTrigger}
      />

      {/* 2. Main Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden p-4 md:p-6 space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center bg-slate-800/80 backdrop-blur-md p-4 rounded-xl border border-slate-700/80 shadow-lg shrink-0">
          <h1 className="text-xl font-bold text-indigo-400">RAG AI Assistant Dashboard</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-medium text-sm transition shadow-md shadow-red-600/20"
          >
            Logout
          </button>
        </div>

        {/* 3. Full Screen Chat Component */}
        <div className="flex-1 min-h-0">
          <Chat 
            currentSessionId={currentSessionId} 
            onRefreshSessions={handleRefreshSessions}
          />
        </div>
      </div>
    </div>
  );
}