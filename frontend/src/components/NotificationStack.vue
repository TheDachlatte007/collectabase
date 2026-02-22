<template>
  <div class="notify-stack" aria-live="polite" aria-atomic="true">
    <div
      v-for="n in notifications"
      :key="n.id"
      class="notify-item"
      :class="`notify-${n.type}`"
      role="status"
    >
      <span class="notify-text">{{ n.message }}</span>
      <button class="notify-close" type="button" @click="dismissNotification(n.id)" aria-label="Close notification">
        ✕
      </button>
    </div>
  </div>
</template>

<script setup>
import { useNotifications } from '../composables/useNotifications'

const { notifications, dismissNotification } = useNotifications()
</script>

<style scoped>
.notify-stack {
  position: fixed;
  top: calc(1rem + env(safe-area-inset-top));
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: min(360px, calc(100vw - 2rem));
}

.notify-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  padding: 0.7rem 0.85rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
}

.notify-text {
  font-size: 0.9rem;
  line-height: 1.35;
}

.notify-close {
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.85rem;
  opacity: 0.8;
}

.notify-close:hover {
  opacity: 1;
}

.notify-success {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.45);
  color: #dcfce7;
}

.notify-error {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.5);
  color: #fee2e2;
}

.notify-info {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.45);
  color: #e0e7ff;
}

@media (max-width: 639px) {
  .notify-stack {
    top: auto;
    bottom: calc(66px + env(safe-area-inset-bottom));
    right: 0.75rem;
    left: 0.75rem;
    width: auto;
  }
}
</style>

