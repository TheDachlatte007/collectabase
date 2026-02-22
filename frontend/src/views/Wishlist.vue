<template>
  <div class="container">
    <h1 class="mb-3">Wishlist</h1>
    
    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else-if="games.length === 0" class="empty">
      <h3>Your wishlist is empty</h3>
      <p>Add games you want to track or purchase</p>
    </div>

    <div v-else class="grid">
      <div v-for="game in games" :key="game.id" class="game-card">
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
          <p v-if="game.wishlist_max_price" class="max-price">
            Max: €{{ game.wishlist_max_price }}
          </p>
        </div>
        <router-link :to="`/game/${game.id}`" class="card-link"></router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gamesApi } from '../api'
import { coverEmoji, makeFallbackCoverDataUrl, needsAutoCover } from '../utils/coverFallback'

const games = ref([])
const loading = ref(true)
const brokenCoverIds = ref({})

function markBroken(id) {
  brokenCoverIds.value[id] = true
}

function coverSrc(game) {
  if (!game) return null
  if (game.cover_url && !brokenCoverIds.value[game.id]) return game.cover_url
  if (needsAutoCover(game.item_type)) return makeFallbackCoverDataUrl(game)
  return null
}

async function loadWishlist() {
  try {
    const res = await gamesApi.list('?wishlist=true')
    games.value = res.data || []
  } catch (e) {
    console.error('Failed to load wishlist:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadWishlist)
</script>

<style scoped>
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

.max-price {
  color: var(--warning);
  font-weight: bold;
  margin-top: 0.5rem;
}

.card-link {
  position: absolute;
  inset: 0;
}
</style>
