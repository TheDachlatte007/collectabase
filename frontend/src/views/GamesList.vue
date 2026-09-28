<template>
  <div class="container">
    <div class="list-header mb-3">
      <div class="collection-heading">
        <p class="collection-kicker">Personal library</p>
        <h1>My Collection</h1>
        <p class="collection-summary">{{ collectionSummary }}</p>
      </div>
      <router-link to="/care" class="care-link" title="Review collection details">
        <span>Collection Care</span>
        <strong>{{ careCount }}</strong>
      </router-link>
      <div class="filters">
        <input
          v-model="search"
          placeholder="Search collection..."
          class="search-input"
        />
        <select v-model="selectedPlatform" class="filter-select">
          <option value="">All Platforms ({{ games.length }})</option>
          <option v-for="p in platforms" :key="p.id" :value="p.id">
            {{ p.name }} ({{ platformCounts[p.id] || 0 }})
          </option>
        </select>
        <select v-model="selectedType" class="filter-select">
          <option value="">All Types</option>
          <option value="game">🎮 Games</option>
          <option value="console">🖥️ Consoles</option>
          <option value="accessory">🕹️ Accessories</option>
          <option value="figure">🧸 Figures</option>
          <option value="comic">📚 Comics</option>
          <option value="funko">🍿 Funko Pops</option>
          <option value="misc">📦 Misc</option>
        </select>
        <select v-model="sortBy" class="filter-select">
          <option value="name_asc">Sort: Name A-Z</option>
          <option value="name_desc">Sort: Name Z-A</option>
          <option value="value_desc">Sort: Value High-Low</option>
          <option value="value_asc">Sort: Value Low-High</option>
          <option value="date_desc">Sort: Date Added Newest</option>
          <option value="date_asc">Sort: Date Added Oldest</option>
          <option value="platform_asc">Sort: Platform A-Z</option>
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
        <div class="cover">
          <img
            v-if="coverSrc(game)"
            :src="coverSrc(game)"
            class="cover-image"
            @error="markBroken(game.id)"
          />
          <span v-else>{{ coverEmoji(game.item_type) }}</span>
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
import { useGameStore } from '../stores/useGameStore'
import { coverEmoji, makeFallbackCoverDataUrl, needsAutoCover } from '../utils/coverFallback'
import { storeToRefs } from 'pinia'

const store = useGameStore()
const { collection: games, platforms, loading } = storeToRefs(store)

const search = ref('')
const selectedPlatform = ref('')
const selectedType = ref('')
const sortBy = ref('name_asc')
const brokenCoverIds = ref({})

const filteredGames = computed(() => {
  const filtered = games.value.filter(g => {
    const haystack = `${g.title || ''} ${g.platform_name || ''} ${g.location || ''}`.toLowerCase()
    const matchesSearch = haystack.includes(search.value.toLowerCase())
    const matchesPlatform = !selectedPlatform.value || String(g.platform_id) === String(selectedPlatform.value)
    const matchesType = !selectedType.value || g.item_type === selectedType.value
    return matchesSearch && matchesPlatform && matchesType
  })

  const sorted = [...filtered]
  sorted.sort((a, b) => compareGames(a, b, sortBy.value))
  return sorted
})

const platformCounts = computed(() => {
  const counts = {}
  for (const g of games.value) {
    const key = g.platform_id
    if (key == null) continue
    counts[key] = (counts[key] || 0) + 1
  }
  return counts
})

const collectionSummary = computed(() => {
  const count = games.value.length
  const platformsCount = new Set(games.value.map((game) => game.platform_id).filter((id) => id != null)).size
  const trackedValue = games.value.reduce((total, game) => total + (safeNumber(game.current_value) ?? 0) * (safeNumber(game.quantity) ?? 1), 0)
  const itemsText = `${count} ${count === 1 ? 'item' : 'items'}`
  const platformsText = `${platformsCount} ${platformsCount === 1 ? 'platform' : 'platforms'}`
  return trackedValue > 0
    ? `${itemsText} across ${platformsText} · €${trackedValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} tracked value`
    : `${itemsText} across ${platformsText}`
})

const careCount = computed(() => games.value.filter((game) => !game.cover_url || safeNumber(game.current_value) == null).length)

function typeLabel(type) {
  const labels = {
    game: '🎮 Game',
    console: '🖥️ Console',
    accessory: '🕹️ Accessory',
    figure: '🧸 Figure',
    comic: '📚 Comic',
    funko: '🍿 Funko',
    manga: '📖 Manga',
    misc: '📦 Misc'
  }
  return labels[type] || type
}

function markBroken(id) {
  brokenCoverIds.value[id] = true
}

function coverSrc(game) {
  if (!game) return null
  if (game.cover_url && !brokenCoverIds.value[game.id]) return game.cover_url
  if (needsAutoCover(game.item_type)) return makeFallbackCoverDataUrl(game)
  return null
}

function safeNumber(value) {
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function safeDate(value) {
  const ts = new Date(value).getTime()
  return Number.isFinite(ts) ? ts : null
}

function compareText(a, b) {
  return String(a || '').localeCompare(String(b || ''), undefined, { sensitivity: 'base' })
}

function compareGames(a, b, mode) {
  if (mode === 'name_desc') return compareText(b.title, a.title)
  if (mode === 'value_desc') {
    const av = safeNumber(a.current_value)
    const bv = safeNumber(b.current_value)
    if (av == null && bv == null) return compareText(a.title, b.title)
    if (av == null) return 1
    if (bv == null) return -1
    if (av !== bv) return bv - av
    return compareText(a.title, b.title)
  }
  if (mode === 'value_asc') {
    const av = safeNumber(a.current_value)
    const bv = safeNumber(b.current_value)
    if (av == null && bv == null) return compareText(a.title, b.title)
    if (av == null) return 1
    if (bv == null) return -1
    if (av !== bv) return av - bv
    return compareText(a.title, b.title)
  }
  if (mode === 'date_desc' || mode === 'date_asc') {
    const at = safeDate(a.created_at) ?? safeNumber(a.id) ?? 0
    const bt = safeDate(b.created_at) ?? safeNumber(b.id) ?? 0
    if (at !== bt) return mode === 'date_desc' ? bt - at : at - bt
    return compareText(a.title, b.title)
  }
  if (mode === 'platform_asc') {
    const platformCmp = compareText(a.platform_name, b.platform_name)
    if (platformCmp !== 0) return platformCmp
    return compareText(a.title, b.title)
  }
  return compareText(a.title, b.title)
}

onMounted(() => store.load())
</script>

<style scoped>
/* ── Filter bar ── */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.collection-heading h1 {
  margin: 0;
}

.collection-kicker {
  margin: 0 0 0.2rem;
  color: var(--primary);
  font-size: 0.73rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.collection-summary {
  margin: 0.3rem 0 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.care-link {
  display: inline-flex;
  align-items: center;
  align-self: center;
  gap: 0.5rem;
  padding: 0.45rem 0.6rem 0.45rem 0.75rem;
  border: 1px solid var(--glass-border);
  border-radius: 999px;
  color: var(--text-muted);
  background: var(--bg-light);
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  transition: border-color 0.18s ease, color 0.18s ease;
}

.care-link:hover {
  border-color: color-mix(in srgb, var(--primary) 50%, transparent);
  color: var(--text);
}

.care-link strong {
  display: grid;
  min-width: 1.4rem;
  height: 1.4rem;
  place-items: center;
  border-radius: 50%;
  color: var(--primary);
  background: var(--primary-soft);
  font-size: 0.7rem;
}

.filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
}

.search-input, .filter-select {
  width: auto;
  min-width: 150px;
}

@media (max-width: 639px) {
  .list-header {
    flex-direction: column;
    align-items: stretch;
  }

  .care-link {
    align-self: flex-start;
  }

  .filters {
    flex-direction: column;
    justify-content: stretch;
  }

  .search-input, .filter-select {
    width: 100%;
    min-width: unset;
  }
}

.game-card {
  background: var(--bg-light);
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid var(--glass-border);
  position: relative;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease, border-color 0.3s ease;
  backdrop-filter: var(--card-blur);
  -webkit-backdrop-filter: var(--card-blur);
  box-shadow: var(--glass-shadow);
}

.game-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px 0 rgba(0, 0, 0, 0.5);
  border-color: var(--glass-border-hover);
}

.cover {
  aspect-ratio: 3/4;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.05), rgba(0, 0, 0, 0.4));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
