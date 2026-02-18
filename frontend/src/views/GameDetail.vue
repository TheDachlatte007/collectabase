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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const game = ref(null)
const loading = ref(true)

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

onMounted(loadGame)
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

</style>
