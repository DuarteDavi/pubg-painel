import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3020'

console.log('[API] VITE_API_URL env:', import.meta.env.VITE_API_URL)
console.log('[API] API_URL resolved:', API_URL)

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

console.log('[API] Axios baseURL:', apiClient.defaults.baseURL)

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.params = config.params || {}
    config.params.token = token
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (login, password) =>
    apiClient.post('/api/admin/login', { login, password }),
  logout: (token) =>
    apiClient.post('/api/admin/logout', {}, { params: { token } }),
}

export const adminAPI = {
  getDashboard: (token) =>
    apiClient.get('/api/admin/dashboard', { params: { token } }),

  getClients: (page = 1, pageSize = 10, search = '', status = 'all', token) =>
    apiClient.get('/api/admin/clients', {
      params: { page, page_size: pageSize, search, status, token },
    }),

  getClient: (clientId, token) =>
    apiClient.get(`/api/admin/clients/${clientId}`, { params: { token } }),

  createClient: (login, password, passwordConfirm, deviceLimit, licenseDays, product, token) =>
    apiClient.post(
      '/api/admin/clients',
      { login, password, password_confirm: passwordConfirm, device_limit: deviceLimit, license_days: licenseDays, product },
      { params: { token } }
    ),

  updateClient: (clientId, login, status, deviceLimit, token) =>
    apiClient.put(
      `/api/admin/clients/${clientId}`,
      { login, status, device_limit: deviceLimit },
      { params: { token } }
    ),

  resetPassword: (clientId, newPassword, token) =>
    apiClient.post(
      `/api/admin/clients/${clientId}/reset-password`,
      { new_password: newPassword },
      { params: { token } }
    ),

  renewLicense: (clientId, days, token) =>
    apiClient.post(
      `/api/admin/clients/${clientId}/renew-license`,
      { days },
      { params: { token } }
    ),

  revokeDevices: (clientId, token) =>
    apiClient.post(
      `/api/admin/clients/${clientId}/revoke-sessions`,
      {},
      { params: { token } }
    ),

  getDevices: (clientId, token) =>
    apiClient.get(`/api/admin/clients/${clientId}/devices`, { params: { token } }),

  removeDevice: (clientId, deviceId, token) =>
    apiClient.delete(
      `/api/admin/clients/${clientId}/devices/${deviceId}`,
      { params: { token } }
    ),

  activateClient: (clientId, token) =>
    apiClient.post(
      `/api/admin/clients/${clientId}/activate`,
      {},
      { params: { token } }
    ),

  deactivateClient: (clientId, token) =>
    apiClient.post(
      `/api/admin/clients/${clientId}/deactivate`,
      {},
      { params: { token } }
    ),

  deleteClient: (clientId, token) =>
    apiClient.delete(`/api/admin/clients/${clientId}`, { params: { token } }),
}

export default apiClient
