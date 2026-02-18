<template>
  <div class="container">
    <h1 class="mb-3">Collection Statistics</h1>
    
    <div v-if="loading" class="loading">Loading stats...</div>
    
    <div v-else class="stats-grid">
      <!-- Overview Cards -->
      <div class="card stat-card">
        <h3>Total Games</h3>
        <p class="stat-value">{{ stats.total_games }}</p>
      </div>
      
      <div class="card stat-card">
        <h3>Collection Value</h3>
        <p class="stat-value text-success">€{{ formatNumber(stats.total_value) }}</p>
      </div>
      
      <div class="card stat-card">
        <h3>Invested</h3>
        <p class="stat-value">€{{ formatNumber(stats.purchase_value) }}</p>
      </div>
      
      <div class="card stat-card">
        <h3>Profit/Loss</h3>
        <p class="stat-value" :class="stats.profit_loss >= 0 ? 'text-success' : 'text-error'">
          {{ stats.profit_loss >= 0 ? '+' : '' }}€{{ formatNumber(stats.profit_loss) }}
        </p>
      </div>
      
      <div class="card stat-card">
        <h3>Wishlist</h3>
        <p class="stat-value">{{ stats.wishlist_count }} items</p>
      </div>
    </div>

    <!-- By Type -->                                        <!-- ← NEU -->
    <div v-if="stats.by_type?.length" class="card mt-3">
      <h3 class="mb-2">By Type</h3>
      <table class="stats-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Count</th>
            <th>Value</th>
            <th>Invested</th>
            <th>Profit/Loss</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in stats.by_type" :key="t.type">
            <td>{{ t.type }}</td>
            <td>{{ t.count }}</td>
            <td>€{{ formatNumber(t.value) }}</td>
            <td>€{{ formatNumber(t.invested) }}</td>
            <td :class="(t.value - t.invested) >= 0 ? 'text-success' : 'text-error'">
              {{ (t.value - t.invested) >= 0 ? '+' : '' }}€{{ formatNumber(t.value - t.invested) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>                                                  <!-- ← NEU ENDE -->

    <!-- Platform Distribution -->
    <div v-if="stats.by_platform?.length" class="card mt-3">
      <h3 class="mb-2">By Platform</h3>
      <table class="stats-table">
        <thead>
          <tr>
            <th>Platform</th>
            <th>Games</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in stats.by_platform" :key="p.name">
            <td>{{ p.name }}</td>
            <td>{{ p.count }}</td>
            <td>€{{ formatNumber(p.value) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  total_games: 0,
  total_value: 0,
  purchase_value: 0,
  profit_loss: 0,
  wishlist_count: 0,
  by_platform: [],
  by_type: []        // ← NEU
})
const loading = ref(true)

function formatNumber(num) {
  return num?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats')
    stats.value = await res.json()
  } catch (e) {
    console.error('Failed to load stats:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  text-align: center;
}

.stat-card h3 {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
}

.stats-table th,
.stats-table td {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.stats-table th {
  color: var(--text-muted);
  font-size: 0.875rem;
}
</style>
