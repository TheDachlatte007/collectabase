<template>
  <div class="container">
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="!game" class="empty">
      <h3>Game not found</h3>
      <router-link to="/">Back to list</router-link>
    </div>

    <div v-else class="detail-layout">
      <!-- LEFT COLUMN -->
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
            <summary class="btn btn-secondary cover-upload-btn focus-ring" :class="{ disabled: coverUploading }">
              {{ coverUploading ? '⏳ Uploading...' : '📷 Cover Actions ▼' }}
            </summary>
            <div class="cover-upload-menu-list">
              <button type="button" class="cover-upload-menu-item" @click="triggerCoverUpload" :disabled="coverUploading">
                📷 Upload Photo...
              </button>
              <button type="button" class="cover-upload-menu-item" @click="openCoverGallery" :disabled="coverUploading">
                🖼 Choose from Gallery...
              </button>
              <hr class="more-menu-divider" />
              <button type="button" class="cover-upload-menu-item" @click="enrichCover" :disabled="enriching">
                {{ enriching ? '⏳ Fetching...' : '🪄 Auto-Fetch Cover' }}
              </button>
              <button type="button" class="cover-upload-menu-item" @click="useConsolePlaceholder" :disabled="placeholderApplying">
                {{ placeholderApplying ? '⏳ Applying...' : '📦 Use Console Logo' }}
              </button>
            </div>
          </details>
          <span v-if="coverUploadError" class="cover-upload-error">{{ coverUploadError }}</span>
        </div>
      </div>

      <!-- RIGHT COLUMN -->
      <div class="info-layout">
        <div class="flex flex-between items-start mb-2 detail-header">
          <div class="detail-title-block">
            <h1>{{ game.title }}</h1>
            <p class="text-muted">{{ game.platform_name }}</p>
          </div>
          <div class="actions actions-compact actions-toolbar">
            <router-link :to="`/edit/${game.id}`" class="btn btn-primary btn-compact">Edit</router-link>
            <details class="more-menu">
              <summary class="btn btn-secondary btn-compact more-trigger" aria-label="More actions" title="More actions">⋮</summary>
              <div class="more-menu-list">
                <button type="button" class="more-menu-link more-menu-btn" @click="openPriceBrowserSearch">🔎 Open in Price Browser</button>
                <a :href="ebayUrl()" target="_blank" rel="noopener" class="more-menu-link">🛒 eBay Sold Items</a>
                <a :href="priceChartingUrl()" target="_blank" rel="noopener" class="more-menu-link">📈 PriceCharting Page</a>
                <a :href="rawgUrl()" target="_blank" rel="noopener" class="more-menu-link">🎮 RAWG Database</a>
                <hr class="more-menu-divider" />
                <button type="button" class="more-menu-link more-menu-btn text-danger" @click="deleteGame">🗑 Delete Game</button>
              </div>
            </details>
          </div>
        </div>

        <div class="info-cards-container">
          <!-- METADATA CARD -->
          <div class="chunk-card">
            <h3 class="chunk-title">Metadata</h3>
            <div class="details-grid">
              <div v-if="game.item_type" class="detail-item">
                <label>Type</label>
                <span>{{ game.item_type.charAt(0).toUpperCase() + game.item_type.slice(1) }}</span>
              </div>
              <div v-if="game.region" class="detail-item">
                <label>Region</label>
                <span>{{ game.region }}</span>
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
            </div>
          </div>

          <!-- MY COPY CARD -->
          <div class="chunk-card">
            <h3 class="chunk-title">My Copy</h3>
            <div class="details-grid">
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
              <div v-if="game.location" class="detail-item">
                <label>Location</label>
                <span>{{ game.location }}</span>
              </div>
              <div v-if="game.purchase_date" class="detail-item">
                <label>Purchase Date</label>
                <span>{{ game.purchase_date }}</span>
              </div>
              <div v-if="game.purchase_price" class="detail-item">
                <label>Purchase Price</label>
                <span>€{{ game.purchase_price }}</span>
              </div>
              <div v-if="game.current_value && game.purchase_price" class="detail-item detail-item-pl">
                <label>Profit / Loss</label>
                <span class="pl-pill" :class="game.current_value >= game.purchase_price ? 'profit' : 'loss'">
                  {{ game.current_value >= game.purchase_price ? '↑' : '↓' }}
                  €{{ Math.abs(game.current_value - game.purchase_price).toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="game.notes" class="notes mt-3 card">
          <label>Personal Notes</label>
          <p>{{ game.notes }}</p>
        </div>
        <div v-if="game.description" class="notes mt-3 card">
          <label>Description</label>
          <p class="description-text" v-html="formattedDescription"></p>
        </div>

        <!-- MARKET PRICES -->
        <div class="price-section card mt-3">
          <div class="price-section-header flex flex-between items-center mb-2">
            <h3 class="chunk-title m-0">Market Prices</h3>
            <div class="actions-compact">
              <button @click="checkPrice" class="btn btn-secondary btn-sm" :disabled="priceLoading">
                {{ priceLoading ? '⏳' : '📊 PriceCharting' }}
              </button>
              <button @click="checkPriceEbay" class="btn btn-secondary btn-sm" :disabled="priceLoading">
                {{ priceLoading ? '⏳' : '🛒 eBay' }}
              </button>
            </div>
          </div>

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
          <div v-if="latestPrice" class="price-meta mt-2">
            Last checked: {{ formatDate(latestPrice.fetched_at) }}
            <span :class="`source-pill source-${latestPrice.source}`">{{ latestPrice.source }}</span>
          </div>

          <div v-if="priceError" class="price-error mt-2">{{ priceError }}</div>
          <div v-if="priceError" class="price-catalog-help mt-1">
            <button class="btn btn-secondary btn-sm" @click="openPriceBrowserSearch">
              🔎 Select from Price Catalog
            </button>
          </div>

          <div class="start-value-row mt-3 pt-2">
            <span class="text-muted">
              Start value:
              <strong>{{ startValue != null ? '€' + formatMoney(startValue) : '—' }}</strong>
            </span>
            <button class="btn btn-secondary btn-sm" @click="editStartValue">Update Base Line</button>
          </div>

          <div v-if="marketSuggestion" class="market-suggestion mt-2">
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
            <div class="market-suggestion-actions mt-2">
              <button class="btn btn-primary btn-sm" @click="setMarketSuggestionAsCurrentValue" :disabled="settingSuggestedValue">
                {{ settingSuggestedValue ? 'Saving...' : 'Set as current value' }}
              </button>
              <button class="btn btn-secondary btn-sm" @click="dismissMarketSuggestion">Dismiss</button>
            </div>
          </div>

          <div v-if="rawgReference" class="rawg-reference mt-3">
            <div class="rawg-title text-muted mb-1">RAWG reference links:</div>
            <div class="flex gap-2 flex-wrap">
              <a v-if="rawgReference.rawg_url" :href="rawgReference.rawg_url" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">
                🎮 RAWG.io Game Page
              </a>
              <a
                v-for="(store, idx) in rawgReference.store_links"
                :key="`${store.url}-${idx}`"
                :href="store.url"
                target="_blank"
                rel="noopener"
                class="btn btn-secondary btn-sm"
              >
                {{ store.name || 'Store' }}
              </a>
            </div>
          </div>

          <!-- Price History Chart -->
          <div v-if="priceHistory.length >= 2" class="price-chart-wrapper mt-3">
            <canvas ref="priceChartEl"></canvas>
          </div>
          <!-- Empty State Chart Info -->
          <div v-else class="empty-chart-state mt-4">
            <div class="icon">📈</div>
            <h4>No Price Trends Yet</h4>
            <p>Fetch the market price directly above to start charting the value of your game over time.</p>
          </div>
          
          <details class="advanced-price-tools mt-4">
            <summary class="text-muted text-sm cursor-pointer hover:text-white transition">Show Advanced Entry Options</summary>
            
            <!-- Manual Entry -->
            <div class="manual-entry mt-3 p-3">
              <div class="manual-entry-label mb-2">Add Manual Price Point</div>
              <div class="manual-entry-fields">
                <div class="manual-field">
                  <span class="p-label text-xs">Loose (€)</span>
                  <input v-model.number="manualEntry.loose_price" type="number" step="0.01" class="search-input py-1 px-2" placeholder="—" />
                </div>
                <div class="manual-field">
                  <span class="p-label text-xs">CIB (€)</span>
                  <input v-model.number="manualEntry.complete_price" type="number" step="0.01" class="search-input py-1 px-2" placeholder="—" />
                </div>
                <div class="manual-field">
                  <span class="p-label text-xs">New (€)</span>
                  <input v-model.number="manualEntry.new_price" type="number" step="0.01" class="search-input py-1 px-2" placeholder="—" />
                </div>
                <button class="btn btn-primary" @click="addManualEntry" :disabled="manualSaving">
                  {{ manualSaving ? 'Saving...' : '+ Add' }}
                </button>
              </div>
            </div>

            <div v-if="priceHistory.length" class="price-history-list mt-3">
              <div class="manual-entry-label text-sm mb-2">Recent History Log</div>
              <div
                v-for="entry in recentPriceEntries"
                :key="entry.id"
                class="price-history-row rounded p-2 mb-1"
                style="background: rgba(255,255,255,0.03);"
              >
                <div class="price-history-main">
                  <span class="text-xs text-muted">{{ formatDate(entry.fetched_at) }}</span>
                  <span :class="`source-pill source-${entry.source} text-xs ml-2`">{{ entry.source }}</span>
                  <span class="ml-auto text-sm font-semibold">{{ entryDisplayValue(entry) }}</span>
                </div>
                <button
                  class="btn btn-danger btn-sm ml-3"
                  :disabled="deletingEntryId === entry.id"
                  @click="removePriceEntry(entry)"
                >
                  ✕
                </button>
              </div>
            </div>
          </details>

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
const deletingEntryId = ref(null)
const startValue = ref(null)
const coverHasError = ref(false)
const coverAutoFixing = ref(false)
const coverAutoEnrichTried = ref(false)
let chartInstance = null

const latestPrice = computed(() => priceHistory.value[0] ?? null)
const recentPriceEntries = computed(() => priceHistory.value.slice(0, 10))
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

function formatDescriptionHtml(input) {
  let text = String(input || '').trim()
  if (!text) return ''

  // Support basic markdown links [text](url) -> <a href="url" target="_blank" rel="noopener">text</a>
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')

  // Convert raw URLs to links (if they are not already inside an href="...")
  const urlRegex = /(?<!href=["'])(https?:\/\/[^\s<>"'()]+)(?![^<]*>|[^<>]*<\/a>)/gi
  text = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')

  // Convert pure linebreaks to <br> if they aren't part of existing HTML blocks
  text = text.replace(/(?:\r\n|\r|\n)/g, '<br>')

  return text
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
              const labels = { pricecharting: '📊 PriceCharting', manual: '✏️ Manual', ebay: '🛒 eBay', 'Start Value': '💰 Start Value' }
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


function entryDisplayValue(entry) {
  if (!entry) return '—'
  if (entry.loose_price != null) return `Loose €${formatMoney(entry.loose_price)}`
  if (entry.complete_price != null) return `CIB €${formatMoney(entry.complete_price)}`
  if (entry.new_price != null) return `New €${formatMoney(entry.new_price)}`
  return '—'
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

async function checkPriceEbay() {
  priceLoading.value = true
  priceError.value = ''
  marketSuggestion.value = null
  rawgReference.value = null
  try {
    const res = await priceApi.check(route.params.id, 'ebay')
    const data = res.data || {}
    if (!res.ok) {
      priceError.value = data?.detail?.message || data?.detail || data?.error || 'eBay price check failed'
      notifyError(priceError.value)
      return
    }
    if (data.error) {
      priceError.value = data.error
    } else {
      marketSuggestion.value = data
      await loadPriceHistory()
    }
  } catch (e) {
    priceError.value = 'eBay price check failed'
    console.error(e)
    notifyError('eBay price check failed.')
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
    if (res.ok) {
      const history = res.data || []
      // Prepend the initial purchase price (startValue) as the oldest record
      // so the chart has a baseline instantly.
      if (startValue.value != null && Number.isFinite(Number(startValue.value))) {
        history.push({
          id: 'base-price',
          source: 'Start Value',
          loose_price: Number(startValue.value),
          complete_price: Number(startValue.value),
          new_price: Number(startValue.value),
          fetched_at: game.value?.purchase_date || game.value?.created_at || new Date(0).toISOString()
        })
      }
      priceHistory.value = history
    }
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

async function removePriceEntry(entry) {
  if (!entry?.id) return
  if (!confirm('Delete this price entry?')) return

  deletingEntryId.value = entry.id
  try {
    const res = await priceApi.deleteHistory(route.params.id, entry.id)
    if (!res.ok) {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to delete price entry.')
      return
    }
    notifySuccess('Price entry removed.')
    await loadPriceHistory()
  } catch (e) {
    console.error('Failed to delete price entry:', e)
    notifyError('Failed to delete price entry.')
  } finally {
    deletingEntryId.value = null
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
  .detail-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.cover-card {
  position: relative;
  z-index: 2;
  border-radius: 1rem;
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--card-blur);
  -webkit-backdrop-filter: var(--card-blur);
  box-shadow: var(--glass-shadow);
  padding: 1rem;
  background: var(--bg-light);
}

.cover-large {
  aspect-ratio: 3/4;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.05), rgba(0, 0, 0, 0.4));
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: transparent;
  display: block;
}

.cover-remove-btn {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(8px);
  color: #fff;
  border: 1px solid var(--glass-border);
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: all 0.2s;
}

.cover-remove-btn:hover {
  background: rgba(239, 68, 68, 0.8);
  transform: scale(1.1);
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

.actions-toolbar > * {
  min-width: 0;
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

.detail-title-block {
  min-width: 0;
}

.detail-title-block h1 {
  overflow-wrap: anywhere;
  line-height: 1.2;
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

.more-trigger {
  min-width: 2rem;
  justify-content: center;
  font-size: 0.9rem !important;
  padding-inline: 0.35rem !important;
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
  max-width: min(88vw, 280px);
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

.info-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0; 
}

.info-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.chunk-card {
  background: var(--bg-light);
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: var(--card-blur);
  -webkit-backdrop-filter: var(--card-blur);
  box-shadow: var(--glass-shadow);
}

.chunk-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text);
  margin-top: 0;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--glass-border);
  letter-spacing: -0.01em;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.85rem;
}

.detail-item {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
  padding: 0.85rem;
  border-radius: 0.75rem;
  min-width: 0;
  overflow-wrap: anywhere;
  transition: transform 0.2s, background 0.2s;
}

.detail-item:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--glass-border-hover);
}

.detail-item label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.detail-item-pl {
  background: transparent !important;
  border: none !important;
  padding: 0.85rem 0 !important;
}

.detail-item-pl span {
  font-size: 1.15rem;
}

.pl-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.85rem;
  border-radius: 2rem;
  font-weight: 700;
  margin-top: 0.25rem;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}

.pl-pill.profit {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  box-shadow: 0 0 12px rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.pl-pill.loss {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.notes {
  background: var(--bg-light);
  border: 1px solid var(--glass-border);
  padding: 1.25rem;
  border-radius: 1rem;
  backdrop-filter: var(--card-blur);
  -webkit-backdrop-filter: var(--card-blur);
  box-shadow: var(--glass-shadow);
}

.notes label {
  display: block;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--glass-border);
  letter-spacing: -0.01em;
}

.description-text {
  white-space: normal;
  line-height: 1.6;
  word-break: break-word;
  color: rgba(255,255,255,0.85);
}

.description-text :deep(a) {
  color: #93c5fd;
  text-decoration: underline;
}

.empty-chart-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  text-align: center;
  background: rgba(0, 0, 0, 0.2);
  border: 1px dashed var(--glass-border);
  border-radius: 0.75rem;
}

.empty-chart-state .icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  filter: drop-shadow(0 0 8px rgba(255,255,255,0.2));
}

.empty-chart-state h4 {
  font-size: 1.1rem;
  margin: 0 0 0.5rem 0;
  color: var(--text);
}

.empty-chart-state p {
  font-size: 0.85rem;
  color: var(--text-muted);
  max-width: 320px;
  margin: 0;
  line-height: 1.4;
}

/* Price section */
.price-section {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
  padding: 1rem;
  border-radius: 0.75rem;
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
  min-width: 0;
}

.manual-field input {
  width: 90px;
  padding: 0.35rem 0.5rem;
  font-size: 0.9rem;
}

.price-history-list {
  border-top: 1px solid var(--border, rgba(255,255,255,0.08));
  padding-top: 0.75rem;
}

.price-history-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
  border-bottom: 1px dashed var(--border, rgba(255,255,255,0.08));
}

.price-history-row:last-child {
  border-bottom: 0;
}

.price-history-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.45rem;
  min-width: 0;
}

.price-history-date {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.price-history-value {
  font-size: 0.85rem;
}

@media (max-width: 639px) {
  .value-badge {
    top: 0.6rem;
    right: 0.6rem;
    font-size: 1rem;
    padding: 0.35rem 0.7rem;
  }

  .actions-toolbar {
    margin-left: 0;
    max-width: none;
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .actions-toolbar .btn-compact,
  .actions-toolbar > .btn,
  .actions-toolbar > .more-menu {
    width: 100%;
    min-height: 34px !important;
    justify-content: center;
    text-align: center;
    white-space: normal;
  }

  .actions-toolbar > .btn-danger {
    grid-column: span 2;
  }

  .more-menu {
    width: 100%;
  }

  .more-menu > summary {
    width: 100%;
    display: inline-flex;
  }

  .more-menu-list {
    left: 0;
    right: 0;
    min-width: 0;
    max-width: none;
    width: 100%;
  }

  .details-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .detail-item {
    padding: 0.8rem;
  }

  .price-cells {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.5rem;
  }

  .price-cell {
    min-width: 0;
  }

  .p-val {
    font-size: 1.05rem;
  }

  .start-value-row {
    flex-direction: column;
    align-items: stretch;
  }

  .start-value-row .btn {
    width: 100%;
  }

  .market-suggestion-actions {
    flex-direction: column;
  }

  .market-suggestion-actions .btn {
    width: 100%;
  }

  .manual-entry-fields {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.6rem;
    align-items: stretch;
  }

  .manual-field input {
    width: 100%;
  }

  .manual-entry-fields > .btn {
    grid-column: span 2;
    width: 100%;
  }

  .price-history-row {
    flex-direction: column;
    align-items: stretch;
  }

  .price-history-row .btn {
    width: 100%;
  }
}
</style>
