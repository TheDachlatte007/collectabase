<template>
  <div class="container">
    <h1 class="mb-3">Import Collection</h1>

    <!-- Normal CSV Import -->
    <div class="card">
      <h3>Import from CSV</h3>
      <p class="text-muted mb-2">
        Upload a CSV file with columns: Title, Platform, Barcode, Region, Condition, Completeness, Purchase Price, Value, Notes
      </p>

      <input
        type="file"
        accept=".csv"
        @change="handleFile"
        class="mb-2"
      />

      <button
        @click="importFile"
        class="btn btn-primary"
        :disabled="!file || importing"
      >
        {{ importing ? 'Importing...' : 'Import' }}
      </button>

      <div v-if="result" class="result mt-2">
        <p v-if="result.imported > 0" class="text-success">
          ✅ Imported {{ result.imported }} games
        </p>
        <div v-if="result.errors?.length" class="error-block">
          <p class="text-error">⚠️ {{ result.errors.length }} row(s) failed:</p>
          <ul class="error-list">
            <li v-for="err in result.errors" :key="err">{{ err }}</li>
          </ul>
        </div>
        <p v-if="result.error" class="text-error">❌ {{ result.error }}</p>
      </div>
    </div>

    <!-- CLZ Import -->
    <div class="card mt-3">
      <h3>Import from CLZ Games</h3>
      <p class="text-muted mb-2">
        Upload a CSV exported from CLZ Games. Handles CLZ column names, European price formats (€, comma decimals) and multiple date formats.
      </p>

      <input
        type="file"
        accept=".csv"
        @change="handleClzFile"
        class="mb-2"
      />

      <button
        @click="importClzFile"
        class="btn btn-primary"
        :disabled="!clzFile || clzImporting"
      >
        {{ clzImporting ? 'Importing...' : 'Import CLZ' }}
      </button>

      <div v-if="clzResult" class="result mt-2">
        <p v-if="clzResult.imported > 0" class="text-success">
          ✅ Imported {{ clzResult.imported }} games
        </p>
        <p v-if="clzResult.skipped > 0" class="text-muted">
          ⏭️ Skipped {{ clzResult.skipped }} rows (empty title)
        </p>
        <div v-if="clzResult.errors?.length" class="error-block">
          <p class="text-error">⚠️ {{ clzResult.errors.length }} row(s) failed:</p>
          <ul class="error-list">
            <li v-for="err in clzResult.errors" :key="err">{{ err }}</li>
          </ul>
        </div>
        <p v-if="clzResult.error" class="text-error">❌ {{ clzResult.error }}</p>
      </div>
    </div>

    <!-- Export -->
    <div class="card mt-3">
      <h3>Export Collection</h3>
      <p class="text-muted mb-2">Download your collection as CSV</p>
      <button @click="exportCsv" class="btn btn-secondary">
        Download CSV
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const file = ref(null)
const importing = ref(false)
const result = ref(null)

const clzFile = ref(null)
const clzImporting = ref(false)
const clzResult = ref(null)

function handleFile(e) {
  file.value = e.target.files[0]
  result.value = null
}

function handleClzFile(e) {
  clzFile.value = e.target.files[0]
  clzResult.value = null
}

async function importFile() {
  if (!file.value) return

  importing.value = true
  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const res = await fetch('/api/import/csv', {
      method: 'POST',
      body: formData
    })
    result.value = await res.json()
  } catch (e) {
    console.error('Import failed:', e)
    result.value = { error: 'Import failed' }
  } finally {
    importing.value = false
  }
}

async function importClzFile() {
  if (!clzFile.value) return

  clzImporting.value = true
  const formData = new FormData()
  formData.append('file', clzFile.value)

  try {
    const res = await fetch('/api/import/clz', {
      method: 'POST',
      body: formData
    })
    clzResult.value = await res.json()
  } catch (e) {
    console.error('CLZ import failed:', e)
    clzResult.value = { error: 'Import failed' }
  } finally {
    clzImporting.value = false
  }
}

async function exportCsv() {
  try {
    const res = await fetch('/api/export/csv')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = 'collectabase_export.csv'
    a.click()

    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export failed:', e)
  }
}
</script>

<style scoped>
.result {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.5rem;
}

.error-block {
  margin-top: 0.5rem;
}

.error-list {
  margin: 0.25rem 0 0 1.25rem;
  font-size: 0.85rem;
  color: var(--error, #ef4444);
}
</style>
