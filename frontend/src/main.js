import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// Views
import GamesList from './views/GamesList.vue'
import GameDetail from './views/GameDetail.vue'
import AddGame from './views/AddGame.vue'
import Wishlist from './views/Wishlist.vue'
import Import from './views/Import.vue'
import Stats from './views/Stats.vue'
import Settings from './views/Settings.vue'

const routes = [
  { path: '/', component: GamesList },
  { path: '/game/:id', component: GameDetail, props: true },
  { path: '/add', component: AddGame },
  { path: '/edit/:id', component: AddGame },
  { path: '/wishlist', component: Wishlist },
  { path: '/import', component: Import },
  { path: '/stats', component: Stats },
  { path: '/settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(() => console.log('SW registered'))
      .catch(err => console.log('SW failed:', err))
  })
}
