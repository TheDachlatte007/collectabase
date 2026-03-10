<template>
  <div id="app" class="app-layout">
    <NotificationStack />

    <!-- Desktop Sidebar -->
    <aside class="desktop-sidebar" :class="{ 'collapsed': collapsed }">
      <div class="sidebar-top">
        <router-link to="/" class="sidebar-logo">
          <img src="/icons/android-chrome-192x192.png" alt="Collectabase Logo" class="logo-img" />
          <span class="logo-text" v-show="!collapsed">Collectabase</span>
        </router-link>
        <button class="collapse-btn" @click="toggleSidebar" :title="collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'">
          <svg v-if="collapsed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"></polyline><polyline points="6 17 11 12 6 7"></polyline></svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"></polyline><polyline points="18 17 13 12 18 7"></polyline></svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" active-class="" exact-active-class="active" title="My Games">
          <span class="nav-icon">🎮</span> <span v-show="!collapsed">My Games</span>
        </router-link>
        <router-link to="/stats" title="Stats">
          <span class="nav-icon">📈</span> <span v-show="!collapsed">Stats</span>
        </router-link>
        <router-link to="/prices" title="Prices Browser">
          <span class="nav-icon">💰</span> <span v-show="!collapsed">Prices</span>
        </router-link>
        <router-link to="/more" title="More Options">
          <span class="nav-icon">⚙️</span> <span v-show="!collapsed">More</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/add" class="btn btn-primary add-btn" active-class="btn-active" title="Add Game">
          <span v-if="collapsed" style="font-size: 1.25rem;">+</span>
          <span v-else>+ Add Game</span>
        </router-link>
      </div>
    </aside>

    <!-- Mobile Top Header -->
    <header class="mobile-header">
      <router-link to="/" class="logo">
        <img src="/icons/android-chrome-192x192.png" alt="Collectabase Logo" class="logo-img" />
        Collectabase
      </router-link>
      <router-link to="/add" class="btn btn-primary btn-compact">+ Add</router-link>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <!-- Mobile-only bottom navigation -->
    <nav class="mobile-nav" aria-label="Main navigation">
      <router-link to="/" active-class="" exact-active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>Games</span>
      </router-link>

      <router-link to="/stats" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <line x1="18" y1="20" x2="18" y2="10"/>
          <line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
        <span>Stats</span>
      </router-link>

      <router-link to="/prices" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        <span>Prices</span>
      </router-link>

      <router-link to="/more" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="1.5"/>
          <circle cx="19" cy="12" r="1.5"/>
          <circle cx="5" cy="12" r="1.5"/>
        </svg>
        <span>More</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import NotificationStack from './components/NotificationStack.vue'

const collapsed = ref(false)

onMounted(() => {
  const saved = localStorage.getItem('collectabase_sidebar_collapsed')
  if (saved === 'true') {
    collapsed.value = true
  }
})

function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('collectabase_sidebar_collapsed', String(collapsed.value))
}
</script>

<style scoped>
/* ── Desktop Layout ── */
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.desktop-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-light);
  border-right: 1px solid var(--glass-border);
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 1.5rem;
  z-index: 100;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), padding 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.desktop-sidebar.collapsed {
  width: 80px;
  padding: 1.5rem 0.75rem;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2.5rem;
}

.desktop-sidebar.collapsed .sidebar-top {
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.collapse-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  border-radius: 0.35rem;
  transition: color 0.2s, background 0.2s;
}

.collapse-btn:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
}

.logo-img {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  object-fit: contain;
  box-shadow: 0 2px 10px rgba(139, 92, 246, 0.2);
  flex-shrink: 0;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.03em;
  white-space: nowrap;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 0.75rem;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  white-space: nowrap;
}

.desktop-sidebar.collapsed .sidebar-nav a {
  justify-content: center;
  padding: 0.875rem 0;
}

.sidebar-nav a:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
}

.sidebar-nav a.active,
.sidebar-nav a.router-link-active {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05));
  border-color: rgba(139, 92, 246, 0.3);
  color: var(--primary);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.nav-icon {
  font-size: 1.25rem;
  opacity: 0.8;
  flex-shrink: 0;
  display: inline-flex;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1.5rem;
}

.add-btn {
  width: 100%;
  justify-content: center;
  font-size: 1.05rem;
  padding: 0.875rem;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25);
  white-space: nowrap;
  overflow: hidden;
}

.desktop-sidebar.collapsed .add-btn {
  padding: 0.875rem 0;
}

.main-content {
  flex: 1;
  min-width: 0; /* Prevents flex children from overflowing */
  display: flex;
  flex-direction: column;
}

/* ── Mobile Layout ── */
.mobile-header {
  display: none;
}

.mobile-nav {
  display: none;
}

.btn-active {
  opacity: 1 !important;
}

/* ── Responsive breakpoints ── */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }

  .desktop-sidebar {
    display: none;
  }

  .mobile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: max(0.875rem, env(safe-area-inset-top)) 1.25rem 0.875rem;
    background: var(--bg-light);
    border-bottom: 1px solid var(--glass-border);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: var(--card-blur);
    -webkit-backdrop-filter: var(--card-blur);
  }

  .mobile-header .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--text);
    text-decoration: none;
  }

  .mobile-header .logo-img {
    width: 24px;
    height: 24px;
    box-shadow: none;
  }

  .main-content {
    padding-bottom: calc(64px + env(safe-area-inset-bottom));
  }

  .mobile-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 64px;
    background: rgba(9, 9, 11, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid var(--glass-border);
    z-index: 100;
    padding-bottom: max(0px, env(safe-area-inset-bottom));
    box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.2);
  }

  .mobile-nav a {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.65rem;
    font-weight: 500;
    gap: 0.25rem;
    transition: color 0.2s;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-nav a svg {
    width: 24px;
    height: 24px;
    stroke-width: 2.2;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .mobile-nav a.nav-active {
    color: var(--primary);
  }

  .mobile-nav a.nav-active svg {
    transform: scale(1.15);
  }
}
</style>
