import axios from 'axios';
import CryptoJS from 'crypto-js';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
//const API_BASE_URL = process.env.REACT_APP_DEV_API_BASE_URL; // DEV ENV
const APP_SECRET = process.env.REACT_APP_APP_SECRET;

if (!API_BASE_URL || !APP_SECRET) {
  throw new Error('API_BASE_URL and APP_SECRET must be defined in environment variables');
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});


const generateSignature = (method: string, timestamp: string, endpoint: string, data?: any): string => {
  let url = `${API_BASE_URL}${endpoint}`;
  let signatureData = `${timestamp}${method}${url}`;

  if (method === 'GET' && data) {
    const params = new URLSearchParams(data);
    const sortedParams = Array.from(params.entries()).sort((a, b) => a[0].localeCompare(b[0]));
    url += '?' + new URLSearchParams(sortedParams).toString();
    signatureData = `${timestamp}${method}${url}`;
  } else if (method === 'POST' && data) {
    signatureData += JSON.stringify(data, Object.keys(data).sort());
  }
  console.log(signatureData)
  const hmac = CryptoJS.HmacSHA256(signatureData, APP_SECRET);
  return hmac.toString(CryptoJS.enc.Hex);
};

api.interceptors.request.use((config) => {
  if (config.method?.toUpperCase() === 'OPTIONS') {
    return config;
  }
  
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const endpoint = config.url ?? '';
  const signature = generateSignature(
    config.method!.toUpperCase(),
    timestamp,
    endpoint,
    config.method!.toUpperCase() === 'GET' ? config.params : config.data
  );

  config.headers['X-Timestamp'] = timestamp;
  config.headers['X-Signature'] = signature;
  config.headers['Content-Type'] = 'application/json';
  config.headers['Accept'] = 'text/event-stream';
  

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response ? error.response.data : error.message);
    return Promise.reject(error);
  }
);