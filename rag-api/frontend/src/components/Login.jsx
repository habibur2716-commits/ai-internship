import React, { useState } from 'react';
import API from '../api/axios';

export default function Login({ onLoginSuccess }) {
  const [mode, setMode] = useState('login'); // 'login', 'signup', 'forgot'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  // OTP States
  const [otp, setOtp] = useState('');
  const [showOtpStep, setShowOtpStep] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // Helper for direct login
  const performLogin = async (loginIdentifier, loginPassword) => {
    const params = new URLSearchParams();
    params.append('username', loginIdentifier.trim());
    params.append('password', loginPassword);

    let response;
    try {
      response = await API.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
    } catch (formErr) {
      if (formErr.response?.status === 422 || formErr.response?.status === 400) {
        response = await API.post('/auth/login', {
          username: loginIdentifier.trim(),
          password: loginPassword,
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
      throw new Error('Invalid token response from server');
    }
  };

  // Step 1: Send OTP for Signup or Forgot Password
  const handleSendOtp = async (purpose) => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await API.post('/auth/send-otp', {
        email: email.trim(),
        purpose: purpose,
      });
      setShowOtpStep(true);
      setSuccess(`OTP sent to ${email.trim()}. Please check your inbox.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP & Finish Action
  const handleVerifyAndSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (mode === 'signup') {
        // 1. Verify OTP
        await API.post('/auth/verify-otp', {
          email: email.trim(),
          code: otp.trim(),
          purpose: 'signup',
        });

        // 2. Register User
        await API.post('/auth/signup', {
          name: name.trim(),
          email: email.trim(),
          username: username.trim(),
          password: password,
        });

        setSuccess('Account verified and created! Logging in...');
        await performLogin(username.trim() || email.trim(), password);

      } else if (mode === 'forgot') {
        // Reset Password with OTP
        await API.post('/auth/reset-password-otp', {
          email: email.trim(),
          code: otp.trim(),
          new_password: newPassword,
        });

        // Success banner show hoga 3 seconds ke liye phir login screen par switch hoga
        setSuccess('🎉 Password reset successfully! Redirecting to login...');
        setShowOtpStep(false);
        setOtp('');
        setNewPassword('');

        setTimeout(() => {
          setMode('login');
          setSuccess('Password updated. Please sign in with your new password.');
        }, 3000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'OTP Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  // Standard Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (mode === 'login') {
      setLoading(true);
      try {
        await performLogin(email.trim(), password);
      } catch (err) {
        setError(err.response?.data?.detail || 'Invalid email/username or password.');
      } finally {
        setLoading(false);
      }
    } else if (mode === 'signup') {
      // Trigger OTP sending first
      await handleSendOtp('signup');
    } else if (mode === 'forgot') {
      // Trigger OTP sending first
      await handleSendOtp('forgot_password');
    }
  };

  const resetForm = (newMode) => {
    setMode(newMode);
    setShowOtpStep(false);
    setError('');
    setSuccess('');
    setOtp('');
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="w-full max-w-md bg-slate-900/60 backdrop-blur-2xl p-8 rounded-3xl border border-slate-800/80 shadow-2xl relative z-10">
        
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30 text-xl">
            {mode === 'signup' ? '🚀' : mode === 'forgot' ? '🔑' : '⚡'}
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">RAG AI Assistant</h2>
          <p className="text-xs text-slate-400 mt-1">
            {mode === 'signup' 
              ? 'Create a new account' 
              : mode === 'forgot' 
              ? 'Reset your password' 
              : 'Sign in to access your assistant'}
          </p>
        </div>

        {/* Notifications */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs p-3 rounded-xl mb-6 flex items-center gap-2">
            <span>⚠️</span> {error}
          </div>
        )}

        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs p-3 rounded-xl mb-6 flex items-center gap-2">
            <span>✅</span> {success}
          </div>
        )}

        {/* OTP Input Step */}
        {showOtpStep ? (
          <form onSubmit={handleVerifyAndSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Enter 6-Digit OTP Code
              </label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                required
                className="w-full px-4 py-3 bg-slate-950/60 border border-indigo-500/50 rounded-xl text-center text-xl font-mono tracking-widest text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                placeholder="000000"
              />
            </div>

            {mode === 'forgot' && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                  placeholder="Enter new password"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm rounded-xl transition duration-200 shadow-lg disabled:opacity-50"
            >
              {loading ? 'Verifying...' : mode === 'signup' ? 'Verify & Complete Signup' : 'Reset Password'}
            </button>

            <button
              type="button"
              onClick={() => setShowOtpStep(false)}
              className="w-full text-xs text-slate-400 hover:underline mt-2"
            >
              ← Back to Details
            </button>
          </form>
        ) : (
          /* Normal Input Step */
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
                    placeholder="Enter name"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
                    placeholder="Enter username"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                {mode === 'login' ? 'Username or Email' : 'Email Address'}
              </label>
              <input
                type={mode === 'login' ? 'text' : 'email'}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
                placeholder={mode === 'login' ? 'Enter username or email' : 'Enter email address'}
              />
            </div>

            {mode !== 'forgot' && (
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-medium text-slate-300">Password</label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => resetForm('forgot')}
                      className="text-xs text-indigo-400 hover:underline"
                    >
                      Forgot?
                    </button>
                  )}
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
                  placeholder="••••••••"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm rounded-xl transition duration-200 shadow-lg disabled:opacity-50 mt-2"
            >
              {loading 
                ? 'Processing...' 
                : mode === 'signup' 
                ? 'Send Verification OTP' 
                : mode === 'forgot' 
                ? 'Send Reset OTP' 
                : 'Sign In'}
            </button>
          </form>
        )}

        {/* Toggle Mode Footer */}
        <div className="mt-6 text-center text-xs text-slate-400">
          {mode === 'login' && (
            <>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => resetForm('signup')}
                className="text-indigo-400 font-medium hover:underline"
              >
                Sign Up
              </button>
            </>
          )}

          {(mode === 'signup' || mode === 'forgot') && (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => resetForm('login')}
                className="text-indigo-400 font-medium hover:underline"
              >
                Sign In
              </button>
            </>
          )}
        </div>

      </div>
    </div>
  );
}