<template>
  <div id="app">
    <nav>
      <span class="logo">📀 Collectabase</span>
      <router-link to="/">My Games</router-link>
      <router-link to="/wishlist">Wishlist</router-link>
      <router-link to="/stats">Stats</router-link>
      <router-link to="/import">Import</router-link>
      <router-link to="/add" class="btn btn-primary">+ Add Game</router-link>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style scoped>
main {
  flex: 1;
}
</style>
