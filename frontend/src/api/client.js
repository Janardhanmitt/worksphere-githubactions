import axios from 'axios'
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api', timeout: 10000 })
api.interceptors.response.use(r => r, error => { error.userMessage = error.response?.data?.detail || 'Could not reach WorkSphere. Check that the API and database are running.'; return Promise.reject(error) })
const query = params => ({ params })
export const employeesApi = { list: p => api.get('/employees', query(p)), get: id => api.get(`/employees/${id}`), save: (data, id) => id ? api.put(`/employees/${id}`, data) : api.post('/employees', data), remove: id => api.delete(`/employees/${id}`) }
export const projectsApi = { list: p => api.get('/projects', query(p)), get: id => api.get(`/projects/${id}`), save: (data, id) => id ? api.put(`/projects/${id}`, data) : api.post('/projects', data), remove: id => api.delete(`/projects/${id}`) }
export const tasksApi = { list: p => api.get('/tasks', query(p)), get: id => api.get(`/tasks/${id}`), save: (data, id) => id ? api.put(`/tasks/${id}`, data) : api.post('/tasks', data), remove: id => api.delete(`/tasks/${id}`) }
export const dashboardApi = { stats: () => api.get('/dashboard/stats'), recent: () => api.get('/dashboard/recent-activity') }
