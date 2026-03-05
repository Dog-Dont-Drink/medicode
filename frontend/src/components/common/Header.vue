<template>
  <header class="fixed top-0 left-0 right-0 z-50 h-16 bg-white/80 backdrop-blur-xl border-b border-gray-100 shadow-soft">
    <div class="h-full flex items-center justify-between px-4 lg:px-6">
      <!-- Left: Menu + Logo -->
      <div class="flex items-center gap-3">
        <button
          @click="$emit('toggle-sidebar')"
          class="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          aria-label="Toggle menu"
        >
          <svg class="w-5 h-5 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <router-link to="/dashboard" class="flex items-center gap-2.5 cursor-pointer">
          <div class="w-8 h-8 bg-gradient-to-br from-primary to-primary-600 rounded-lg flex items-center justify-center shadow-sm">
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <span class="text-lg font-heading font-bold text-gray-900 hidden sm:block">MediCode</span>
        </router-link>
      </div>

      <!-- Center: Search -->
      <div class="hidden md:flex flex-1 max-w-md mx-8">
        <div class="relative w-full">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="搜索项目、分析..."
            class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm
                   placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white
                   transition-all duration-200"
          />
        </div>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-2">
        <!-- Token Balance -->
        <div class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-primary-50 rounded-lg">
          <svg class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/>
          </svg>
          <span class="text-sm font-medium text-primary-700">{{ tokenBalance }}</span>
        </div>

        <!-- Notifications -->
        <button class="relative p-2 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer" aria-label="Notifications">
          <svg class="w-5 h-5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
          <span class="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full"></span>
        </button>

        <!-- User Avatar -->
        <div class="relative" ref="userMenuRef">
          <button
            @click="showUserMenu = !showUserMenu"
            class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div class="w-8 h-8 overflow-hidden bg-gradient-to-br from-primary to-accent rounded-full flex items-center justify-center">
              <img v-if="avatarUrl" :src="avatarUrl" alt="头像" class="w-full h-full object-cover" />
              <span v-else class="text-sm font-semibold text-white">{{ userInitial }}</span>
            </div>
            <svg class="w-4 h-4 text-gray-400 hidden sm:block" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>

          <!-- Dropdown -->
          <transition name="scale">
            <div v-if="showUserMenu" class="absolute right-0 top-12 w-56 bg-white rounded-xl shadow-elevated border border-gray-100 py-2 z-50">
              <div class="px-4 py-3 border-b border-gray-100">
                <p class="text-sm font-medium text-gray-900">{{ userName }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ userEmail }}</p>
              </div>
              <div class="py-1">
                <router-link to="/account/profile" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer" @click="showUserMenu = false">
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  个人资料
                </router-link>
                <router-link to="/account/settings" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer" @click="showUserMenu = false">
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
                  账户设置
                </router-link>
                <router-link to="/account/billing" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer" @click="showUserMenu = false">
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                  账单管理
                </router-link>
              </div>
              <div class="border-t border-gray-100 pt-1">
                <button
                  @click="handleLogout"
                  class="flex items-center gap-3 w-full px-4 py-2 text-sm text-danger hover:bg-red-50 cursor-pointer"
                >
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                  退出登录
                </button>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineEmits<{
  'toggle-sidebar': []
}>()

const router = useRouter()
const authStore = useAuthStore()

const showUserMenu = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)

const userName = computed(() => authStore.user?.name || '用户')
const userEmail = computed(() => authStore.user?.email || 'user@medicode.com')
const userInitial = computed(() => (authStore.user?.name?.[0] || 'U').toUpperCase())
const avatarUrl = computed(() => authStore.user?.avatar || '')
const tokenBalance = computed(() => authStore.user?.tokenBalance?.toLocaleString() || '0')

function handleLogout() {
  authStore.logout()
  showUserMenu.value = false
  router.push({ name: 'Login' })
}

function handleClickOutside(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  if (authStore.token && !authStore.user) {
    authStore.loadProfile()
  }
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
