const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  // Taxonomy
  suggestTags: (q, exclude = []) => {
    const params = new URLSearchParams({ q, exclude: exclude.join(','), limit: 12 })
    return request(`/taxonomy/suggest?${params}`)
  },
  getTaxonomyTree: () => request('/taxonomy/tree'),
  createTaxonomyNode: (node) => request('/taxonomy/', { method: 'POST', body: JSON.stringify(node) }),

  // Documents
  createDocument: (doc) => request('/documents/', { method: 'POST', body: JSON.stringify(doc) }),
  deleteDocument: (id) => request(`/documents/${id}`, { method: 'DELETE' }),

  // Search
  search: ({ filters = [], q = '', size = 100 } = {}) => {
    const params = new URLSearchParams({
      filters: filters.join(','),
      q,
      size,
    })
    return request(`/search/?${params}`)
  },

  // Seed
  health: () => request('/health'),
}
