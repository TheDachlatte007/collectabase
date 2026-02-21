<template>
  <div class="container">
    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="!game" class="empty">
      <h3>Game not found</h3>
      <router-link to="/">Back to list</router-link>
    </div>

    <div v-else class="detail-layout">
      <div class="card cover-card">
        <div class="cover-large" :style="coverStyle(game.cover_url)">
          <span v-if="!game.cover_url">🎮</span>
        </div>
        <div v-if="game.current_value" class="value-badge">
          €{{ game.current_value }}
        </div>
      </div>

      <div class="info-card">
        <div class="flex flex-between items-start mb-2">
          <div>
            <h1>{{ game.title }}</h1>
            <p class="text-muted">{{ game.platform_name }}</p>
          </div>
          <div class="actions">
            <router-link :to="`/edit/${game.id}`" class="btn btn-secondary">Edit</router-link>
            <button @click="enrichCover" class="btn btn-secondary" :disabled="enriching">
              {{ enriching ? '⏳ Fetching...' : '🖼 Enrich Cover' }}
            </button>
            <button @click="checkPrice" class="btn btn-secondary" :disabled="priceLoading">
              {{ priceLoading ? '⏳ Checking...' : '💰 Check Price' }}
            </button>
            <a :href="ebayUrl()" target="_blank" rel="noopener" class="btn btn-secondary">🛒 eBay.de</a>
            <button @click="deleteGame" class="btn btn-danger">Delete</button>
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
          <p>{{ game.description }}</p>
        </div>

        <!-- Market Prices -->
        <div class="price-section mt-3">
          <label>Market Prices (PriceCharting)</label>
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
          <p v-else class="text-muted" style="margin:0.5rem 0 0">No price data yet — click "Check Price" to fetch.</p>
          <div v-if="latestPrice" class="price-meta">
            Last checked: {{ formatDate(latestPrice.fetched_at) }}
          </div>
          <div v-if="priceError" class="price-error">{{ priceError }}</div>

          <!-- Price History Chart -->
          <div v-if="priceHistory.length >= 2" class="price-chart-wrapper mt-3">
            <canvas ref="priceChartEl"></canvas>
          </div>
          <p v-else-if="priceHistory.length === 1" class="text-muted price-chart-hint">
            Check price at least twice to see history chart
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
const priceChartEl = ref(null)
let chartInstance = null

const latestPrice = computed(() => priceHistory.value[0] ?? null)

function formatChartDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
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

  chartInstance = new Chart(priceChartEl.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
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
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false }
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

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

async function checkPrice() {
  priceLoading.value = true
  priceError.value = ''
  try {
    const res = await fetch(`/api/games/${route.params.id}/price-check`, { method: 'POST' })
    const data = await res.json()
    if (data.error) {
      priceError.value = data.error
    } else {
      await loadPriceHistory()
    }
  } catch (e) {
    priceError.value = 'Price check failed'
    console.error(e)
  } finally {
    priceLoading.value = false
  }
}

async function loadPriceHistory() {
  try {
    const res = await fetch(`/api/games/${route.params.id}/price-history`)
    if (res.ok) priceHistory.value = await res.json()
  } catch (e) {
    console.error('Failed to load price history:', e)
  }
}

async function enrichCover() {
  enriching.value = true
  try {
    const res = await fetch(`/api/games/${route.params.id}/enrich`, { method: 'POST' })
    if (res.ok) await loadGame()
  } catch (e) {
    console.error('Enrich failed:', e)
  } finally {
    enriching.value = false
  }
}

function coverStyle(url) {
  return url ? { backgroundImage: `url(${url})` } : {}
}

async function loadGame() {
  try {
    const res = await fetch(`/api/games/${route.params.id}`)
    if (res.ok) {
      game.value = await res.json()
    }
  } catch (e) {
    console.error('Failed to load game:', e)
  } finally {
    loading.value = false
  }
}

async function deleteGame() {
  if (!confirm('Are you sure you want to delete this game?')) return

  try {
    const res = await fetch(`/api/games/${route.params.id}`, { method: 'DELETE' })
    if (res.ok) {
      router.push('/')
    }
  } catch (e) {
    console.error('Failed to delete:', e)
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
  background-size: cover;
  background-position: center;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
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

.price-chart-wrapper {
  margin-top: 1rem;
}

.price-chart-hint {
  margin-top: 0.75rem;
  font-size: 0.8rem;
}
</style>
