<template>
  <div id="app">
    <header class="top-bar">
      <router-link to="/" class="logo" active-class="" exact-active-class="">🗃️ Collectabase</router-link>

      <!-- Desktop: inline nav links -->
      <nav class="desktop-nav">
        <router-link to="/" active-class="" exact-active-class="active">My Games</router-link>
        <router-link to="/wishlist">Wishlist</router-link>
        <router-link to="/stats">Stats</router-link>
        <router-link to="/import">Import</router-link>
        <router-link to="/settings">Settings</router-link>
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

      <router-link to="/wishlist" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span>Wishlist</span>
      </router-link>

      <router-link to="/stats" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <line x1="18" y1="20" x2="18" y2="10"/>
          <line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
        <span>Stats</span>
      </router-link>

      <router-link to="/import" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <span>Import</span>
      </router-link>

      <router-link to="/settings" active-class="nav-active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>Settings</span>
      </router-link>
    </nav>
  </div>
</template>

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
  transition: color 0.2s;
  white-space: nowrap;
}

.desktop-nav a:hover,
.desktop-nav a.active,
.desktop-nav a.router-link-active {
  color: var(--text);
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
  padding-bottom: env(safe-area-inset-bottom);
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
  padding: 0.4rem 0.25rem;
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
