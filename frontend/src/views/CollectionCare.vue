<template>
  <div class="container care-page">
    <header class="care-header">
      <div>
        <p class="care-kicker">Collection Care</p>
        <h1>Keep the collection complete</h1>
        <p class="text-muted">Review entries that still need a cover, current value, or a few useful collection details.</p>
      </div>
      <router-link to="/add" class="btn btn-primary">+ Add Item</router-link>
    </header>

    <div v-if="loading" class="loading">Reviewing your collection...</div>

    <template v-else>
      <section class="care-overview" aria-label="Collection care summary">
        <button
          v-for="group in issueGroups"
          :key="group.key"
          type="button"
          class="care-summary"
          :class="{ active: activeFilter === group.key }"
          :aria-pressed="activeFilter === group.key"
          @click="activeFilter = group.key"
        >
          <span class="summary-icon">{{ group.icon }}</span>
          <span class="summary-copy">
            <span>{{ group.label }}</span>
            <strong>{{ group.count }}</strong>
          </span>
          <span class="summary-note">{{ group.note }}</span>
        </button>
      </section>

      <section class="care-panel card">
        <div class="care-toolbar">
          <div>
            <p class="care-kicker">{{ activeGroup.label }}</p>
            <h2>{{ filteredItems.length }} {{ filteredItems.length === 1 ? 'item' : 'items' }} to review</h2>
          </div>
          <input v-model.trim="search" class="care-search" type="search" placeholder="Search this list..." />
        </div>

        <div v-if="filteredItems.length" class="care-list">
          <article v-for="game in filteredItems" :key="game.id" class="care-item">
            <div class="care-cover" :class="{ 'care-cover-placeholder': !coverSrc(game) }">
              <img v-if="coverSrc(game)" :src="coverSrc(game)" :alt="`${game.title} cover`" @error="markBroken(game.id)" />
              <span v-else>{{ coverEmoji(game.item_type) }}</span>
            </div>
            <div class="care-item-copy">
              <h3>{{ game.title }}</h3>
              <p class="text-muted">{{ game.platform_name || typeLabel(game.item_type) }}</p>
              <div class="issue-list">
                <span v-for="issue in issuesFor(game)" :key="issue.key" class="issue-pill" :class="`issue-${issue.key}`">
                  {{ issue.label }}
                </span>
              </div>
            </div>
            <div class="care-actions">
              <router-link :to="`/game/${game.id}`" class="btn btn-secondary btn-small">View</router-link>
              <router-link :to="`/edit/${game.id}`" class="btn btn-primary btn-small">Fix</router-link>
            </div>
          </article>
        </div>

        <div v-else class="care-empty">
          <span class="care-empty-icon">✓</span>
          <h3>{{ search ? 'No matching items' : 'Nothing needs attention here' }}</h3>
          <p>{{ search ? 'Try a different search term.' : 'This part of your collection is in good shape.' }}</p>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../stores/useGameStore'
import { coverEmoji, makeFallbackCoverDataUrl, needsAutoCover } from '../utils/coverFallback'

const store = useGameStore()
const { collection, loading } = storeToRefs(store)
const activeFilter = ref('all')
const search = ref('')
const brokenCoverIds = ref({})

function isMissingValue(value) {
  return value === null || value === undefined || value === ''
}

function issuesFor(game) {
  const issues = []
  if (!game.cover_url) issues.push({ key: 'cover', label: 'Missing cover' })
  if (isMissingValue(game.current_value)) issues.push({ key: 'value', label: 'No current value' })
  if (!game.condition) issues.push({ key: 'condition', label: 'No condition' })
  if (!game.location) issues.push({ key: 'location', label: 'No location' })
  if (game.item_type === 'game' && !game.platform_id) issues.push({ key: 'platform', label: 'No platform' })
  return issues
}

const issueGroups = computed(() => {
  const items = collection.value || []
  const withIssue = (key) => items.filter((game) => issuesFor(game).some((issue) => issue.key === key)).length
  const needsDetails = items.filter((game) => issuesFor(game).some((issue) => ['condition', 'location', 'platform'].includes(issue.key))).length
  const complete = items.filter((game) => issuesFor(game).length === 0).length
  return [
    { key: 'all', icon: '✦', label: 'All reviews', count: items.length - complete, note: `${complete} complete` },
    { key: 'cover', icon: '▣', label: 'Covers', count: withIssue('cover'), note: 'Add or enrich artwork' },
    { key: 'value', icon: '€', label: 'Values', count: withIssue('value'), note: 'Set a current value' },
    { key: 'details', icon: '≡', label: 'Details', count: needsDetails, note: 'Condition, location, platform' },
  ]
})

const activeGroup = computed(() => issueGroups.value.find((group) => group.key === activeFilter.value) || issueGroups.value[0])

const filteredItems = computed(() => {
  const query = search.value.toLocaleLowerCase()
  return (collection.value || [])
    .filter((game) => {
      const issues = issuesFor(game)
      if (activeFilter.value === 'cover') return issues.some((issue) => issue.key === 'cover')
      if (activeFilter.value === 'value') return issues.some((issue) => issue.key === 'value')
      if (activeFilter.value === 'details') return issues.some((issue) => ['condition', 'location', 'platform'].includes(issue.key))
      return issues.length > 0
    })
    .filter((game) => !query || `${game.title} ${game.platform_name || ''} ${game.item_type || ''}`.toLocaleLowerCase().includes(query))
    .sort((a, b) => issuesFor(b).length - issuesFor(a).length || String(a.title).localeCompare(String(b.title)))
})

function markBroken(id) {
  brokenCoverIds.value[id] = true
}

function coverSrc(game) {
  if (!game || brokenCoverIds.value[game.id]) return null
  if (game.cover_url) return game.cover_url
  if (needsAutoCover(game.item_type)) return makeFallbackCoverDataUrl(game)
  return null
}

function typeLabel(type) {
  const labels = {
    game: 'Game', console: 'Console', controller: 'Controller', accessory: 'Accessory',
    figure: 'Figure', comic: 'Comic', funko: 'Funko Pop', manga: 'Manga', vinyl: 'Vinyl', misc: 'Misc',
  }
  return labels[type] || 'Item'
}

onMounted(() => store.load())
</script>

<style scoped>
.care-page { display: grid; gap: 1rem; }

.care-header,
.care-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.care-header h1,
.care-toolbar h2 { margin: 0; }

.care-header > div > .text-muted { margin-top: 0.4rem; max-width: 620px; }

.care-kicker {
  margin: 0 0 0.22rem;
  color: var(--primary);
  font-size: 0.73rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.care-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.7rem;
}

.care-summary {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.45rem 0.65rem;
  padding: 0.9rem;
  color: var(--text);
  text-align: left;
  background: var(--bg-light);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.care-summary:hover,
.care-summary.active {
  border-color: color-mix(in srgb, var(--primary) 55%, transparent);
  background: color-mix(in srgb, var(--bg-light) 88%, var(--primary));
}

.summary-icon {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: 0.5rem;
  color: var(--primary);
  background: var(--primary-soft);
  font-weight: 700;
}

.summary-copy { display: grid; gap: 0.05rem; font-size: 0.82rem; color: var(--text-muted); }
.summary-copy strong { color: var(--text); font-size: 1.35rem; line-height: 1; }
.summary-note { grid-column: 1 / -1; color: var(--text-muted); font-size: 0.72rem; }

.care-panel { display: grid; gap: 1rem; }
.care-search { width: min(100%, 260px); }
.care-list { display: grid; border-top: 1px solid var(--glass-border); }

.care-item {
  display: grid;
  grid-template-columns: 3.5rem minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--glass-border);
}

.care-cover {
  width: 3.5rem;
  height: 4.5rem;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--glass-border);
  border-radius: 0.5rem;
  background: var(--bg);
  font-size: 1.45rem;
}

.care-cover img { width: 100%; height: 100%; object-fit: cover; }
.care-cover-placeholder { color: var(--text-muted); }
.care-item-copy { min-width: 0; }
.care-item-copy h3 { margin: 0; font-size: 1rem; }
.care-item-copy p { margin: 0.1rem 0 0; font-size: 0.8rem; }

.issue-list { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.45rem; }
.issue-pill { padding: 0.15rem 0.4rem; border-radius: 999px; font-size: 0.69rem; font-weight: 600; background: rgba(255, 255, 255, 0.06); color: var(--text-muted); }
.issue-cover { color: #e9ba74; background: rgba(233, 186, 116, 0.12); }
.issue-value { color: #8fc5e7; background: rgba(143, 197, 231, 0.12); }
.issue-platform { color: #e4a6d1; background: rgba(228, 166, 209, 0.12); }

.care-actions { display: flex; gap: 0.45rem; }
.care-empty { padding: 2.2rem 1rem; text-align: center; color: var(--text-muted); }
.care-empty h3 { margin: 0.5rem 0 0.15rem; color: var(--text); }
.care-empty p { margin: 0; }
.care-empty-icon { display: inline-grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: 50%; color: var(--success); border: 1px solid color-mix(in srgb, var(--success) 45%, transparent); }

@media (max-width: 850px) {
  .care-overview { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 639px) {
  .care-header > .btn { width: 100%; }
  .care-search { width: 100%; }
  .care-item { grid-template-columns: 2.8rem minmax(0, 1fr); align-items: start; }
  .care-cover { width: 2.8rem; height: 3.7rem; }
  .care-actions { grid-column: 2; }
}
</style>
