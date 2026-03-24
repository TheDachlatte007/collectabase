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
      <div class="charts-row mb-4">
        <!-- Donut: By Platform (Count) -->
        <div class="card chart-card premium-glass">
          <h3 class="mb-3 flex items-center gap-2">
            <span class="icon">📊</span> Items by Platform
          </h3>
          <div class="chart-container">
            <Doughnut v-if="platformChartData" :data="platformChartData" :options="donutOptions" />
          </div>
        </div>

        <!-- Donut: By Platform (Value) -->
        <div class="card chart-card premium-glass">
          <h3 class="mb-3 flex items-center gap-2">
            <span class="icon">💰</span> Value by Platform
          </h3>
          <div class="chart-container">
            <Doughnut v-if="platformValueChartData" :data="platformValueChartData" :options="donutOptions" />
          </div>
        </div>
      </div>

      <div class="charts-row mb-4">
        <!-- Donut: By Condition -->
        <div class="card chart-card premium-glass">
          <h3 class="mb-3 flex items-center gap-2">
            <span class="icon">✨</span> By Condition
          </h3>
          <div class="chart-container">
            <Doughnut v-if="conditionChartData" :data="conditionChartData" :options="donutOptions" />
          </div>
        </div>

        <!-- Bar: Value by Type -->
        <div class="card chart-card premium-glass">
          <h3 class="mb-3 flex items-center gap-2">
            <span class="icon">🏷️</span> Value by Type
          </h3>
          <div class="chart-container">
            <Bar v-if="typeChartData" :data="typeChartData" :options="barOptions" />
          </div>
        </div>
      </div>

      <!-- Top Widgets Row -->
      <div class="top-widgets-row mb-4" v-if="stats.top_valuable?.length || stats.top_gainers?.length">
        <div class="card widget-card premium-glass" v-if="stats.top_valuable?.length">
          <div class="flex flex-between items-center mb-4">
            <h3 class="m-0 flex items-center gap-2">
              <span class="icon">🏆</span> Most Valuable Items
            </h3>
            <button class="btn btn-sm btn-ghost" @click="showAllValuable = !showAllValuable" v-if="stats.top_valuable.length > 5">
              {{ showAllValuable ? 'Show Less' : 'Show All' }}
            </button>
          </div>
          <div class="widget-list">
            <router-link :to="`/game/${item.id}`" class="widget-item premium-hover" v-for="item in visibleValuable" :key="item.id">
              <div class="widget-img-wrapper">
                <img :src="item.cover_url || '/placeholder.png'" class="widget-img" alt="Cover" />
              </div>
              <div class="widget-info">
                <span class="widget-title">{{ item.title }}</span>
                <span class="widget-value text-gradient-success">€{{ formatNumber(item.current_value) }}</span>
              </div>
            </router-link>
          </div>
        </div>

        <div class="card widget-card premium-glass" v-if="stats.top_gainers?.length">
          <div class="flex flex-between items-center mb-4">
            <h3 class="m-0 flex items-center gap-2">
              <span class="icon">📈</span> Top Gainers
            </h3>
            <button class="btn btn-sm btn-ghost" @click="showAllGainers = !showAllGainers" v-if="stats.top_gainers.length > 5">
              {{ showAllGainers ? 'Show Less' : 'Show All' }}
            </button>
          </div>
          <div class="widget-list">
            <router-link :to="`/game/${item.id}`" class="widget-item premium-hover" v-for="item in visibleGainers" :key="item.id">
              <div class="widget-img-wrapper">
                <img :src="item.cover_url || '/placeholder.png'" class="widget-img" alt="Cover" />
              </div>
              <div class="widget-info">
                <span class="widget-title">{{ item.title }}</span>
                <span class="widget-value" :class="item.profit_loss >= 0 ? 'text-gradient-success' : 'text-error'">
                   {{ item.profit_loss >= 0 ? '+' : '' }}€{{ formatNumber(item.profit_loss) }}
                </span>
              </div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Historical Value Chart -->
      <div class="card chart-card mb-4 history-card premium-glass">
        <div class="flex flex-between items-center mb-4">
          <h3 class="m-0 flex items-center gap-2">
            <span class="icon">📅</span> Value History
          </h3>
          <select v-model="historyDays" @change="loadHistory" class="filter-select select-sm premium-select">
            <option :value="30">Last 30 Days</option>
            <option :value="90">Last 90 Days</option>
            <option :value="365">Last Year</option>
          </select>
        </div>
        <div v-if="historyLoading" class="loading-state">
           <div class="spinner"></div>
           <span>Loading history...</span>
        </div>
        <div v-else-if="!historyChartData" class="empty-state">Not enough data to display history yet. It will automatically populate daily.</div>
        <div v-else class="history-chart-wrapper">
          <Line :data="historyChartData" :options="lineOptions" />
        </div>
      </div>

      <div v-if="stats.lots_summary?.total_lots" class="card chart-card mb-4 premium-glass">
        <div class="flex flex-between items-center mb-4">
          <h3 class="m-0 flex items-center gap-2">
            <span class="icon">📦</span> Lots & Resale
          </h3>
          <router-link to="/lots" class="btn btn-sm btn-secondary">
            Open Lots
          </router-link>
        </div>

        <div class="lot-summary-grid mb-3">
          <div class="lot-summary-card">
            <span class="summary-label">Lots</span>
            <strong>{{ stats.lots_summary.total_lots }}</strong>
            <small>{{ stats.lots_summary.item_count }} items tracked</small>
          </div>
          <div class="lot-summary-card">
            <span class="summary-label">Cost Basis</span>
            <strong>€{{ formatNumber(stats.lots_summary.total_cost_basis) }}</strong>
            <small>Bundle purchase total</small>
          </div>
          <div class="lot-summary-card">
            <span class="summary-label">Net Sales</span>
            <strong>€{{ formatNumber(stats.lots_summary.net_sales) }}</strong>
            <small>Recovered from sold items</small>
          </div>
          <div class="lot-summary-card">
            <span class="summary-label">Realized Profit</span>
            <strong :class="stats.lots_summary.realized_profit >= 0 ? 'text-success' : 'text-error'">
              {{ stats.lots_summary.realized_profit >= 0 ? '+' : '' }}€{{ formatNumber(stats.lots_summary.realized_profit) }}
            </strong>
            <small>Closed sales only</small>
          </div>
          <div class="lot-summary-card">
            <span class="summary-label">Remaining Cost</span>
            <strong>€{{ formatNumber(stats.lots_summary.remaining_cost_basis) }}</strong>
            <small>Still tied to inventory</small>
          </div>
          <div class="lot-summary-card">
            <span class="summary-label">Expected Remaining</span>
            <strong>€{{ formatNumber(stats.lots_summary.expected_remaining_value) }}</strong>
            <small>
              Gap: €{{ formatNumber(stats.lots_summary.break_even_gap) }}
            </small>
          </div>
        </div>

        <table v-if="stats.lots_overview?.length" class="stats-table">
          <thead>
            <tr>
              <th>Lot</th>
              <th>Items</th>
              <th>Cost Basis</th>
              <th>Net Sales</th>
              <th>Profit</th>
              <th>Recovery</th>
              <th>Break-even Gap</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lot in stats.lots_overview.slice(0, 6)" :key="lot.id">
              <td>
                <div class="lot-name-cell">
                  <strong>{{ lot.name }}</strong>
                  <span v-if="lot.purchase_date">{{ lot.purchase_date }}</span>
                </div>
              </td>
              <td>{{ lot.item_count }}</td>
              <td>€{{ formatNumber(lot.total_cost_basis) }}</td>
              <td>€{{ formatNumber(lot.net_sales) }}</td>
              <td :class="lot.realized_profit >= 0 ? 'text-success' : 'text-error'">
                {{ lot.realized_profit >= 0 ? '+' : '' }}€{{ formatNumber(lot.realized_profit) }}
              </td>
              <td>{{ formatNumber(lot.recovery_rate_pct) }}%</td>
              <td>€{{ formatNumber(lot.break_even_gap) }}</td>
            </tr>
          </tbody>
        </table>
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
  top_gainers: [],
  lots_summary: {
    total_lots: 0,
    item_count: 0,
    total_cost_basis: 0,
    net_sales: 0,
    realized_profit: 0,
    remaining_cost_basis: 0,
    expected_remaining_value: 0,
    break_even_gap: 0
  },
  lots_overview: []
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
  const top = [...stats.value.by_platform].sort((a,b) => b.count - a.count).slice(0, 9)
  return {
    labels: top.map(p => p.name),
    datasets: [{
      data: top.map(p => p.count),
      backgroundColor: COLORS,
      borderWidth: 0,
      hoverOffset: 15
    }]
  }
})

const platformValueChartData = computed(() => {
  if (!stats.value.by_platform?.length) return null
  const top = [...stats.value.by_platform].sort((a,b) => b.value - a.value).slice(0, 9)
  return {
    labels: top.map(p => p.name),
    datasets: [{
      data: top.map(p => p.value),
      backgroundColor: COLORS,
      borderWidth: 0,
      hoverOffset: 15
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
      borderWidth: 0,
      hoverOffset: 15
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
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}

.stat-card { 
  text-align: center; 
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: default;
  background: linear-gradient(135deg, rgba(30, 30, 50, 0.7), rgba(20, 20, 40, 0.8));
  border: 1px solid rgba(139, 92, 246, 0.2);
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s;
}

.stat-card:hover::after {
  opacity: 1;
}

.stat-card:hover { 
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 15px 35px rgba(0,0,0,0.4), 0 0 25px rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.4);
}

.stat-card h3 { 
  font-size: 0.9rem; 
  color: var(--text-muted); 
  margin-bottom: 0.5rem; 
  text-transform: uppercase; 
  letter-spacing: 1px;
}

.stat-value { 
  font-size: 2.25rem; 
  font-weight: 800; 
  background: linear-gradient(to bottom, #fff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.text-success { color: #10b981; }
.text-gradient-success {
  background: linear-gradient(45deg, #10b981, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.premium-glass {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
}

.premium-glass:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
}

.chart-card { padding: 1.8rem; }
.chart-container {
  position: relative;
  height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.top-widgets-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.widget-card { padding: 1.8rem; }
.widget-list { display: flex; flex-direction: column; gap: 1rem; }

.widget-item {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 0.75rem;
  background: rgba(255,255,255,0.02);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.premium-hover:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(139, 92, 246, 0.4);
  transform: translateX(8px);
  box-shadow: -4px 0 15px rgba(139, 92, 246, 0.1);
}

.widget-img-wrapper {
  position: relative;
  flex-shrink: 0;
}

.widget-img { 
  width: 50px; 
  height: 68px; 
  object-fit: cover; 
  border-radius: var(--radius-sm); 
  box-shadow: 0 5px 15px rgba(0,0,0,0.4);
  transition: transform 0.3s;
}

.widget-item:hover .widget-img {
  transform: scale(1.05);
}

.widget-info { display: flex; flex-direction: column; gap: 0.25rem; }
.widget-title { font-weight: 600; font-size: 1rem; }
.widget-value { font-size: 0.9rem; font-weight: 700; }

.history-card { padding: 1.8rem; }
.history-chart-wrapper { height: 350px; width: 100%; }

.lot-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.lot-summary-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1rem;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
}

.lot-summary-card strong {
  font-size: 1.25rem;
}

.summary-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.lot-summary-card small {
  color: var(--text-muted);
}

.lot-name-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.lot-name-cell span {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.stats-table { width: 100%; border-collapse: separate; border-spacing: 0 0.5rem; }
.stats-table th { 
  padding: 1rem; 
  font-weight: 600; 
  text-transform: uppercase; 
  font-size: 0.75rem; 
  letter-spacing: 1px;
}
.stats-table td { 
  padding: 1rem; 
  background: rgba(255,255,255,0.02);
  border-top: 1px solid rgba(255,255,255,0.05);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.stats-table td:first-child { border-left: 1px solid rgba(255,255,255,0.05); border-radius: 8px 0 0 8px; }
.stats-table td:last-child { border-right: 1px solid rgba(255,255,255,0.05); border-radius: 0 8px 8px 0; }

.loading-state, .empty-state {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(139, 92, 246, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .charts-row, .top-widgets-row { grid-template-columns: 1fr; }
}
</style>
