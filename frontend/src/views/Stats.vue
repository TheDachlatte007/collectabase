<template>
  <div class="container">
    <h1 class="mb-3">Collection Statistics</h1>

    <div v-if="loading" class="loading">Loading stats...</div>

    <div v-else>
      <!-- KPI Cards -->
      <div class="stats-grid mb-3">
        <div class="card stat-card">
          <h3>Total Items</h3>
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

      <!-- Charts Row -->
      <div class="charts-row mb-3">
        <!-- Donut: By Platform -->
        <div class="card chart-card">
          <h3 class="mb-2">By Platform</h3>
          <Doughnut v-if="platformChartData" :data="platformChartData" :options="donutOptions" />
        </div>

        <!-- Bar: Value by Type -->
        <div class="card chart-card">
          <h3 class="mb-2">Value by Type</h3>
          <Bar v-if="typeChartData" :data="typeChartData" :options="barOptions" />
        </div>
      </div>

      <!-- By Type Table -->
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
            <tr v-for="t in stats.by_type" :key="t.item_type">
              <td>{{ capitalize(t.item_type) }}</td>
              <td>{{ t.count }}</td>
              <td>€{{ formatNumber(t.value) }}</td>
              <td>€{{ formatNumber(t.invested) }}</td>
              <td :class="(t.value - t.invested) >= 0 ? 'text-success' : 'text-error'">
                {{ (t.value - t.invested) >= 0 ? '+' : '' }}€{{ formatNumber(t.value - t.invested) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- By Platform Table -->
      <div v-if="stats.by_platform?.length" class="card mt-3">
        <h3 class="mb-2">By Platform</h3>
        <table class="stats-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Items</th>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const stats = ref({
  total_games: 0,
  total_value: 0,
  purchase_value: 0,
  profit_loss: 0,
  wishlist_count: 0,
  by_platform: [],
  by_type: []
})
const loading = ref(true)

const COLORS = [
  '#6366f1','#22d3ee','#f59e0b','#10b981','#ef4444',
  '#8b5cf6','#ec4899','#14b8a6','#f97316','#84cc16'
]

const platformChartData = computed(() => {
  if (!stats.value.by_platform?.length) return null
  const top = stats.value.by_platform.slice(0, 9)
  return {
    labels: top.map(p => p.name),
    datasets: [{
      data: top.map(p => p.count),
      backgroundColor: COLORS,
      borderWidth: 2,
      borderColor: '#1a1a2e'
    }]
  }
})

const typeChartData = computed(() => {
  if (!stats.value.by_type?.length) return null
  return {
    labels: stats.value.by_type.map(t => capitalize(t.item_type)),
    datasets: [
      {
        label: 'Value',
        data: stats.value.by_type.map(t => t.value),
        backgroundColor: '#6366f1'
      },
      {
        label: 'Invested',
        data: stats.value.by_type.map(t => t.invested),
        backgroundColor: '#22d3ee'
      }
    ]
  }
})

const donutOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'right', labels: { color: '#e2e8f0', boxWidth: 12 } }
  }
}

const barOptions = {
  responsive: true,
  plugins: {
    legend: { labels: { color: '#e2e8f0' } }
  },
  scales: {
    x: { ticks: { color: '#94a3b8' }, grid: { color: '#2d2d4e' } },
    y: { ticks: { color: '#94a3b8' }, grid: { color: '#2d2d4e' } }
  }
}

function formatNumber(num) {
  return num?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : ''
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

.stat-card { text-align: center; }
.stat-card h3 { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.stat-value { font-size: 2rem; font-weight: bold; }

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 639px) {
  .charts-row { grid-template-columns: 1fr; }

  /* KPI cards: 2 per row on phones */
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  .stat-value { font-size: 1.5rem; }

  /* Tables: allow horizontal scroll instead of overflowing */
  .stats-table {
    display: block;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    white-space: nowrap;
  }
  .stats-table th,
  .stats-table td {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
}

.chart-card { padding: 1.5rem; }

.stats-table { width: 100%; border-collapse: collapse; }
.stats-table th,
.stats-table td { text-align: left; padding: 0.75rem; border-bottom: 1px solid var(--border); }
.stats-table th { color: var(--text-muted); font-size: 0.875rem; }

.text-success { color: var(--success); }
.text-error { color: #ef4444; }
</style>
