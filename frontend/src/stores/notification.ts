import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
    duration?: number
}

export const useNotificationStore = defineStore('notification', () => {
    const notifications = ref<Notification[]>([])

    function add(notification: Omit<Notification, 'id'>) {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 9)
        const n = { ...notification, id }
        notifications.value.push(n)
        const duration = notification.duration ?? 3000
        if (duration > 0) {
            setTimeout(() => remove(id), duration)
        }
    }

    function remove(id: string) {
        notifications.value = notifications.value.filter(n => n.id !== id)
    }

    function success(title: string, message?: string) {
        add({ type: 'success', title, message })
    }

    function error(title: string, message?: string) {
        add({ type: 'error', title, message })
    }

    function warning(title: string, message?: string) {
        add({ type: 'warning', title, message })
    }

    function info(title: string, message?: string) {
        add({ type: 'info', title, message })
    }

    return { notifications, add, remove, success, error, warning, info }
})
