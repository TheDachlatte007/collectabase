<template>
  <div id="app">
    <NotificationStack />
    <header class="top-bar">
      <router-link to="/" class="logo" active-class="" exact-active-class="">🗃️ Collectabase</router-link>

      <!-- Desktop: inline nav links -->
      <nav class="desktop-nav">
        <router-link to="/" active-class="" exact-active-class="active">My Games</router-link>
        <router-link to="/stats">Stats</router-link>
        <router-link to="/prices">Prices</router-link>
        <router-link to="/more">More</router-link>
      </nav>

      <router-link to="/add" class="btn btn-primary add-btn" active-class="btn-active">+ Add</router-link>
    </header>

    <main>
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
import NotificationStack from './components/NotificationStack.vue'
</script>

<style scoped>
/* ── Top bar ── */
.top-bar {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.875rem 2rem;
  background: var(--bg-light);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  /* Accommodate iOS status bar in standalone mode */
  padding-top: max(0.875rem, env(safe-area-inset-top));
}

.logo {
  font-weight: bold;
  font-size: 1.1rem;
  color: var(--text);
  text-decoration: none;
  margin-right: auto;
  flex-shrink: 0;
}

/* ── Desktop nav links ── */
.desktop-nav {
  display: flex;
  gap: 1.5rem;
}

.desktop-nav a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.2s, border-color 0.2s;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  padding-bottom: 0.2rem;
}

.desktop-nav a:hover,
.desktop-nav a.active,
.desktop-nav a.router-link-active {
  color: var(--text);
  border-bottom-color: var(--primary);
}

.add-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

.btn-active {
  opacity: 1 !important;
}

/* ── Main content ── */
main {
  flex: 1;
}

/* ── Mobile bottom navigation ── */
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--bg-light);
  border-top: 1px solid var(--border);
  z-index: 100;
  /* Safe area for iPhone home indicator */
  padding-bottom: max(16px, env(safe-area-inset-bottom));
}

.mobile-nav a {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.6rem;
  gap: 0.2rem;
  padding: 12px 0.25rem 0.4rem;
  /* Ensure 44px minimum touch target */
  min-height: 44px;
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.mobile-nav a svg {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.mobile-nav a.nav-active {
  color: var(--primary);
  font-weight: 700;
  box-shadow: inset 0 -2px 0 var(--primary);
}

/* ── Responsive breakpoint ── */
@media (max-width: 639px) {
  .desktop-nav {
    display: none;
  }

  .mobile-nav {
    display: flex;
  }

  .top-bar {
    padding: max(0.75rem, env(safe-area-inset-top)) 1rem 0.75rem;
  }

  /* Push page content above the fixed bottom nav */
  main {
    padding-bottom: calc(56px + env(safe-area-inset-bottom));
  }
}
</style>
