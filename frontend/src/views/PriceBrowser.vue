<template>
  <div class="container">
    <!-- Header -->
    <div class="list-header mb-3">
      <h1>Price Browser</h1>
      <div class="filters">
        <input
          v-model="search"
          placeholder="Search games..."
          class="search-input"
          @input="onSearchInput"
        />
        <select v-model="selectedPlatform" class="filter-select" @change="loadPage(1)">
          <option value="">All Platforms</option>
          <option v-for="p in platforms" :key="p.key || p" :value="p.key || p">
            {{ p.label || p }}<template v-if="p.count > 0"> ({{ p.count.toLocaleString() }})</template>
          </option>
        </select>
        <select v-model="sortField" class="filter-select" @change="loadPage(1)">
          <option value="title">Sort: Title</option>
          <option value="loose_eur">Sort: Loose Price</option>
          <option value="cib_eur">Sort: CIB Price</option>
          <option value="new_eur">Sort: New Price</option>
        </select>
        <button class="btn btn-secondary sort-dir-btn" @click="toggleOrder">
          {{ sortOrder === 'asc' ? '↑ Asc' : '↓ Desc' }}
        </button>
      </div>
    </div>

    <!-- Catalog stats + scrape controls -->
    <div class="catalog-bar mb-3">
      <span class="text-muted catalog-count">
        {{ total.toLocaleString() }} entries in current view
        <span v-if="lastScraped"> · last updated {{ lastScraped }}</span>
      </span>
      <div class="scrape-controls">
        <select v-model="scrapeTarget" class="filter-select scrape-select">
          <option value="all">All Platforms</option>
          <option v-for="p in scrapePlatforms" :key="p.key" :value="p.scraper_slug || p.key">
            {{ p.label }}
          </option>
        </select>
        <button class="btn btn-secondary" :disabled="scraping" @click="startScrape">
          <span v-if="scraping">Scraping…</span>
          <span v-else>{{ search.trim() ? 'Scrape This Search' : 'Scrape Prices' }}</span>
        </button>
        <button class="btn btn-secondary" :disabled="scraping || enrichingLibrary" @click="startMassScrape">
          Mass Scrape All
        </button>
        <button class="btn btn-secondary" :disabled="scraping || enrichingLibrary" @click="startLibraryEnrich">
          <span v-if="enrichingLibrary">Enriching…</span>
          <span v-else>Enrich from Library</span>
        </button>
	        <button class="btn btn-danger-outline" :disabled="scraping" @click="clearCatalog">
	          Clear
	        </button>
	      </div>
	    </div>
    <!-- Linked game banner with details, current price history, and alternative title chips -->
    <div v-if="linkedGameId" class="linked-card mb-3">
      <div class="linked-header">
        <div class="linked-main-info">
          <span class="linked-badge">🔗 Linked Item</span>
          <h2 class="linked-title">{{ linkedGame?.title || `Game #${linkedGameId}` }}</h2>
          <span v-if="linkedGame?.platform_name" class="linked-platform-badge">{{ linkedGame.platform_name }}</span>
        </div>
        <router-link v-if="returnToUrl" :to="returnToUrl" class="btn btn-secondary btn-sm linked-back-btn">
          ← Back to Item
        </router-link>
      </div>

      <div class="linked-body">
        <div class="linked-stats">
          <div class="linked-stat">
            <span class="stat-label">Tracked Value:</span>
            <span class="stat-value">
              {{ linkedGame?.current_value != null ? `€${Number(linkedGame.current_value).toFixed(2)}` : 'Not set' }}
            </span>
          </div>
          <div class="linked-stat">
            <span class="stat-label">Condition:</span>
            <span class="stat-value">{{ linkedGame?.condition || '—' }}</span>
          </div>
          <div class="linked-stat">
            <span class="stat-label">Completeness:</span>
            <span class="stat-value">{{ linkedGame?.completeness || '—' }}</span>
          </div>
          <div v-if="latestLinkedPrice" class="linked-stat linked-stat-price">
            <span class="stat-label">Last Recorded:</span>
            <span class="stat-value">
              L: {{ latestLinkedPrice.loose_price != null ? `€${latestLinkedPrice.loose_price.toFixed(2)}` : '—' }} ·
              CIB: {{ latestLinkedPrice.complete_price != null ? `€${latestLinkedPrice.complete_price.toFixed(2)}` : '—' }} ·
              New: {{ latestLinkedPrice.new_price != null ? `€${latestLinkedPrice.new_price.toFixed(2)}` : '—' }}
            </span>
          </div>
        </div>

        <!-- Alternative Titles / Quick search chips -->
        <div v-if="allSearchTitles.length > 1" class="linked-chips-container mt-2">
          <span class="chips-label">Search title variants:</span>
          <div class="chips-list">
            <button
              v-for="t in allSearchTitles"
              :key="t"
              type="button"
              class="chip-btn"
              :class="{ 'chip-active': isSearchActive(t) }"
              @click="selectSearchTitle(t)"
            >
              {{ t }}
              <span v-if="t === linkedGame?.title" class="chip-tag">Primary</span>
              <span v-else class="chip-tag">Alias</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Scrape progress message -->
	    <div v-if="scraping" class="scrape-notice mb-3">
	      Scraping PriceCharting catalog – this may take several minutes. You can keep using the app.
	    </div>
	    <div v-if="scrapeResult" class="scrape-result mb-3">
	      <span v-if="scrapeResult.library">
	        ✓ Library enrich finished
	      </span>
	      <span v-if="scrapeResult.targeted">
	        ✓ Targeted scrape for "{{ scrapeResult.query }}" finished
	        <span v-if="scrapeResult.error"> · {{ scrapeResult.error }}</span>
	      </span>
	      <span v-else-if="!scrapeResult.library">✓ Scrape finished for: {{ scrapeResult.platforms.join(', ') }}</span>
	      <span class="scrape-kpi">
	        <template v-if="scrapeResult.library">
	          scanned {{ (scrapeResult.scanned || 0).toLocaleString() }} ·
	          fetched {{ (scrapeResult.fetched || 0).toLocaleString() }} ·
	          failed {{ (scrapeResult.failed || 0).toLocaleString() }} ·
	          skipped {{ (scrapeResult.skipped_existing || 0).toLocaleString() }} ·
	        </template>
	        processed {{ (scrapeResult.scraped || 0).toLocaleString() }} ·
	        new {{ (scrapeResult.inserted || 0).toLocaleString() }} ·
	        changed {{ (scrapeResult.updated || 0).toLocaleString() }} ·
	        unchanged {{ (scrapeResult.unchanged || 0).toLocaleString() }}
	      </span>
    </div>
    <div v-if="selectedPlatform" class="filter-notice mb-3">
      Filter active: showing only platform "{{ selectedPlatformLabel }}"
      <button class="btn-reset-filter" @click="clearPlatformFilter">Reset</button>
    </div>

    <div v-if="loading" class="loading">Loading catalog…</div>

    <div v-else-if="items.length === 0 && total === 0 && !search && !selectedPlatform" class="empty">
      <h3>Catalog is empty</h3>
      <p>Use "Scrape Prices" to fetch the PriceCharting catalog for one or all platforms.</p>
    </div>

    <div v-else-if="items.length === 0" class="empty empty-interactive">
      <div class="empty-icon">🔎</div>
      <h3>No results in local price catalog</h3>
      <p class="text-muted">
        <template v-if="search">
          No matches found for "<strong>{{ search }}</strong>"
          <template v-if="selectedPlatformLabel"> on {{ selectedPlatformLabel }}</template>.
        </template>
        <template v-else>
          No catalog entries match your active filters.
        </template>
      </p>

      <!-- Suggested Alt Titles if any exist that differ from current search -->
      <div v-if="suggestedAltTitles.length > 0" class="empty-suggestions mt-2">
        <p class="text-sm text-muted">Try an alternative title from this item:</p>
        <div class="chips-list mt-1">
          <button
            v-for="alt in suggestedAltTitles"
            :key="alt"
            type="button"
            class="chip-btn"
            @click="selectSearchTitle(alt)"
          >
            🔍 {{ alt }}
          </button>
        </div>
      </div>

      <!-- Quick Scrape Call-to-Action -->
      <div class="empty-actions mt-3">
        <button
          v-if="search.trim()"
          type="button"
          class="btn btn-primary"
          :disabled="scraping"
          @click="startScrape"
        >
          <span v-if="scraping">Scraping…</span>
          <span v-else>🔍 Scrape Online Prices for "{{ search.trim() }}"</span>
        </button>
        <button
          v-if="selectedPlatform"
          type="button"
          class="btn btn-secondary"
          @click="clearPlatformFilter"
        >
          Clear Platform Filter
        </button>
      </div>
    </div>

    <template v-else>
      <!-- Price table -->
      <div class="table-wrap">
        <table class="price-table">
          <thead>
            <tr>
              <th class="col-title">Title</th>
              <th class="col-platform">Platform</th>
              <th class="col-price" @click="setSort('loose_eur')">
                Loose <span class="sort-indicator">{{ sortIndicator('loose_eur') }}</span>
              </th>
              <th class="col-price" @click="setSort('cib_eur')">
                CIB <span class="sort-indicator">{{ sortIndicator('cib_eur') }}</span>
              </th>
              <th class="col-price" @click="setSort('new_eur')">
                New <span class="sort-indicator">{{ sortIndicator('new_eur') }}</span>
              </th>
              <th class="col-actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="col-title">
                <a
                  v-if="item.page_url"
                  :href="item.page_url"
                  target="_blank"
                  rel="noopener"
                  class="title-link"
                >{{ item.title }}</a>
                <span v-else>{{ item.title }}</span>
                <span v-if="isInCollection(item)" class="owned-badge" title="Already in your collection">✓ Owned</span>
              </td>
              <td class="col-platform">
                <span class="badge">{{ item.platform }}</span>
              </td>
              <td class="col-price">
                <span v-if="item.loose_eur != null" class="price">€{{ item.loose_eur.toFixed(2) }}</span>
                <span v-else class="na-value">N/A</span>
              </td>
              <td class="col-price">
                <span v-if="item.cib_eur != null" class="price">€{{ item.cib_eur.toFixed(2) }}</span>
                <span v-else class="na-value">N/A</span>
              </td>
              <td class="col-price">
                <span v-if="item.new_eur != null" class="price">€{{ item.new_eur.toFixed(2) }}</span>
                <span v-else class="na-value">N/A</span>
              </td>
              <td class="col-actions">
                <button
                  v-if="linkedGameId"
                  class="btn btn-sm btn-primary"
                  :disabled="applyLoadingId === item.id"
                  @click="applyToLinkedGame(item)"
                >
                  {{ applyLoadingId === item.id ? 'Applying…' : 'Use Price' }}
                </button>
                <button v-else class="btn btn-sm btn-primary" @click="openAddModal(item)">+ Add</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination mt-3">
        <button class="btn btn-secondary" :disabled="page <= 1" @click="loadPage(page - 1)">
          ← Prev
        </button>
        <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn btn-secondary" :disabled="page >= totalPages" @click="loadPage(page + 1)">
          Next →
        </button>
      </div>
    </template>

    <!-- Quick-Add Modal -->
    <div v-if="addModal.open" class="modal-backdrop" @click.self="closeAddModal">
      <div class="modal">
        <h2>Add to Collection</h2>
        <p class="modal-game-title">{{ addModal.item?.title }}</p>
        <p class="text-muted">{{ addModal.item?.platform }}</p>

        <div class="form-group">
          <label>Condition</label>
          <select v-model="addModal.condition" class="filter-select w-full">
            <option value="">– not set –</option>
            <option>Mint</option>
            <option>Very Good</option>
            <option>Good</option>
            <option>Fair</option>
            <option>Poor</option>
          </select>
        </div>

        <div class="form-group">
          <label>Completeness</label>
          <select v-model="addModal.completeness" class="filter-select w-full">
            <option value="">– not set –</option>
            <option>Complete</option>
            <option>Game Only</option>
            <option>Box Only</option>
            <option>Manual Only</option>
          </select>
        </div>

        <div class="form-group">
          <label>Purchase Price (€)</label>
          <input v-model="addModal.purchasePrice" type="number" step="0.01" min="0" class="search-input w-full" placeholder="0.00" />
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeAddModal">Cancel</button>
          <button class="btn btn-primary" :disabled="addModal.saving" @click="confirmAdd">
            {{ addModal.saving ? 'Adding…' : 'Add to Collection' }}
          </button>
        </div>

        <p v-if="addModal.error" class="error-text">{{ addModal.error }}</p>
        <p v-if="addModal.success" class="success-text">✓ Added to your collection!</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { priceApi, priceCatalogApi, gamesApi, platformsApi } from '../api'
import { notifyError, notifySuccess } from '../composables/useNotifications'

const items = ref([])
const platforms = ref([])
const total = ref(0)
const page = ref(1)
const limit = 50
const loading = ref(false)

const search = ref('')
const selectedPlatform = ref('')
const sortField = ref('title')
const sortOrder = ref('asc')

const scraping = ref(false)
const enrichingLibrary = ref(false)
const scrapeTarget = ref('all')
const scrapeResult = ref(null)
const lastScraped = ref('')
const linkedGameId = ref(null)
const applyLoadingId = ref(null)
const linkedGame = ref(null)
const linkedGameHistory = ref([])
const linkedGameLoading = ref(false)
const libraryMarkers = ref(new Set()) // Combined "Title|Platform" keys
const route = useRoute()
const router = useRouter()

const returnToUrl = computed(() => {
  return typeof route.query.returnTo === 'string' && route.query.returnTo.trim()
    ? route.query.returnTo.trim()
    : (linkedGameId.value ? `/game/${linkedGameId.value}` : null)
})

const latestLinkedPrice = computed(() => {
  return linkedGameHistory.value?.[0] || null
})

const allSearchTitles = computed(() => {
  if (!linkedGame.value) return []
  const list = []
  if (linkedGame.value.title) list.push(linkedGame.value.title.trim())
  if (Array.isArray(linkedGame.value.alt_titles_list)) {
    linkedGame.value.alt_titles_list.forEach(t => {
      const clean = String(t || '').trim()
      if (clean && !list.includes(clean)) list.push(clean)
    })
  } else if (typeof linkedGame.value.alt_titles === 'string') {
    try {
      const parsed = JSON.parse(linkedGame.value.alt_titles)
      if (Array.isArray(parsed)) {
        parsed.forEach(t => {
          const clean = String(t || '').trim()
          if (clean && !list.includes(clean)) list.push(clean)
        })
      }
    } catch {
      linkedGame.value.alt_titles.split(',').forEach(t => {
        const clean = t.trim()
        if (clean && !list.includes(clean)) list.push(clean)
      })
    }
  }
  return list
})

const suggestedAltTitles = computed(() => {
  const current = search.value.trim().toLowerCase()
  return allSearchTitles.value.filter(t => t.toLowerCase() !== current)
})

function isSearchActive(title) {
  return search.value.trim().toLowerCase() === String(title || '').trim().toLowerCase()
}

function selectSearchTitle(title) {
  search.value = title
  loadPage(1)
}

async function loadLinkedGameDetails(id) {
  linkedGameLoading.value = true
  try {
    const [gameRes, histRes] = await Promise.all([
      gamesApi.get(id),
      priceApi.history(id)
    ])
    if (gameRes.ok) linkedGame.value = gameRes.data
    if (histRes.ok && Array.isArray(histRes.data)) linkedGameHistory.value = histRes.data
  } catch (e) {
    console.warn('Failed to load linked game details:', e)
  } finally {
    linkedGameLoading.value = false
  }
}

let searchTimer = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

const scrapePlatforms = computed(() => {
  return platforms.value.filter(p => !!p.scraper_slug)
})

const selectedPlatformLabel = computed(() => {
  if (!selectedPlatform.value) return ''
  const val = String(selectedPlatform.value).toLowerCase()
  const found = platforms.value.find(p => {
    const k = String(p.key || '').toLowerCase()
    const l = String(p.label || '').toLowerCase()
    return k === val || l === val
  })
  return found ? (found.label || found) : selectedPlatform.value
})

function clearPlatformFilter() {
  selectedPlatform.value = ''
  loadPage(1)
}

function buildParams() {
  const p = new URLSearchParams()
  if (search.value) p.set('search', search.value)
  if (selectedPlatform.value) p.set('platform', selectedPlatform.value)
  p.set('sort', sortField.value)
  p.set('order', sortOrder.value)
  p.set('page', String(page.value))
  p.set('limit', String(limit))
  return p.toString() ? `?${p.toString()}` : ''
}

async function loadPage(p) {
  page.value = p
  loading.value = true
  try {
    const res = await priceCatalogApi.search(buildParams())
    if (res.ok && res.data) {
      items.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (e) {
    console.error('Failed to load price catalog:', e)
  } finally {
    loading.value = false
  }
}

async function loadPlatforms() {
  try {
    const res = await priceCatalogApi.platforms()
    if (res.ok && Array.isArray(res.data)) {
      platforms.value = res.data
    }
  } catch (e) {
    console.error('Failed to load catalog platforms:', e)
  }
}

function normalizePlatformName(name) {
  if (!name) return ''
  const clean = String(name).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const aliases = {
    ps5: 'playstation 5',
    ps4: 'playstation 4',
    ps3: 'playstation 3',
    ps2: 'playstation 2',
    'xbox series x': 'xbox series x s',
    'super nintendo': 'snes',
    genesis: 'sega genesis mega drive',
    'mega drive': 'sega genesis mega drive',
  }
  return aliases[clean] || clean
}

async function loadLibraryMarkers() {
  try {
    const res = await gamesApi.list()
    if (res.ok && Array.isArray(res.data)) {
      const markers = new Set()
      res.data.forEach(g => {
        const titleKey = String(g.title).toLowerCase().trim()
        const platKey = normalizePlatformName(g.platform_name)
        markers.add(`${titleKey}|${platKey}`)
        markers.add(`${titleKey}|${String(g.platform_name).toLowerCase().trim()}`)
      })
      libraryMarkers.value = markers
    }
  } catch (e) {
    console.error('Failed to load library markers:', e)
  }
}

function isInCollection(item) {
  const titleKey = String(item.title).toLowerCase().trim()
  const platKey = normalizePlatformName(item.platform)
  return libraryMarkers.value.has(`${titleKey}|${platKey}`) ||
         libraryMarkers.value.has(`${titleKey}|${String(item.platform).toLowerCase().trim()}`)
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadPage(1), 300)
}

function toggleOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  loadPage(1)
}

function setSort(field) {
  if (sortField.value === field) {
    toggleOrder()
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
    loadPage(1)
  }
}

function sortIndicator(field) {
  if (sortField.value !== field) return ''
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

async function startScrape(options = {}) {
  const forceAll = options.forceAll === true
  scraping.value = true
  scrapeResult.value = null
  try {
    const query = forceAll ? '' : search.value.trim()
    const scrapePlatform = forceAll
      ? 'all'
      : query
      ? (selectedPlatform.value || (scrapeTarget.value !== 'all' ? scrapeTarget.value : 'all'))
      : scrapeTarget.value
    const res = await priceCatalogApi.scrape(scrapePlatform, query)
    if (res.ok && res.data) {
      scrapeResult.value = res.data
      lastScraped.value = new Date().toLocaleString('de-DE')
      if (!query && scrapeTarget.value === 'all') {
        selectedPlatform.value = ''
      }
      await Promise.all([loadPage(1), loadPlatforms()])
    }
  } catch (e) {
    console.error('Scrape failed:', e)
  } finally {
    scraping.value = false
  }
}

function startMassScrape() {
  return startScrape({ forceAll: true })
}

async function startLibraryEnrich() {
  enrichingLibrary.value = true
  scrapeResult.value = null
  try {
    const res = await priceCatalogApi.enrichLibrary(160)
    if (res.ok && res.data) {
      scrapeResult.value = res.data
      lastScraped.value = new Date().toLocaleString('de-DE')
      await Promise.all([loadPage(1), loadPlatforms()])
    }
  } catch (e) {
    console.error('Library enrich failed:', e)
  } finally {
    enrichingLibrary.value = false
  }
}

async function clearCatalog() {
  if (!confirm('Delete all price catalog entries?')) return
  await priceCatalogApi.clear()
  items.value = []
  total.value = 0
  scrapeResult.value = null
  await loadPlatforms()
}

async function applyToLinkedGame(item) {
  const gameId = Number(linkedGameId.value)
  if (!Number.isFinite(gameId) || gameId <= 0) return
  applyLoadingId.value = item.id
  try {
    const applyRes = await priceApi.applyCatalog(gameId, item.id)
    if (!applyRes.ok) {
      const detail = applyRes.data?.detail
      notifyError(detail?.message || detail || 'Could not apply catalog price.')
      return
    }
    notifySuccess(`Price from "${item.title}" applied to game #${gameId}.`)
    const returnTo = returnToUrl.value
    if (returnTo) {
      setTimeout(() => router.push(returnTo), 600)
    }
  } catch (e) {
    console.error('Apply catalog price failed:', e)
    notifyError('Could not apply catalog price.')
  } finally {
    applyLoadingId.value = null
  }
}

// ── Quick-Add Modal ───────────────────────────────────────────────────────────
const backendPlatforms = ref([])

const addModal = ref({
  open: false,
  item: null,
  condition: '',
  completeness: '',
  purchasePrice: '',
  saving: false,
  error: '',
  success: false,
})

function openAddModal(item) {
  addModal.value = {
    open: true,
    item,
    condition: '',
    completeness: '',
    purchasePrice: '',
    saving: false,
    error: '',
    success: false,
  }
}

function closeAddModal() {
  addModal.value.open = false
}

async function confirmAdd() {
  const item = addModal.value.item
  if (!item) return

  // Find matching platform_id from backend platforms list
  const itemNorm = normalizePlatformName(item.platform)
  const platformMatch = backendPlatforms.value.find(p => {
    return p.name.toLowerCase() === item.platform.toLowerCase() ||
           normalizePlatformName(p.name) === itemNorm
  })

  if (!platformMatch) {
    addModal.value.error = `Platform "${item.platform}" not found in your platform list.`
    return
  }

  addModal.value.saving = true
  addModal.value.error = ''
  addModal.value.success = false

  const payload = {
    title: item.title,
    platform_id: platformMatch.id,
    condition: addModal.value.condition || null,
    completeness: addModal.value.completeness || null,
    purchase_price: addModal.value.purchasePrice ? parseFloat(addModal.value.purchasePrice) : null,
    current_value: item.loose_eur ?? null,
  }

  try {
    const res = await gamesApi.create(payload)
    if (res.ok) {
      addModal.value.success = true
      setTimeout(closeAddModal, 1200)
    } else {
      addModal.value.error = res.data?.message || 'Failed to add game.'
    }
  } catch (e) {
    addModal.value.error = 'Network error.'
  } finally {
    addModal.value.saving = false
  }
}

onMounted(async () => {
  const routeSearch = typeof route.query.search === 'string' ? route.query.search : ''
  const routePlatform = typeof route.query.platform === 'string' ? route.query.platform.trim() : ''
  const routeLinkGame = typeof route.query.linkGame === 'string' ? route.query.linkGame : ''
  if (routeSearch) search.value = routeSearch
  if (routeLinkGame && Number.isFinite(Number(routeLinkGame))) {
    linkedGameId.value = Number(routeLinkGame)
    loadLinkedGameDetails(linkedGameId.value)
  }

  await loadPlatforms()
  await loadLibraryMarkers()
  if (routePlatform) {
    const target = routePlatform.toLowerCase()
    const matched = platforms.value.find(p => {
      const k = String(p.key || '').toLowerCase()
      const l = String(p.label || '').toLowerCase()
      return k === target || l === target
    })
    selectedPlatform.value = matched ? matched.key : routePlatform
  }
  await loadPage(1)
  try {
    const res = await platformsApi.list()
    if (res.ok && Array.isArray(res.data)) {
      backendPlatforms.value = res.data
    }
  } catch {}
})
</script>

<style scoped>
/* ── Filter bar (reused pattern from GamesList) ── */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
  align-items: center;
}

.search-input,
.filter-select {
  width: auto;
  min-width: 150px;
}

.sort-dir-btn {
  white-space: nowrap;
}

/* ── Catalog bar ── */
.catalog-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.catalog-count {
  font-size: 0.9rem;
}

.scrape-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.scrape-select {
  min-width: 160px;
}

.scrape-notice {
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.scrape-result {
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  color: var(--text);
}

.scrape-kpi {
  display: block;
  margin-top: 0.2rem;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.filter-notice {
  font-size: 0.85rem;
  color: #fbbf24;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-reset-filter {
  background: transparent;
  border: 1px solid rgba(251, 191, 36, 0.4);
  color: #fbbf24;
  border-radius: 4px;
  padding: 0.15rem 0.45rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-reset-filter:hover {
  background: rgba(251, 191, 36, 0.15);
  border-color: #fbbf24;
}

.link-notice {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.28);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  font-size: 0.85rem;
  color: #bfdbfe;
}

/* ── Linked Game Banner ── */
.linked-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
  border: 1px solid rgba(59, 130, 246, 0.35);
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.linked-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.linked-main-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.linked-badge {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.4);
  color: #93c5fd;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.linked-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: #f8fafc;
}

.linked-platform-badge {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  font-size: 0.75rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.linked-back-btn {
  font-size: 0.82rem;
}

.linked-stats {
  display: flex;
  gap: 1.25rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
}

.linked-stat {
  display: flex;
  gap: 0.35rem;
}

.stat-label {
  color: var(--text-muted, #94a3b8);
}

.stat-value {
  color: #e2e8f0;
  font-weight: 500;
}

.linked-stat-price .stat-value {
  color: #38bdf8;
}

.linked-chips-container {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.chips-label {
  font-size: 0.78rem;
  color: var(--text-muted, #94a3b8);
}

.chips-list {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.chip-btn.chip-active {
  background: rgba(59, 130, 246, 0.25);
  border-color: #3b82f6;
  color: #93c5fd;
  font-weight: 600;
}

.chip-tag {
  font-size: 0.68rem;
  opacity: 0.7;
}

.empty-interactive {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 3rem 1.5rem;
}

.empty-icon {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
}

.empty-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: center;
}

/* ── Table ── */
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  background: var(--surface);
  -webkit-overflow-scrolling: touch;
}

.price-table {
  width: 100%;
  min-width: 540px;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.price-table thead th {
  background: var(--surface-subtle);
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--glass-border);
  white-space: nowrap;
  user-select: none;
}

.price-table thead th.col-price {
  cursor: pointer;
}

.price-table thead th.col-price:hover {
  color: var(--text);
}

.sort-indicator {
  color: var(--primary);
  margin-left: 0.25rem;
}

.price-table tbody tr {
  border-bottom: 1px solid var(--glass-border);
  transition: background 0.1s;
}

.price-table tbody tr:last-child {
  border-bottom: none;
}

.price-table tbody tr:hover {
  background: rgba(255,255,255,0.02);
}

.price-table td {
  padding: 0.65rem 1rem;
  vertical-align: middle;
}

.col-title {
  max-width: 260px;
}

.col-platform {
  white-space: nowrap;
}

.col-price {
  text-align: right;
  white-space: nowrap;
}

.col-actions {
  text-align: right;
  white-space: nowrap;
}

.title-link {
  color: var(--text);
  text-decoration: none;
}

.title-link:hover {
  color: var(--primary);
  text-decoration: underline;
}

.owned-badge {
  display: inline-block;
  margin-left: 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border-radius: 4px;
  border: 1px solid rgba(16, 185, 129, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.price {
  font-family: var(--font-data);
  color: var(--primary);
  font-weight: 600;
}

.na-value {
  color: var(--text-muted);
  font-family: var(--font-data);
  font-size: 0.82rem;
  opacity: 0.55;
}

/* ── Pagination ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.page-info {
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* ── Modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 1rem;
}

.modal {
  background: var(--bg-light);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--card-blur);
  -webkit-backdrop-filter: var(--card-blur);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--glass-shadow);
}

.modal h2 {
  margin: 0 0 0.25rem;
}

.modal-game-title {
  font-weight: 600;
  font-size: 1rem;
  margin: 0 0 0.1rem;
}

.form-group {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-group label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.w-full {
  width: 100%;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

.btn-danger-outline {
  background: transparent;
  border: 1px solid var(--danger, #e74c3c);
  color: var(--danger, #e74c3c);
}

.btn-danger-outline:hover:not(:disabled) {
  background: var(--danger, #e74c3c);
  color: #fff;
}

.error-text {
  color: var(--danger, #e74c3c);
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.success-text {
  color: #27ae60;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

/* ── Responsive ── */
@media (max-width: 639px) {
  .list-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filters {
    flex-direction: column;
    justify-content: stretch;
  }

  .search-input,
  .filter-select,
  .sort-dir-btn {
    width: 100%;
  }

  .catalog-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .scrape-controls {
    flex-direction: column;
  }

  .scrape-select {
    width: 100%;
  }

  .col-platform {
    display: none;
  }
}
</style>
