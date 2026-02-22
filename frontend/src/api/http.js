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
  const res = await fetch(url)
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiDelete(url) {
  const res = await fetch(url, { method: 'DELETE' })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPost(url, body, options = {}) {
  const init = { method: 'POST', ...options }
  if (body !== undefined) {
    init.headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
    init.body = JSON.stringify(body)
  }
  const res = await fetch(url, init)
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPut(url, body) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiPostForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData })
  const data = await parseJsonSafe(res)
  return { ok: res.ok, status: res.status, data }
}

export async function apiDownload(url, fallbackFilename = 'download.bin') {
  const res = await fetch(url)
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
