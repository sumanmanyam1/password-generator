// api.js — thin wrapper around the PassGen Flask API.
// Requests go to /api/* and Vite proxies them to http://127.0.0.1:5000.

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`)
  }
  return data
}

export const api = {
  health: () => request('/health'),

  generate: (body) =>
    request('/generate', { method: 'POST', body: JSON.stringify(body) }),

  bulk: (body) =>
    request('/bulk', { method: 'POST', body: JSON.stringify(body) }),

  analyze: (body) =>
    request('/analyze', { method: 'POST', body: JSON.stringify(body) }),

  list: () => request('/passwords'),

  reveal: (label) => request(`/passwords/${encodeURIComponent(label)}`),

  remove: (label) =>
    request(`/passwords/${encodeURIComponent(label)}`, { method: 'DELETE' }),
}
