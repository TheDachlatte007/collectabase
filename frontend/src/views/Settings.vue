<template>
  <div class="container">
    <h1 class="mb-3">⚙️ Settings</h1>

    <p class="section-label">System</p>
    <div class="card mb-3">
      <div class="card-head mb-2">
        <h3 class="mb-0">System Overview</h3>
        <button @click="loadInfo" class="btn btn-secondary btn-small" :disabled="infoLoading">
          {{ infoLoading ? 'Refreshing…' : '↻ Refresh' }}
        </button>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card">
          <label>Providers</label>
          <div class="kpi-value">{{ providersConfigured }}/{{ providersTotal }}</div>
        </div>
        <div class="kpi-card">
          <label>Cover Coverage</label>
          <div class="kpi-value">{{ coverCoverage.toFixed(1) }}%</div>
          <div class="coverage-track"><div class="coverage-fill" :style="{ width: `${coverCoverage}%` }" /></div>
        </div>
        <div class="kpi-card">
          <label>Items</label>
          <div class="kpi-value">{{ info.total_items ?? 0 }}</div>
          <div class="kpi-sub">{{ info.game_items ?? 0 }} games · {{ info.non_game_items ?? 0 }} others</div>
        </div>
        <div class="kpi-card">
          <label>Storage</label>
          <div class="kpi-value">{{ info.db_size || '—' }}</div>
          <div class="kpi-sub">Uploads: {{ info.uploads_size || '—' }}</div>
        </div>
      </div>

      <div v-if="setupHints.length" class="setup-hints mt-2">
        <div class="hint-title">Recommended next steps</div>
        <ul class="hint-list">
          <li v-for="hint in setupHints" :key="hint">{{ hint }}</li>
        </ul>
      </div>
    </div>

    <div class="card mb-3">
      <h3 class="mb-2">Appearance</h3>
      <div class="appearance-grid">
        <div class="form-group mb-0">
          <label for="theme-select">Theme Variant</label>
          <select id="theme-select" :value="uiPrefs.theme" @change="onThemeChange">
            <option value="indigo">Indigo</option>
            <option value="emerald">Emerald</option>
            <option value="sunset">Sunset</option>
          </select>
        </div>
        <div class="form-group mb-0">
          <label for="density-select">Density</label>
          <select id="density-select" :value="uiPrefs.density" @change="onDensityChange">
            <option value="comfortable">Comfortable</option>
            <option value="compact">Compact</option>
          </select>
        </div>
      </div>
      <p class="text-muted mt-2">Saved in your browser and applied instantly.</p>
    </div>

    <!-- Integrations & Storage -->
    <div class="card mb-3">
      <h3 class="mb-2">Integrations & Storage</h3>
      <div class="info-grid">
        <div class="info-item">
          <label>Version</label>
          <span>{{ info.version || '—' }}</span>
        </div>
        <div class="info-item">
          <label>IGDB</label>
          <span :class="info.igdb_configured ? 'status-ok' : 'status-error'">
            {{ info.igdb_configured ? '✅ Configured' : '❌ Not configured' }}
          </span>
        </div>
        <div class="info-item">
          <label>PriceCharting</label>
          <span :class="info.pricecharting_configured ? 'status-ok' : 'status-warn'">
            {{ info.pricecharting_configured ? '✅ configured' : '⚠️ PRICECHARTING_TOKEN not set' }}
          </span>
        </div>
        <div class="info-item">
          <label>eBay Market Prices</label>
          <span :class="info.ebay_configured ? 'status-ok' : 'status-warn'">
            {{ info.ebay_configured
              ? '✅ configured'
              : (info.ebay_client_id_set ? '⚠️ EBAY_CLIENT_SECRET not set' : '⚠️ EBAY_CLIENT_ID not set') }}
          </span>
        </div>
        <div class="info-item">
          <label>RAWG</label>
          <span :class="info.rawg_configured ? 'status-ok' : 'status-warn'">
            {{ info.rawg_configured ? '✅ configured' : '⚠️ RAWG_API_KEY not set' }}
          </span>
        </div>
        <div class="info-item">
          <label>Total Items</label>
          <span>{{ info.total_items ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Without Cover</label>
          <span>{{ info.missing_covers ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Covered Items</label>
          <span>{{ info.covered_items ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Local Covers</label>
          <span>{{ info.local_covers ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Remote Covers</label>
          <span>{{ info.remote_covers ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>DB Size</label>
          <span>{{ info.db_size || '—' }}</span>
        </div>
        <div class="info-item">
          <label>Upload Files</label>
          <span>{{ info.uploads_files ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Uploads Size</label>
          <span>{{ info.uploads_size || '—' }}</span>
        </div>
        <div class="info-item">
          <label>Platforms</label>
          <span>{{ info.platforms_count ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Wishlist Items</label>
          <span>{{ info.wishlist_count ?? '—' }}</span>
        </div>
      </div>
    </div>

    <p class="section-label">Automation</p>
    <div class="card mb-3">
      <h3 class="mb-2">Scheduler Status</h3>
      <div class="scheduler-status">
        <span :class="schedulerEnabled ? 'status-ok' : 'status-warn'">
          {{ schedulerEnabled ? '✅ Enabled' : '⚠️ Not enabled' }}
        </span>
        <span class="text-muted">{{ schedulerTypeLabel }}</span>
      </div>
      <div class="info-grid mt-2">
        <div class="info-item">
          <label>Cron</label>
          <span>{{ info.scheduler_cron || '—' }}</span>
        </div>
        <div class="info-item">
          <label>Source</label>
          <span>{{ info.scheduler_source || '—' }}</span>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <h3 class="mb-2">Last Runs</h3>
      <div class="run-grid">
        <div class="run-card">
          <div class="run-title">Bulk Enrich</div>
          <div class="run-time">{{ formatTimestamp(info.last_bulk_enrich_at) }}</div>
          <div class="run-meta">
            {{ info.last_bulk_enrich_success ?? 0 }} ok · {{ info.last_bulk_enrich_failed ?? 0 }} failed · {{ info.last_bulk_enrich_total ?? 0 }} total
          </div>
        </div>
        <div class="run-card">
          <div class="run-title">Bulk Price Update</div>
          <div class="run-time">{{ formatTimestamp(info.last_bulk_price_update_at) }}</div>
          <div class="run-meta">
            {{ info.last_bulk_price_update_success ?? 0 }} ok · {{ info.last_bulk_price_update_failed ?? 0 }} failed · {{ info.last_bulk_price_update_total ?? 0 }} total
          </div>
          <div v-if="info.last_bulk_price_update_error" class="run-error">
            {{ info.last_bulk_price_update_error }}
          </div>
        </div>
        <div class="run-card">
          <div class="run-title">Catalog Scrape</div>
          <div class="run-time">{{ formatTimestamp(info.last_catalog_scrape_at) }}</div>
          <div class="run-meta">
            {{ info.last_catalog_scrape_total ?? 0 }} rows · Platforms: {{ info.last_catalog_scrape_platforms || '—' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Cover Enrichment -->
    <div class="card mb-3">
      <h3 class="mb-2">🖼 Cover Enrichment</h3>
      <p class="text-muted mb-2">Automatically fetch covers for all items without one from IGDB and GameTDB.</p>
      <div class="flex gap-2 items-center mb-2 limit-row">
        <label class="text-muted">Limit per run:</label>
        <input v-model.number="enrichLimit" type="number" min="1" max="500" class="limit-input" />
      </div>
      <button @click="runBulkEnrich" class="btn btn-primary" :disabled="enriching">
        {{ enriching ? `⏳ Enriching... (${enrichProgress.success + enrichProgress.failed}/${enrichProgress.total})` : '🚀 Run Bulk Enrich' }}
      </button>
      <div v-if="enrichDone" class="result-box mt-2">
        ✅ Done: {{ enrichProgress.success }} covers fetched, {{ enrichProgress.failed }} failed out of {{ enrichProgress.total }} items
      </div>
    </div>

    <!-- Price Tracking -->
    <div class="card mb-3">
      <h3 class="mb-2">💰 Price Tracking</h3>
      <p class="text-muted mb-2">Fetch current market prices from PriceCharting (USD → EUR) for all games.</p>
      <div class="flex gap-2 items-center mb-2 limit-row">
        <label class="text-muted">Limit per run:</label>
        <input v-model.number="priceLimit" type="number" min="1" max="500" class="limit-input" />
      </div>
      <button @click="runBulkPriceUpdate" class="btn btn-primary" :disabled="priceUpdating">
        {{ priceUpdating ? `⏳ Updating... (${priceProgress.done}/${priceProgress.total})` : '💰 Run Bulk Price Update' }}
      </button>
      <div v-if="priceUpdateDone" class="result-box mt-2">
        ✅ Done: {{ priceProgress.success }} updated, {{ priceProgress.failed }} not found out of {{ priceProgress.total }} games
      </div>
    </div>

    <p class="section-label">Data</p>
    <!-- CLZ Import -->
    <div class="card mb-3">
    <h3>CLZ / Collectorz Import</h3>
    <p class="text-muted">Importiert CLZ Game Collector CSV Export direkt.</p>
    <div class="flex gap-2 items-center import-row">
        <input type="file" accept=".csv" @change="onClzFile" ref="clzInput" />
        <button class="btn btn-primary" @click="importClz" :disabled="!clzFile || clzLoading">
        {{ clzLoading ? 'Importiere...' : 'CLZ Import' }}
        </button>
    </div>
    <div v-if="clzResult" class="mt-2">
        <p class="text-success">✅ {{ clzResult.imported }} importiert</p>
        <p v-if="clzResult.skipped" class="text-muted">⚠️ {{ clzResult.skipped }} übersprungen</p>
        <p v-for="err in clzResult.errors" :key="err" class="text-danger">❌ {{ err }}</p>
    </div>
    </div>


    <!-- Database -->
    <div class="card mb-3">
      <h3 class="mb-2">🗄 Database</h3>
      <p class="text-muted mb-2">Export your entire collection as CSV backup.</p>
      <button @click="exportCSV" class="btn btn-secondary">📥 Export Collection as CSV</button>
    </div>

    <p class="section-label">Danger Zone</p>
    <!-- Danger Zone -->
    <div class="card danger-card mb-3">
      <h3 class="mb-2">⚠️ Danger Zone</h3>
      <p class="text-muted mb-2">Remove all cover URLs from the database (useful to re-enrich from scratch).</p>
      <button @click="clearCovers" class="btn btn-danger" :disabled="clearing">
        {{ clearing ? '⏳ Clearing...' : '🗑 Clear All Covers' }}
      </button>
      <div v-if="clearDone" class="result-box mt-2">✅ All covers cleared – run Bulk Enrich to re-fetch.</div>
    </div>

    <!-- Database Reset -->
    <div class="card mb-3">
        <h3>🔥 Database Reset</h3>
        <p class="text-muted">Löscht alle Games und Plattformen. Nur für Testing!</p>
        <button @click="clearDatabase" class="btn btn-danger" :disabled="clearLoading">
        {{ clearLoading ? 'Lösche...' : 'Clear Database' }}
        </button>
        <div v-if="clearResult" class="mt-2 p-2 bg-success text-white rounded">
        ✅ {{ clearResult.message }}
        </div>
    </div>


  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { importApi, priceApi, settingsApi } from '../api'
import { notifyError, notifySuccess } from '../composables/useNotifications'
import { loadUiPrefs, setUiPrefs } from '../utils/uiPreferences'

const info = ref({})
const infoLoading = ref(false)
const enriching = ref(false)
const enrichDone = ref(false)
const enrichLimit = ref(500)
const enrichProgress = ref({ success: 0, failed: 0, total: 0 })
const clearing = ref(false)
const clearDone = ref(false)
const clzFile = ref(null)
const clzLoading = ref(false)
const clzResult = ref(null)
const clearLoading = ref(false)
const clearResult = ref(null)
const priceUpdating = ref(false)
const priceUpdateDone = ref(false)
const priceLimit = ref(100)
const priceProgress = ref({ success: 0, failed: 0, total: 0, done: 0 })
const uiPrefs = ref(loadUiPrefs())

const coverCoverage = computed(() => Number(info.value.cover_coverage_pct || 0))
const providersConfigured = computed(() => Number(info.value.providers_configured || 0))
const providersTotal = computed(() => Number(info.value.providers_total || 4))
const schedulerEnabled = computed(() => Boolean(info.value.scheduler_enabled))
const schedulerTypeLabel = computed(() => {
  if (!info.value.scheduler_type || info.value.scheduler_type === 'manual') return 'Manual only'
  if (info.value.scheduler_type === 'github_actions') return 'GitHub Actions'
  return String(info.value.scheduler_type)
})
const setupHints = computed(() => {
  const hints = []
  if (!info.value.igdb_configured) hints.push('Set IGDB_CLIENT_ID + IGDB_CLIENT_SECRET to improve metadata and cover lookup.')
  if (!info.value.pricecharting_configured && !info.value.ebay_configured) {
    hints.push('Set PRICECHARTING_TOKEN or EBAY credentials to enable reliable market prices.')
  }
  if ((info.value.missing_covers ?? 0) > 0) hints.push('Run Bulk Enrich to reduce missing covers.')
  if ((info.value.remote_covers ?? 0) > 0) hints.push('Some covers still use remote URLs; re-enrich to cache more locally.')
  return hints
})

function onThemeChange(event) {
  const nextTheme = event?.target?.value || 'indigo'
  uiPrefs.value = setUiPrefs({ ...uiPrefs.value, theme: nextTheme })
}

function onDensityChange(event) {
  const nextDensity = event?.target?.value || 'comfortable'
  uiPrefs.value = setUiPrefs({ ...uiPrefs.value, density: nextDensity })
}

function formatTimestamp(value) {
  if (!value) return 'Never'
  try {
    const raw = String(value)
    const normalized = raw.includes('T') ? raw : `${raw.replace(' ', 'T')}Z`
    const dt = new Date(normalized)
    if (Number.isNaN(dt.getTime())) return raw
    return dt.toLocaleString()
  } catch {
    return String(value)
  }
}

function onClzFile(e) {
  clzFile.value = e.target.files[0]
}

async function importClz() {
  if (!clzFile.value) return
  clzLoading.value = true
  clzResult.value = null
  const formData = new FormData()
  formData.append('file', clzFile.value)
  try {
    const res = await importApi.clz(formData)
    clzResult.value = res.data
    if (res.ok) {
      notifySuccess(`CLZ import finished (${clzResult.value?.imported ?? 0} imported).`)
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || clzResult.value?.error || 'CLZ import failed.')
    }
  } catch (e) {
    clzResult.value = { imported: 0, skipped: 0, errors: ['Import fehlgeschlagen'] }
    notifyError('CLZ import failed.')
  } finally {
    clzLoading.value = false
  }
}

async function loadInfo() {
  infoLoading.value = true
  try {
    const res = await settingsApi.info()
    if (res.ok) info.value = res.data
    else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to load settings.')
    }
  } catch (e) {
    console.error('Failed to load settings:', e)
    notifyError('Failed to load settings.')
  } finally {
    infoLoading.value = false
  }
}

async function runBulkEnrich() {
  enriching.value = true
  enrichDone.value = false
  enrichProgress.value = { success: 0, failed: 0, total: 0 }
  try {
    const res = await settingsApi.bulkEnrich(enrichLimit.value)
    if (res.ok) {
      enrichProgress.value = res.data
      enrichDone.value = true
      notifySuccess(`Bulk enrich finished (${res.data?.success ?? 0} success).`)
      await loadInfo() // refresh missing covers count
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Bulk enrich failed.')
    }
  } catch (e) {
    console.error('Bulk enrich failed:', e)
    notifyError('Bulk enrich failed.')
  } finally {
    enriching.value = false
  }
}

async function runBulkPriceUpdate() {
  priceUpdating.value = true
  priceUpdateDone.value = false
  priceProgress.value = { success: 0, failed: 0, total: 0, done: 0 }
  try {
    const res = await priceApi.bulk(priceLimit.value)
    if (res.ok) {
      const data = res.data
      priceProgress.value = { ...data, done: data.total }
      priceUpdateDone.value = true
      notifySuccess(`Bulk price update finished (${data?.success ?? 0} updated).`)
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Bulk price update failed.')
    }
  } catch (e) {
    console.error('Bulk price update failed:', e)
    notifyError('Bulk price update failed.')
  } finally {
    priceUpdating.value = false
  }
}

async function exportCSV() {
  try {
    const res = await importApi.exportCsv()
    if (res.ok) notifySuccess(`Export downloaded (${res.data?.filename || 'collectabase_export.csv'}).`)
    else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Export failed.')
    }
  } catch (e) {
    notifyError('Export failed.')
  }
}

async function clearCovers() {
  if (!confirm('Are you sure? This will remove ALL cover URLs from your collection.')) return
  clearing.value = true
  clearDone.value = false
  try {
    const res = await settingsApi.clearCovers()
    if (res.ok) {
      clearDone.value = true
      notifySuccess('All covers cleared.')
      await loadInfo()
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to clear covers.')
    }
  } catch (e) {
    console.error('Clear covers failed:', e)
    notifyError('Failed to clear covers.')
  } finally {
    clearing.value = false
  }
}

async function clearDatabase() {
  if (!confirm('Wirklich ALLES löschen? Das kann nicht rückgängig gemacht werden!')) return
  
  clearLoading.value = true
  try {
    const res = await settingsApi.clearDatabase()
    clearResult.value = res.data
    if (res.ok) notifySuccess('Database cleared.')
    else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to clear database.')
    }
    // Refresh Games List nach Clear
    location.reload()
  } catch (e) {
    clearResult.value = { message: 'Fehler: ' + e.message }
    notifyError('Failed to clear database.')
  } finally {
    clearLoading.value = false
  }
}

onMounted(loadInfo)
</script>

<style scoped>
.section-label {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0.2rem 0 0.5rem;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.mb-0 {
  margin-bottom: 0;
}

.mt-2 {
  margin-top: 1rem;
}

.btn-small {
  min-height: 34px;
  padding: 0.35rem 0.7rem;
  font-size: 0.82rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.kpi-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.kpi-card label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}

.kpi-value {
  font-size: 1.2rem;
  font-weight: 700;
}

.kpi-sub {
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.coverage-track {
  margin-top: 0.35rem;
  width: 100%;
  height: 6px;
  background: #1e293b;
  border-radius: 999px;
  overflow: hidden;
}

.coverage-fill {
  height: 100%;
  background: linear-gradient(90deg, #34d399, #22c55e);
}

.setup-hints {
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.hint-title {
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.hint-list {
  margin: 0;
  padding-left: 1.15rem;
  display: grid;
  gap: 0.15rem;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.appearance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.info-item {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.5rem;
}

.info-item label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.status-ok { color: var(--success); font-weight: bold; }
.status-error { color: #ef4444; font-weight: bold; }
.status-warn { color: #f59e0b; font-weight: bold; }

.scheduler-status {
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
}

.run-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.run-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.run-title {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.run-time {
  margin-top: 0.2rem;
  font-weight: 600;
}

.run-meta {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.run-error {
  margin-top: 0.35rem;
  font-size: 0.75rem;
  color: var(--warning);
}

.limit-input {
  width: 80px;
  padding: 0.4rem;
  border-radius: 0.4rem;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
}

.result-box {
  background: var(--bg);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  color: var(--success);
}

.danger-card {
  border: 1px solid #ef444440;
}

@media (max-width: 639px) {
  /* 2-column info grid on phones */
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  /* Stack label + input for the limit row */
  .limit-row {
    flex-direction: column;
    align-items: stretch;
  }
  .limit-input {
    width: 100%;
  }

  /* Stack file input + button for the CLZ import row */
  .import-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
