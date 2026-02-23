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
          <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
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
          <option v-for="[label, slug] in platformSlugs" :key="slug" :value="slug">
            {{ label }}
          </option>
        </select>
        <button class="btn btn-secondary" :disabled="scraping" @click="startScrape">
          <span v-if="scraping">Scraping…</span>
          <span v-else>{{ search.trim() ? 'Scrape This Search' : 'Scrape Prices' }}</span>
        </button>
        <button class="btn btn-danger-outline" :disabled="scraping" @click="clearCatalog">
          Clear
        </button>
      </div>
    </div>

    <!-- Scrape progress message -->
    <div v-if="scraping" class="scrape-notice mb-3">
      Scraping PriceCharting catalog – this may take several minutes. You can keep using the app.
    </div>
    <div v-if="scrapeResult" class="scrape-result mb-3">
      <span v-if="scrapeResult.targeted">
        ✓ Targeted scrape for "{{ scrapeResult.query }}" finished
        <span v-if="scrapeResult.error"> · {{ scrapeResult.error }}</span>
      </span>
      <span v-else>✓ Scrape finished for: {{ scrapeResult.platforms.join(', ') }}</span>
      <span class="scrape-kpi">
        processed {{ (scrapeResult.scraped || 0).toLocaleString() }} ·
        new {{ (scrapeResult.inserted || 0).toLocaleString() }} ·
        changed {{ (scrapeResult.updated || 0).toLocaleString() }} ·
        unchanged {{ (scrapeResult.unchanged || 0).toLocaleString() }}
      </span>
    </div>
    <div v-if="selectedPlatform" class="filter-notice mb-3">
      Filter active: showing only platform "{{ selectedPlatform }}"
    </div>

    <div v-if="loading" class="loading">Loading catalog…</div>

    <div v-else-if="items.length === 0 && total === 0 && !search && !selectedPlatform" class="empty">
      <h3>Catalog is empty</h3>
      <p>Use "Scrape Prices" to fetch the PriceCharting catalog for one or all platforms.</p>
    </div>

    <div v-else-if="items.length === 0" class="empty">
      <h3>No results found</h3>
      <p>Try a different search or platform filter.</p>
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
              </td>
              <td class="col-platform">
                <span class="badge">{{ item.platform }}</span>
              </td>
              <td class="col-price">
                <span v-if="item.loose_eur != null" class="price">€{{ item.loose_eur.toFixed(2) }}</span>
                <span v-else class="text-muted">–</span>
              </td>
              <td class="col-price">
                <span v-if="item.cib_eur != null" class="price">€{{ item.cib_eur.toFixed(2) }}</span>
                <span v-else class="text-muted">–</span>
              </td>
              <td class="col-price">
                <span v-if="item.new_eur != null" class="price">€{{ item.new_eur.toFixed(2) }}</span>
                <span v-else class="text-muted">–</span>
              </td>
              <td class="col-actions">
                <button class="btn btn-sm btn-primary" @click="openAddModal(item)">+ Add</button>
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
import { useRoute } from 'vue-router'
import { priceCatalogApi, gamesApi, platformsApi } from '../api'

// Known platform slug mapping (mirrors backend PLATFORM_SLUGS)
const platformSlugs = [
  ['PlayStation 5', 'playstation-5'],
  ['PlayStation 4', 'playstation-4'],
  ['PlayStation 3', 'playstation-3'],
  ['PlayStation 2', 'playstation-2'],
  ['PlayStation', 'playstation'],
  ['PSP', 'psp'],
  ['PS Vita', 'ps-vita'],
  ['Xbox Series X/S', 'xbox-series-x'],
  ['Xbox One', 'xbox-one'],
  ['Xbox 360', 'xbox-360'],
  ['Xbox', 'xbox'],
  ['Nintendo Switch', 'nintendo-switch'],
  ['Nintendo Switch 2', 'nintendo-switch-2'],
  ['Wii U', 'wii-u'],
  ['Wii', 'wii'],
  ['GameCube', 'gamecube'],
  ['Nintendo 64', 'nintendo-64'],
  ['SNES', 'super-nintendo'],
  ['NES', 'nes'],
  ['Game Boy Advance', 'gameboy-advance'],
  ['Game Boy Color', 'gameboy-color'],
  ['Game Boy', 'gameboy'],
  ['Nintendo 3DS', '3ds'],
  ['Nintendo DS', 'nintendo-ds'],
  ['Sega Dreamcast', 'sega-dreamcast'],
  ['Sega Saturn', 'sega-saturn'],
  ['Sega Genesis/Mega Drive', 'sega-genesis'],
  ['Sega Master System', 'sega-master-system'],
  ['Sega Game Gear', 'game-gear'],
]

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
const scrapeTarget = ref('all')
const scrapeResult = ref(null)
const lastScraped = ref('')
const route = useRoute()

let searchTimer = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

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

async function startScrape() {
  scraping.value = true
  scrapeResult.value = null
  try {
    const query = search.value.trim()
    const scrapePlatform = query
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

async function clearCatalog() {
  if (!confirm('Delete all price catalog entries?')) return
  await priceCatalogApi.clear()
  items.value = []
  total.value = 0
  platforms.value = []
  scrapeResult.value = null
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
  const platformMatch = backendPlatforms.value.find(
    p => p.name.toLowerCase() === item.platform.toLowerCase()
  )

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
  const routePlatform = typeof route.query.platform === 'string' ? route.query.platform : ''
  if (routeSearch) search.value = routeSearch
  if (routePlatform) selectedPlatform.value = routePlatform

  await Promise.all([loadPlatforms(), loadPage(1)])
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
}

/* ── Table ── */
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.price-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.price-table thead th {
  background: var(--bg-light);
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
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
  border-bottom: 1px solid var(--border);
  transition: background 0.1s;
}

.price-table tbody tr:last-child {
  border-bottom: none;
}

.price-table tbody tr:hover {
  background: var(--bg-light);
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

.price {
  font-variant-numeric: tabular-nums;
  color: var(--primary);
  font-weight: 500;
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
  background: var(--bg);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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
