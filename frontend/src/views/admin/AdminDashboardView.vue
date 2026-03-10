<template>
  <div class="space-y-6">
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <div
        v-for="metric in dashboard?.overview || []"
        :key="metric.label"
        class="rounded-3xl border border-slate-200 bg-white px-5 py-5 shadow-sm shadow-slate-200/60"
      >
        <p class="text-xs uppercase tracking-[0.2em] text-slate-400">{{ metric.label }}</p>
        <p class="mt-3 text-3xl font-heading font-semibold text-slate-900">{{ metric.value }}</p>
        <p v-if="metric.hint" class="mt-2 text-xs text-slate-500">{{ metric.hint }}</p>
      </div>
    </div>

    <div v-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-heading font-semibold text-slate-900">近 7 日运营趋势</h2>
            <p class="mt-1 text-sm text-slate-500">同时观察每日新增用户和每日资源消耗。</p>
          </div>
        </div>

        <div v-if="isLoading" class="mt-6 space-y-3">
          <div v-for="index in 6" :key="index" class="h-12 animate-pulse rounded-2xl bg-slate-100"></div>
        </div>

        <div v-else class="mt-6 space-y-4">
          <div
            v-for="item in dashboard?.daily_metrics || []"
            :key="item.date"
            class="rounded-2xl bg-slate-50 px-4 py-4"
          >
            <div class="flex items-center justify-between gap-4">
              <p class="text-sm font-medium text-slate-700">{{ formatDay(item.date) }}</p>
              <div class="flex items-center gap-4 text-xs text-slate-500">
                <span>新增 {{ item.users }}</span>
                <span>资源 {{ item.token_consumed }}</span>
              </div>
            </div>
            <div class="mt-3 grid gap-2">
              <div>
                <div class="mb-1 flex items-center justify-between text-[11px] text-slate-400">
                  <span>新增用户</span>
                  <span>{{ item.users }}</span>
                </div>
                <div class="h-2 rounded-full bg-white">
                  <div class="h-2 rounded-full bg-emerald-500" :style="{ width: `${barWidth(item.users, maxUsers)}%` }"></div>
                </div>
              </div>
              <div>
                <div class="mb-1 flex items-center justify-between text-[11px] text-slate-400">
                  <span>资源消耗</span>
                  <span>{{ item.token_consumed }}</span>
                </div>
                <div class="h-2 rounded-full bg-white">
                  <div class="h-2 rounded-full bg-slate-800" :style="{ width: `${barWidth(item.token_consumed, maxTokens)}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
        <h2 class="text-lg font-heading font-semibold text-slate-900">今日重点</h2>
        <div class="mt-6 space-y-4">
          <div class="rounded-2xl bg-emerald-50 px-4 py-4">
            <p class="text-xs uppercase tracking-[0.2em] text-emerald-700">New Users</p>
            <p class="mt-2 text-3xl font-semibold text-slate-900">{{ dashboard?.recent_signups || 0 }}</p>
          </div>
          <div class="rounded-2xl bg-slate-50 px-4 py-4">
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Billed Resources</p>
            <p class="mt-2 text-3xl font-semibold text-slate-900">{{ dashboard?.today_token_consumed || 0 }}</p>
          </div>
          <div class="rounded-2xl bg-amber-50 px-4 py-4">
            <p class="text-xs uppercase tracking-[0.2em] text-amber-700">Model Usage</p>
            <p class="mt-2 text-3xl font-semibold text-slate-900">{{ dashboard?.today_actual_token_consumed || 0 }}</p>
          </div>
          <div class="rounded-2xl bg-sky-50 px-4 py-4">
            <p class="text-xs uppercase tracking-[0.2em] text-sky-700">Paid Revenue</p>
            <p class="mt-2 text-3xl font-semibold text-slate-900">¥ {{ dashboard?.paid_orders_total || '0.00' }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { getAdminDashboard, type AdminDashboardResponse } from '@/services/api'

const dashboard = ref<AdminDashboardResponse | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

const maxUsers = computed(() => Math.max(...(dashboard.value?.daily_metrics.map((item) => item.users) || [1]), 1))
const maxTokens = computed(() => Math.max(...(dashboard.value?.daily_metrics.map((item) => item.token_consumed) || [1]), 1))

function formatDay(value: string) {
  return new Date(value).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function barWidth(value: number, maxValue: number) {
  if (!maxValue) return 0
  return Math.max((value / maxValue) * 100, value > 0 ? 8 : 0)
}

onMounted(async () => {
  try {
    dashboard.value = await getAdminDashboard()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || error.message || '后台概览加载失败'
  } finally {
    isLoading.value = false
  }
})
</script>
