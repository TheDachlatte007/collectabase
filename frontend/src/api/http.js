const ADMIN_KEY_STORAGE = 'collectabase.admin_api_key'

function readAdminApiKey() {
  if (typeof window === 'undefined') return ''
  try {
    return String(window.localStorage.getItem(ADMIN_KEY_STORAGE) || '').trim()
  } catch {
    return ''
  }
}

function withAdminHeaders(headers = {}) {
  const key = readAdminApiKey()
  if (!key) return { ...(headers || {}) }
  return { ...(headers || {}), 'X-Admin-Key': key }
}

async function parseJsonSafe(res) {
  try {
    return await res.json()
  } catch {
    return null
  }
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) return null
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1])
  const asciiMatch = disposition.match(/filename=\"?([^\";]+)\"?/i)
  return asciiMatch?.[1] || null
}

export async function apiGet(url) {
  const res = await fetch(url, { headers: withAdminHeaders() })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiDelete(url) {
  const res = await fetch(url, { method: 'DELETE', headers: withAdminHeaders() })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPost(url, body, options = {}) {
  const init = { method: 'POST', ...options }
  const customHeaders = withAdminHeaders(options.headers || {})
  if (body !== undefined) {
    init.headers = { 'Content-Type': 'application/json', ...customHeaders }
    init.body = JSON.stringify(body)
  } else if (Object.keys(customHeaders).length) {
    init.headers = customHeaders
  }
  const res = await fetch(url, init)
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPut(url, body) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...withAdminHeaders() },
    body: JSON.stringify(body)
  })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPostForm(url, formData) {
  const res = await fetch(url, { method: 'POST', headers: withAdminHeaders(), body: formData })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiDownload(url, fallbackFilename = 'download.bin') {
  const res = await fetch(url, { headers: withAdminHeaders() })
  if (!res.ok) {
    const data = await parseJsonSafe(res)
    return { ok: false, status: res.status, data }
  }

  const blob = await res.blob()
  const disposition = res.headers.get('content-disposition')
  const filename = getFilenameFromDisposition(disposition) || fallbackFilename
  const objectUrl = URL.createObjectURL(blob)
  try {
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    a.click()
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
  return { ok: true, status: res.status, data: { filename } }
}

export function getAdminApiKey() {
  return readAdminApiKey()
}

export function setAdminApiKey(value) {
  if (typeof window === 'undefined') return
  try {
    const cleaned = String(value || '').trim()
    if (cleaned) window.localStorage.setItem(ADMIN_KEY_STORAGE, cleaned)
    else window.localStorage.removeItem(ADMIN_KEY_STORAGE)
  } catch {
    // ignore storage errors
  }
}
