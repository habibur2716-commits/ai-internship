import axios from 'axios';

// FastAPI backend ka URL
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

// Har request ke sath JWT token include karne ke liye
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default API;