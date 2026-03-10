<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="inline-flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2">
        <div class="relative inline-flex rounded-[10px] bg-white p-1 shadow-sm">
          <span
            class="absolute top-1 h-8 w-[4.75rem] rounded-[8px] bg-emerald-500 transition-transform duration-200"
            :class="language === 'zh' ? 'translate-x-0' : 'translate-x-[4.75rem]'"
          />
          <button
            type="button"
            class="relative z-10 inline-flex h-8 w-[4.75rem] items-center justify-center text-xs font-semibold transition-colors"
            :class="language === 'zh' ? 'text-white' : 'text-slate-500'"
            @click="$emit('language-change', 'zh')"
          >
            中文
          </button>
          <button
            type="button"
            class="relative z-10 inline-flex h-8 w-[4.75rem] items-center justify-center text-xs font-semibold transition-colors"
            :class="language === 'en' ? 'text-white' : 'text-slate-500'"
            @click="$emit('language-change', 'en')"
          >
            English
          </button>
        </div>

        <button
          type="button"
          :disabled="interpretDisabled"
          class="inline-flex h-10 items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 text-sm font-semibold text-amber-700 transition-colors hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
          @click="$emit('interpret')"
        >
          {{ isInterpreting ? interpretLoadingLabel : interpretLabel }}
          <span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 drop-shadow-[0_0_10px_rgba(16,185,129,0.45)]">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>
            {{ aiCost }}
          </span>
        </button>
      </div>

      <button
        v-if="showDownload"
        type="button"
        :disabled="downloadDisabled"
        class="inline-flex h-10 items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 text-sm font-semibold text-emerald-700 transition-colors hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
        @click="$emit('download')"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3V15" />
          <path d="M7 10L12 15L17 10" />
          <path d="M5 21H19" />
        </svg>
        {{ isDownloading ? downloadLoadingLabel : downloadLabel }}
      </button>
    </div>

    <div class="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <p class="text-sm font-semibold text-slate-900">{{ title }}</p>
            <span
              v-if="showPremiumBadge"
              class="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700"
            >
              {{ premiumBadgeLabel }}
            </span>
          </div>
          <p class="mt-1 text-xs leading-5 text-slate-500">{{ description }}</p>
        </div>
        <p class="text-[11px] text-slate-400">
          {{ language === 'zh' ? outputLabelZh : outputLabelEn }}
        </p>
      </div>

      <div
        v-if="isInterpreting"
        class="mt-4 rounded-xl border border-white bg-white/90 px-4 py-4 shadow-sm"
      >
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M21 12a9 9 0 1 1-3.47-7.09" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-900">{{ loadingTitle }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ loadingDescription }}</p>
          </div>
        </div>
        <div class="mt-4 space-y-2.5">
          <div class="h-3 w-full animate-pulse rounded-full bg-slate-100"></div>
          <div class="h-3 w-11/12 animate-pulse rounded-full bg-slate-100"></div>
          <div class="h-3 w-10/12 animate-pulse rounded-full bg-slate-100"></div>
          <div class="h-3 w-8/12 animate-pulse rounded-full bg-slate-100"></div>
        </div>
      </div>

      <div v-else-if="content" class="mt-4 rounded-xl border border-white bg-white/90 px-4 py-3 shadow-sm">
        <div class="relative">
          <p class="whitespace-pre-line pr-12 text-sm leading-7 text-slate-700">{{ content }}</p>
          <button
            type="button"
            class="absolute bottom-0 right-0 inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:border-primary/30 hover:text-primary"
            :aria-label="copied ? '已复制结果解读' : '复制结果解读'"
            :title="copied ? '已复制' : '复制到剪切板'"
            @click="$emit('copy')"
          >
            <svg v-if="copied" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 6L9 17L4 12" />
            </svg>
            <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="11" height="11" rx="2" />
              <path d="M5 15V6a2 2 0 0 1 2-2h9" />
            </svg>
          </button>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <span v-if="chargedResources > 0" class="inline-flex rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] text-emerald-700">
            本次消耗 {{ chargedResources }} 资源
          </span>
          <span v-if="remainingResources !== null" class="inline-flex rounded-full bg-amber-50 px-2.5 py-1 text-[11px] text-amber-700">
            剩余 {{ remainingResources }} 资源
          </span>
          <span v-if="savedAt" class="inline-flex rounded-full bg-sky-50 px-2.5 py-1 text-[11px] text-sky-700">
            已保存 {{ formatSavedAt(savedAt) }}
          </span>
        </div>
      </div>

      <div v-else class="mt-4 rounded-xl border border-dashed border-slate-200 bg-white/70 px-4 py-5 text-sm text-slate-400">
        {{ emptyText }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  language: 'zh' | 'en'
  isInterpreting: boolean
  isDownloading: boolean
  content: string
  copied: boolean
  chargedResources?: number
  remainingResources?: number | null
  savedAt?: string
  description: string
  loadingDescription: string
  emptyText: string
  title?: string
  premiumBadgeLabel?: string
  showPremiumBadge?: boolean
  interpretLabel?: string
  interpretLoadingLabel?: string
  downloadLabel?: string
  downloadLoadingLabel?: string
  outputLabelZh?: string
  outputLabelEn?: string
  aiCost?: number
  showDownload?: boolean
  interpretDisabled?: boolean
  downloadDisabled?: boolean
  loadingTitle?: string
}

withDefaults(defineProps<Props>(), {
  chargedResources: 0,
  remainingResources: null,
  savedAt: '',
  title: 'AI结果解读',
  premiumBadgeLabel: '高级功能',
  showPremiumBadge: true,
  interpretLabel: 'AI结果解读',
  interpretLoadingLabel: '解读中...',
  downloadLabel: '下载 Excel',
  downloadLoadingLabel: '下载中...',
  outputLabelZh: '输出语言：中文',
  outputLabelEn: 'Output: English',
  aiCost: 1,
  showDownload: true,
  interpretDisabled: false,
  downloadDisabled: false,
  loadingTitle: 'AI 正在整理结果描述',
})

defineEmits<{
  (e: 'language-change', language: 'zh' | 'en'): void
  (e: 'interpret'): void
  (e: 'download'): void
  (e: 'copy'): void
}>()

function formatSavedAt(value: string) {
  return new Date(value).toLocaleString()
}
</script>
