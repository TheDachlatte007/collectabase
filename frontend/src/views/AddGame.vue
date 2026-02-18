<template>
  <div class="container">
    <h1 class="mb-3">{{ isEditMode ? 'Edit Game' : 'Add Game' }}</h1>

    <div class="form-layout">
      <!-- IGDB Search -->
      <div class="card mb-3">
        <h3>Search IGDB (optional)</h3>
        <div class="flex gap-2 mb-2">
          <input v-model="igdbSearch" placeholder="Search by title..." @keyup.enter="searchIgdb" />
          <button @click="searchIgdb" class="btn btn-secondary" :disabled="igdbLoading">
            {{ igdbLoading ? 'Searching...' : 'Search' }}
          </button>
        </div>
        <div v-if="igdbResults.length > 0" class="igdb-results">
          <div v-for="result in igdbResults" :key="result.igdb_id" 
               class="igdb-item" @click="fillFromIgdb(result)">
            <img v-if="result.cover_url" :src="result.cover_url" />
            <div>
              <strong>{{ result.title }}</strong>
              <p class="text-muted">{{ result.platforms?.join(', ') }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Game Form -->
      <form @submit.prevent="saveGame" class="card">
        <div class="form-grid">
          <div class="form-group">
            <label>Title *</label>
            <input v-model="game.title" required />
          </div>
          
          <div class="form-group">
            <label>Platform *</label>
            <select v-model="game.platform_id" required>
              <option value="">Select platform</option>
              <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Barcode</label>
            <input v-model="game.barcode" />
          </div>

          <div class="form-group">
            <label>Region</label>
            <select v-model="game.region">
              <option value="">Select</option>
              <option>PAL</option>
              <option>NTSC</option>
              <option>EU</option>
              <option>US</option>
              <option>JP</option>
            </select>
          </div>

          <div class="form-group">
            <label>Condition</label>
            <select v-model="game.condition">
              <option value="">Select</option>
              <option>Mint</option>
              <option>Good</option>
              <option>Fair</option>
              <option>Poor</option>
            </select>
          </div>

          <div class="form-group">
            <label>Completeness</label>
            <select v-model="game.completeness">
              <option value="">Select</option>
              <option>New/Sealed</option>
              <option>CIB (Complete In Box)</option>
              <option>Box + Game</option>
              <option>Game + Manual</option>
              <option>Loose</option>
            </select>
          </div>

          <div class="form-group">
            <label>Purchase Price (€)</label>
            <input v-model.number="game.purchase_price" type="number" step="0.01" />
          </div>

          <div class="form-group">
            <label>Current Value (€)</label>
            <input v-model.number="game.current_value" type="number" step="0.01" />
          </div>

          <div class="form-group full-width">
            <label>Notes</label>
            <textarea v-model="game.notes" rows="3"></textarea>
          </div>

          <div class="form-group full-width">
            <label class="flex items-center gap-2">
              <input v-model="game.is_wishlist" type="checkbox" />
              Add to Wishlist
            </label>
          </div>
        </div>

        <div class="flex gap-2 mt-3">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : (isEditMode ? 'Update Game' : 'Save Game') }}
          </button>
          <router-link to="/" class="btn btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const platforms = ref([])
const saving = ref(false)
const igdbSearch = ref('')
const igdbResults = ref([])
const igdbLoading = ref(false)
const isEditMode = ref(false)
const editId = ref(null)

const game = ref({
  title: '',
  platform_id: '',
  barcode: '',
  region: '',
  condition: '',
  completeness: '',
  purchase_price: null,
  current_value: null,
  notes: '',
  is_wishlist: false
})

async function loadPlatforms() {
  const res = await fetch('/api/platforms')
  platforms.value = await res.json()
}

async function loadGame(id) {
  try {
    const res = await fetch(`/api/games/${id}`)
    if (res.ok) {
      const data = await res.json()
      game.value = {
        title: data.title || '',
        platform_id: data.platform_id || '',
        barcode: data.barcode || '',
        region: data.region || '',
        condition: data.condition || '',
        completeness: data.completeness || '',
        purchase_price: data.purchase_price || null,
        current_value: data.current_value || null,
        notes: data.notes || '',
        is_wishlist: data.is_wishlist || false,
        igdb_id: data.igdb_id || null,
        cover_url: data.cover_url || null,
        genre: data.genre || null,
        description: data.description || null,
      }
    }
  } catch (e) {
    console.error('Failed to load game:', e)
  }
}

async function searchIgdb() {
  if (!igdbSearch.value) return
  igdbLoading.value = true
  try {
    const res = await fetch('/api/lookup/igdb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: igdbSearch.value })
    })
    const data = await res.json()
    igdbResults.value = data.results || []
  } catch (e) {
    console.error('IGDB search failed:', e)
  } finally {
    igdbLoading.value = false
  }
}

function fillFromIgdb(result) {
  game.value.title = result.title
  game.value.igdb_id = result.igdb_id
  game.value.cover_url = result.cover_url
  game.value.genre = result.genre
  game.value.description = result.description
  igdbResults.value = []
}

async function saveGame() {
  saving.value = true
  try {
    const url = isEditMode.value ? `/api/games/${editId.value}` : '/api/games'
    const method = isEditMode.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(game.value)
    })
    if (res.ok) {
      router.push(isEditMode.value ? `/game/${editId.value}` : '/')
    }
  } catch (e) {
    console.error('Failed to save:', e)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadPlatforms()
  if (route.params.id) {
    isEditMode.value = true
    editId.value = route.params.id
    await loadGame(route.params.id)
  }
})
</script>


<style scoped>
.form-layout {
  max-width: 800px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.form-grid .full-width {
  grid-column: 1 / -1;
}

.igdb-results {
  margin-top: 1rem;
}

.igdb-item {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.igdb-item:hover {
  background: var(--bg-lighter);
}

.igdb-item img {
  width: 60px;
  height: 80px;
  object-fit: cover;
  border-radius: 0.25rem;
}
</style>
