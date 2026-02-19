const CACHE_NAME = 'collectabase-v1'
const STATIC_ASSETS = ['/', '/index.html']

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  )
})

self.addEventListener('fetch', e => {
  // API calls niemals cachen
  if (e.request.url.includes('/api/')) return

  e.respondWith(
    caches.match(e.request).then(cached => {
      return cached || fetch(e.request)
    })
  )
})
