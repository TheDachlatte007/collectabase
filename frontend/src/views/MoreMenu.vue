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

        <router-link to="/lots" class="more-card">
          <div class="more-icon">📦</div>
          <div class="more-copy">
            <div class="more-title">Lots & Resale</div>
            <div class="more-sub">Bundle cost basis and sales</div>
          </div>
        </router-link>

        <router-link to="/care" class="more-card">
          <div class="more-icon">✦</div>
          <div class="more-copy">
            <div class="more-title">Collection Care</div>
            <div class="more-sub">Review covers, values and details</div>
          </div>
        </router-link>
      </div>
    </div>

    <div class="more-section">
      <h2 class="more-section-title">Data & Admin</h2>
      <div class="more-grid">
        <router-link to="/import" class="more-card">
          <div class="more-icon">🧾</div>
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
  gap: 0.75rem;
  background: var(--surface-raised, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md, 0.75rem);
  padding: 0.9rem 1rem;
  text-decoration: none;
  color: var(--text);
  transition: border-color 0.18s ease, transform 0.18s ease, background 0.18s ease;
}

.more-card:hover {
  border-color: var(--primary);
  background: var(--surface-hover, rgba(255, 255, 255, 0.06));
  transform: translateY(-1px);
}

.more-icon {
  width: 2.1rem;
  height: 2.1rem;
  border-radius: var(--radius-sm, 0.5rem);
  background: var(--surface, rgba(0, 0, 0, 0.2));
  border: 1px solid var(--glass-border);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  font-size: 1.05rem;
}

.more-copy {
  min-width: 0;
}

.more-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.more-sub {
  margin-top: 0.2rem;
  font-size: 0.82rem;
  color: var(--text-muted);
}

@media (max-width: 480px) {
  .more-grid {
    grid-template-columns: 1fr;
  }
}
</style>
