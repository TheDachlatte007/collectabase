<template>
  <div class="container">
    <h1 class="mb-3">Wishlist</h1>
    
    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else-if="games.length === 0" class="empty">
      <h3>Your wishlist is empty</h3>
      <p>Add games you want to track or purchase</p>
      <router-link to="/prices" class="btn btn-secondary empty-cta">Browse Prices →</router-link>
    </div>

    <div v-else class="grid">
      <div v-for="game in games" :key="game.id" class="game-card">
        <div class="cover">
          <img
            v-if="coverSrc(game)"
            :src="coverSrc(game)"
            :alt="game.title"
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
import { useGameStore } from '../stores/useGameStore'
import { storeToRefs } from 'pinia'
import { coverEmoji, makeFallbackCoverDataUrl, needsAutoCover } from '../utils/coverFallback'

const store = useGameStore()
const { wishlist: games, loading } = storeToRefs(store)

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

onMounted(() => store.load())
</script>

<style scoped>
.game-card {
  background: var(--surface-raised, rgba(255, 255, 255, 0.03));
  border-radius: var(--radius-md, 0.75rem);
  overflow: hidden;
  border: 1px solid var(--glass-border);
  position: relative;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.game-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
}

.cover {
  aspect-ratio: 3/4;
  background: var(--surface, rgba(0, 0, 0, 0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3.5rem;
  overflow: hidden;
  border-bottom: 1px solid var(--glass-border);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.info {
  padding: 0.85rem 1rem;
}

.info h3 {
  font-size: 1rem;
  margin: 0 0 0.25rem;
}

.max-price {
  color: var(--warning);
  font-weight: 700;
  font-family: var(--font-data);
  margin-top: 0.5rem;
}

.card-link {
  position: absolute;
  inset: 0;
}

.empty-cta {
  margin-top: 0.75rem;
}
</style>
