import { apiDelete, apiDownload, apiGet, apiPost, apiPostForm, apiPut } from './http'

export const gamesApi = {
  list: (params = '') => apiGet(`/api/games${params}`),
  get: (id) => apiGet(`/api/games/${id}`),
  create: (payload, force = false) => apiPost(`/api/games${force ? '?force=true' : ''}`, payload),
  update: (id, payload) => apiPut(`/api/games/${id}`, payload),
  remove: (id) => apiDelete(`/api/games/${id}`),
  enrich: (id) => apiPost(`/api/games/${id}/enrich`),
  uploadCover: (formData) => apiPostForm('/api/upload/cover', formData)
}

export const platformsApi = {
  list: () => apiGet('/api/platforms')
}

export const lookupApi = {
  combined: (title) => apiPost('/api/lookup/combined', { title }),
  barcode: (barcode) => apiPost('/api/lookup/barcode', { barcode })
}

export const importApi = {
  csv: (formData) => apiPostForm('/api/import/csv', formData),
  clz: (formData) => apiPostForm('/api/import/clz', formData),
  exportCsv: () => apiDownload('/api/export/csv', 'collectabase_export.csv')
}

export const statsApi = {
  get: () => apiGet('/api/stats')
}

export const priceApi = {
  check: (id) => apiPost(`/api/games/${id}/fetch-market-price`),
  history: (id) => apiGet(`/api/games/${id}/price-history`),
  manual: (id, payload) => apiPost(`/api/games/${id}/price-manual`, payload),
  bulk: (limit) => apiPost(`/api/prices/update-all?limit=${limit}`)
}

export const settingsApi = {
  info: () => apiGet('/api/settings/info'),
  clearCovers: () => apiPost('/api/settings/clear-covers'),
  clearDatabase: () => apiDelete('/api/database/clear'),
  bulkEnrich: (limit) => apiPost(`/api/enrich/all?limit=${limit}`)
}

export const priceCatalogApi = {
  search: (params = '') => apiGet(`/api/price-catalog${params}`),
  platforms: () => apiGet('/api/price-catalog/platforms'),
  scrape: (platform = 'all') => apiPost(`/api/price-catalog/scrape?platform=${encodeURIComponent(platform)}`),
  clear: (platform = null) => apiDelete(`/api/price-catalog${platform ? `?platform=${encodeURIComponent(platform)}` : ''}`)
}
