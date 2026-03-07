<template>
  <teleport to="body">
    <div class="fixed bottom-4 right-4 z-[100] space-y-3 w-80 max-w-[calc(100vw-2rem)]">
      <transition-group name="slide-up">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'rounded-xl shadow-elevated border p-4 flex items-start gap-3',
            'animate-slide-up',
            typeClasses[notification.type]
          ]"
        >
          <!-- Icon -->
          <div :class="['w-5 h-5 mt-0.5 flex-shrink-0', iconColor[notification.type]]">
            <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <svg v-else-if="notification.type === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <svg v-else-if="notification.type === 'warning'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-gray-900">{{ notification.title }}</p>
            <p v-if="notification.message" class="text-sm text-gray-600 mt-0.5">{{ notification.message }}</p>
          </div>

          <!-- Close -->
          <button @click="store.remove(notification.id)" class="p-1 rounded hover:bg-black/5 transition-colors cursor-pointer flex-shrink-0">
            <svg class="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNotificationStore } from '@/stores/notification'

const store = useNotificationStore()
const notifications = computed(() => store.notifications)

const typeClasses: Record<string, string> = {
  success: 'bg-white border-green-200',
  error: 'bg-white border-red-200',
  warning: 'bg-white border-amber-200',
  info: 'bg-white border-blue-200',
}

const iconColor: Record<string, string> = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-amber-500',
  info: 'text-blue-500',
}
</script>
