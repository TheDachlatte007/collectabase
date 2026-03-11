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

        <!-- Donut: By Condition -->
        <div class="card chart-card">
          <h3 class="mb-2">By Condition</h3>
          <Doughnut v-if="conditionChartData" :data="conditionChartData" :options="donutOptions" />
        </div>

        <!-- Bar: Value by Type -->
        <div class="card chart-card">
          <h3 class="mb-2">Value by Type</h3>
          <Bar v-if="typeChartData" :data="typeChartData" :options="barOptions" />
        </div>
      </div>

      <!-- Top Widgets Row -->
      <div class="top-widgets-row mb-3" v-if="stats.top_valuable?.length || stats.top_gainers?.length">
        <div class="card widget-card" v-if="stats.top_valuable?.length">
          <div class="flex flex-between items-center mb-3">
            <h3 class="m-0">Most Valuable Items</h3>
            <button class="btn btn-sm btn-ghost" @click="showAllValuable = !showAllValuable" v-if="stats.top_valuable.length > 5">
              {{ showAllValuable ? 'Show Less' : 'Show All' }}
            </button>
          </div>
          <div class="widget-list">
            <router-link :to="`/game/${item.id}`" class="widget-item" v-for="item in visibleValuable" :key="item.id">
              <img :src="item.cover_url || '/placeholder.png'" class="widget-img" alt="Cover" />
              <div class="widget-info">
                <span class="widget-title">{{ item.title }}</span>
                <span class="widget-value text-success">€{{ formatNumber(item.current_value) }}</span>
              </div>
            </router-link>
          </div>
        </div>

        <div class="card widget-card" v-if="stats.top_gainers?.length">
          <div class="flex flex-between items-center mb-3">
            <h3 class="m-0">Top Gainers</h3>
            <button class="btn btn-sm btn-ghost" @click="showAllGainers = !showAllGainers" v-if="stats.top_gainers.length > 5">
              {{ showAllGainers ? 'Show Less' : 'Show All' }}
            </button>
          </div>
          <div class="widget-list">
            <router-link :to="`/game/${item.id}`" class="widget-item" v-for="item in visibleGainers" :key="item.id">
              <img :src="item.cover_url || '/placeholder.png'" class="widget-img" alt="Cover" />
              <div class="widget-info">
                <span class="widget-title">{{ item.title }}</span>
                <span class="widget-value" :class="item.profit_loss >= 0 ? 'text-success' : 'text-error'">
                   {{ item.profit_loss >= 0 ? '+' : '' }}€{{ formatNumber(item.profit_loss) }}
                </span>
              </div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Historical Value Chart -->
      <div class="card chart-card mb-3 history-card">
        <div class="flex flex-between items-center mb-2">
          <h3 class="m-0">Value History</h3>
          <select v-model="historyDays" @change="loadHistory" class="filter-select select-sm">
            <option :value="30">Last 30 Days</option>
            <option :value="90">Last 90 Days</option>
            <option :value="365">Last Year</option>
          </select>
        </div>
        <div v-if="historyLoading" class="text-muted">Loading history...</div>
        <div v-else-if="!historyChartData" class="text-muted">Not enough data to display history yet. It will automatically populate daily.</div>
        <div v-else class="history-chart-wrapper">
          <Line :data="historyChartData" :options="lineOptions" />
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
              <th>Invested</th>
              <th>Profit/Loss</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in stats.by_platform" :key="p.name">
              <td>{{ p.name }}</td>
              <td>{{ p.count }}</td>
              <td>€{{ formatNumber(p.value) }}</td>
              <td>€{{ formatNumber(p.invested) }}</td>
              <td :class="(p.profit_loss || 0) >= 0 ? 'text-success' : 'text-error'">
                {{ (p.profit_loss || 0) >= 0 ? '+' : '' }}€{{ formatNumber(p.profit_loss || 0) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title)

const stats = ref({
  total_games: 0,
  total_value: 0,
  purchase_value: 0,
  profit_loss: 0,
  wishlist_count: 0,
  by_platform: [],
  by_type: [],
  by_condition: [],
  top_valuable: [],
  top_gainers: []
})
const visibleValuable = computed(() => {
  return showAllValuable.value ? stats.value.top_valuable : stats.value.top_valuable.slice(0, 5)
})
const visibleGainers = computed(() => {
  return showAllGainers.value ? stats.value.top_gainers : stats.value.top_gainers.slice(0, 5)
})

const showAllValuable = ref(false)
const showAllGainers = ref(false)
const historyData = ref([])
const historyDays = ref(30)
const historyLoading = ref(false)
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

const conditionChartData = computed(() => {
  if (!stats.value.by_condition?.length) return null
  return {
    labels: stats.value.by_condition.map(c => capitalize(c.condition) || 'Unknown'),
    datasets: [{
      data: stats.value.by_condition.map(c => c.count),
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6'],
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

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#e2e8f0' } }
  },
  scales: {
    x: { ticks: { color: '#94a3b8' }, grid: { color: '#2d2d4e' } },
    y: { ticks: { color: '#94a3b8' }, grid: { color: '#2d2d4e' }, title: { display: true, text: 'EUR', color: '#94a3b8' } }
  }
}

function formatNumber(num) {
  return num?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(typeof dt === 'string' ? dt.replace(' ', 'T') : dt)
  if (isNaN(d.getTime())) return String(dt)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${dd}.${mm}`
}

const historyChartData = computed(() => {
  if (!historyData.value || historyData.value.length < 2) return null
  // Data comes from API ordered by recorded_at DESC, so we need to reverse it to display chronologically (ASC)
  const ordered = [...historyData.value].reverse()
  return {
    labels: ordered.map(h => formatDate(h.date)),
    datasets: [
      {
        label: 'Total Value',
        data: ordered.map(h => h.total),
        borderColor: '#facc15',
        backgroundColor: 'transparent',
        tension: 0.3,
        pointRadius: 3
      },
      {
        label: 'Games',
        data: ordered.map(h => h.games),
        borderColor: '#60a5fa',
        backgroundColor: 'transparent',
        tension: 0.3,
        pointRadius: 3
      },
      {
        label: 'Hardware/Misc',
        data: ordered.map(h => h.hardware),
        borderColor: '#ef4444',
        backgroundColor: 'transparent',
        tension: 0.3,
        pointRadius: 3
      }
    ]
  }
})

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await statsApi.getHistory(historyDays.value)
    historyData.value = res.data || []
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    historyLoading.value = false
  }
}

async function loadStats() {
  try {
    const res = await statsApi.get()
    stats.value = res.data || stats.value
  } catch (e) {
    console.error('Failed to load stats:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadHistory()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card { 
  text-align: center; 
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s;
  cursor: default;
}
.stat-card:hover { 
  transform: translateY(-5px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.3), 0 0 20px rgba(139, 92, 246, 0.15);
}
.stat-card h3 { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.stat-value { font-size: 2rem; font-weight: bold; transition: color 0.3s; }

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 639px) {
  .charts-row, .top-widgets-row { grid-template-columns: 1fr; }

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

  .history-chart-wrapper {
    height: 250px;
  }
}

.chart-card { padding: 1.5rem; }

.history-card {
  width: 100%;
}

.history-chart-wrapper {
  position: relative;
  height: 320px;
  width: 100%;
}

.top-widgets-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
.widget-card { padding: 1.5rem; }
.widget-list { display: flex; flex-direction: column; gap: 0.75rem; }
.widget-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}
.widget-item:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(139, 92, 246, 0.3);
  transform: translateX(4px);
}
.widget-img { width: 44px; height: 60px; object-fit: cover; border-radius: var(--radius-sm); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
.widget-info { display: flex; flex-direction: column; overflow: hidden; }
.widget-title { 
  font-weight: 600; 
  font-size: 0.95rem; 
  line-height: 1.2; 
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.widget-value { font-size: 0.85rem; font-weight: 700; }

.stats-table { width: 100%; border-collapse: collapse; }
.stats-table th,
.stats-table td { text-align: left; padding: 0.75rem; border-bottom: 1px solid var(--glass-border); }
.stats-table th { color: var(--text-muted); font-size: 0.875rem; background: rgba(0,0,0,0.2); }
.stats-table tr:hover { background: rgba(255,255,255,0.02); }

.text-success { color: var(--success); }
.text-error { color: #ef4444; }
</style>
