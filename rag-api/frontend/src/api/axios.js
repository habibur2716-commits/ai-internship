import axios from 'axios';

// FastAPI backend ka URL
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

// 1. Har request ke sath JWT token include karne ke liye
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 2. Response Interceptor for Expired Token (401 Error) Handling
API.interceptors.response.use(
  (response) => response,
  (error) => {
    // Agar Backend 401 Unauthorized (Token Expired) return kare
    if (error.response && error.response.status === 401) {
      console.warn("JWT Token expired or invalid. Logging out automatically...");
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Auto redirect to login page by reloading app safely
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      } else {
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export default API;