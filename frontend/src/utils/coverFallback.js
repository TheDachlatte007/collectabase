function escapeXml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function coverColors(type) {
  const t = String(type || '').toLowerCase()
  if (t === 'console') return { bg: '#1d4ed8', bg2: '#1e293b' }
  if (t === 'accessory') return { bg: '#c2410c', bg2: '#1e293b' }
  if (t === 'misc') return { bg: '#0f766e', bg2: '#1e293b' }
  return { bg: '#475569', bg2: '#1e293b' }
}

export function coverEmoji(type) {
  const t = String(type || '').toLowerCase()
  if (t === 'console') return '🖥️'
  if (t === 'accessory') return '🕹️'
  if (t === 'misc') return '📦'
  return '🎮'
}

export function needsAutoCover(type) {
  const t = String(type || '').toLowerCase()
  return t === 'console' || t === 'accessory'
}

export function isSvgDataCover(url) {
  return typeof url === 'string' && url.startsWith('data:image/svg+xml')
}

export function makeFallbackCoverDataUrl(item = {}) {
  const title = escapeXml(item.title || 'Collection Item')
  const platform = escapeXml(item.platform_name || item.platform || '')
  const type = String(item.item_type || '').toLowerCase()
  const { bg, bg2 } = coverColors(type)
  const typeLabel = type ? type.toUpperCase() : 'ITEM'
  const icon = escapeXml(coverEmoji(type))
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="${bg}"/>
<stop offset="100%" stop-color="${bg2}"/>
</linearGradient>
</defs>
<rect width="600" height="800" fill="url(#g)"/>
<rect x="34" y="34" width="532" height="732" rx="22" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
<text x="300" y="150" text-anchor="middle" fill="#f8fafc" font-size="84">${icon}</text>
<text x="300" y="230" text-anchor="middle" fill="#f1f5f9" font-family="Segoe UI, Arial, sans-serif" font-size="28" font-weight="700">${escapeXml(typeLabel)}</text>
<text x="300" y="300" text-anchor="middle" fill="#e2e8f0" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="700">${title.slice(0, 30)}</text>
<text x="300" y="344" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Arial, sans-serif" font-size="20">${platform.slice(0, 38)}</text>
</svg>`
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}
