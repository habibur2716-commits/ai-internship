import React, { useState } from 'react';
import API from '../api/axios';

export default function Login({ onLoginSuccess }) {
  const [isSignup, setIsSignup] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (isSignup) {
        // Signup Payload
        await API.post('/auth/signup', {
          name: name.trim(),
          email: email.trim(),
          username: username.trim(),
          password: password,
        });

        setSuccess('Account created successfully!');
        setTimeout(() => {
          setIsSignup(false);
          setSuccess('Account created! Please sign in with your email.');
        }, 1500);
      } else {
        // Sign In: Backend expects email inside the 'username' field for OAuth2 Form Data
        const params = new URLSearchParams();
        params.append('username', email.trim());
        params.append('password', password);

        let response;
        try {
          response = await API.post('/auth/login', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          });
        } catch (formErr) {
          // Fallback if backend expects JSON body instead of form-data
          if (formErr.response?.status === 422 || formErr.response?.status === 400) {
            response = await API.post('/auth/login', {
              username: email.trim(),
              password: password,
            });
          } else {
            throw formErr;
          }
        }

        if (response?.data?.access_token) {
          localStorage.setItem('access_token', response.data.access_token);
          if (response.data.refresh_token) {
            localStorage.setItem('refresh_token', response.data.refresh_token);
          }
          onLoginSuccess();
        } else {
          setError('Invalid login response from server.');
        }
      }
    } catch (err) {
      console.error("API Error Details:", err.response?.data);
      const detail = err.response?.data?.detail;

      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        const missingFields = detail
          .map((item) => `${item.loc ? item.loc[item.loc.length - 1] : 'field'}: ${item.msg}`)
          .join(' | ');
        setError(missingFields || 'Validation error.');
      } else {
        setError('Invalid credentials or server issue.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white p-4">
      <div className="w-full max-w-md bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700">
        <h2 className="text-3xl font-bold text-center mb-2 text-indigo-400">RAG AI Assistant</h2>
        <p className="text-slate-400 text-center mb-6">
          {isSignup ? 'Create a new account' : 'Sign in to access your document assistant'}
        </p>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-emerald-500/20 border border-emerald-500 text-emerald-200 text-sm p-3 rounded-lg mb-4">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignup && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1 text-slate-300">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-white"
                  placeholder="Enter name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1 text-slate-300">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-white"
                  placeholder="Enter username"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium mb-1 text-slate-300">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-white"
              placeholder="Enter email address"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-slate-300">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none text-white"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-semibold transition duration-200 disabled:opacity-50 mt-2"
          >
            {loading ? 'Processing...' : isSignup ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-400">
          {isSignup ? 'Already have an account? ' : "Don't have an account? "}
          <button
            type="button"
            onClick={() => {
              setIsSignup(!isSignup);
              setError('');
              setSuccess('');
            }}
            className="text-indigo-400 hover:underline font-medium"
          >
            {isSignup ? 'Sign In' : 'Sign Up'}
          </button>
        </div>
      </div>
    </div>
  );
}