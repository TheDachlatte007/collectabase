<template>
  <div class="container">
    <div class="flex flex-between items-center mb-3">
      <h1>My Games</h1>
      <div class="flex gap-2">
        <input 
          v-model="search" 
          placeholder="Search games..." 
          class="search-input"
        />
        <select v-model="selectedPlatform" class="filter-select">
          <option value="">All Platforms</option>
          <option v-for="p in platforms" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>
        <select v-model="selectedType" class="filter-select">
          <option value="">All Types</option>
          <option value="game">🎮 Games</option>
          <option value="console">🖥️ Consoles</option>
          <option value="accessory">🕹️ Accessories</option>
          <option value="misc">📦 Misc</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading games...</div>
    
    <div v-else-if="filteredGames.length === 0" class="empty">
      <h3>No games found</h3>
      <p>Add your first game or import from CSV</p>
    </div>

    <div v-else class="grid">
      <div v-for="game in filteredGames" :key="game.id" class="game-card">
        <div class="cover" :style="coverStyle(game.cover_url)">
          <span v-if="!game.cover_url">🎮</span>
        </div>
        <div class="info">
          <h3>{{ game.title }}</h3>
          <p class="text-muted">{{ game.platform_name }}</p>
          <div class="meta">
            <span v-if="game.condition" class="badge">{{ game.condition }}</span>
            <span v-if="game.completeness" class="badge">{{ game.completeness }}</span>
            <span v-if="game.item_type" class="badge type-badge">{{ typeLabel(game.item_type) }}</span>
          </div>
          <p v-if="game.current_value" class="value">€{{ game.current_value }}</p>
        </div>
        <router-link :to="`/game/${game.id}`" class="card-link"></router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const games = ref([])
const platforms = ref([])
const loading = ref(true)
const search = ref('')
const selectedPlatform = ref('')
const selectedType = ref('')

const filteredGames = computed(() => {
  return games.value.filter(g => {
    const matchesSearch = g.title.toLowerCase().includes(search.value.toLowerCase())
    const matchesPlatform = !selectedPlatform.value || g.platform_id === selectedPlatform.value
    const matchesType = !selectedType.value || g.item_type === selectedType.value
    return matchesSearch && matchesPlatform && matchesType
  })
})

function typeLabel(type) {
  const labels = {
    game: '🎮 Game',
    console: '🖥️ Console',
    accessory: '🕹️ Accessory',
    misc: '📦 Misc'
  }
  return labels[type] || type
}

function coverStyle(url) {
  return url ? { backgroundImage: `url(${url})` } : {}
}

async function loadData() {
  try {
    const [gamesRes, platformsRes] = await Promise.all([
      fetch('/api/games'),
      fetch('/api/platforms')
    ])
    games.value = await gamesRes.json()
    platforms.value = await platformsRes.json()
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.search-input, .filter-select {
  width: auto;
  min-width: 150px;
}

.game-card {
  background: var(--bg-light);
  border-radius: 0.75rem;
  overflow: hidden;
  border: 1px solid var(--border);
  position: relative;
  transition: transform 0.2s;
}

.game-card:hover {
  transform: translateY(-4px);
}

.cover {
  aspect-ratio: 3/4;
  background: var(--bg);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
}

.info {
  padding: 1rem;
}

.info h3 {
  font-size: 1rem;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.badge {
  background: var(--bg);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.value {
  color: var(--success);
  font-weight: bold;
  margin-top: 0.5rem;
}

.card-link {
  position: absolute;
  inset: 0;
}

.type-badge {
  background: var(--primary, #6366f1);
  color: white;
}

</style>
