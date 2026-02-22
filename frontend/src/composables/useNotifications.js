import { readonly, ref } from 'vue'

const notifications = ref([])
let nextId = 1

export function notify(message, type = 'info', timeoutMs = 3500) {
  const id = nextId++
  notifications.value.push({ id, type, message })
  if (timeoutMs > 0) {
    window.setTimeout(() => dismissNotification(id), timeoutMs)
  }
  return id
}

export function notifySuccess(message, timeoutMs = 2800) {
  return notify(message, 'success', timeoutMs)
}

export function notifyError(message, timeoutMs = 4200) {
  return notify(message, 'error', timeoutMs)
}

export function dismissNotification(id) {
  const idx = notifications.value.findIndex(n => n.id === id)
  if (idx >= 0) notifications.value.splice(idx, 1)
}

export function useNotifications() {
  return {
    notifications: readonly(notifications),
    dismissNotification
  }
}

