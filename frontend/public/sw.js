const CACHE_NAME = 'collectabase-v2'

// On install: take control immediately and pre-cache the shell
self.addEventListener('install', e => {
  self.skipWaiting()
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(['/', '/index.html']))
  )
})

// On activate: delete any old caches and claim clients right away
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', e => {
  const { request } = e
  const url = new URL(request.url)

  // Never intercept API calls — always go to network
  if (url.pathname.startsWith('/api/')) return

  // Only handle same-origin GET requests
  if (request.method !== 'GET' || url.origin !== self.location.origin) return

  // Navigation requests (HTML pages): network first, fall back to cached index.html
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request).catch(() => caches.match('/index.html'))
    )
    return
  }

  // Static assets (JS, CSS, images): cache first, update cache in background
  e.respondWith(
    caches.open(CACHE_NAME).then(async cache => {
      const cached = await cache.match(request)
      const networkPromise = fetch(request).then(response => {
        if (response.ok) cache.put(request, response.clone())
        return response
      })
      return cached ?? networkPromise
    })
  )
})
