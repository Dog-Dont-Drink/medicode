<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_#dff5e8,_transparent_32%),linear-gradient(180deg,#f7fbf9_0%,#eef4f1_100%)] px-4 py-10">
    <div class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section class="hidden rounded-[32px] border border-emerald-100 bg-[#122420] p-10 text-white shadow-[0_30px_100px_rgba(16,34,28,0.18)] lg:block">
        <p class="text-xs uppercase tracking-[0.28em] text-emerald-200/80">MediCode Admin</p>
        <h1 class="mt-5 max-w-lg text-4xl font-heading font-semibold leading-tight">
          平台运营、用户状态和 Token 消耗都在这一张后台面板里。
        </h1>
        <p class="mt-5 max-w-xl text-base leading-8 text-slate-300">
          管理员后台支持集中查看每日新增用户、每日 Token 消耗、累计收入，以及直接维护用户余额、套餐、角色和启停状态。
        </p>
        <div class="mt-10 grid gap-4 sm:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-5">
            <p class="text-sm text-slate-300">用户管理</p>
            <p class="mt-2 text-2xl font-semibold">统一编辑账户数据</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-5">
            <p class="text-sm text-slate-300">运营概览</p>
            <p class="mt-2 text-2xl font-semibold">每日趋势实时可见</p>
          </div>
        </div>
      </section>

      <section class="flex items-center">
        <div class="w-full rounded-[32px] border border-white/70 bg-white/92 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
          <div>
            <p class="text-xs uppercase tracking-[0.24em] text-emerald-600">Admin Login</p>
            <h2 class="mt-3 text-3xl font-heading font-semibold text-slate-900">管理员登录</h2>
          </div>

          <form class="mt-8 space-y-5" @submit.prevent="handleLogin">
            <div>
              <label class="mb-2 block text-sm font-medium text-slate-600">管理员邮箱</label>
              <input v-model="email" type="email" class="input-field" placeholder="admin@medicode.com" />
            </div>
            <div>
              <label class="mb-2 block text-sm font-medium text-slate-600">密码</label>
              <input v-model="password" :type="showPassword ? 'text' : 'password'" class="input-field" placeholder="请输入密码" />
            </div>
            <label class="inline-flex items-center gap-2 text-sm text-slate-500">
              <input v-model="showPassword" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary" />
              显示密码
            </label>

            <button type="submit" :disabled="loading" class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0f9f6e] px-4 py-3.5 text-base font-semibold text-white transition hover:bg-[#0b8a60] disabled:cursor-not-allowed disabled:opacity-60">
              <svg v-if="loading" class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <span>{{ loading ? '登录中...' : '进入后台' }}</span>
            </button>

            <div v-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {{ errorMessage }}
            </div>
          </form>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''
  if (!email.value.trim() || !password.value) {
    errorMessage.value = '请输入管理员邮箱和密码'
    return
  }

  loading.value = true
  const result = await authStore.adminLogin(email.value.trim(), password.value)
  loading.value = false

  if (result.success) {
    router.push('/admin')
    return
  }

  errorMessage.value = result.error || '管理员登录失败'
}
</script>
