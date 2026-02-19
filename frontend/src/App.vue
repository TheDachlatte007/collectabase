<template>
  <div id="app">
    <nav>
      <router-link to="/" class="logo">🗃️ Collectabase</router-link>
      <div class="nav-links">
        <router-link to="/">My Games</router-link>
        <router-link to="/wishlist">Wishlist</router-link>
        <router-link to="/stats">Stats</router-link>
        <router-link to="/import">Import</router-link>
        <router-link to="/settings">Settings</router-link>
      </div>
      <router-link to="/add" class="btn btn-primary" active-class="btn-active">+ Add</router-link>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style scoped>
nav {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 2rem;
  background: var(--bg-light);
  border-bottom: 1px solid var(--border);
}

.logo {
  font-weight: bold;
  font-size: 1.1rem;
  color: var(--text);
  text-decoration: none;
  margin-right: auto;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: var(--text);
}

.btn-active {
  opacity: 1 !important;
}

main {
  flex: 1;
}
</style>
