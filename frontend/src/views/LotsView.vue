<template>
  <div class="container">
    <div class="page-head mb-3">
      <div>
        <h1>Lots & Resale</h1>
        <p class="text-muted">Track bundle purchases, cost basis allocation, and realized resale results.</p>
      </div>
      <button class="btn btn-primary" @click="showCreate = !showCreate">
        {{ showCreate ? 'Close' : '+ New Lot' }}
      </button>
    </div>

    <div v-if="showCreate" class="card mb-3">
      <h2 class="section-title">Create Lot</h2>
      <div class="form-grid">
        <div class="form-group"><label>Name</label><input v-model.trim="newLot.name" placeholder="Konvolut A" /></div>
        <div class="form-group"><label>Date</label><input v-model="newLot.purchase_date" type="date" /></div>
        <div class="form-group"><label>Seller</label><input v-model.trim="newLot.seller" /></div>
        <div class="form-group"><label>Purchase (EUR)</label><input v-model="newLot.purchase_price_gross" type="number" min="0" step="0.01" /></div>
        <div class="form-group"><label>Shipping In</label><input v-model="newLot.shipping_in" type="number" min="0" step="0.01" /></div>
        <div class="form-group"><label>Fees In</label><input v-model="newLot.fees_in" type="number" min="0" step="0.01" /></div>
        <div class="form-group"><label>Other Costs</label><input v-model="newLot.other_costs" type="number" min="0" step="0.01" /></div>
      </div>
      <div class="form-group mb-2"><label>Notes</label><textarea v-model="newLot.notes" rows="2" /></div>
      <button class="btn btn-primary" :disabled="creatingLot" @click="createLot">{{ creatingLot ? 'Creating…' : 'Create Lot' }}</button>
    </div>

    <div v-if="loading" class="loading">Loading lots...</div>

    <div v-else class="layout">
      <aside class="sidebar">
        <div class="card">
          <div class="section-head">
            <h2 class="section-title">Lots</h2>
            <span class="pill">{{ lots.length }}</span>
          </div>
          <div v-if="!lots.length" class="text-muted">No lots yet.</div>
          <button v-for="lot in lots" :key="lot.id" class="lot-btn" :class="{ active: selectedLotId === lot.id }" @click="selectLot(lot.id)">
            <strong>{{ lot.name }}</strong>
            <span>{{ formatCurrency(lot.total_cost_basis) }} · {{ lot.summary.item_count }} items</span>
            <small>{{ formatCurrency(lot.summary.net_sales) }} sales · {{ formatCurrency(lot.summary.remaining_cost_basis) }} open</small>
          </button>
        </div>
      </aside>

      <section>
        <div v-if="selectedLot" class="detail-grid">
          <div class="card">
            <div class="section-head">
              <h2 class="section-title">Lot Details</h2>
              <div class="actions">
                <button class="btn btn-secondary btn-small" @click="reloadLot">Refresh</button>
                <button class="btn btn-primary btn-small" :disabled="savingLot" @click="saveLot">{{ savingLot ? 'Saving…' : 'Save' }}</button>
                <button class="btn btn-danger btn-small" :disabled="deletingLot" @click="deleteLot">Delete</button>
              </div>
            </div>

            <div class="form-grid">
              <div class="form-group"><label>Name</label><input v-model.trim="lotForm.name" /></div>
              <div class="form-group"><label>Date</label><input v-model="lotForm.purchase_date" type="date" /></div>
              <div class="form-group"><label>Seller</label><input v-model.trim="lotForm.seller" /></div>
              <div class="form-group"><label>Purchase (EUR)</label><input v-model="lotForm.purchase_price_gross" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Shipping In</label><input v-model="lotForm.shipping_in" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Fees In</label><input v-model="lotForm.fees_in" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Other Costs</label><input v-model="lotForm.other_costs" type="number" min="0" step="0.01" /></div>
            </div>
            <div class="form-group mb-0"><label>Notes</label><textarea v-model="lotForm.notes" rows="2" /></div>
          </div>

          <div class="kpis">
            <div class="card kpi"><label>Total Cost</label><strong>{{ formatCurrency(selectedLot.total_cost_basis) }}</strong></div>
            <div class="card kpi"><label>Net Sales</label><strong>{{ formatCurrency(selectedLot.summary.net_sales) }}</strong></div>
            <div class="card kpi"><label>Realized Profit</label><strong :class="valueClass(selectedLot.summary.realized_profit)">{{ formatCurrency(selectedLot.summary.realized_profit) }}</strong></div>
            <div class="card kpi"><label>Remaining Cost</label><strong>{{ formatCurrency(selectedLot.summary.remaining_cost_basis) }}</strong></div>
            <div class="card kpi"><label>Estimated Remaining</label><strong>{{ formatCurrency(selectedLot.summary.expected_remaining_value) }}</strong></div>
            <div class="card kpi"><label>Recovery</label><strong>{{ formatPercent(selectedLot.summary.recovery_rate_pct) }}</strong></div>
          </div>

          <div class="card">
            <h2 class="section-title">Add Item</h2>
            <div class="form-group">
              <label>Link collection item (optional)</label>
              <input v-model.trim="librarySearch" placeholder="Search collection..." @input="searchLibrary" />
            </div>
            <div v-if="libraryResults.length" class="search-results mb-2">
              <button v-for="game in libraryResults" :key="game.id" class="search-result" @click="pickGame(game)">
                {{ game.title }} · {{ game.platform_name || 'No platform' }}
              </button>
            </div>
            <div v-if="itemForm.game_id" class="linked mb-2">Linked: {{ itemForm.title_snapshot }} <button class="link-btn" @click="clearLinkedGame">Clear</button></div>
            <div class="form-grid">
              <div class="form-group"><label>Title</label><input v-model.trim="itemForm.title_snapshot" :disabled="Boolean(itemForm.game_id)" /></div>
              <div class="form-group"><label>Platform</label><input v-model.trim="itemForm.platform_snapshot" :disabled="Boolean(itemForm.game_id)" /></div>
              <div class="form-group"><label>Type</label>
                <select v-model="itemForm.item_type_snapshot" :disabled="Boolean(itemForm.game_id)">
                  <option value="game">Game</option>
                  <option value="console">Console</option>
                  <option value="accessory">Accessory</option>
                  <option value="figure">Figure</option>
                  <option value="funko">Funko</option>
                  <option value="misc">Misc</option>
                </select>
              </div>
              <div class="form-group"><label>Estimated Value</label><input v-model="itemForm.estimated_value" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Cost Override</label><input v-model="itemForm.cost_basis_override" type="number" min="0" step="0.01" placeholder="Optional" /></div>
              <div class="form-group"><label>Status</label>
                <select v-model="itemForm.status">
                  <option value="inventory">Inventory</option>
                  <option value="kept">Kept</option>
                  <option value="discarded">Discarded</option>
                </select>
              </div>
            </div>
            <div class="form-group mb-2"><label>Notes</label><textarea v-model="itemForm.notes" rows="2" /></div>
            <button class="btn btn-primary" :disabled="creatingItem" @click="addItem">{{ creatingItem ? 'Adding…' : 'Add Item' }}</button>
          </div>

          <div class="card">
            <div class="section-head">
              <h2 class="section-title">Items</h2>
              <span class="pill">{{ selectedLot.items.length }}</span>
            </div>
            <div v-if="!selectedLot.items.length" class="text-muted">No items yet.</div>
            <div v-else class="table-wrap">
              <table class="lot-table">
                <thead>
                  <tr><th>Item</th><th>Estimated</th><th>Override</th><th>Allocated</th><th>Status</th><th>Sale</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in selectedLot.items" :key="item.id">
                    <td>
                      <strong>{{ item.title_snapshot }}</strong>
                      <small class="text-muted block">{{ item.platform_snapshot || 'No platform' }} · {{ item.item_type_snapshot || 'game' }}</small>
                      <router-link v-if="item.game_id" :to="`/game/${item.game_id}`" class="mini-link">Open linked item</router-link>
                    </td>
                    <td><input v-model="itemDrafts[item.id].estimated_value" type="number" min="0" step="0.01" /></td>
                    <td><input v-model="itemDrafts[item.id].cost_basis_override" type="number" min="0" step="0.01" placeholder="Auto" /></td>
                    <td><strong>{{ formatCurrency(item.allocated_cost_basis) }}</strong><small class="text-muted block">{{ item.allocation_method }}</small></td>
                    <td>
                      <select v-model="itemDrafts[item.id].status">
                        <option value="inventory">Inventory</option>
                        <option value="sold">Sold</option>
                        <option value="kept">Kept</option>
                        <option value="discarded">Discarded</option>
                      </select>
                    </td>
                    <td>{{ item.sale ? formatCurrency(item.sale.net_proceeds) : '—' }}</td>
                    <td class="actions">
                      <button class="btn btn-secondary btn-small" :disabled="savingItemId === item.id" @click="saveItem(item)">Save</button>
                      <button class="btn btn-secondary btn-small" @click="editSale(item)">{{ item.sale ? 'Edit Sale' : 'Add Sale' }}</button>
                      <button class="btn btn-danger btn-small" :disabled="deletingItemId === item.id" @click="deleteItem(item)">Delete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="card">
            <h2 class="section-title">{{ editingSaleItemId ? 'Edit Sale' : 'Add Sale' }}</h2>
            <div class="form-grid">
              <div class="form-group"><label>Item</label>
                <select v-model="saleForm.item_id">
                  <option value="">Select item</option>
                  <option v-for="item in saleItems" :key="item.id" :value="String(item.id)">{{ item.title_snapshot }}</option>
                </select>
              </div>
              <div class="form-group"><label>Sold At</label><input v-model="saleForm.sold_at" type="date" /></div>
              <div class="form-group"><label>Channel</label><input v-model.trim="saleForm.channel" /></div>
              <div class="form-group"><label>Sale Price</label><input v-model="saleForm.sale_price_gross" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Fees</label><input v-model="saleForm.platform_fees" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Shipping Out</label><input v-model="saleForm.shipping_out" type="number" min="0" step="0.01" /></div>
              <div class="form-group"><label>Other Costs</label><input v-model="saleForm.other_costs" type="number" min="0" step="0.01" /></div>
            </div>
            <div class="form-group mb-2"><label>Notes</label><textarea v-model="saleForm.notes" rows="2" /></div>
            <div class="actions mb-2">
              <button class="btn btn-secondary" @click="resetSale">Reset</button>
              <button class="btn btn-primary" :disabled="savingSale" @click="saveSale">{{ savingSale ? 'Saving…' : 'Save Sale' }}</button>
            </div>
            <div v-if="selectedLot.sales.length" class="table-wrap">
              <table class="lot-table">
                <thead><tr><th>Item</th><th>Date</th><th>Channel</th><th>Net</th><th>Profit</th><th></th></tr></thead>
                <tbody>
                  <tr v-for="sale in selectedLot.sales" :key="sale.id">
                    <td>{{ sale.item_title }}</td>
                    <td>{{ formatDate(sale.sold_at) }}</td>
                    <td>{{ sale.channel || '—' }}</td>
                    <td>{{ formatCurrency(sale.net_proceeds) }}</td>
                    <td :class="valueClass(sale.realized_profit)">{{ formatCurrency(sale.realized_profit) }}</td>
                    <td class="actions">
                      <button class="btn btn-secondary btn-small" @click="editSale(findItem(sale.lot_item_id))">Edit</button>
                      <button class="btn btn-danger btn-small" @click="deleteSale(sale.lot_item_id)">Delete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div v-else class="card empty-state">Select or create a lot to start.</div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { gamesApi, lotsApi } from '../api'
import { notifyError, notifySuccess } from '../composables/useNotifications'

const lots = ref([])
const selectedLot = ref(null)
const selectedLotId = ref(null)
const loading = ref(false)
const showCreate = ref(false)
const creatingLot = ref(false)
const savingLot = ref(false)
const deletingLot = ref(false)
const creatingItem = ref(false)
const savingItemId = ref(null)
const deletingItemId = ref(null)
const savingSale = ref(false)
const editingSaleItemId = ref(null)
const librarySearch = ref('')
const libraryResults = ref([])
const searchToken = ref(0)

const newLot = reactive(makeLot())
const lotForm = reactive(makeLot())
const itemForm = reactive(makeItem())
const saleForm = reactive(makeSale())
const itemDrafts = reactive({})

const saleItems = computed(() => (selectedLot.value?.items || []).filter((item) => !item.sale || Number(saleForm.item_id) === item.id))

function makeLot() {
  return { name: '', purchase_date: '', seller: '', purchase_price_gross: '0', shipping_in: '0', fees_in: '0', other_costs: '0', notes: '' }
}

function makeItem() {
  return { game_id: null, title_snapshot: '', platform_snapshot: '', item_type_snapshot: 'game', estimated_value: '', cost_basis_override: '', status: 'inventory', notes: '' }
}

function makeSale() {
  return { item_id: '', sold_at: '', channel: '', sale_price_gross: '', platform_fees: '', shipping_out: '', other_costs: '', notes: '' }
}

function assign(target, source) {
  Object.keys(target).forEach((key) => { target[key] = source[key] })
}

function num(value, fallback = null) {
  if (value === '' || value === null || value === undefined) return fallback
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function formatCurrency(value) {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(Number(value || 0))
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function formatDate(value) {
  return value || '—'
}

function valueClass(value) {
  if (Number(value) > 0) return 'value-positive'
  if (Number(value) < 0) return 'value-negative'
  return ''
}

function buildItemDrafts() {
  Object.keys(itemDrafts).forEach((key) => delete itemDrafts[key])
  for (const item of selectedLot.value?.items || []) {
    itemDrafts[item.id] = {
      estimated_value: item.estimated_value ?? '',
      cost_basis_override: item.cost_basis_override ?? '',
      status: item.status || 'inventory',
      notes: item.notes || ''
    }
  }
}

function applyLotToForm(lot) {
  assign(lotForm, {
    name: lot.name || '',
    purchase_date: lot.purchase_date || '',
    seller: lot.seller || '',
    purchase_price_gross: String(lot.purchase_price_gross ?? 0),
    shipping_in: String(lot.shipping_in ?? 0),
    fees_in: String(lot.fees_in ?? 0),
    other_costs: String(lot.other_costs ?? 0),
    notes: lot.notes || ''
  })
}

async function loadLots(preferredId = null) {
  loading.value = true
  try {
    const res = await lotsApi.list()
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to load lots')
    lots.value = Array.isArray(res.data) ? res.data : []
    const targetId = preferredId ?? selectedLotId.value ?? lots.value[0]?.id ?? null
    if (targetId) await loadLot(targetId)
    else { selectedLotId.value = null; selectedLot.value = null }
  } catch (err) {
    notifyError(err.message || 'Failed to load lots')
  } finally {
    loading.value = false
  }
}

async function loadLot(id) {
  const res = await lotsApi.get(id)
  if (!res.ok) {
    notifyError(res.data?.detail?.message || 'Failed to load lot')
    return
  }
  selectedLotId.value = id
  selectedLot.value = res.data
  applyLotToForm(res.data)
  buildItemDrafts()
  resetSale()
}

function selectLot(id) {
  loadLot(id)
}

async function createLot() {
  if (!newLot.name.trim()) return notifyError('Lot name is required')
  creatingLot.value = true
  try {
    const res = await lotsApi.create({
      ...newLot,
      purchase_price_gross: num(newLot.purchase_price_gross, 0),
      shipping_in: num(newLot.shipping_in, 0),
      fees_in: num(newLot.fees_in, 0),
      other_costs: num(newLot.other_costs, 0)
    })
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to create lot')
    notifySuccess('Lot created')
    assign(newLot, makeLot())
    showCreate.value = false
    await loadLots(res.data.id)
  } catch (err) {
    notifyError(err.message || 'Failed to create lot')
  } finally {
    creatingLot.value = false
  }
}

async function saveLot() {
  if (!selectedLot.value) return
  savingLot.value = true
  try {
    const res = await lotsApi.update(selectedLot.value.id, {
      ...lotForm,
      purchase_price_gross: num(lotForm.purchase_price_gross, 0),
      shipping_in: num(lotForm.shipping_in, 0),
      fees_in: num(lotForm.fees_in, 0),
      other_costs: num(lotForm.other_costs, 0)
    })
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to save lot')
    selectedLot.value = res.data
    applyLotToForm(res.data)
    buildItemDrafts()
    await refreshLotList()
    notifySuccess('Lot saved')
  } catch (err) {
    notifyError(err.message || 'Failed to save lot')
  } finally {
    savingLot.value = false
  }
}

async function deleteLot() {
  if (!selectedLot.value || !window.confirm(`Delete ${selectedLot.value.name}?`)) return
  deletingLot.value = true
  try {
    const res = await lotsApi.remove(selectedLot.value.id)
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to delete lot')
    notifySuccess('Lot deleted')
    selectedLot.value = null
    selectedLotId.value = null
    await loadLots()
  } catch (err) {
    notifyError(err.message || 'Failed to delete lot')
  } finally {
    deletingLot.value = false
  }
}

async function reloadLot() {
  if (selectedLotId.value) {
    await loadLot(selectedLotId.value)
    await refreshLotList()
  }
}

async function refreshLotList() {
  const res = await lotsApi.list()
  if (res.ok && Array.isArray(res.data)) lots.value = res.data
}

async function searchLibrary() {
  const term = librarySearch.value.trim()
  if (term.length < 2) { libraryResults.value = []; return }
  const token = ++searchToken.value
  const res = await gamesApi.list(`?search=${encodeURIComponent(term)}`)
  if (token !== searchToken.value || !res.ok) return
  libraryResults.value = (Array.isArray(res.data) ? res.data : []).filter((game) => !game.is_wishlist).slice(0, 8)
}

function pickGame(game) {
  itemForm.game_id = game.id
  itemForm.title_snapshot = game.title || ''
  itemForm.platform_snapshot = game.platform_name || ''
  itemForm.item_type_snapshot = game.item_type || 'game'
  librarySearch.value = ''
  libraryResults.value = []
}

function clearLinkedGame() {
  assign(itemForm, makeItem())
}

async function addItem() {
  if (!selectedLot.value) return
  if (!itemForm.game_id && !itemForm.title_snapshot.trim()) return notifyError('Item title is required')
  creatingItem.value = true
  try {
    const res = await lotsApi.addItem(selectedLot.value.id, {
      game_id: itemForm.game_id,
      title_snapshot: itemForm.game_id ? null : itemForm.title_snapshot.trim(),
      platform_snapshot: itemForm.game_id ? null : itemForm.platform_snapshot.trim(),
      item_type_snapshot: itemForm.game_id ? null : itemForm.item_type_snapshot,
      estimated_value: num(itemForm.estimated_value, null),
      cost_basis_override: num(itemForm.cost_basis_override, null),
      status: itemForm.status,
      notes: itemForm.notes || null
    })
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to add item')
    selectedLot.value = res.data.lot
    buildItemDrafts()
    assign(itemForm, makeItem())
    await refreshLotList()
    notifySuccess('Item added')
  } catch (err) {
    notifyError(err.message || 'Failed to add item')
  } finally {
    creatingItem.value = false
  }
}

async function saveItem(item) {
  if (!selectedLot.value) return
  savingItemId.value = item.id
  try {
    const draft = itemDrafts[item.id]
    const res = await lotsApi.updateItem(selectedLot.value.id, item.id, {
      estimated_value: num(draft.estimated_value, null),
      cost_basis_override: num(draft.cost_basis_override, null),
      clear_cost_basis_override: draft.cost_basis_override === '' || draft.cost_basis_override === null,
      status: draft.status,
      notes: draft.notes
    })
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to save item')
    selectedLot.value = res.data
    buildItemDrafts()
    await refreshLotList()
    notifySuccess('Item updated')
  } catch (err) {
    notifyError(err.message || 'Failed to save item')
  } finally {
    savingItemId.value = null
  }
}

async function deleteItem(item) {
  if (!selectedLot.value || !window.confirm(`Delete ${item.title_snapshot}?`)) return
  deletingItemId.value = item.id
  try {
    const res = await lotsApi.deleteItem(selectedLot.value.id, item.id)
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to delete item')
    selectedLot.value = res.data
    buildItemDrafts()
    await refreshLotList()
    notifySuccess('Item deleted')
  } catch (err) {
    notifyError(err.message || 'Failed to delete item')
  } finally {
    deletingItemId.value = null
  }
}

function findItem(id) {
  return (selectedLot.value?.items || []).find((item) => item.id === id)
}

function editSale(item) {
  if (!item) return
  editingSaleItemId.value = item.id
  assign(saleForm, {
    item_id: String(item.id),
    sold_at: item.sale?.sold_at || '',
    channel: item.sale?.channel || '',
    sale_price_gross: item.sale?.sale_price_gross ?? '',
    platform_fees: item.sale?.platform_fees ?? '',
    shipping_out: item.sale?.shipping_out ?? '',
    other_costs: item.sale?.other_costs ?? '',
    notes: item.sale?.notes || ''
  })
}

function resetSale() {
  editingSaleItemId.value = null
  assign(saleForm, makeSale())
}

async function saveSale() {
  const itemId = Number(saleForm.item_id)
  if (!itemId) return notifyError('Select an item first')
  savingSale.value = true
  try {
    const res = await lotsApi.saveSale(itemId, {
      sold_at: saleForm.sold_at || null,
      channel: saleForm.channel || null,
      sale_price_gross: num(saleForm.sale_price_gross, 0),
      platform_fees: num(saleForm.platform_fees, 0),
      shipping_out: num(saleForm.shipping_out, 0),
      other_costs: num(saleForm.other_costs, 0),
      notes: saleForm.notes || null
    })
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to save sale')
    selectedLot.value = res.data
    buildItemDrafts()
    await refreshLotList()
    resetSale()
    notifySuccess('Sale saved')
  } catch (err) {
    notifyError(err.message || 'Failed to save sale')
  } finally {
    savingSale.value = false
  }
}

async function deleteSale(itemId) {
  if (!window.confirm('Delete this sale entry?')) return
  try {
    const res = await lotsApi.deleteSale(itemId)
    if (!res.ok) throw new Error(res.data?.detail?.message || 'Failed to delete sale')
    selectedLot.value = res.data
    buildItemDrafts()
    await refreshLotList()
    if (Number(saleForm.item_id) === itemId) resetSale()
    notifySuccess('Sale deleted')
  } catch (err) {
    notifyError(err.message || 'Failed to delete sale')
  }
}

onMounted(() => loadLots())
</script>

<style scoped>
.page-head, .section-head, .actions { display: flex; gap: .75rem; flex-wrap: wrap; }
.page-head, .section-head { justify-content: space-between; align-items: flex-start; }
.layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 1rem; }
.sidebar { position: sticky; top: 1rem; align-self: start; }
.detail-grid { display: grid; gap: 1rem; }
.form-grid, .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .9rem; }
.kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.section-title { margin: 0 0 .9rem; font-size: 1.05rem; }
.pill { display:inline-flex; align-items:center; justify-content:center; min-width:1.8rem; height:1.8rem; padding:0 .55rem; border-radius:999px; background:rgba(255,255,255,.06); color:var(--text-muted); font-size:.82rem; }
.lot-btn { width:100%; margin-top:.6rem; border:1px solid var(--glass-border); background:rgba(255,255,255,.03); color:var(--text); text-align:left; border-radius:.85rem; padding:.85rem; cursor:pointer; }
.lot-btn.active { border-color:rgba(139,92,246,.45); background:rgba(139,92,246,.12); }
.lot-btn span, .lot-btn small, .block { display:block; }
.search-results { display:grid; gap:.45rem; }
.search-result { padding:.65rem .75rem; border-radius:.7rem; border:1px solid var(--glass-border); background:rgba(255,255,255,.03); color:var(--text); text-align:left; cursor:pointer; }
.linked { display:inline-flex; gap:.45rem; align-items:center; padding:.4rem .7rem; border-radius:999px; background:rgba(16,185,129,.15); color:#c7f9dd; }
.link-btn { background:none; border:0; color:inherit; text-decoration:underline; cursor:pointer; }
.table-wrap { overflow-x:auto; }
.lot-table { width:100%; border-collapse:collapse; }
.lot-table th, .lot-table td { padding:.75rem; border-bottom:1px solid var(--glass-border); vertical-align:top; text-align:left; }
.lot-table th { color:var(--text-muted); font-size:.8rem; }
.btn-small { min-height:34px; padding:.4rem .75rem; font-size:.82rem; }
.mini-link { display:block; margin-top:.2rem; color:var(--text-muted); }
.kpi label { display:block; margin-bottom:.2rem; color:var(--text-muted); font-size:.78rem; }
.kpi strong { font-size:1.15rem; }
.empty-state { min-height:220px; display:grid; place-items:center; color:var(--text-muted); }
.value-positive { color:var(--success); }
.value-negative { color:var(--error); }
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } .sidebar { position:static; } }
@media (max-width: 768px) { .form-grid, .kpis { grid-template-columns: 1fr; } .page-head, .section-head { flex-direction:column; } .actions { width:100%; } }
</style>
