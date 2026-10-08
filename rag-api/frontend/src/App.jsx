import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [token, setToken] = useState(localStorage.getItem('access_token') || '');
  const [toastMessage, setToastMessage] = useState(null);

  // Mobile Sidebar Toggle State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

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

  const handleRefreshSessions = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex flex-col md:flex-row h-screen w-screen bg-slate-900 text-white overflow-hidden relative">
      {/* Toast Notification Container */}
      {toastMessage && (
        <div className={`fixed top-4 right-4 z-[60] px-4 py-2.5 rounded-xl border text-xs font-medium shadow-xl backdrop-blur-md transition-all animate-bounce ${
          toastMessage.type === 'error' 
            ? 'bg-rose-500/20 border-rose-500/40 text-rose-200' 
            : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-200'
        }`}>
          {toastMessage.msg}
        </div>
      )}

      {/* Mobile Backdrop / Overlay */}
      {isSidebarOpen && (
        <div 
          onClick={() => setIsSidebarOpen(false)} 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      {/* 1. Sidebar Component (Responsive Drawer) */}
      <div className={`fixed md:relative z-50 h-full transition-transform duration-300 ease-in-out ${
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <Sidebar
          currentSessionId={currentSessionId}
          onSelectSession={(id) => {
            setCurrentSessionId(id);
            setIsSidebarOpen(false); // Mobile screen par session click karte hi sidebar close ho jaye
          }}
          onNewChat={(id) => {
            setCurrentSessionId(id);
            setIsSidebarOpen(false);
          }}
          token={token}
          onLogout={handleLogout}
          refreshTrigger={refreshTrigger}
          onCloseMobile={() => setIsSidebarOpen(false)}
        />
      </div>

      {/* 2. Main Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden p-2 md:p-6 space-y-2 md:space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center bg-slate-800/80 backdrop-blur-md p-3 md:p-4 rounded-xl border border-slate-700/80 shadow-lg shrink-0">
          <div className="flex items-center gap-2">
            {/* Mobile Hamburger Menu Button */}
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="md:hidden p-2 text-slate-300 hover:text-white bg-slate-700/50 rounded-lg text-lg"
            >
              ☰
            </button>
            <h1 className="text-base md:text-xl font-bold text-indigo-400 truncate">
              RAG AI Assistant
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 md:px-4 md:py-2 bg-red-600 hover:bg-red-500 rounded-lg font-medium text-xs md:text-sm transition shadow-md shadow-red-600/20"
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