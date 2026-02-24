<template>
  <div class="container">
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="!game" class="empty">
      <h3>Game not found</h3>
      <router-link to="/">Back to list</router-link>
    </div>

    <div v-else class="detail-layout">
      <div class="card cover-card">
        <div class="cover-large">
          <img v-if="currentCoverSrc" :src="currentCoverSrc" class="cover-image" @error="onDetailCoverError" />
          <span v-else>{{ coverEmoji(game?.item_type) }}</span>
          <button
            v-if="game.cover_url && !isSvgDataCover(game.cover_url)"
            @click="removeCover"
            class="cover-remove-btn"
            title="Remove cover"
          >✕</button>
        </div>
        <div v-if="game.current_value" class="value-badge">
          €{{ game.current_value }}
        </div>
        <div class="cover-upload-row">
          <input
            ref="coverFileInput"
            type="file"
            accept="image/*"
            capture="environment"
            style="display:none"
            @change="onCoverFileSelected"
          />
          <details ref="coverUploadMenu" class="cover-upload-menu">
            <summary class="btn btn-secondary cover-upload-btn" :class="{ disabled: coverUploading }">
              {{ coverUploading ? '⏳ Uploading...' : '📷 Cover Actions' }}
            </summary>
            <div class="cover-upload-menu-list">
              <button
                type="button"
                class="cover-upload-menu-item"
                @click="triggerCoverUpload"
                :disabled="coverUploading"
              >
                📷 Upload Photo
              </button>
              <button
                type="button"
                class="cover-upload-menu-item"
                @click="openCoverGallery"
                :disabled="coverUploading"
              >
                🖼 Galerie anschauen
              </button>
            </div>
          </details>
          <span v-if="coverUploadError" class="cover-upload-error">{{ coverUploadError }}</span>
        </div>
      </div>

      <div class="info-card">
        <div class="flex flex-between items-start mb-2">
          <div>
            <h1>{{ game.title }}</h1>
            <p class="text-muted">{{ game.platform_name }}</p>
          </div>
          <div class="actions actions-compact actions-toolbar">
            <router-link :to="`/edit/${game.id}`" class="btn btn-secondary btn-compact">Edit</router-link>
            <button @click="enrichCover" class="btn btn-secondary btn-compact" :disabled="enriching">
              {{ enriching ? '⏳ Fetching...' : '🖼 Enrich Cover' }}
            </button>
            <button @click="checkPrice" class="btn btn-secondary btn-compact" :disabled="priceLoading">
              {{ priceLoading ? '⏳ Fetching...' : '💰 Fetch Market Price' }}
            </button>
            <details class="more-menu">
              <summary class="btn btn-secondary btn-compact">⋯ More</summary>
              <div class="more-menu-list">
                <button type="button" class="more-menu-link more-menu-btn" @click="openPriceBrowserSearch">🔎 Open in Prices</button>
                <button type="button" class="more-menu-link more-menu-btn" @click="useConsolePlaceholder" :disabled="placeholderApplying">
                  {{ placeholderApplying ? '⏳ Applying...' : '🖼 Use Console Placeholder' }}
                </button>
                <a :href="ebayUrl()" target="_blank" rel="noopener" class="more-menu-link">🛒 eBay Sold</a>
                <a :href="priceChartingUrl()" target="_blank" rel="noopener" class="more-menu-link">📈 PriceCharting</a>
                <a :href="rawgUrl()" target="_blank" rel="noopener" class="more-menu-link">🎮 RAWG</a>
              </div>
            </details>
            <button @click="deleteGame" class="btn btn-danger btn-compact">Delete</button>
          </div>
        </div>

        <div class="details-grid">
          <div v-if="game.item_type" class="detail-item">
            <label>Type</label>
            <span>{{ game.item_type.charAt(0).toUpperCase() + game.item_type.slice(1) }}</span>
          </div>
          <div v-if="game.region" class="detail-item">
            <label>Region</label>
            <span>{{ game.region }}</span>
          </div>
          <div v-if="game.condition" class="detail-item">
            <label>Condition</label>
            <span>{{ game.condition }}</span>
          </div>
          <div v-if="game.completeness" class="detail-item">
            <label>Completeness</label>
            <span>{{ game.completeness }}</span>
          </div>
          <div v-if="game.barcode" class="detail-item">
            <label>Barcode</label>
            <span>{{ game.barcode }}</span>
          </div>
          <div v-if="game.purchase_price" class="detail-item">
            <label>Purchase Price</label>
            <span>€{{ game.purchase_price }}</span>
          </div>
          <div v-if="game.purchase_date" class="detail-item">
            <label>Purchase Date</label>
            <span>{{ game.purchase_date }}</span>
          </div>
          <div v-if="game.location" class="detail-item">
            <label>Location</label>
            <span>{{ game.location }}</span>
          </div>
          <div v-if="game.release_date" class="detail-item">
            <label>Release Date</label>
            <span>{{ game.release_date }}</span>
          </div>
          <div v-if="game.genre" class="detail-item">
            <label>Genre</label>
            <span>{{ game.genre }}</span>
          </div>
          <div v-if="game.developer" class="detail-item">
            <label>Developer</label>
            <span>{{ game.developer }}</span>
          </div>
          <div v-if="game.publisher" class="detail-item">
            <label>Publisher</label>
            <span>{{ game.publisher }}</span>
          </div>
          <div v-if="game.is_wishlist && game.wishlist_max_price" class="detail-item">
            <label>Max Wishlist Price</label>
            <span>€{{ game.wishlist_max_price }}</span>
          </div>
          <div v-if="game.current_value && game.purchase_price" class="detail-item">
            <label>Profit/Loss</label>
            <span :class="game.current_value >= game.purchase_price ? 'profit' : 'loss'">
              {{ game.current_value >= game.purchase_price ? '+' : '' }}€{{ (game.current_value - game.purchase_price).toFixed(2) }}
            </span>
          </div>
        </div>

        <div v-if="game.notes" class="notes mt-3">
          <label>Notes</label>
          <p>{{ game.notes }}</p>
        </div>
        <div v-if="game.description" class="notes mt-3">
          <label>Description</label>
          <p class="description-text" v-html="formattedDescription"></p>
        </div>

        <!-- Market Prices -->
        <div class="price-section mt-3">
          <label>Market Prices</label>
          <div v-if="latestPrice" class="price-cells">
            <div class="price-cell" :class="{ relevant: relevantKey() === 'loose' }">
              <span class="p-label">Loose</span>
              <span class="p-val">{{ latestPrice.loose_price != null ? '€' + latestPrice.loose_price.toFixed(2) : '—' }}</span>
            </div>
            <div class="price-cell" :class="{ relevant: relevantKey() === 'complete' }">
              <span class="p-label">CIB</span>
              <span class="p-val">{{ latestPrice.complete_price != null ? '€' + latestPrice.complete_price.toFixed(2) : '—' }}</span>
            </div>
            <div class="price-cell" :class="{ relevant: relevantKey() === 'new' }">
              <span class="p-label">New</span>
              <span class="p-val">{{ latestPrice.new_price != null ? '€' + latestPrice.new_price.toFixed(2) : '—' }}</span>
            </div>
          </div>
          <p v-else class="text-muted" style="margin:0.5rem 0 0">Add a price entry to start tracking.</p>
          <div v-if="latestPrice" class="price-meta">
            Last checked: {{ formatDate(latestPrice.fetched_at) }}
            <span :class="`source-pill source-${latestPrice.source}`">{{ latestPrice.source }}</span>
          </div>
          <div v-if="priceError" class="price-error">{{ priceError }}</div>
          <div v-if="priceError" class="price-catalog-help">
            <button class="btn btn-secondary btn-sm" @click="openPriceBrowserSearch">
              🔎 Select from Price Catalog
            </button>
          </div>
          <div class="start-value-row">
            <span class="text-muted">
              Start value:
              <strong>{{ startValue != null ? '€' + formatMoney(startValue) : '—' }}</strong>
            </span>
            <button class="btn btn-secondary btn-sm" @click="editStartValue">Update Start Value</button>
          </div>
          <div v-if="marketSuggestion" class="market-suggestion">
            <div v-if="marketSuggestion.source === 'pricecharting'" class="market-suggestion-text">
              📊 €{{ formatMoney(marketSuggestion.market_price) }} (PriceCharting - Loose)
              <div v-if="marketSuggestion.matched_title" class="market-match">
                Match: {{ marketSuggestion.matched_title }}
                <span v-if="marketSuggestion.matched_platform"> ({{ marketSuggestion.matched_platform }})</span>
                <span v-if="marketSuggestion.match_score != null"> · confidence {{ formatMatchScore(marketSuggestion.match_score) }}</span>
              </div>
            </div>
            <div v-else-if="marketSuggestion.source === 'ebay'" class="market-suggestion-text">
              🛒 ~€{{ formatMoney(marketSuggestion.market_price) }}
              (Median of {{ marketSuggestion.sample_size }} eBay listings, €{{ formatMoney(marketSuggestion.price_min) }}-€{{ formatMoney(marketSuggestion.price_max) }})
            </div>
            <div class="market-suggestion-actions">
              <button class="btn btn-secondary" @click="setMarketSuggestionAsCurrentValue" :disabled="settingSuggestedValue">
                {{ settingSuggestedValue ? 'Saving...' : 'Set as current value' }}
              </button>
              <button class="btn btn-secondary" @click="dismissMarketSuggestion">Dismiss</button>
            </div>
          </div>
          <div v-if="rawgReference" class="rawg-reference">
            <div class="rawg-title">RAWG reference links:</div>
            <a v-if="rawgReference.rawg_url" :href="rawgReference.rawg_url" target="_blank" rel="noopener" class="rawg-link">
              Open RAWG game page
            </a>
            <div v-if="rawgReference.store_links?.length" class="rawg-stores">
              <a
                v-for="(store, idx) in rawgReference.store_links"
                :key="`${store.url}-${idx}`"
                :href="store.url"
                target="_blank"
                rel="noopener"
                class="rawg-link"
              >
                {{ store.name || 'Store' }}
              </a>
            </div>
          </div>

          <!-- Price History Chart -->
          <div v-if="priceHistory.length >= 2" class="price-chart-wrapper mt-3">
            <canvas ref="priceChartEl"></canvas>
          </div>
          <p v-else-if="priceHistory.length === 1" class="text-muted price-chart-hint">
            Add one more entry to see the history chart.
          </p>

          <!-- Manual Entry -->
          <div class="manual-entry mt-3">
            <div class="manual-entry-label">Add Manual Entry</div>
            <div class="manual-entry-fields">
              <div class="manual-field">
                <span class="p-label">Loose (€)</span>
                <input v-model.number="manualEntry.loose_price" type="number" step="0.01" placeholder="—" />
              </div>
              <div class="manual-field">
                <span class="p-label">CIB (€)</span>
                <input v-model.number="manualEntry.complete_price" type="number" step="0.01" placeholder="—" />
              </div>
              <div class="manual-field">
                <span class="p-label">New (€)</span>
                <input v-model.number="manualEntry.new_price" type="number" step="0.01" placeholder="—" />
              </div>
              <button class="btn btn-secondary" @click="addManualEntry" :disabled="manualSaving">
                {{ manualSaving ? 'Saving...' : '+ Add Entry' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="coverGalleryOpen" class="cover-gallery-backdrop" @click.self="closeCoverGallery">
      <div class="cover-gallery-modal card">
        <div class="cover-gallery-header">
          <strong>Console Gallery</strong>
          <button type="button" class="cover-gallery-close" @click="closeCoverGallery">✕</button>
        </div>
        <input
          v-model.trim="coverGalleryFilter"
          class="search-input cover-gallery-search"
          placeholder="Filter gallery..."
        />
        <div v-if="coverGalleryLoading" class="text-muted">Loading gallery...</div>
        <div v-else-if="coverGalleryError" class="cover-upload-error">{{ coverGalleryError }}</div>
        <div v-else-if="filteredCoverGalleryItems.length === 0" class="text-muted">
          No images found.
        </div>
        <div v-else class="cover-gallery-grid">
          <button
            v-for="item in filteredCoverGalleryItems"
            :key="item.url"
            type="button"
            class="cover-gallery-item"
            @click="applyGalleryCover(item.url)"
            :disabled="coverGalleryApplying"
          >
            <img :src="item.url" :alt="item.name || item.filename || 'Cover image'" loading="lazy" />
            <span>{{ item.name || item.filename }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { gamesApi, lookupApi, priceApi } from '../api'
import { notifyError, notifySuccess } from '../composables/useNotifications'
import { coverEmoji, isSvgDataCover, makeFallbackCoverDataUrl, needsAutoCover } from '../utils/coverFallback'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Legend,
  Tooltip
} from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Legend, Tooltip)

const route = useRoute()
const router = useRouter()
const game = ref(null)
const loading = ref(true)
const enriching = ref(false)
const priceLoading = ref(false)
const priceHistory = ref([])
const priceError = ref('')
const marketSuggestion = ref(null)
const rawgReference = ref(null)
const settingSuggestedValue = ref(false)
const priceChartEl = ref(null)
const coverFileInput = ref(null)
const coverUploadMenu = ref(null)
const coverUploading = ref(false)
const coverUploadError = ref('')
const placeholderApplying = ref(false)
const coverGalleryOpen = ref(false)
const coverGalleryLoading = ref(false)
const coverGalleryApplying = ref(false)
const coverGalleryError = ref('')
const coverGalleryFilter = ref('')
const coverGalleryItems = ref([])
const manualEntry = ref({ loose_price: null, complete_price: null, new_price: null })
const manualSaving = ref(false)
const startValue = ref(null)
const coverHasError = ref(false)
const coverAutoFixing = ref(false)
const coverAutoEnrichTried = ref(false)
let chartInstance = null

const latestPrice = computed(() => priceHistory.value[0] ?? null)
const currentCoverSrc = computed(() => {
  if (!game.value) return null
  if (game.value.cover_url && !coverHasError.value) return game.value.cover_url
  if (needsAutoCover(game.value.item_type)) return makeFallbackCoverDataUrl(game.value)
  return null
})
const formattedDescription = computed(() => formatDescriptionHtml(game.value?.description || ''))
const filteredCoverGalleryItems = computed(() => {
  const query = normalizeSearch(coverGalleryFilter.value)
  if (!query) return coverGalleryItems.value
  return coverGalleryItems.value.filter((item) => {
    return normalizeSearch(item.name).includes(query) || normalizeSearch(item.filename).includes(query)
  })
})

function decodeHtmlEntities(input) {
  const area = document.createElement('textarea')
  area.innerHTML = String(input || '')
  return area.value
}

function normalizeDescriptionInput(input) {
  let text = decodeHtmlEntities(input || '').trim()
  if (!text) return ''

  text = text.replace(
    /<a\b[^>]*href=(["'])(https?:\/\/[^"']+)\1[^>]*>(.*?)<\/a>/gi,
    (_m, _q, href, label) => `${(label || href).trim()} (${href.trim()})`
  )
  text = text.replace(/<\/?br\s*\/?>/gi, '\n')
  return text
}

function normalizeSearch(value) {
  return String(value || '').trim().toLowerCase()
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function formatDescriptionHtml(input) {
  const normalized = normalizeDescriptionInput(input)
  if (!normalized) return ''

  const escaped = escapeHtml(normalized)
  const withBreaks = escaped.replace(/\r\n|\r|\n/g, '<br>')
  const urlRegex = /https?:\/\/[^\s<>"']*[^\s<>"'.,;:!?)]/gi
  return withBreaks.replace(urlRegex, (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`)
}

function formatChartDate(dt) {
  if (!dt) return ''
  // SQLite CURRENT_TIMESTAMP is "YYYY-MM-DD HH:MM:SS" — replace space with T for valid ISO 8601
  const d = new Date(typeof dt === 'string' ? dt.replace(' ', 'T') : dt)
  if (isNaN(d.getTime())) return String(dt)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yy = String(d.getFullYear()).slice(-2)
  return `${dd}.${mm}.${yy}`
}

function buildChart() {
  if (!priceChartEl.value) return
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  // priceHistory is ordered newest-first; reverse for chronological order on chart
  const ordered = [...priceHistory.value].reverse()
  const labels = ordered.map(r => formatChartDate(r.fetched_at))
  const datasets = [
    {
      label: 'Loose',
      data: ordered.map(r => r.loose_price),
      borderColor: '#60a5fa',
      backgroundColor: 'transparent',
      tension: 0.3,
      pointRadius: 4,
      spanGaps: true
    },
    {
      label: 'CIB',
      data: ordered.map(r => r.complete_price),
      borderColor: '#34d399',
      backgroundColor: 'transparent',
      tension: 0.3,
      pointRadius: 4,
      spanGaps: true
    },
    {
      label: 'New',
      data: ordered.map(r => r.new_price),
      borderColor: '#fb923c',
      backgroundColor: 'transparent',
      tension: 0.3,
      pointRadius: 4,
      spanGaps: true
    }
  ]
  if (startValue.value != null && Number.isFinite(Number(startValue.value))) {
    datasets.push({
      label: 'Start Value',
      data: labels.map(() => Number(startValue.value)),
      borderColor: '#facc15',
      backgroundColor: 'transparent',
      borderDash: [6, 4],
      tension: 0,
      pointRadius: 0
    })
  }

  chartInstance = new Chart(priceChartEl.value, {
    type: 'line',
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            footer(items) {
              const idx = items[0]?.dataIndex
              if (idx == null) return []
              const src = ordered[idx]?.source || ''
              const labels = { pricecharting: '📊 PriceCharting', manual: '✏️ Manual', ebay: '🛒 eBay' }
              return [labels[src] || src]
            }
          }
        }
      },
      scales: {
        x: { title: { display: false } },
        y: {
          title: { display: true, text: 'EUR' },
          beginAtZero: false
        }
      }
    }
  })
}

watch(
  () => priceHistory.value,
  async (newVal) => {
    if (newVal.length >= 2) {
      await nextTick()
      buildChart()
    } else {
      if (chartInstance) {
        chartInstance.destroy()
        chartInstance = null
      }
    }
  },
  { deep: true }
)

function relevantKey() {
  const c = (game.value?.completeness || '').toLowerCase()
  if (c.includes('new') || c.includes('sealed')) return 'new'
  if (c.includes('cib') || c.includes('complete') || c.includes('box')) return 'complete'
  return 'loose'
}

function ebayUrl() {
  const q = encodeURIComponent(`${game.value?.title || ''} ${game.value?.platform_name || ''}`)
  return `https://www.ebay.de/sch/i.html?_nkw=${q}&LH_Sold=1&LH_Complete=1`
}

function priceChartingUrl() {
  const q = encodeURIComponent(`${game.value?.title || ''} ${game.value?.platform_name || ''}`.trim())
  return `https://www.pricecharting.com/search-products?type=prices&q=${q}`
}

function rawgUrl() {
  const q = encodeURIComponent(`${game.value?.title || ''} ${game.value?.platform_name || ''}`.trim())
  return `https://rawg.io/search?query=${q}`
}

function openPriceBrowserSearch() {
  if (!game.value) return
  const query = {}
  const title = String(game.value.title || '').trim()
  const platform = String(game.value.platform_name || '').trim().toLowerCase()
  if (title) query.search = title
  if (platform) query.platform = platform
  if (game.value.id != null) query.linkGame = String(game.value.id)
  query.returnTo = `/game/${game.value.id}`
  router.push({ path: '/prices', query })
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(typeof dt === 'string' ? dt.replace(' ', 'T') : dt)
  if (isNaN(d.getTime())) return String(dt)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatMoney(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}

function formatMatchScore(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 'n/a'
  const percent = Math.max(0, Math.min(100, Math.round(num * 100)))
  return `${percent}%`
}

async function checkPrice() {
  priceLoading.value = true
  priceError.value = ''
  marketSuggestion.value = null
  rawgReference.value = null
  try {
    const res = await priceApi.check(route.params.id)
    const data = res.data || {}
    if (!res.ok) {
      priceError.value = data?.detail?.message || data?.detail || data?.error || 'Price check failed'
      notifyError(priceError.value)
      return
    }
    if (data.error) {
      if (data.source === 'rawg') {
        priceError.value = data.error
        rawgReference.value = data
      } else {
        priceError.value = data.error
      }
    } else {
      marketSuggestion.value = data
      await loadPriceHistory()
    }
  } catch (e) {
    priceError.value = 'Price check failed'
    console.error(e)
    notifyError('Price check failed.')
  } finally {
    priceLoading.value = false
  }
}

async function setMarketSuggestionAsCurrentValue() {
  if (!marketSuggestion.value || !game.value) return
  const marketPrice = Number(marketSuggestion.value.market_price)
  if (!Number.isFinite(marketPrice)) return

  settingSuggestedValue.value = true
  try {
    const res = await gamesApi.update(route.params.id, { ...game.value, current_value: marketPrice })
    if (res.ok) {
      game.value.current_value = marketPrice
      startValue.value = marketPrice
      marketSuggestion.value = null
      notifySuccess('Current value updated.')
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to set current value.')
    }
  } catch (e) {
    console.error('Failed setting current value:', e)
    notifyError('Failed to set current value.')
  } finally {
    settingSuggestedValue.value = false
  }
}

function dismissMarketSuggestion() {
  marketSuggestion.value = null
}

async function editStartValue() {
  if (!game.value) return
  const current = startValue.value != null ? String(startValue.value) : ''
  const raw = window.prompt('Enter start value (EUR)', current)
  if (raw == null) return

  const parsed = Number(raw.replace(',', '.'))
  if (!Number.isFinite(parsed) || parsed < 0) {
    notifyError('Please enter a valid number.')
    return
  }

  try {
    const res = await gamesApi.update(route.params.id, { ...game.value, current_value: parsed })
    if (!res.ok) {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to update start value.')
      return
    }
    game.value.current_value = parsed
    startValue.value = parsed
    notifySuccess('Start value updated.')
    if (priceHistory.value.length >= 2) {
      await nextTick()
      buildChart()
    }
  } catch (e) {
    console.error('Failed updating start value:', e)
    notifyError('Failed to update start value.')
  }
}

async function loadPriceHistory() {
  try {
    const res = await priceApi.history(route.params.id)
    if (res.ok) priceHistory.value = res.data || []
  } catch (e) {
    console.error('Failed to load price history:', e)
    notifyError('Failed to load price history.')
  }
}

async function enrichCover() {
  enriching.value = true
  try {
    const res = await gamesApi.enrich(route.params.id)
    if (res.ok) {
      notifySuccess('Cover enriched.')
      await loadGame()
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Could not enrich cover.')
    }
  } catch (e) {
    console.error('Enrich failed:', e)
    notifyError('Cover enrichment failed.')
  } finally {
    enriching.value = false
  }
}

async function useConsolePlaceholder() {
  if (!game.value) return
  placeholderApplying.value = true
  try {
    const res = await gamesApi.placeholderCover(route.params.id)
    if (!res.ok) {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Could not apply console placeholder.')
      return
    }
    const newUrl = res.data?.cover_url
    if (newUrl) {
      game.value.cover_url = newUrl
      coverHasError.value = false
    }
    notifySuccess('Console placeholder applied.')
  } catch (e) {
    console.error('Placeholder apply failed:', e)
    notifyError('Could not apply console placeholder.')
  } finally {
    placeholderApplying.value = false
  }
}

function hasMissingOrFallbackCover() {
  if (!game.value) return true
  const url = game.value.cover_url
  if (!url) return true
  return isSvgDataCover(url)
}

async function tryAutoEnrichNonGameCover() {
  if (!game.value || !needsAutoCover(game.value.item_type)) return false
  if (coverAutoEnrichTried.value) return false
  coverAutoEnrichTried.value = true

  try {
    const res = await gamesApi.enrich(route.params.id)
    const enriched = res.ok ? (res.data?.cover_url || null) : null
    if (enriched) {
      game.value.cover_url = enriched
      coverHasError.value = false
      return true
    }
  } catch (e) {
    console.warn('Auto enrich cover failed:', e)
  }
  return false
}

async function ensureNonGameCover() {
  if (!game.value || !needsAutoCover(game.value.item_type)) return
  if (coverAutoFixing.value) return
  if (!coverHasError.value && !hasMissingOrFallbackCover()) return

  coverAutoFixing.value = true
  try {
    const enriched = await tryAutoEnrichNonGameCover()
    if (enriched) return

    const fallback = makeFallbackCoverDataUrl(game.value)
    if (game.value.cover_url !== fallback) {
      const saved = await saveCoverUrl(fallback)
      if (saved) {
        game.value.cover_url = fallback
        coverHasError.value = false
      }
    } else {
      coverHasError.value = false
    }
  } finally {
    coverAutoFixing.value = false
  }
}

async function onDetailCoverError() {
  coverHasError.value = true
  await ensureNonGameCover()
}

async function loadGame() {
  try {
    const res = await gamesApi.get(route.params.id)
    if (res.ok) {
      game.value = res.data
      coverAutoEnrichTried.value = false
      coverHasError.value = false
      if (startValue.value == null) {
        const v = Number(game.value.current_value)
        startValue.value = Number.isFinite(v) ? v : null
      }
      await ensureNonGameCover()
    }
  } catch (e) {
    console.error('Failed to load game:', e)
    notifyError('Failed to load game.')
  } finally {
    loading.value = false
  }
}

async function deleteGame() {
  if (!confirm('Are you sure you want to delete this game?')) return

  try {
    const res = await gamesApi.remove(route.params.id)
    if (res.ok) {
      notifySuccess('Game deleted.')
      router.push('/')
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to delete game.')
    }
  } catch (e) {
    console.error('Failed to delete:', e)
    notifyError('Failed to delete game.')
  }
}

async function saveCoverUrl(url) {
  const res = await gamesApi.update(route.params.id, { ...game.value, cover_url: url })
  if (res.ok) {
    game.value.cover_url = url
    coverHasError.value = false
    return true
  }
  if (res.status !== 404) {
    const detail = res.data?.detail
    notifyError(detail?.message || detail || 'Failed to save cover.')
  }
  return false
}

function closeCoverUploadMenu() {
  if (coverUploadMenu.value?.open) {
    coverUploadMenu.value.open = false
  }
}

function triggerCoverUpload() {
  if (coverUploading.value) return
  closeCoverUploadMenu()
  coverFileInput.value?.click()
}

async function loadCoverGallery() {
  coverGalleryLoading.value = true
  coverGalleryError.value = ''
  try {
    const res = await lookupApi.consoleFallbacks()
    if (!res.ok) {
      const detail = res.data?.detail
      coverGalleryError.value = detail?.message || detail || 'Could not load gallery.'
      return
    }
    const items = Array.isArray(res.data?.items) ? res.data.items : []
    coverGalleryItems.value = items
  } catch (e) {
    console.error('Failed loading console gallery:', e)
    coverGalleryError.value = 'Could not load gallery.'
  } finally {
    coverGalleryLoading.value = false
  }
}

async function openCoverGallery() {
  closeCoverUploadMenu()
  coverGalleryOpen.value = true
  if (!coverGalleryItems.value.length) {
    await loadCoverGallery()
  }
}

function closeCoverGallery() {
  coverGalleryOpen.value = false
}

async function applyGalleryCover(url) {
  if (!url || coverGalleryApplying.value) return
  coverGalleryApplying.value = true
  try {
    const saved = await saveCoverUrl(url)
    if (saved) {
      notifySuccess('Cover set from gallery.')
      closeCoverGallery()
    }
  } finally {
    coverGalleryApplying.value = false
  }
}

async function onCoverFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  coverUploadError.value = ''
  if (file.size > 5 * 1024 * 1024) {
    coverUploadError.value = 'File exceeds 5 MB limit.'
    event.target.value = ''
    return
  }
  coverUploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await gamesApi.uploadCover(form)
    if (!res.ok) {
      const err = res.data || {}
      coverUploadError.value = err?.detail?.message || err?.detail || err?.error || 'Upload failed.'
      notifyError(coverUploadError.value)
      return
    }
    const { url } = res.data
    const saved = await saveCoverUrl(url)
    if (saved) notifySuccess('Cover uploaded.')
  } catch (e) {
    coverUploadError.value = 'Upload failed.'
    console.error(e)
    notifyError('Upload failed.')
  } finally {
    coverUploading.value = false
    event.target.value = ''
  }
}

async function removeCover() {
  const saved = await saveCoverUrl('')
  if (saved) notifySuccess('Cover removed.')
}

async function addManualEntry() {
  const { loose_price, complete_price, new_price } = manualEntry.value
  if (loose_price == null && complete_price == null && new_price == null) return
  manualSaving.value = true
  try {
    const res = await priceApi.manual(route.params.id, { loose_price, complete_price, new_price })
    if (res.ok) {
      manualEntry.value = { loose_price: null, complete_price: null, new_price: null }
      notifySuccess('Manual price entry added.')
      await loadPriceHistory()
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to save manual entry.')
    }
  } catch (e) {
    console.error('Failed to save manual entry:', e)
    notifyError('Failed to save manual entry.')
  } finally {
    manualSaving.value = false
  }
}

onMounted(async () => {
  await loadGame()
  await loadPriceHistory()
})
</script>

<style scoped>
.detail-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
}

@media (max-width: 768px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 639px) {
  /* Cap cover height so info section is visible without scrolling */
  .cover-large {
    max-height: 260px;
    font-size: 4rem;
  }

  /* Title + actions: stack on very small screens */
  .flex.flex-between.items-start {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.cover-card {
  position: relative;
}

.cover-large {
  aspect-ratio: 3/4;
  background: var(--bg);
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
  position: relative;
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: rgba(15, 23, 42, 0.55);
  display: block;
}

.cover-remove-btn {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  background: rgba(0,0,0,0.55);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.cover-upload-row {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.cover-upload-btn {
  width: 100%;
}

.cover-upload-menu {
  position: relative;
}

.cover-upload-menu > summary {
  list-style: none;
}

.cover-upload-menu > summary::-webkit-details-marker {
  display: none;
}

.cover-upload-menu > summary.disabled {
  opacity: 0.65;
  pointer-events: none;
}

.cover-upload-menu-list {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 0.35rem);
  z-index: 20;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.cover-upload-menu-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--text);
  font-size: 0.85rem;
  padding: 0.42rem 0.5rem;
  border-radius: 0.35rem;
  cursor: pointer;
}

.cover-upload-menu-item:hover {
  background: var(--bg-lighter);
}

.cover-upload-menu-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cover-upload-error {
  font-size: 0.8rem;
  color: #ef4444;
}

.value-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: var(--success);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: bold;
  font-size: 1.25rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  flex-shrink: 0;
  justify-content: flex-end;
}

.actions-toolbar {
  margin-left: auto;
  justify-content: flex-end;
  align-items: flex-start;
  align-content: flex-start;
  row-gap: 0.35rem;
  column-gap: 0.35rem;
  max-width: 760px;
}

.actions-toolbar .btn-compact {
  min-height: 28px !important;
  padding: 0.22rem 0.5rem !important;
  font-size: 0.72rem !important;
  gap: 0.28rem;
  line-height: 1.1;
  border-radius: 0.4rem;
  white-space: nowrap;
}

.items-start {
  align-items: flex-start;
}

.more-menu {
  position: relative;
}

.more-menu > summary {
  list-style: none;
}

.more-menu > summary::-webkit-details-marker {
  display: none;
}

.more-menu-list {
  position: absolute;
  right: 0;
  top: calc(100% + 0.35rem);
  min-width: 190px;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
  padding: 0.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  z-index: 25;
}

.more-menu-link {
  color: var(--text);
  text-decoration: none;
  font-size: 0.78rem;
  padding: 0.4rem 0.5rem;
  border-radius: 0.35rem;
}

.more-menu-link:hover {
  background: var(--bg-lighter);
}

.more-menu-btn {
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
}

.more-menu-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cover-gallery-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.72);
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 1rem;
}

.cover-gallery-modal {
  width: min(940px, 96vw);
  max-height: min(85vh, 900px);
  overflow: auto;
}

.cover-gallery-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.cover-gallery-close {
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  border-radius: 0.35rem;
  width: 30px;
  height: 30px;
  cursor: pointer;
}

.cover-gallery-search {
  margin-bottom: 0.75rem;
}

.cover-gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.65rem;
}

.cover-gallery-item {
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 0.45rem;
  overflow: hidden;
  text-align: left;
  padding: 0;
  color: var(--text);
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.cover-gallery-item img {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: contain;
  background: rgba(15, 23, 42, 0.7);
}

.cover-gallery-item span {
  font-size: 0.72rem;
  padding: 0.45rem 0.5rem 0.5rem;
  word-break: break-word;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.detail-item {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.5rem;
}

.detail-item label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.notes {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.5rem;
}

.notes label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.description-text {
  white-space: normal;
  line-height: 1.5;
  word-break: break-word;
}

.description-text :deep(a) {
  color: #93c5fd;
  text-decoration: underline;
}

.profit { color: var(--success); font-weight: bold; }
.loss { color: #ef4444; font-weight: bold; }

/* Price section */
.price-section {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.5rem;
}

.price-section > label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.price-cells {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.price-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.p-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.p-val {
  font-size: 1.4rem;
  font-weight: bold;
}

.price-cell.relevant .p-val {
  color: var(--success);
}

.price-meta {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.price-error {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #ef4444;
}

.price-catalog-help {
  margin-top: 0.45rem;
}

.price-warning {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #f59e0b;
}

.market-suggestion {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
}

.market-suggestion-text {
  font-size: 0.9rem;
}

.market-match {
  margin-top: 0.3rem;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.market-suggestion-actions {
  margin-top: 0.6rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.start-value-row {
  margin-top: 0.6rem;
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.rawg-reference {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
}

.rawg-title {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
}

.rawg-stores {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.4rem;
}

.rawg-link {
  color: #93c5fd;
  text-decoration: underline;
  font-size: 0.85rem;
}

.price-chart-wrapper {
  margin-top: 1rem;
}

.price-chart-hint {
  margin-top: 0.75rem;
  font-size: 0.8rem;
}

.source-pill {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-left: 0.4rem;
  vertical-align: middle;
}
.source-pill.source-pricecharting { background: rgba(96,165,250,0.15); color: #60a5fa; }
.source-pill.source-manual        { background: rgba(52,211,153,0.15);  color: #34d399; }
.source-pill.source-ebay          { background: rgba(251,146,60,0.15);  color: #fb923c; }

.manual-entry {
  border-top: 1px solid var(--border, rgba(255,255,255,0.08));
  padding-top: 0.75rem;
}

.manual-entry-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.manual-entry-fields {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.manual-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.manual-field input {
  width: 90px;
  padding: 0.35rem 0.5rem;
  font-size: 0.9rem;
}
</style>
