<template>
  <div class="container">
    <h1 class="mb-3">{{ isEditMode ? 'Edit Game' : 'Add Game' }}</h1>

    <div class="form-layout">
      <!-- IGDB Search -->
      <div class="card mb-3">
        <h3>Search IGDB (optional)</h3>
        <div class="flex gap-2 mb-2 search-row">
          <input v-model="igdbSearch" placeholder="Search by title..." @keyup.enter="searchIgdb" />
          <button @click="searchIgdb" class="btn btn-secondary" style="flex-shrink:0" :disabled="igdbLoading">
            {{ igdbLoading ? 'Searching...' : 'Search' }}
          </button>
        </div>
        <div v-if="igdbResults.length === 0 && igdbSearch && !igdbLoading" class="text-muted mt-2">
          No results found
        </div>
        <div v-for="result in igdbResults" :key="result.igdb_id || result.gametdb_id" 
            class="igdb-item" @click="fillFromIgdb(result)">
        <img v-if="result.cover_url" :src="result.cover_url" />
        <div>
          <strong>{{ result.title }}</strong>
          <p class="text-muted">{{ result.platforms?.join(', ') || result.platform }}</p>
          <span class="source-badge">{{ result.source === 'gametdb' ? '🖼️ GameTDB' : '🎮 IGDB' }}</span>
        </div>
      </div>
      </div>

      <!-- Game Form -->
      <form @submit.prevent="saveGame" class="card">
        <div class="form-grid">
          <div class="form-group">
            <label>Title *</label>
            <input v-model="game.title" required />
          </div>
          
          <div class="form-group">
            <label>Platform *</label>
            <select v-model="game.platform_id" required>
              <option value="">Select platform</option>
              <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Type</label>
            <select v-model="game.item_type">
              <option value="game">Game</option>
              <option value="console">Console</option>
              <option value="accessory">Accessory</option>
              <option value="misc">Misc</option>
            </select>
          </div>


          <div class="form-group">
            <label>Barcode</label>
            <div class="barcode-row">
              <input v-model="game.barcode" @keyup.enter="lookupBarcode" />
              <button type="button" class="btn btn-secondary barcode-btn" @click="lookupBarcode" :disabled="barcodeLookupLoading || !game.barcode" title="Lookup barcode">
                {{ barcodeLookupLoading ? '...' : '🔎' }}
              </button>
              <button type="button" class="btn btn-secondary barcode-btn" @click="openScanner" title="Scan barcode">
                📷
              </button>
            </div>
            <p v-if="barcodeLookupInfo" class="barcode-status">{{ barcodeLookupInfo }}</p>
          </div>

          <div class="form-group">
            <label>Region</label>
            <select v-model="game.region">
              <option value="">Select</option>
              <option>PAL</option>
              <option>NTSC</option>
              <option>EU</option>
              <option>US</option>
              <option>JP</option>
            </select>
          </div>

          <div class="form-group">
            <label>Condition</label>
            <select v-model="game.condition">
              <option value="">Select</option>
              <option>Mint</option>
              <option>Good</option>
              <option>Fair</option>
              <option>Poor</option>
            </select>
          </div>

          <div class="form-group">
            <label>Completeness</label>
            <select v-model="game.completeness">
              <option value="">Select</option>
              <option>New/Sealed</option>
              <option>CIB (Complete In Box)</option>
              <option>Box + Game</option>
              <option>Game + Manual</option>
              <option>Loose</option>
            </select>
          </div>

          <div class="form-group">
            <label>Release Date</label>
            <input v-model="game.release_date" type="date" />
          </div>

          <div class="form-group">
            <label>Location</label>
            <input v-model="game.location" placeholder="e.g. Shelf A, Box 3" />
          </div>

          <div class="form-group">
            <label>Purchase Date</label>
            <input v-model="game.purchase_date" type="date" />
          </div>

          <div class="form-group">
            <label>Purchase Price (€)</label>
            <input v-model.number="game.purchase_price" type="number" step="0.01" />
          </div>

          <div class="form-group">
            <label>Current Value (€)</label>
            <input v-model.number="game.current_value" type="number" step="0.01" />
          </div>

          <div class="form-group">
            <label>Genre</label>
            <input v-model="game.genre" placeholder="e.g. RPG, Platformer" />
          </div>

          <div class="form-group">
            <label>Developer</label>
            <input v-model="game.developer" />
          </div>

          <div class="form-group">
            <label>Publisher</label>
            <input v-model="game.publisher" />
          </div>

          <div class="form-group full-width">
            <label>Cover Photo</label>
            <div class="cover-preview-row">
              <div v-if="game.cover_url" class="cover-thumb-wrap">
                <img :src="game.cover_url" class="cover-thumb" />
                <button type="button" class="cover-thumb-remove" @click="game.cover_url = ''" title="Remove cover">✕</button>
              </div>
              <div class="cover-upload-actions">
                <input
                  ref="coverFileInput"
                  type="file"
                  accept="image/*"
                  capture="environment"
                  style="display:none"
                  @change="onCoverFileSelected"
                />
                <button type="button" class="btn btn-secondary" @click="coverFileInput.click()" :disabled="coverUploading">
                  {{ coverUploading ? '⏳ Uploading...' : '📷 Upload Photo' }}
                </button>
                <span v-if="coverUploadError" class="cover-upload-error">{{ coverUploadError }}</span>
              </div>
            </div>
          </div>

          <div class="form-group full-width">
            <label>Description</label>
            <textarea v-model="game.description" rows="3"></textarea>
          </div>

          <div class="form-group full-width">
            <label>Notes</label>
            <textarea v-model="game.notes" rows="3"></textarea>
          </div>

          <div class="form-group full-width">
            <label class="flex items-center gap-2">
              <input v-model="game.is_wishlist" type="checkbox" />
              Add to Wishlist
            </label>
          </div>

          <div v-if="game.is_wishlist" class="form-group">
            <label>Max Wishlist Price (€)</label>
            <input v-model.number="game.wishlist_max_price" type="number" step="0.01" />
          </div>
        </div>

        <div v-if="duplicateWarning" class="duplicate-warning mt-3">
          <span>⚠️ This game already exists in your collection.</span>
          <div class="flex gap-2 mt-2">
            <router-link v-if="duplicateWarning.existing_id" :to="`/game/${duplicateWarning.existing_id}`" class="btn btn-secondary">View existing</router-link>
            <button type="button" class="btn btn-secondary" @click="saveAnyway" :disabled="saving">Save anyway</button>
          </div>
        </div>

        <div class="flex gap-2 mt-3">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : (isEditMode ? 'Update Game' : 'Save Game') }}
          </button>
          <router-link to="/" class="btn btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>

    <!-- Barcode Scanner Modal -->
    <div v-if="scannerOpen" class="scanner-overlay" @click.self="closeScanner">
      <div class="scanner-modal">
        <div class="scanner-header">
          <span>Scan Barcode</span>
          <button type="button" class="scanner-close" @click="closeScanner">✕</button>
        </div>
        <div class="scanner-body">
          <video ref="scannerVideo" class="scanner-video" autoplay playsinline muted></video>
          <div class="scanner-reticle"></div>
          <p v-if="scannerError" class="scanner-error">{{ scannerError }}</p>
          <p v-else class="scanner-hint">Point camera at barcode {{ scannerMode ? `(${scannerMode})` : '' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { gamesApi, lookupApi, platformsApi } from '../api'
import { notifyError, notifySuccess } from '../composables/useNotifications'

const router = useRouter()
const route = useRoute()
const platforms = ref([])
const saving = ref(false)
const igdbSearch = ref('')
const igdbResults = ref([])
const igdbLoading = ref(false)
const isEditMode = ref(false)
const editId = ref(null)
const coverFileInput = ref(null)
const coverUploading = ref(false)
const coverUploadError = ref('')
const duplicateWarning = ref(null)  // { existing_id } when 409
const saveForced = ref(false)
const scannerOpen = ref(false)
const scannerError = ref('')
const scannerMode = ref('')
const scannerVideo = ref(null)
const barcodeLookupLoading = ref(false)
const barcodeLookupInfo = ref('')
let cameraStream = null
let scanFrame = null
let zxingControls = null

const game = ref({
  title: '',
  platform_id: '',
  item_type: 'game',
  barcode: '',
  region: '',
  condition: '',
  completeness: '',
  purchase_price: null,
  current_value: null,
  purchase_date: null,
  notes: '',
  is_wishlist: false,
  igdb_id: null,
  cover_url: null,
  genre: null,
  description: null,
  developer: null,
  publisher: null,
  release_date: null,
  location: null,
  wishlist_max_price: null
})

async function loadPlatforms() {
  const res = await platformsApi.list()
  platforms.value = res.data || []
  if (!res.ok) notifyError('Failed to load platforms.')
}

async function loadGame(id) {
  try {
    const res = await gamesApi.get(id)
    if (res.ok) {
      const data = res.data
      game.value = {
        title: data.title || '',
        platform_id: data.platform_id || '',
        item_type: data.item_type || 'game',
        barcode: data.barcode || '',
        region: data.region || '',
        condition: data.condition || '',
        completeness: data.completeness || '',
        purchase_price: data.purchase_price ?? null,
        current_value: data.current_value ?? null,
        purchase_date: data.purchase_date || null,
        notes: data.notes || '',
        is_wishlist: data.is_wishlist || false,
        igdb_id: data.igdb_id || null,
        cover_url: data.cover_url || null,
        genre: data.genre || null,
        description: data.description || null,
        developer: data.developer || null,
        publisher: data.publisher || null,
        release_date: data.release_date || null,
        location: data.location || null,
        wishlist_max_price: data.wishlist_max_price ?? null
      }
    }
  } catch (e) {
    console.error('Failed to load game:', e)
    notifyError('Failed to load game.')
  }
}


async function searchIgdb() {
  if (!igdbSearch.value) return
  igdbLoading.value = true
  try {
    const res = await lookupApi.combined(igdbSearch.value)
    const data = res.data || {}
    igdbResults.value = data.results || [
      ...(data.igdb || []),
      ...(data.gametdb || [])
    ]
  } catch (e) {
    console.error('Search failed:', e)
    notifyError('Search failed.')
  } finally {
    igdbLoading.value = false
  }
}

function normalizeBarcode(value) {
  return String(value || '').replace(/\D+/g, '')
}

async function lookupBarcode() {
  await lookupBarcodeByValue(game.value.barcode, { fromScan: false })
}

async function lookupBarcodeByValue(value, { fromScan = false } = {}) {
  const normalized = normalizeBarcode(value)
  if (normalized.length < 8) {
    barcodeLookupInfo.value = 'Barcode seems too short. Please scan a valid UPC/EAN.'
    if (fromScan) notifyError('Invalid barcode scanned.')
    return
  }

  game.value.barcode = normalized
  barcodeLookupLoading.value = true
  barcodeLookupInfo.value = 'Looking up barcode...'

  try {
    const res = await lookupApi.barcode(normalized)
    if (!res.ok) {
      const detail = res.data?.detail
      const message = detail?.message || detail || 'Barcode lookup failed.'
      barcodeLookupInfo.value = message
      notifyError(message)
      return
    }

    const data = res.data || {}
    const suggestions = data.suggestions || []
    const titleCandidates = data.title_candidates || []
    const existing = data.existing || null

    if (existing?.id) {
      duplicateWarning.value = { existing_id: existing.id }
      barcodeLookupInfo.value = `Already in collection: ${existing.title}${existing.platform_name ? ` (${existing.platform_name})` : ''}`
    } else {
      duplicateWarning.value = null
    }

    if (suggestions.length > 0) {
      igdbResults.value = suggestions
      igdbSearch.value = data.lookup_title || titleCandidates[0] || ''
      barcodeLookupInfo.value = `Found ${suggestions.length} metadata matches. Tap one to apply.`
      if (!existing?.id) notifySuccess('Barcode recognized. Choose a match below.')
      return
    }

    if (titleCandidates.length > 0) {
      igdbSearch.value = titleCandidates[0]
      await searchIgdb()
      if (igdbResults.value.length > 0) {
        barcodeLookupInfo.value = `Found title "${titleCandidates[0]}". Choose a match below.`
        if (!existing?.id) notifySuccess('Title candidate found for barcode.')
      } else {
        barcodeLookupInfo.value = `Found title "${titleCandidates[0]}", but no IGDB/GameTDB match.`
      }
      return
    }

    if (!existing?.id) {
      barcodeLookupInfo.value = 'No metadata found. You can still add this item manually.'
      if (fromScan) notifyError('No metadata found for barcode.')
    }
  } catch (e) {
    console.error('Barcode lookup failed:', e)
    barcodeLookupInfo.value = 'Barcode lookup failed.'
    notifyError('Barcode lookup failed.')
  } finally {
    barcodeLookupLoading.value = false
  }
}

async function handleDetectedBarcode(rawValue) {
  const normalized = normalizeBarcode(rawValue)
  if (!normalized) return

  closeScanner()
  await lookupBarcodeByValue(normalized, { fromScan: true })
}

function fillFromIgdb(result) {
  const incomingCover = result.source === 'gametdb'
    ? (result.cover_front || result.cover_url)
    : result.cover_url

  // Determine which fields would be overwritten
  const overwrites = []
  if (game.value.title && result.title && game.value.title !== result.title)
    overwrites.push('Title')
  if (game.value.cover_url && incomingCover && game.value.cover_url !== incomingCover)
    overwrites.push('Cover')
  if (game.value.platform_id) {
    // Check if a platform match exists and differs
    let matchId = null
    if (result.source === 'igdb' && result.platforms?.length > 0) {
      const match = platforms.value.find(p =>
        result.platforms.some(rp =>
          rp.toLowerCase().includes(p.name.toLowerCase()) ||
          p.name.toLowerCase().includes(rp.toLowerCase())
        )
      )
      matchId = match?.id ?? null
    } else if (result.source === 'gametdb') {
      const platformMap = { 'wii': 'Wii', 'wiiu': 'Wii U', 'gc': 'GameCube', 'ds': 'Nintendo DS', '3ds': 'Nintendo 3DS', 'ps3': 'PlayStation 3', '360': 'Xbox 360' }
      const platformName = platformMap[result.platform]
      if (platformName) {
        const match = platforms.value.find(p => p.name.toLowerCase().includes(platformName.toLowerCase()))
        matchId = match?.id ?? null
      }
    }
    if (matchId && matchId !== game.value.platform_id) overwrites.push('Platform')
  }
  if (result.source === 'igdb') {
    if (game.value.release_date && result.release_date) overwrites.push('Year')
  }

  if (overwrites.length > 0) {
    const ok = window.confirm(
      `Apply IGDB data?\n\nThis will overwrite: ${overwrites.join(', ')}\n\nClick OK to apply or Cancel to keep your data.`
    )
    if (!ok) {
      igdbResults.value = []
      igdbSearch.value = ''
      return
    }
  }

  // Apply common fields
  game.value.title = result.title
  game.value.cover_url = incomingCover

  if (result.source === 'igdb') {
    game.value.igdb_id = result.igdb_id
    game.value.genre = result.genre
    game.value.description = result.description
    game.value.release_date = result.release_date
    game.value.developer = result.developer || null
    game.value.publisher = result.publisher || null
    if (result.platforms?.length > 0) {
      const match = platforms.value.find(p =>
        result.platforms.some(rp =>
          rp.toLowerCase().includes(p.name.toLowerCase()) ||
          p.name.toLowerCase().includes(rp.toLowerCase())
        )
      )
      if (match) game.value.platform_id = match.id
    }
  }

  if (result.source === 'gametdb') {
    game.value.gametdb_id = result.gametdb_id
    const platformMap = { 'wii': 'Wii', 'wiiu': 'Wii U', 'gc': 'GameCube', 'ds': 'Nintendo DS', '3ds': 'Nintendo 3DS', 'ps3': 'PlayStation 3', '360': 'Xbox 360' }
    const platformName = platformMap[result.platform]
    if (platformName) {
      const match = platforms.value.find(p => p.name.toLowerCase().includes(platformName.toLowerCase()))
      if (match) game.value.platform_id = match.id
    }
  }

  igdbResults.value = []
  igdbSearch.value = ''
}

async function onCoverFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  coverUploadError.value = ''
  if (file.size > 5 * 1024 * 1024) {
    coverUploadError.value = 'File exceeds 5 MB limit.'
    event.target.value = ''
    return
  }
  coverUploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await gamesApi.uploadCover(form)
    if (!res.ok) {
      const err = res.data || {}
      coverUploadError.value = err?.detail?.message || err?.detail || err?.error || 'Upload failed.'
      notifyError(coverUploadError.value)
      return
    }
    const { url } = res.data
    game.value.cover_url = url
    notifySuccess('Cover uploaded.')
  } catch (e) {
    coverUploadError.value = 'Upload failed.'
    console.error(e)
    notifyError('Upload failed.')
  } finally {
    coverUploading.value = false
    event.target.value = ''
  }
}

async function saveGame() {
  saving.value = true
  duplicateWarning.value = null
  try {
    const res = isEditMode.value
      ? await gamesApi.update(editId.value, game.value)
      : await gamesApi.create(game.value, saveForced.value)
    if (res.status === 409) {
      const data = res.data?.detail || res.data || {}
      duplicateWarning.value = { existing_id: data.existing_id }
      notifyError('Game already exists in this platform.')
      return
    }
    if (res.ok) {
      saveForced.value = false
      notifySuccess(isEditMode.value ? 'Game updated.' : 'Game created.')
      router.push(isEditMode.value ? `/game/${editId.value}` : '/')
    } else {
      const detail = res.data?.detail
      const message = detail?.message || detail || res.data?.error || 'Failed to save game.'
      notifyError(message)
    }
  } catch (e) {
    console.error('Failed to save:', e)
    notifyError('Failed to save game.')
  } finally {
    saving.value = false
  }
}

function saveAnyway() {
  saveForced.value = true
  saveGame()
}

function openScanner() {
  scannerOpen.value = true
  scannerError.value = ''
  scannerMode.value = ''
  nextTick(() => startCamera())
}

function closeScanner() {
  scannerOpen.value = false
  stopCamera()
}

function stopCamera() {
  if (scanFrame) {
    cancelAnimationFrame(scanFrame)
    scanFrame = null
  }
  if (zxingControls && typeof zxingControls.stop === 'function') {
    zxingControls.stop()
    zxingControls = null
  }
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop())
    cameraStream = null
  }
  if (scannerVideo.value) {
    scannerVideo.value.srcObject = null
  }
}

async function startCamera() {
  try {
    if (!window.isSecureContext && !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      scannerError.value = 'Camera requires HTTPS (or localhost).'
      return
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      scannerError.value = 'Camera API is not available in this browser.'
      return
    }

    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    })
    scannerVideo.value.srcObject = cameraStream
    await scannerVideo.value.play()

    let supportsNative = false
    if (window.BarcodeDetector) {
      try {
        if (typeof window.BarcodeDetector.getSupportedFormats === 'function') {
          const supported = await window.BarcodeDetector.getSupportedFormats()
          supportsNative = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39'].some(f => supported.includes(f))
        } else {
          supportsNative = true
        }
      } catch {
        supportsNative = false
      }
    }

    if (supportsNative) {
      scannerMode.value = 'native scanner'
      const detector = new window.BarcodeDetector({
        formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39'],
      })
      const scan = async () => {
        if (!scannerOpen.value) return
        try {
          const codes = await detector.detect(scannerVideo.value)
          if (codes?.length) {
            const raw = codes[0]?.rawValue
            if (raw) {
              await handleDetectedBarcode(raw)
              return
            }
          }
        } catch {
          // Keep scanning; errors here are usually transient while frames are warming up.
        }
        scanFrame = requestAnimationFrame(scan)
      }
      scanFrame = requestAnimationFrame(scan)
      return
    }

    scannerMode.value = 'zxing fallback'
    const { BrowserMultiFormatReader } = await import('@zxing/browser')
    const reader = new BrowserMultiFormatReader()
    zxingControls = await reader.decodeFromStream(
      cameraStream,
      scannerVideo.value,
      async (result) => {
        if (!result) return
        const raw = result.getText?.() || ''
        if (raw) {
          await handleDetectedBarcode(raw)
        }
      }
    )
  } catch (e) {
    console.error('Scanner error:', e)
    scannerError.value = 'Camera access denied or unavailable. Please allow camera access in Safari settings.'
  }
}



onMounted(async () => {
  await loadPlatforms()
  if (route.params.id) {
    isEditMode.value = true
    editId.value = route.params.id
    await loadGame(route.params.id)
  }
})

onUnmounted(() => {
  stopCamera()
})

</script>


<style scoped>
.form-layout {
  max-width: 800px;
}

.duplicate-warning {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.form-grid .full-width {
  grid-column: 1 / -1;
}

.igdb-results {
  margin-top: 1rem;
}

.igdb-item {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
  /* Touch-friendly: no flash, snappy tap */
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  min-height: 44px;
}

.igdb-item:hover {
  background: var(--bg-lighter);
}

.igdb-item img {
  width: 60px;
  height: 80px;
  object-fit: cover;
  border-radius: 0.25rem;
}
.source-badge {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  display: block;
}

/* Prevent search input overflowing and squeezing the button */
.search-row input {
  flex: 1;
  min-width: 0;
}

.cover-preview-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.cover-thumb-wrap {
  position: relative;
  flex-shrink: 0;
}

.cover-thumb {
  width: 80px;
  height: 107px;
  object-fit: cover;
  border-radius: 0.25rem;
  display: block;
}

.cover-thumb-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.65rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.cover-upload-actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  justify-content: center;
}

.cover-upload-error {
  font-size: 0.8rem;
  color: #ef4444;
}

.barcode-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.barcode-row input {
  min-width: 0;
  flex: 1;
}

.barcode-btn {
  min-width: 42px;
  padding: 0.45rem 0.65rem;
  justify-content: center;
}

.barcode-status {
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.scanner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 80;
  padding: 1rem;
}

.scanner-modal {
  width: min(560px, 100%);
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  overflow: hidden;
}

.scanner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
}

.scanner-close {
  border: none;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.scanner-body {
  position: relative;
  aspect-ratio: 16 / 10;
  background: #000;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.scanner-reticle {
  position: absolute;
  inset: 18% 14%;
  border: 2px solid rgba(34, 197, 94, 0.9);
  border-radius: 0.5rem;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.18);
  pointer-events: none;
}

.scanner-hint,
.scanner-error {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0.6rem;
  text-align: center;
  font-size: 0.82rem;
  padding: 0 0.75rem;
}

.scanner-hint {
  color: #d1d5db;
}

.scanner-error {
  color: #fca5a5;
}

@media (max-width: 639px) {
  .barcode-btn {
    min-width: 38px;
    padding: 0.35rem 0.45rem;
  }
}
</style>
