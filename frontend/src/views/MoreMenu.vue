<template>
  <div class="container">
    <h1 class="mb-3">More</h1>
    <div class="more-grid">
      <router-link to="/add" class="more-card">
        <div class="more-title">+ Add Game</div>
        <div class="more-sub">Create a new entry</div>
      </router-link>

      <router-link to="/wishlist" class="more-card">
        <div class="more-title">Wishlist</div>
        <div class="more-sub">Track wanted games</div>
      </router-link>

      <router-link to="/import" class="more-card">
        <div class="more-title">Import / Export</div>
        <div class="more-sub">CSV and CLZ tools</div>
      </router-link>

      <router-link to="/settings" class="more-card">
        <div class="more-title">Settings</div>
        <div class="more-sub">System, jobs, cleanup</div>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.more-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.more-card {
  display: block;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  padding: 0.9rem;
  text-decoration: none;
  color: var(--text);
  transition: border-color 0.18s ease, transform 0.18s ease;
}

.more-card:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
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
