<template>
  <div class="space-y-6 animate-fade-in">
    <div>
      <div>
        <h1 class="text-2xl font-heading font-bold text-gray-900">报告中心</h1>
        <p class="mt-1 text-sm text-gray-500">
          这里集中展示已保存的 AI 结果解读。当前保存于项目结果库，刷新页面不会丢失。
        </p>
      </div>
    </div>

    <div v-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="grid gap-4">
      <div v-for="index in 2" :key="index" class="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm shadow-gray-100/70">
        <div class="h-5 w-40 animate-pulse rounded bg-gray-100"></div>
        <div class="mt-3 h-4 w-64 animate-pulse rounded bg-gray-100"></div>
        <div class="mt-3 h-16 animate-pulse rounded-2xl bg-gray-50"></div>
      </div>
    </div>

    <div v-else-if="reports.length === 0" class="rounded-3xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center shadow-sm shadow-gray-100/80">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-50 text-slate-400">
        <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="8" y1="13" x2="16" y2="13"/>
          <line x1="8" y1="17" x2="14" y2="17"/>
        </svg>
      </div>
      <h2 class="mt-5 text-lg font-heading font-semibold text-gray-900">还没有已保存的报告</h2>
      <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-gray-500">
        在描述统计页面生成 AI 结果解读后，系统会自动将结果保存到这里，便于后续回看与整理。
      </p>
      <router-link to="/analysis/descriptive" class="mt-6 inline-flex items-center gap-2 rounded-2xl bg-primary px-5 py-3 text-sm font-medium text-white transition hover:bg-primary-600">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
        前往生成报告
      </router-link>
    </div>

    <div v-else class="space-y-4">
      <article
        v-for="report in reports"
        :key="report.analysis_id"
        class="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm shadow-gray-100/80"
      >
        <div class="border-b border-gray-100 bg-gradient-to-r from-slate-50 via-white to-emerald-50/50 px-5 py-4">
          <div class="flex flex-col gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold tracking-[0.16em] text-emerald-700">
                  基线特征
                </span>
                <span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
                  {{ report.language === 'en' ? 'English' : '中文' }}
                </span>
              </div>
              <h2 class="mt-2 text-lg font-heading font-semibold text-gray-900">{{ reportDisplayTitle(report) }}</h2>
              <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-gray-500">
                <span>{{ report.project_name }}</span>
                <span v-if="report.dataset_name">{{ report.dataset_name }}</span>
                <span v-if="report.group_variable">分组变量 {{ report.group_variable }}</span>
                <span>{{ formatDate(report.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="px-5 py-4">
          <div class="rounded-2xl bg-slate-50 px-4 py-3.5">
            <p class="whitespace-pre-line text-[14px] leading-6 text-slate-700">
              {{ expandedReports[report.analysis_id] ? report.content || '该报告暂未写入正文。' : previewText(report.content) }}
            </p>
          </div>

          <div class="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <div class="flex items-center gap-3">
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-2xl border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-primary/40 hover:text-primary"
                @click="toggleExpanded(report.analysis_id)"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline :points="expandedReports[report.analysis_id] ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/>
                </svg>
                {{ expandedReports[report.analysis_id] ? '收起全文' : '查看全文' }}
              </button>
     
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getReports, type ReportListItem } from '@/services/api'

const reports = ref<ReportListItem[]>([])
const expandedReports = ref<Record<string, boolean>>({})
const isLoading = ref(true)
const errorMessage = ref('')

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function previewText(content?: string | null) {
  if (!content) return '该报告暂未写入正文。'
  if (content.length <= 220) return content
  return `${content.slice(0, 220).trim()}...`
}

function reportDisplayTitle(report: ReportListItem) {
  if (report.group_variable) {
    return `基线特征结果解读 · ${report.group_variable}`
  }
  return '基线特征结果解读'
}

function toggleExpanded(analysisId: string) {
  expandedReports.value[analysisId] = !expandedReports.value[analysisId]
}

onMounted(async () => {
  try {
    reports.value = await getReports()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || error.message || '报告加载失败'
  } finally {
    isLoading.value = false
  }
})
</script>
