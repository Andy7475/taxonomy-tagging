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
  browseTags: (exclude = []) => {
    const params = new URLSearchParams({ exclude: exclude.join(',') })
    return request(`/taxonomy/browse?${params}`)
  },
  getTaxonomyTree: () => request('/taxonomy/tree'),
  createTaxonomyNode: (node) => request('/taxonomy/', { method: 'POST', body: JSON.stringify(node) }),

  // Documents
  createDocument: (doc) => request('/documents/', { method: 'POST', body: JSON.stringify(doc) }),
  getDocument: (id) => request(`/documents/${id}`),
  deleteDocument: (id) => request(`/documents/${id}`, { method: 'DELETE' }),

  // Search
  search: ({ andFilters = [], orFilters = [], notFilters = [], q = '', size = 100 } = {}) => {
    const params = new URLSearchParams({
      filters: andFilters.join(','),
      or_filters: orFilters.join(','),
      exclude: notFilters.join(','),
      q,
      size,
    })
    return request(`/search/?${params}`)
  },

  // Seed
  health: () => request('/health'),

  // Locations
  suggestLocations: (q, exclude = []) => {
    const params = new URLSearchParams({ q, exclude: exclude.join(','), limit: 12 })
    return request(`/locations/suggest?${params}`)
  },
  browseLocations: (exclude = []) => {
    const params = new URLSearchParams({ exclude: exclude.join(',') })
    return request(`/locations/browse?${params}`)
  },
  resolveLocation: (uri) => {
    const params = new URLSearchParams({ uri })
    return request(`/locations/resolve?${params}`)
  },
  ingestLocations: () => request('/locations/ingest', { method: 'POST' }),

  // Maintenance issues
  createMaintenanceIssue: (issue) =>
    request('/maintenance-issues/', { method: 'POST', body: JSON.stringify(issue) }),
  listMaintenanceIssues: ({ under = '' } = {}) => {
    const params = new URLSearchParams({ under })
    return request(`/maintenance-issues/?${params}`)
  },
  deleteMaintenanceIssue: (id) => request(`/maintenance-issues/${id}`, { method: 'DELETE' }),
}
