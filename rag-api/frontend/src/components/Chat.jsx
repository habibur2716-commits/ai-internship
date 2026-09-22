import React, { useState } from 'react';
import API from '../api/axios';

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! Ask me anything about your uploaded documents or indexed web pages.' }
  ]);
  const [query, setQuery] = useState('');
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = query.trim();
    setQuery('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // Backend expects /chat/ask with 'question' and 'enable_web_search'
      const response = await API.post('/chat/ask', {
        question: userMessage,
        enable_web_search: enableWebSearch
      });

      const botReply = response.data?.answer || 'No answer received.';
      
      setMessages((prev) => [
        ...prev,
        { 
          role: 'assistant', 
          content: botReply,
          docSources: response.data?.doc_sources || [],
          webSources: response.data?.web_sources || []
        }
      ]);
    } catch (err) {
      console.error("Chat Query Error:", err.response);
      const errorMessage = err.response?.data?.detail || 'Could not retrieve response from backend.';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${errorMessage}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-lg flex flex-col h-[550px]">
      <div className="p-4 border-b border-slate-700 font-semibold text-indigo-400 flex justify-between items-center">
        <span>RAG AI Assistant Chat</span>
        
        {/* Toggle Web Search */}
        <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
          <input 
            type="checkbox" 
            checked={enableWebSearch} 
            onChange={(e) => setEnableWebSearch(e.target.checked)}
            className="rounded text-indigo-600 focus:ring-indigo-500 bg-slate-900 border-slate-700"
          />
          Enable Web Search
        </label>
      </div>

      {/* Messages area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : 'bg-slate-700 text-slate-100 rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>

            {/* Display Sources if available */}
            {msg.docSources && msg.docSources.length > 0 && (
              <div className="text-[11px] text-slate-400 mt-1 max-w-[80%]">
                <span className="font-semibold text-indigo-400">Sources:</span> {msg.docSources.join(', ')}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-700 text-slate-400 rounded-2xl rounded-bl-none px-4 py-3 text-sm animate-pulse">
              Thinking & Searching ChromaDB...
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <form onSubmit={handleSend} className="p-4 border-t border-slate-700 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question from uploaded documents..."
          className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}