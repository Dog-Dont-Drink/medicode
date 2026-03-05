<template>
  <div class="flex min-h-screen bg-[#f5f7fa]">
    <Sidebar :open="sidebarOpen" @close="sidebarOpen = false" />

    <!-- Main content area -->
    <div class="flex-1 lg:ml-[240px] flex flex-col min-h-screen">
      <!-- Top bar -->
      <header class="sticky top-0 z-30 h-14 bg-white/80 backdrop-blur-xl border-b border-gray-100/60 flex items-center justify-between px-5">
        <!-- Mobile menu toggle -->
        <button class="lg:hidden p-2 rounded-lg hover:bg-gray-100 text-gray-500 cursor-pointer" @click="sidebarOpen = true">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>

        <!-- Search -->
        <div class="hidden sm:flex items-center flex-1 max-w-md">
          <div class="relative w-full">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" placeholder="搜索项目、数据、分析..." class="w-full pl-10 pr-4 py-2 bg-gray-50 border-0 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all" />
          </div>
        </div>

        <!-- Right actions -->
        <div class="flex items-center gap-2">
          <button class="p-2 rounded-xl hover:bg-gray-100 text-gray-400 hover:text-gray-600 relative transition-colors cursor-pointer">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
            <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full"></span>
          </button>
          <div class="w-8 h-8 overflow-hidden bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center text-white text-sm font-semibold cursor-pointer">
            <img v-if="avatarUrl" :src="avatarUrl" alt="头像" class="w-full h-full object-cover" />
            <span v-else>{{ userInitial }}</span>
          </div>
          <button @click="handleLogout" class="flex items-center gap-1.5 ml-1 px-3 py-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 text-xs font-medium transition-all cursor-pointer" title="退出登录">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            <span class="hidden sm:inline">退出</span>
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-5 lg:p-6">
        <router-view />
      </main>
    </div>

    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/common/Sidebar.vue'
import NotificationToast from '@/components/common/NotificationToast.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const sidebarOpen = ref(false)
const authStore = useAuthStore()
const userInitial = computed(() => (authStore.user?.name?.[0] || 'U').toUpperCase())
const avatarUrl = computed(() => authStore.user?.avatar || '')

onMounted(() => {
  if (authStore.token && !authStore.user) {
    authStore.loadProfile()
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>
