import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import API from '../api/axios';

export default function Chat({ currentSessionId, onRefreshSessions }) {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Har message update (stream chunk) par bottom auto scroll hoga
  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // 1. Load chat messages history whenever active session changes
  useEffect(() => {
    const fetchSessionMessages = async () => {
      if (!currentSessionId) {
        setMessages([
          { role: 'assistant', content: 'Select or create a chat session from the sidebar to begin!' }
        ]);
        return;
      }

      try {
        setLoading(true);
        const response = await API.get(`/chat/sessions/${currentSessionId}/messages`);
        
        const formattedMessages = response.data.map((msg) => ({
          role: msg.sender,
          content: msg.content
        }));

        if (formattedMessages.length === 0) {
          setMessages([
            { role: 'assistant', content: 'New chat session started. Upload files or ask anything!' }
          ]);
        } else {
          setMessages(formattedMessages);
        }
      } catch (err) {
        console.error("Error loading chat messages:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSessionMessages();
  }, [currentSessionId]);

  // Handle Inline File Upload (+ Icon Click)
  const handleFileSelect = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile || !currentSessionId) return;

    setUploadingFile(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('session_id', currentSessionId);

    try {
      await API.post('/documents/upload-pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAttachedFile(selectedFile.name);
    } catch (err) {
      console.error("File upload error:", err);
      alert(err.response?.data?.detail || "Failed to upload document.");
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Streaming Send Handler
  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading || !currentSessionId) return;

    const userMessage = query.trim();
    setQuery('');
    setAttachedFile(null);

    // 1. Append User Message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    // Get Auth Token for fetch request
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const baseURL = API.defaults.baseURL || 'http://127.0.0.1:8000';

    if (!token) {
      console.error("No token found in localStorage!");
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Authentication error: Please log out and log in again.' }
      ]);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${baseURL}/chat/ask-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: userMessage,
          session_id: currentSessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.statusText}`);
      }

      setLoading(false);

      // Append empty assistant message for streaming
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '', docSources: [], webSources: [] }
      ]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let buffer = '';

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // Keep partial line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (dataStr === '[DONE]') break;

              try {
                const parsed = JSON.parse(dataStr);

                // Handle metadata (sources)
                if (parsed.meta) {
                  setMessages((prev) => {
                    const lastMsg = { ...prev[prev.length - 1] };
                    lastMsg.docSources = parsed.meta.doc_sources || [];
                    lastMsg.webSources = parsed.meta.web_sources || [];
                    return [...prev.slice(0, -1), lastMsg];
                  });
                }

                // Handle text streaming
                if (parsed.text) {
                  setMessages((prev) => {
                    const lastMsg = { ...prev[prev.length - 1] };
                    lastMsg.content += parsed.text;
                    return [...prev.slice(0, -1), lastMsg];
                  });
                }
              } catch (err) {
                console.error("Error parsing JSON stream chunk:", err);
              }
            }
          }
        }
      }

      if (onRefreshSessions) {
        onRefreshSessions();
      }
    } catch (err) {
      console.error("Streaming Error:", err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: Could not retrieve response from server.` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-800/80 shadow-2xl flex flex-col h-full overflow-hidden">
      {/* Top Bar */}
      <div className="p-4 px-6 border-b border-slate-800/80 bg-slate-900/40 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          <span className="font-semibold text-xs md:text-sm text-slate-200">Autonomous RAG Agent</span>
        </div>
        <span className="text-[10px] text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
          Streaming Active
        </span>
      </div>

      {/* Messages area */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4 custom-scrollbar">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-3.5 px-4 text-xs md:text-sm leading-relaxed shadow-md ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-br-none'
                  : 'bg-slate-800/90 text-slate-200 rounded-bl-none border border-slate-700/60'
              }`}
            >
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <div className="space-y-2 text-slate-200 text-xs md:text-sm">
                  <ReactMarkdown
                    components={{
                      h1: ({ node, ...props }) => <h1 className="text-base font-bold text-indigo-300 mt-2 mb-1" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-indigo-300 mt-2 mb-1" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-xs font-bold text-indigo-300 mt-2 mb-1" {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc pl-4 space-y-1 my-1" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal pl-4 space-y-1 my-1" {...props} />,
                      li: ({ node, ...props }) => <li className="text-slate-200" {...props} />,
                      strong: ({ node, ...props }) => <strong className="font-semibold text-white" {...props} />,
                      a: ({ node, ...props }) => <a className="text-indigo-400 underline hover:text-indigo-300" target="_blank" rel="noreferrer" {...props} />
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Display Document & Web Sources */}
            {((msg.docSources && msg.docSources.length > 0) || (msg.webSources && msg.webSources.length > 0)) && (
              <div className="text-[11px] text-slate-400 mt-2 px-1 max-w-[85%] flex flex-wrap gap-2 items-center">
                {msg.docSources && msg.docSources.length > 0 && (
                  <div className="flex items-center gap-1 bg-indigo-950/60 border border-indigo-800/50 px-2.5 py-1 rounded-lg text-indigo-300">
                    <span className="font-semibold">📄 Document:</span>
                    <span>{msg.docSources.join(', ')}</span>
                  </div>
                )}
                {msg.webSources && msg.webSources.length > 0 && (
                  <div className="flex items-center gap-1 bg-violet-950/60 border border-violet-800/50 px-2.5 py-1 rounded-lg text-violet-300">
                    <span className="font-semibold">🌐 Web Search:</span>
                    <span className="truncate max-w-[200px]">{msg.webSources.join(', ')}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800/80 text-slate-400 border border-slate-700/50 rounded-2xl rounded-bl-none px-4 py-3 text-xs flex items-center gap-2 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
              Agent analyzing query & deciding sources...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-3.5 px-4 border-t border-slate-800/80 bg-slate-950/40 shrink-0">
        {/* Attachment preview tag */}
        {attachedFile && (
          <div className="mb-2 text-[11px] text-indigo-300 bg-indigo-500/10 border border-indigo-500/30 px-3 py-1 rounded-lg w-fit flex items-center gap-2">
            <span>📎 Attached: {attachedFile}</span>
            <button onClick={() => setAttachedFile(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        <form onSubmit={handleSend} className="flex items-center gap-2">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf"
            className="hidden"
          />

          {/* ChatGPT/Gemini Style Inline '+' Upload Button */}
          <button
            type="button"
            disabled={!currentSessionId || uploadingFile}
            onClick={() => fileInputRef.current?.click()}
            className="p-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition disabled:opacity-40 flex items-center justify-center"
            title="Attach Document"
          >
            {uploadingFile ? (
              <span className="animate-spin text-xs">⏳</span>
            ) : (
              <span className="text-lg leading-none font-bold">+</span>
            )}
          </button>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={currentSessionId ? "Ask a question or upload a document..." : "Please select or create a session first..."}
            disabled={!currentSessionId}
            className="flex-1 px-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-xs md:text-sm focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 disabled:opacity-40 transition"
          />

          <button
            type="submit"
            disabled={!query.trim() || loading || !currentSessionId}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-medium text-xs md:text-sm rounded-xl transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}