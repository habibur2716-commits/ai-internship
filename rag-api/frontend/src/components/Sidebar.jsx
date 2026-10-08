import React, { useState, useEffect } from 'react';
import API from '../api/axios';

const Sidebar = ({ currentSessionId, onSelectSession, onNewChat, token, onLogout, refreshTrigger, onCloseMobile }) => {
  const [sessions, setSessions] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [loading, setLoading] = useState(false);

  const getAuthConfig = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  const fetchSessions = async () => {
    if (!token) return;
    try {
      const response = await API.get('/chat/sessions', getAuthConfig());
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
    }
  };

  useEffect(() => {
    if (token) {
      fetchSessions();
    }
  }, [token, refreshTrigger]);

  const handleCreateNewChat = async () => {
    setLoading(true);
    try {
      const response = await API.post('/chat/sessions', {}, getAuthConfig());
      setSessions([response.data, ...sessions]);
      onNewChat(response.data.id);
    } catch (error) {
      console.error('Error creating chat:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRename = async (id) => {
    if (!newTitle.trim()) {
      setEditingId(null);
      return;
    }
    try {
      await API.patch(`/chat/sessions/${id}`, { title: newTitle }, getAuthConfig());
      setEditingId(null);
      fetchSessions();
    } catch (error) {
      console.error('Error renaming chat:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this chat?')) return;
    try {
      await API.delete(`/chat/sessions/${id}`, getAuthConfig());
      setSessions(sessions.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        onNewChat(null);
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  return (
    <div className="w-72 md:w-64 h-screen bg-slate-950 text-slate-200 flex flex-col p-4 border-r border-slate-800/80 shadow-2xl">
      {/* Header / Brand */}
      <div className="mb-6 px-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
            ⚡
          </div>
          <div>
            <h1 className="text-base font-bold tracking-wide text-white">RAG Chatbot</h1>
            <p className="text-[10px] text-indigo-400 font-medium">AI Document Intelligence</p>
          </div>
        </div>
        {/* Mobile Close Button */}
        {onCloseMobile && (
          <button 
            onClick={onCloseMobile}
            className="md:hidden p-1 text-slate-400 hover:text-white text-lg font-bold"
          >
            ✕
          </button>
        )}
      </div>

      {/* New Chat Button */}
      <button
        onClick={handleCreateNewChat}
        disabled={loading}
        className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 mb-5 transition-all duration-200 shadow-lg shadow-indigo-600/20 active:scale-[0.98] disabled:opacity-50"
      >
        <span className="text-lg font-bold">+</span>
        <span className="text-sm">{loading ? 'Creating...' : 'New Chat'}</span>
      </button>

      {/* Section Label */}
      <div className="px-2 mb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
        Recent Chats
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
        {sessions.length === 0 ? (
          <p className="text-slate-500 text-xs text-center py-8 bg-slate-900/40 rounded-xl border border-dashed border-slate-800/60">
            No chat sessions yet
          </p>
        ) : (
          sessions.map((session) => {
            const isActive = currentSessionId === session.id;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between p-2.5 px-3 rounded-xl cursor-pointer transition-all duration-200 border ${
                  isActive
                    ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-200 font-medium shadow-sm'
                    : 'bg-transparent border-transparent hover:bg-slate-900/60 hover:border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {editingId === session.id ? (
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onBlur={() => handleRename(session.id)}
                    onKeyDown={(e) => e.key === 'Enter' && handleRename(session.id)}
                    className="bg-slate-800 text-white px-2 py-1 rounded-lg w-full text-xs outline-none border border-indigo-500"
                    autoFocus
                  />
                ) : (
                  <span className="truncate text-xs w-40 md:w-36">{session.title || 'Untitled Chat'}</span>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingId(session.id);
                      setNewTitle(session.title || '');
                    }}
                    className="text-xs hover:text-indigo-400 p-1 rounded transition"
                    title="Rename"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(session.id);
                    }}
                    className="text-xs hover:text-rose-400 p-1 rounded transition"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Logout / User Footer */}
      {onLogout && (
        <div className="pt-4 border-t border-slate-800/80 mt-auto">
          <button
            onClick={onLogout}
            className="w-full text-left px-3 py-2 text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all flex items-center justify-between"
          >
            <span>Sign Out</span>
            <span>🚪</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default Sidebar;