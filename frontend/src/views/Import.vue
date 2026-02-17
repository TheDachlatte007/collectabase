<template>
  <div class="container">
    <h1 class="mb-3">Import Collection</h1>
    
    <div class="card">
      <h3>Import from CSV</h3>
      <p class="text-muted mb-2">
        Upload a CSV file exported from CLZ Games or similar tools.
        Expected columns: Title, Platform, Barcode, Region, Condition, Completeness, Purchase Price, Value, Notes
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
        <p v-if="result.errors?.length" class="text-error">
          ⚠️ {{ result.errors.length }} errors
        </p>
      </div>
    </div>

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

function handleFile(e) {
  file.value = e.target.files[0]
  result.value = null
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

async function exportCsv() {
  try {
    const res = await fetch('/api/games')
    const games = await res.json()
    
    // Convert to CSV
    const headers = ['Title', 'Platform', 'Region', 'Condition', 'Completeness', 'Purchase Price', 'Current Value', 'Notes']
    const rows = games.map(g => [
      g.title,
      g.platform_name,
      g.region,
      g.condition,
      g.completeness,
      g.purchase_price,
      g.current_value,
      g.notes
    ])
    
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
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
</style>
