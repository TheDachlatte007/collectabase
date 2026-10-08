<template>
  <div class="container settings-page">
    <div class="settings-header mb-3">
      <div>
        <h1>Settings</h1>
        <p class="text-muted">System status, integrations, automation and backup guidance in one place.</p>
      </div>
      <button @click="loadInfo" class="btn btn-secondary btn-small" :disabled="infoLoading">
        {{ infoLoading ? 'Refreshing…' : 'Refresh Overview' }}
      </button>
    </div>

    <div class="settings-stack">
      <section class="card settings-section">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">System</p>
            <h2>Overview</h2>
          </div>
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
            <div class="kpi-sub">{{ info.game_items ?? 0 }} games · {{ info.non_game_items ?? 0 }} other items</div>
          </div>
          <div class="kpi-card">
            <label>Storage</label>
            <div class="kpi-value">{{ info.db_size || '—' }}</div>
            <div class="kpi-sub">Uploads: {{ info.uploads_size || '—' }}</div>
            <div class="storage-status" :class="`storage-status-${info.storage_health || 'empty'}`">
              {{ storageHealthLabel }}
            </div>
          </div>
        </div>

        <div v-if="info.storage_health === 'attention'" class="storage-alert">
          <strong>Storage needs attention</strong>
          <span>{{ info.storage_health_message }}</span>
        </div>

        <div v-if="setupHints.length" class="setup-hints mt-2">
          <div class="hint-title">Recommended next steps</div>
          <ul class="hint-list">
            <li v-for="hint in setupHints" :key="hint">{{ hint }}</li>
          </ul>
        </div>

        <div class="info-grid mt-2">
          <div class="info-item">
            <label>Version</label>
            <span>{{ info.version || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Total Items</label>
            <span>{{ info.total_items ?? '—' }}</span>
          </div>
          <div class="info-item">
            <label>Covered Items</label>
            <span>{{ info.covered_items ?? '—' }}</span>
          </div>
          <div class="info-item">
            <label>Missing Covers</label>
            <span>{{ info.missing_covers ?? '—' }}</span>
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
      </section>

      <section class="card settings-section">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">Appearance</p>
            <h2>Theme & Density</h2>
          </div>
        </div>
        <div class="appearance-grid">
          <div class="form-group mb-0">
            <label for="theme-select">Collection Theme</label>
            <select id="theme-select" :value="uiPrefs.theme" @change="onThemeChange">
              <option value="indigo">Archive Violet</option>
              <option value="emerald">Forest Shelf</option>
              <option value="sunset">Amber Room</option>
              <option value="ocean">Harbor Blue</option>
              <option value="rose">Rosewood</option>
              <option value="slate">Graphite</option>
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
        <div class="theme-preview-grid mt-2">
          <div v-for="theme in themeSwatches" :key="theme.value" class="theme-chip" :class="{ active: uiPrefs.theme === theme.value }">
            <span class="theme-dot" :style="{ background: theme.color }"></span>
            <span>{{ theme.label }}</span>
          </div>
        </div>
        <p class="text-muted mt-2">Each theme changes the full collection palette. Preferences are saved in this browser and applied instantly.</p>
      </section>

      <section class="card settings-section">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">Integrations</p>
            <h2>Providers & Credentials</h2>
          </div>
        </div>
        <div class="info-grid mb-2">
          <div class="info-item">
            <label>IGDB</label>
            <span :class="info.igdb_configured ? 'status-ok' : 'status-error'">
              {{ info.igdb_configured ? 'Configured' : 'Not configured' }}
            </span>
          </div>
          <div v-if="info.pricecharting_configured" class="info-item">
            <label>PriceCharting</label>
            <span class="status-ok">Configured</span>
          </div>
          <div class="info-item">
            <label>eBay</label>
            <span :class="info.ebay_configured ? 'status-ok' : 'status-warn'">
              {{ info.ebay_configured ? 'Configured' : (info.ebay_client_id_set ? 'Client secret missing' : 'Client ID missing') }}
            </span>
          </div>
          <div class="info-item">
            <label>RAWG</label>
            <span :class="info.rawg_configured ? 'status-ok' : 'status-warn'">
              {{ info.rawg_configured ? 'Configured' : 'API key missing' }}
            </span>
          </div>
          <div class="info-item">
            <label>Admin Guard</label>
            <span :class="info.admin_key_configured ? 'status-ok' : 'status-warn'">
              {{ info.admin_key_configured ? 'API key protection enabled' : 'Local-only protection active' }}
            </span>
          </div>
        </div>

        <p class="text-muted mb-2">Provider credentials are stored server-side. Values are write-only in the UI.</p>
        <div class="secrets-grid">
          <div class="form-group mb-0">
            <label>Admin API Key (local browser)</label>
            <input
              v-model.trim="localAdminKey"
              type="password"
              autocomplete="off"
              placeholder="Used for protected admin actions"
            />
            <div class="secret-actions mt-2">
              <button @click="saveLocalAdminKey" class="btn btn-secondary btn-small">Save Local Key</button>
              <button @click="clearLocalAdminKey" class="btn btn-secondary btn-small">Clear</button>
            </div>
          </div>
          <div class="form-group mb-0">
            <label>IGDB Client ID</label>
            <input v-model.trim="secretsForm.igdb_client_id" type="text" autocomplete="off" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_igdb_client_id" type="checkbox" /> Clear stored value</label>
          </div>
          <div class="form-group mb-0">
            <label>IGDB Client Secret</label>
            <input v-model.trim="secretsForm.igdb_client_secret" type="password" autocomplete="new-password" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_igdb_client_secret" type="checkbox" /> Clear stored value</label>
          </div>
          <div class="form-group mb-0">
            <label>eBay Client ID</label>
            <input v-model.trim="secretsForm.ebay_client_id" type="text" autocomplete="off" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_ebay_client_id" type="checkbox" /> Clear stored value</label>
          </div>
          <div class="form-group mb-0">
            <label>eBay Client Secret</label>
            <input v-model.trim="secretsForm.ebay_client_secret" type="password" autocomplete="new-password" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_ebay_client_secret" type="checkbox" /> Clear stored value</label>
          </div>
          <div class="form-group mb-0">
            <label>RAWG API Key</label>
            <input v-model.trim="secretsForm.rawg_api_key" type="password" autocomplete="new-password" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_rawg_api_key" type="checkbox" /> Clear stored value</label>
          </div>
          <div class="form-group mb-0">
            <label>PriceCharting Token</label>
            <input v-model.trim="secretsForm.pricecharting_token" type="password" autocomplete="new-password" placeholder="Leave empty to keep current value" />
            <label class="clear-check"><input v-model="secretsForm.clear_pricecharting_token" type="checkbox" /> Clear stored value</label>
          </div>
        </div>
        <div class="secret-actions mt-2">
          <button @click="saveSecrets" class="btn btn-primary" :disabled="secretsSaving">
            {{ secretsSaving ? 'Saving…' : 'Save Credentials' }}
          </button>
        </div>
      </section>

      <section class="card settings-section">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">Automation</p>
            <h2>Maintenance Jobs</h2>
          </div>
        </div>

        <div class="info-grid mb-2">
          <div class="info-item">
            <label>Price Update Scheduler</label>
            <span :class="priceSchedulerEnabled ? 'status-ok' : 'status-warn'">
              {{ priceSchedulerEnabled ? `Active (${info.scheduler_cron})` : 'Disabled' }}
            </span>
          </div>
          <div class="info-item">
            <label>Automatic Backup</label>
            <span :class="autoBackupEnabled ? 'status-ok' : 'status-warn'">
              {{ autoBackupEnabled ? `Active (${info.auto_backup_count ?? 0} saved)` : 'Disabled' }}
            </span>
          </div>
          <div class="info-item">
            <label>Bulk Enrich</label>
            <span>{{ formatTimestamp(info.last_bulk_enrich_at) }}</span>
          </div>
          <div class="info-item">
            <label>Bulk Price Update</label>
            <span>{{ formatTimestamp(info.last_bulk_price_update_at) }}</span>
          </div>
          <div class="info-item">
            <label>Catalog Scrape</label>
            <span>{{ formatTimestamp(info.last_catalog_scrape_at) }}</span>
          </div>
        </div>

        <div class="settings-columns">
          <div class="subpanel">
            <h3>Automated Price Updates</h3>
            <p class="text-muted mb-2">Automatically refresh market prices on a schedule.</p>
            <div class="flex gap-2 items-center wrap-mobile">
              <select class="limit-input" v-model="schedulerInterval" style="width: auto;">
                <option :value="0">Off (manual only)</option>
                <option :value="2">Every 2 hours</option>
                <option :value="6">Every 6 hours</option>
                <option :value="12">Every 12 hours</option>
                <option :value="24">Every 24 hours</option>
                <option :value="168">Weekly</option>
              </select>
              <button @click="saveScheduler" class="btn btn-secondary" :disabled="schedulerSaving">
                {{ schedulerSaving ? 'Saving…' : 'Save Schedule' }}
              </button>
            </div>
          </div>

          <div class="subpanel">
            <h3>Automatic Backup</h3>
            <p class="text-muted mb-2">Create a local recovery ZIP every day at 02:15. Database, Price Browser catalog and uploads are included; provider credentials are excluded.</p>
            <label class="clear-check">
              <input v-model="autoBackupEnabled" type="checkbox" />
              Enable daily local backup
            </label>
            <div class="flex gap-2 items-center mt-2 wrap-mobile">
              <label class="text-muted">Keep:</label>
              <select class="limit-input" v-model.number="autoBackupRetention" style="width: auto;">
                <option :value="7">7 backups</option>
                <option :value="14">14 backups</option>
                <option :value="30">30 backups</option>
                <option :value="60">60 backups</option>
              </select>
              <button @click="saveAutoBackup" class="btn btn-secondary" :disabled="autoBackupSaving">
                {{ autoBackupSaving ? 'Saving…' : 'Save Backup Schedule' }}
              </button>
            </div>
            <p v-if="info.last_auto_backup_at" class="text-muted mt-2">Last backup: {{ formatTimestamp(info.last_auto_backup_at) }}{{ info.last_auto_backup_name ? ` · ${info.last_auto_backup_name}` : '' }}</p>
            <p v-if="info.last_auto_backup_error" class="text-error mt-2">Last backup error: {{ info.last_auto_backup_error }}</p>
          </div>

          <div class="subpanel">
            <h3>Bulk Cover Enrichment</h3>
            <p class="text-muted mb-2">Fetch missing covers from metadata providers.</p>
            <div class="flex gap-2 items-center mb-2 wrap-mobile">
              <label class="text-muted">Limit per run:</label>
              <input v-model.number="enrichLimit" type="number" min="1" max="500" class="limit-input" />
            </div>
            <button @click="runBulkEnrich" class="btn btn-primary" :disabled="enriching">
              {{ enriching ? `Enriching… (${enrichProgress.success + enrichProgress.failed}/${enrichProgress.total})` : 'Run Bulk Enrich' }}
            </button>
            <div v-if="enrichDone" class="result-box mt-2">
              {{ enrichProgress.success }} covers fetched, {{ enrichProgress.failed }} failed, {{ enrichProgress.total }} processed.
            </div>
          </div>

          <div class="subpanel">
            <h3>Bulk Price Update</h3>
            <p class="text-muted mb-2">Refresh market values across the library.</p>
            <div class="flex gap-2 items-center mb-2 wrap-mobile">
              <label class="text-muted">Limit per run:</label>
              <input v-model.number="priceLimit" type="number" min="1" max="500" class="limit-input" />
            </div>
            <button @click="runBulkPriceUpdate" class="btn btn-primary" :disabled="priceUpdating">
              {{ priceUpdating ? `Updating… (${priceProgress.done}/${priceProgress.total})` : 'Run Bulk Price Update' }}
            </button>
            <div v-if="priceUpdateDone" class="result-box mt-2">
              {{ priceProgress.success }} updated, {{ priceProgress.failed }} not found, {{ priceProgress.total }} total.
            </div>
          </div>
        </div>
      </section>

      <section class="card settings-section">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">Data</p>
            <h2>Import, Export & Backup</h2>
          </div>
        </div>

        <div class="backup-note mb-2">
          <strong>CSV export is not a full backup:</strong> use Full Backup to include your collection, lots, price history, Price Browser catalog and uploaded images in one ZIP file.
        </div>

        <div class="settings-columns">
          <div class="subpanel">
            <h3>CLZ Import</h3>
            <p class="text-muted mb-2">Import a CSV exported from CLZ / Collectorz.</p>
            <div class="flex gap-2 items-center import-row">
              <input type="file" accept=".csv" @change="onClzFile" ref="clzInput" />
              <button class="btn btn-primary" @click="importClz" :disabled="!clzFile || clzLoading">
                {{ clzLoading ? 'Importing…' : 'Import CLZ CSV' }}
              </button>
            </div>
            <div v-if="clzResult" class="mt-2">
              <p class="text-success">{{ clzResult.imported }} imported</p>
              <p v-if="clzResult.skipped" class="text-muted">{{ clzResult.skipped }} skipped</p>
              <p v-for="err in clzResult.errors" :key="err" class="text-error">{{ err }}</p>
            </div>
          </div>

          <div class="subpanel">
            <h3>Collection Export</h3>
            <p class="text-muted mb-2">Download the current collection as CSV.</p>
            <button @click="exportCSV" class="btn btn-secondary">Download CSV Export</button>
          </div>
        </div>

        <div class="settings-columns">
          <div class="subpanel">
            <h3>Full Backup</h3>
            <p class="text-muted mb-2">Create one portable ZIP with collection data, lots, price history, Price Browser catalog and every uploaded image.</p>
            <label class="clear-check">
              <input v-model="includeProviderCredentials" type="checkbox" />
              Include provider credentials in an encrypted file
            </label>
            <input
              v-if="includeProviderCredentials"
              v-model="backupPassword"
              type="password"
              minlength="12"
              autocomplete="new-password"
              placeholder="Backup password (12+ characters)"
              class="mt-2"
            />
            <p v-if="includeProviderCredentials" class="text-muted mt-2">The password is required to restore IGDB, eBay, RAWG and PriceCharting settings. Your admin key is never included.</p>
            <button class="btn btn-primary mt-2" @click="createFullBackup" :disabled="backupCreating">
              {{ backupCreating ? 'Creating backup…' : 'Download Full Backup' }}
            </button>
          </div>

          <div class="subpanel">
            <h3>Restore Full Backup</h3>
            <p class="text-muted mb-2">Inspect a Collectabase ZIP before restoring it. Restoring replaces this collection and creates a server-side safety backup first.</p>
            <input type="file" accept=".zip,application/zip" @change="onBackupFile" />
            <button class="btn btn-secondary mt-2" @click="inspectFullBackup" :disabled="!backupFile || backupInspecting">
              {{ backupInspecting ? 'Inspecting…' : 'Inspect Backup' }}
            </button>
            <div v-if="restorePreview" class="restore-preview mt-2">
              <strong>Backup preview</strong>
              <p>{{ restorePreview.counts?.games ?? 0 }} items · {{ restorePreview.counts?.lots ?? 0 }} lots · {{ restorePreview.uploads?.files ?? 0 }} images</p>
              <p class="text-muted">Created {{ formatBackupDate(restorePreview.created_at) }} · app {{ restorePreview.app_version || 'unknown' }}</p>
              <input
                v-if="restorePreview.includes_provider_credentials"
                v-model="restorePassword"
                type="password"
                autocomplete="current-password"
                placeholder="Backup password"
              />
              <input v-model="restoreConfirmation" type="text" placeholder="Type RESTORE to confirm" class="mt-2" />
              <button class="btn btn-danger mt-2" @click="restoreFullBackup" :disabled="restoring || restoreConfirmation.trim().toUpperCase() !== 'RESTORE'">
                {{ restoring ? 'Restoring…' : 'Restore This Backup' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="card settings-section danger-card">
        <div class="section-header mb-2">
          <div>
            <p class="section-kicker">Danger Zone</p>
            <h2>Reset & Cleanup</h2>
          </div>
        </div>
        <div class="settings-columns danger-columns">
          <div class="subpanel subpanel-danger">
            <h3>Clear Cover Links</h3>
            <p class="text-muted mb-2">Remove all saved cover URLs so the library can be enriched again from scratch.</p>
            <button @click="clearCovers" class="btn btn-danger" :disabled="clearing">
              {{ clearing ? 'Clearing…' : 'Clear All Covers' }}
            </button>
            <div v-if="clearDone" class="result-box mt-2">All covers cleared. You can run Bulk Enrich again now.</div>
          </div>

          <div class="subpanel subpanel-danger">
            <h3>Clear Database</h3>
            <p class="text-muted mb-2">Delete all games from the database. Use this only for test environments.</p>
            <button @click="clearDatabase" class="btn btn-danger" :disabled="clearLoading">
              {{ clearLoading ? 'Clearing…' : 'Clear Database' }}
            </button>
            <div v-if="clearResult" class="result-box mt-2">{{ clearResult.message }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { backupsApi, importApi, priceApi, settingsApi } from '../api'
import { getAdminApiKey, setAdminApiKey } from '../api/http'
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
const backupCreating = ref(false)
const includeProviderCredentials = ref(false)
const backupPassword = ref('')
const backupFile = ref(null)
const backupInspecting = ref(false)
const restorePreview = ref(null)
const restorePassword = ref('')
const restoreConfirmation = ref('')
const restoring = ref(false)
const priceUpdating = ref(false)
const priceUpdateDone = ref(false)
const priceLimit = ref(100)
const priceProgress = ref({ success: 0, failed: 0, total: 0, done: 0 })
const schedulerInterval = ref(0)
const schedulerSaving = ref(false)
const autoBackupEnabled = ref(true)
const autoBackupRetention = ref(14)
const autoBackupSaving = ref(false)
const uiPrefs = ref(loadUiPrefs())
const localAdminKey = ref(getAdminApiKey())
const secretsSaving = ref(false)
const secretsForm = ref({
  igdb_client_id: '',
  igdb_client_secret: '',
  ebay_client_id: '',
  ebay_client_secret: '',
  rawg_api_key: '',
  pricecharting_token: '',
  clear_igdb_client_id: false,
  clear_igdb_client_secret: false,
  clear_ebay_client_id: false,
  clear_ebay_client_secret: false,
  clear_rawg_api_key: false,
  clear_pricecharting_token: false,
})

const coverCoverage = computed(() => Number(info.value.cover_coverage_pct || 0))
const providersConfigured = computed(() => Number(info.value.providers_configured || 0))
const providersTotal = computed(() => Number(info.value.providers_total || 4))
const priceSchedulerEnabled = computed(() => Boolean(info.value.price_scheduler_enabled))
const storageHealthLabel = computed(() => {
  const labels = {
    healthy: 'Storage healthy',
    empty: 'New or empty collection',
    attention: 'Check storage',
  }
  return labels[info.value.storage_health] || 'Checking storage'
})
const setupHints = computed(() => {
  const hints = []
  if (!info.value.igdb_configured) hints.push('Set IGDB credentials to improve metadata and cover lookup.')
  if (!info.value.ebay_configured) hints.push('Add eBay credentials to enable reliable market prices.')
  if ((info.value.missing_covers ?? 0) > 0) hints.push('Run Bulk Enrich to reduce missing covers.')
  if ((info.value.remote_covers ?? 0) > 0) hints.push('Some covers still use remote URLs; re-enrich to cache more locally.')
  return hints
})
const themeSwatches = [
  { value: 'indigo', label: 'Archive Violet', color: '#aa87ff' },
  { value: 'emerald', label: 'Forest Shelf', color: '#62c696' },
  { value: 'sunset', label: 'Amber Room', color: '#e99a62' },
  { value: 'ocean', label: 'Harbor Blue', color: '#66bdda' },
  { value: 'rose', label: 'Rosewood', color: '#dd8198' },
  { value: 'slate', label: 'Graphite', color: '#a9b2c0' },
]

function onThemeChange(event) {
  const nextTheme = event?.target?.value || 'indigo'
  uiPrefs.value = setUiPrefs({ ...uiPrefs.value, theme: nextTheme })
}

function onDensityChange(event) {
  const nextDensity = event?.target?.value || 'comfortable'
  uiPrefs.value = setUiPrefs({ ...uiPrefs.value, density: nextDensity })
}

function saveLocalAdminKey() {
  setAdminApiKey(localAdminKey.value)
  notifySuccess('Local admin key saved for this browser.')
}

function clearLocalAdminKey() {
  localAdminKey.value = ''
  setAdminApiKey('')
  notifySuccess('Local admin key removed from this browser.')
}

function resetSecretsForm() {
  secretsForm.value = {
    igdb_client_id: '',
    igdb_client_secret: '',
    ebay_client_id: '',
    ebay_client_secret: '',
    rawg_api_key: '',
    pricecharting_token: '',
    clear_igdb_client_id: false,
    clear_igdb_client_secret: false,
    clear_ebay_client_id: false,
    clear_ebay_client_secret: false,
    clear_rawg_api_key: false,
    clear_pricecharting_token: false,
  }
}

async function saveSecrets() {
  const payload = { clear: [] }
  const fields = ['igdb_client_id', 'igdb_client_secret', 'ebay_client_id', 'ebay_client_secret', 'rawg_api_key', 'pricecharting_token']
  let changed = false

  for (const field of fields) {
    const value = String(secretsForm.value[field] || '').trim()
    const clearFlag = Boolean(secretsForm.value[`clear_${field}`])
    if (value) {
      payload[field] = value
      changed = true
      continue
    }
    if (clearFlag) {
      payload.clear.push(field)
      changed = true
    }
  }

  if (!changed) {
    notifyError('No credential changes to save.')
    return
  }

  secretsSaving.value = true
  try {
    const res = await settingsApi.updateSecrets(payload)
    if (!res.ok) {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to save credentials.')
      return
    }
    notifySuccess('Credentials saved server-side.')
    resetSecretsForm()
    await loadInfo()
  } catch (e) {
    console.error('Save credentials failed:', e)
    notifyError('Failed to save credentials.')
  } finally {
    secretsSaving.value = false
  }
}

async function saveScheduler() {
  schedulerSaving.value = true
  try {
    const res = await settingsApi.updateScheduler({ interval: schedulerInterval.value })
    if (res.ok) {
      notifySuccess('Scheduler updated.')
      await loadInfo()
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to update scheduler.')
    }
  } catch (e) {
    console.error('Update scheduler failed:', e)
    notifyError('Failed to update scheduler.')
  } finally {
    schedulerSaving.value = false
  }
}

async function saveAutoBackup() {
  autoBackupSaving.value = true
  try {
    const res = await settingsApi.updateAutoBackup({
      enabled: autoBackupEnabled.value,
      retention: autoBackupRetention.value,
    })
    if (res.ok) {
      notifySuccess(autoBackupEnabled.value ? 'Daily backup schedule saved.' : 'Automatic backups disabled.')
      await loadInfo()
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to update automatic backups.')
    }
  } catch (e) {
    console.error('Update automatic backups failed:', e)
    notifyError('Failed to update automatic backups.')
  } finally {
    autoBackupSaving.value = false
  }
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
    clzResult.value = { imported: 0, skipped: 0, errors: ['Import failed'] }
    notifyError('CLZ import failed.')
  } finally {
    clzLoading.value = false
  }
}

async function loadInfo() {
  infoLoading.value = true
  try {
    const res = await settingsApi.info()
    if (res.ok) {
      info.value = res.data
      schedulerInterval.value = res.data.scheduler_interval || 0
      autoBackupEnabled.value = res.data.auto_backup_enabled !== false
      autoBackupRetention.value = res.data.auto_backup_retention || 14
    } else {
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
      await loadInfo()
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

function onBackupFile(event) {
  backupFile.value = event.target.files?.[0] || null
  restorePreview.value = null
  restorePassword.value = ''
  restoreConfirmation.value = ''
}

function formatBackupDate(value) {
  if (!value) return 'unknown date'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

async function createFullBackup() {
  if (includeProviderCredentials.value && backupPassword.value.length < 12) {
    notifyError('Use a backup password with at least 12 characters when including provider credentials.')
    return
  }
  backupCreating.value = true
  try {
    const res = await backupsApi.create({
      include_provider_credentials: includeProviderCredentials.value,
      backup_password: includeProviderCredentials.value ? backupPassword.value : null
    })
    if (res.ok) notifySuccess(`Full backup downloaded (${res.data?.filename || 'collectabase-backup.zip'}).`)
    else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Full backup failed.')
    }
  } catch (error) {
    console.error('Full backup failed:', error)
    notifyError('Full backup failed.')
  } finally {
    backupCreating.value = false
  }
}

async function inspectFullBackup() {
  if (!backupFile.value) return
  backupInspecting.value = true
  restorePreview.value = null
  try {
    const formData = new FormData()
    formData.append('file', backupFile.value)
    const res = await backupsApi.inspect(formData)
    if (res.ok) {
      restorePreview.value = res.data
      notifySuccess('Backup inspected. Review the preview before restoring.')
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Backup inspection failed.')
    }
  } catch (error) {
    console.error('Backup inspection failed:', error)
    notifyError('Backup inspection failed.')
  } finally {
    backupInspecting.value = false
  }
}

async function restoreFullBackup() {
  if (!restorePreview.value?.token || restoreConfirmation.value.trim().toUpperCase() !== 'RESTORE') return
  if (!confirm('Restore this backup and replace the current collection? A safety backup will be created first.')) return
  restoring.value = true
  try {
    const res = await backupsApi.restore({
      restore_token: restorePreview.value.token,
      confirmation: restoreConfirmation.value,
      backup_password: restorePassword.value || null
    })
    if (res.ok) {
      notifySuccess('Collection restored. Reloading the app…')
      window.setTimeout(() => window.location.reload(), 1200)
    } else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Restore failed. The current collection was not changed.')
    }
  } catch (error) {
    console.error('Restore failed:', error)
    notifyError('Restore failed. The current collection was not changed.')
  } finally {
    restoring.value = false
  }
}

async function clearCovers() {
  if (!confirm('Are you sure? This will remove all cover URLs from your collection.')) return
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
  if (!confirm('Really delete the entire collection database? This cannot be undone.')) return
  clearLoading.value = true
  try {
    const res = await settingsApi.clearDatabase()
    clearResult.value = res.data
    if (res.ok) notifySuccess('Database cleared.')
    else {
      const detail = res.data?.detail
      notifyError(detail?.message || detail || 'Failed to clear database.')
    }
    location.reload()
  } catch (e) {
    clearResult.value = { message: `Error: ${e.message}` }
    notifyError('Failed to clear database.')
  } finally {
    clearLoading.value = false
  }
}

onMounted(loadInfo)
</script>

<style scoped>
.settings-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.settings-stack {
  display: grid;
  gap: 1rem;
}

.settings-section {
  display: grid;
  gap: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.15rem;
}

.section-kicker {
  margin: 0 0 0.2rem;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.mb-0 { margin-bottom: 0; }
.mt-2 { margin-top: 1rem; }
.wrap-mobile { flex-wrap: wrap; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.kpi-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
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
  font-family: var(--font-data);
}

.kpi-sub {
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.storage-status {
  display: inline-flex;
  margin-top: 0.55rem;
  padding: 0.18rem 0.45rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.storage-status-healthy {
  color: var(--success);
  background: color-mix(in srgb, var(--success) 12%, transparent);
}

.storage-status-empty {
  color: var(--text-muted);
  background: rgba(148, 163, 184, 0.12);
}

.storage-status-attention {
  color: var(--warning);
  background: color-mix(in srgb, var(--warning) 12%, transparent);
}

.storage-alert {
  display: grid;
  gap: 0.3rem;
  padding: 0.85rem 1rem;
  border: 1px solid rgba(245, 158, 11, 0.32);
  border-radius: 0.75rem;
  background: rgba(245, 158, 11, 0.08);
  color: var(--text);
  font-size: 0.84rem;
}

.storage-alert span {
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
  border-radius: 0.75rem;
  padding: 0.85rem;
}

.hint-title {
  font-size: 0.82rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.hint-list {
  margin: 0;
  padding-left: 1.15rem;
  display: grid;
  gap: 0.15rem;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.appearance-grid,
.secrets-grid,
.info-grid,
.run-grid,
.settings-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
}

.theme-preview-grid {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.theme-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
  font-size: 0.82rem;
}

.theme-chip.active {
  border-color: color-mix(in srgb, var(--primary) 55%, transparent);
  color: var(--text);
}

.theme-dot {
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 999px;
  display: inline-block;
}

.clear-check {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.secret-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.info-item,
.subpanel {
  background: rgba(0, 0, 0, 0.2);
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--glass-border);
}

.info-item label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.subpanel h3 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
}

.backup-note {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.25);
  border-radius: 0.75rem;
  padding: 0.85rem 1rem;
  color: #fcd34d;
}

.restore-preview {
  padding: 0.8rem;
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 0.65rem;
  background: rgba(245, 158, 11, 0.06);
}

.restore-preview p {
  margin: 0.35rem 0;
  font-size: 0.82rem;
}

.status-ok { color: var(--success); font-weight: 700; }
.status-error { color: var(--error); font-weight: 700; }
.status-warn { color: var(--warning); font-weight: 700; }

.limit-input {
  width: 80px;
  padding: 0.4rem;
  border-radius: var(--radius-sm, 0.4rem);
  border: 1px solid var(--glass-border);
  background: var(--surface, rgba(0, 0, 0, 0.2));
  color: var(--text);
}

.result-box {
  background: var(--surface, rgba(0, 0, 0, 0.2));
  border: 1px solid var(--glass-border);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md, 0.5rem);
  font-size: 0.9rem;
  color: var(--success);
}

.danger-card {
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.subpanel-danger {
  border-color: rgba(239, 68, 68, 0.2);
}

@media (max-width: 639px) {
  .settings-header,
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .limit-input {
    width: 100%;
  }

  .import-row {
    flex-direction: column;
    align-items: stretch;
  }

  .appearance-grid,
  .secrets-grid,
  .info-grid,
  .run-grid,
  .settings-columns,
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .secret-actions {
    flex-direction: column;
  }

  .secret-actions .btn {
    width: 100%;
  }
}
</style>
