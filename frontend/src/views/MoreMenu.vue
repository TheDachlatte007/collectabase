<template>
  <div class="container">
    <h1 class="mb-3">More</h1>
    <p class="more-intro">Collection tools and admin actions.</p>

    <div class="more-section">
      <h2 class="more-section-title">Collection</h2>
      <div class="more-grid">
        <router-link to="/add" class="more-card">
          <div class="more-icon">➕</div>
          <div class="more-copy">
            <div class="more-title">Add Game</div>
            <div class="more-sub">Create a new entry</div>
          </div>
        </router-link>

        <router-link to="/wishlist" class="more-card">
          <div class="more-icon">⭐</div>
          <div class="more-copy">
            <div class="more-title">Wishlist</div>
            <div class="more-sub">Track wanted games</div>
          </div>
        </router-link>
      </div>
    </div>

    <div class="more-section">
      <h2 class="more-section-title">Data & Admin</h2>
      <div class="more-grid">
        <router-link to="/import" class="more-card">
          <div class="more-icon">📦</div>
          <div class="more-copy">
            <div class="more-title">Import / Export</div>
            <div class="more-sub">CSV and CLZ tools</div>
          </div>
        </router-link>

        <router-link to="/settings" class="more-card">
          <div class="more-icon">⚙️</div>
          <div class="more-copy">
            <div class="more-title">Settings</div>
            <div class="more-sub">System, jobs, cleanup</div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.more-intro {
  margin: -0.5rem 0 1rem;
  color: var(--text-muted);
  max-width: 560px;
}

.more-section + .more-section {
  margin-top: 1rem;
}

.more-section-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin: 0 0 0.45rem;
}

.more-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.more-card {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  padding: 0.8rem 0.9rem;
  text-decoration: none;
  color: var(--text);
  transition: border-color 0.18s ease, transform 0.18s ease;
}

.more-card:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
}

.more-icon {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.45rem;
  background: var(--bg);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.more-copy {
  min-width: 0;
}

.more-title {
  font-weight: 700;
}

.more-sub {
  margin-top: 0.2rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}
</style>
