import { apiDelete, apiDownload, apiGet, apiPost, apiPostForm, apiPut } from './http'

export const gamesApi = {
  list: (params = '') => apiGet(`/api/games${params}`),
  get: (id) => apiGet(`/api/games/${id}`),
  create: (payload, force = false) => apiPost(`/api/games${force ? '?force=true' : ''}`, payload),
  update: (id, payload) => apiPut(`/api/games/${id}`, payload),
  remove: (id) => apiDelete(`/api/games/${id}`),
  enrich: (id) => apiPost(`/api/games/${id}/enrich`),
  placeholderCover: (id) => apiPost(`/api/games/${id}/cover-placeholder`),
  uploadCover: (formData) => apiPostForm('/api/upload/cover', formData),
  getImages: (id) => apiGet(`/api/games/${id}/images`),
  uploadImage: (id, payload) => apiPost(`/api/games/${id}/images`, payload),
  deleteImage: (id, imageId) => apiDelete(`/api/games/${id}/images/${imageId}`),
  setPrimaryImage: (id, imageId) => apiPost(`/api/games/${id}/images/${imageId}/primary`)
}

export const platformsApi = {
  list: () => apiGet('/api/platforms')
}

export const lookupApi = {
  combined: (title) => apiPost('/api/lookup/combined', { title }),
  comicvine: (title) => apiPost('/api/lookup/comicvine', { title }),
  hobbydb: (title) => apiPost('/api/lookup/hobbydb', { title }),
  mfc: (title) => apiPost('/api/lookup/mfc', { title }),
  barcode: (barcode) => apiPost('/api/lookup/barcode', { barcode }),
  consoleFallbacks: () => apiGet('/api/console-fallbacks')
}

export const importApi = {
  csv: (formData) => apiPostForm('/api/import/csv', formData),
  clz: (formData) => apiPostForm('/api/import/clz', formData),
  exportCsv: () => apiDownload('/api/export/csv', 'collectabase_export.csv')
}

export const statsApi = {
  get: () => apiGet('/api/stats'),
  getHistory: (days) => apiGet(`/api/stats/history${days ? `?days=${days}` : ''}`)
}

export const priceApi = {
  check: (id, source = null) => apiPost(`/api/games/${id}/fetch-market-price${source ? `?source=${source}` : ''}`),
  history: (id) => apiGet(`/api/games/${id}/price-history`),
  manual: (id, payload) => apiPost(`/api/games/${id}/price-manual`, payload),
  deleteHistory: (id, entryId) => apiDelete(`/api/games/${id}/price-history/${entryId}`),
  applyCatalog: (id, catalogId) => apiPost(`/api/games/${id}/price-from-catalog`, { catalog_id: catalogId }),
  bulk: (limit) => apiPost(`/api/prices/update-all?limit=${limit}`)
}

export const settingsApi = {
  info: () => apiGet('/api/settings/info'),
  updateSecrets: (payload) => apiPost('/api/settings/secrets', payload),
  updateScheduler: (payload) => apiPost('/api/settings/scheduler', payload),
  clearCovers: () => apiPost('/api/settings/clear-covers'),
  clearDatabase: () => apiDelete('/api/database/clear'),
  bulkEnrich: (limit) => apiPost(`/api/enrich/all?limit=${limit}`)
}

export const priceCatalogApi = {
  search: (params = '') => apiGet(`/api/price-catalog${params}`),
  platforms: () => apiGet('/api/price-catalog/platforms'),
  enrichLibrary: (limit = 120) => apiPost(`/api/price-catalog/enrich-library?limit=${limit}`),
  scrape: (platform = 'all', q = '') => {
    const params = new URLSearchParams()
    if (platform) params.set('platform', platform)
    if (q) params.set('q', q)
    const query = params.toString()
    return apiPost(`/api/price-catalog/scrape${query ? `?${query}` : ''}`)
  },
  clear: (platform = null) => apiDelete(`/api/price-catalog${platform ? `?platform=${encodeURIComponent(platform)}` : ''}`)
}

export const lotsApi = {
  list: () => apiGet('/api/lots'),
  get: (id) => apiGet(`/api/lots/${id}`),
  create: (payload) => apiPost('/api/lots', payload),
  update: (id, payload) => apiPut(`/api/lots/${id}`, payload),
  remove: (id) => apiDelete(`/api/lots/${id}`),
  addItem: (lotId, payload) => apiPost(`/api/lots/${lotId}/items`, payload),
  updateItem: (lotId, itemId, payload) => apiPut(`/api/lots/${lotId}/items/${itemId}`, payload),
  deleteItem: (lotId, itemId) => apiDelete(`/api/lots/${lotId}/items/${itemId}`),
  saveSale: (itemId, payload) => apiPost(`/api/lots/items/${itemId}/sale`, payload),
  deleteSale: (itemId) => apiDelete(`/api/lots/items/${itemId}/sale`)
}
