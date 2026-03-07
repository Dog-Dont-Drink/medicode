<template>
  <div class="min-h-screen bg-[#eef3f1] text-slate-900">
    <div class="flex min-h-screen">
      <aside class="hidden w-[260px] flex-col border-r border-slate-200 bg-[#13231f] px-4 py-5 text-slate-100 lg:flex">
        <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
          <p class="text-xs uppercase tracking-[0.22em] text-emerald-200/80">MediCode</p>
          <h1 class="mt-2 text-xl font-heading font-semibold">Admin Console</h1>
          <p class="mt-2 text-sm leading-6 text-slate-300">集中管理用户数据、Token 消耗和平台运营情况。</p>
        </div>

        <nav class="mt-6 space-y-2">
          <router-link to="/admin" :class="navClass('/admin', true)">
            <span>后台概览</span>
          </router-link>
          <router-link to="/admin/users" :class="navClass('/admin/users')">
            <span>用户管理</span>
          </router-link>
          <div class="pt-3">
            <p class="px-4 text-[11px] uppercase tracking-[0.2em] text-slate-400">数据库表</p>
            <div class="mt-2 space-y-2">
              <router-link
                v-for="table in tables"
                :key="table.name"
                :to="`/admin/tables/${table.name}`"
                :class="navClass(`/admin/tables/${table.name}`)"
              >
                <span class="truncate">{{ table.label }}</span>
                <span class="ml-auto rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-slate-300">{{ table.row_count }}</span>
              </router-link>
            </div>
          </div>
        </nav>

        <div class="mt-auto rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
          <p class="text-sm font-medium text-white">{{ authStore.user?.name || '管理员' }}</p>
          <p class="mt-1 text-xs text-slate-300">{{ authStore.user?.email }}</p>
          <button
            type="button"
            class="mt-4 inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/10"
            @click="handleLogout"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <path d="M16 17L21 12L16 7" />
              <path d="M21 12H9" />
            </svg>
            退出后台
          </button>
        </div>
      </aside>

      <div class="flex min-h-screen flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/85 backdrop-blur-xl">
          <div class="flex items-center justify-between px-5 py-4 lg:px-8">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Administrator</p>
              <p class="mt-1 text-lg font-heading font-semibold text-slate-900">{{ pageTitle }}</p>
            </div>
            <div class="flex items-center gap-3">
            <div class="hidden rounded-2xl bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 sm:block">
                仅管理员可访问
              </div>
              <div class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-2xl bg-slate-900 text-sm font-semibold text-white">
                <img v-if="avatarUrl" :src="avatarUrl" alt="管理员头像" class="h-full w-full object-cover" />
                <span v-else>{{ userInitial }}</span>
              </div>
            </div>
          </div>
        </header>

        <main class="flex-1 px-5 py-6 lg:px-8">
          <router-view />
        </main>
      </div>
    </div>

    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import NotificationToast from '@/components/common/NotificationToast.vue'
import { getAdminTables, type AdminTableInfo } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const tables = ref<AdminTableInfo[]>([])

const pageTitle = computed(() => {
  if (route.path.startsWith('/admin/users')) return '用户管理'
  if (route.path.startsWith('/admin/tables')) return '数据库表管理'
  return '后台概览'
})

const userInitial = computed(() => (authStore.user?.name?.[0] || 'A').toUpperCase())
const avatarUrl = computed(() => authStore.user?.avatar || '')

function navClass(path: string, exact = false) {
  const active = exact ? route.path === path : route.path.startsWith(path)
  return [
    'flex items-center rounded-2xl px-4 py-3 text-sm font-medium transition',
    active ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-950/20' : 'text-slate-300 hover:bg-white/10 hover:text-white',
  ]
}

function handleLogout() {
  authStore.logout()
  router.push('/admin/login')
}

onMounted(() => {
  if (authStore.token && !authStore.user) {
    void authStore.loadProfile()
  }
  void loadAdminTables()
})

async function loadAdminTables() {
  try {
    const result = await getAdminTables()
    tables.value = result.tables
  } catch (error) {
    console.error('Failed to load admin tables', error)
  }
}
</script>
