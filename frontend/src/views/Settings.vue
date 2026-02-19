<template>
  <div class="container">
    <h1 class="mb-3">⚙️ Settings</h1>

    <!-- App Info -->
    <div class="card mb-3">
      <h3 class="mb-2">App Info</h3>
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
          <label>Total Items</label>
          <span>{{ info.total_items ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>Without Cover</label>
          <span>{{ info.missing_covers ?? '—' }}</span>
        </div>
        <div class="info-item">
          <label>DB Size</label>
          <span>{{ info.db_size || '—' }}</span>
        </div>
        <div class="info-item">
          <label>Wishlist Items</label>
          <span>{{ info.wishlist_count ?? '—' }}</span>
        </div>
      </div>
    </div>

    <!-- Cover Enrichment -->
    <div class="card mb-3">
      <h3 class="mb-2">🖼 Cover Enrichment</h3>
      <p class="text-muted mb-2">Automatically fetch covers for all items without one from IGDB and GameTDB.</p>
      <div class="flex gap-2 items-center mb-2">
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

    <!-- Database -->
    <div class="card mb-3">
      <h3 class="mb-2">🗄 Database</h3>
      <p class="text-muted mb-2">Export your entire collection as CSV backup.</p>
      <button @click="exportCSV" class="btn btn-secondary">📥 Export Collection as CSV</button>
    </div>

    <!-- Danger Zone -->
    <div class="card danger-card mb-3">
      <h3 class="mb-2">⚠️ Danger Zone</h3>
      <p class="text-muted mb-2">Remove all cover URLs from the database (useful to re-enrich from scratch).</p>
      <button @click="clearCovers" class="btn btn-danger" :disabled="clearing">
        {{ clearing ? '⏳ Clearing...' : '🗑 Clear All Covers' }}
      </button>
      <div v-if="clearDone" class="result-box mt-2">✅ All covers cleared – run Bulk Enrich to re-fetch.</div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const info = ref({})
const enriching = ref(false)
const enrichDone = ref(false)
const enrichLimit = ref(500)
const enrichProgress = ref({ success: 0, failed: 0, total: 0 })
const clearing = ref(false)
const clearDone = ref(false)

async function loadInfo() {
  try {
    const res = await fetch('/api/settings/info')
    if (res.ok) info.value = await res.json()
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
}

async function runBulkEnrich() {
  enriching.value = true
  enrichDone.value = false
  enrichProgress.value = { success: 0, failed: 0, total: 0 }
  try {
    const res = await fetch(`/api/enrich/all?limit=${enrichLimit.value}`, { method: 'POST' })
    if (res.ok) {
      enrichProgress.value = await res.json()
      enrichDone.value = true
      await loadInfo() // refresh missing covers count
    }
  } catch (e) {
    console.error('Bulk enrich failed:', e)
  } finally {
    enriching.value = false
  }
}

async function exportCSV() {
  window.open('/api/export/csv', '_blank')
}

async function clearCovers() {
  if (!confirm('Are you sure? This will remove ALL cover URLs from your collection.')) return
  clearing.value = true
  clearDone.value = false
  try {
    const res = await fetch('/api/settings/clear-covers', { method: 'POST' })
    if (res.ok) {
      clearDone.value = true
      await loadInfo()
    }
  } catch (e) {
    console.error('Clear covers failed:', e)
  } finally {
    clearing.value = false
  }
}

onMounted(loadInfo)
</script>

<style scoped>
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
</style>
