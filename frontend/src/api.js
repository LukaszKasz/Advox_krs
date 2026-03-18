import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests if available
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// API functions
export const authAPI = {
    register: async (username, email, password) => {
        const response = await api.post('/register', { username, email, password });
        return response.data;
    },

    login: async (username, password) => {
        const response = await api.post('/login', { username, password });
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await api.get('/me');
        return response.data;
    },
};

export const rejestrioAPI = {
    getSettings: async () => {
        const response = await api.get('/api/settings/rejestrio');
        return response.data;
    },

    saveSettings: async (apiKey) => {
        const response = await api.post('/api/settings/rejestrio', { apiKey });
        return response.data;
    },

    fetchCompany: async (krs) => {
        const response = await api.post('/api/rejestrio/company', { krs });
        return response.data;
    },

    fetchFinancialDocument: async (krs) => {
        const response = await api.post('/api/rejestrio/financial-document', { krs });
        return response.data;
    },

    getSavedOrganizations: async () => {
        const response = await api.get('/api/rejestrio/organizations');
        return response.data;
    },

    getSavedOrganizationsCsvUrl: () => {
        return `${API_BASE_URL}/api/rejestrio/organizations/export`;
    },

    getSavedOrganizationsXlsxUrl: () => {
        return `${API_BASE_URL}/api/rejestrio/organizations/export/xlsx`;
    },
};

// Token management
export const tokenManager = {
    setToken: (token) => {
        localStorage.setItem('token', token);
    },

    getToken: () => {
        return localStorage.getItem('token');
    },

    removeToken: () => {
        localStorage.removeItem('token');
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },
};

export default api;
