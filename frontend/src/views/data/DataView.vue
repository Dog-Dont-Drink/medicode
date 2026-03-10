<template>
  <div>
    <!-- Header -->
    <div class="flex items-start justify-between gap-6 mb-6">
      <div class="flex-1 rounded-2xl border border-emerald-100 bg-emerald-50/70 px-5 py-4">
        <p class="text-sm font-semibold text-emerald-900">上传前请先完成数据脱敏</p>
        <p class="mt-1 text-sm leading-6 text-emerald-800">
          为保护患者隐私，建议您在上传前隐藏或提前删除姓名、身份证号、手机号、住址、住院号等可直接识别个人身份的关键信息，
          并尽量避免上传能够反向定位患者身份的敏感字段。平台会对您上传的数据严格保密，仅用于您授权的分析处理。
        </p>
      </div>
      <!-- Project Selection -->
      <div class="flex items-center gap-3">
        <label class="text-sm text-gray-700">当前项目</label>
        <select v-model="selectedProjectId" @change="handleProjectChange" class="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white min-w-[200px]" :disabled="isLoadingProjects">
          <option value="">请选择项目...</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <!-- Left: Upload area -->
      <div class="xl:col-span-4">
        <div class="bg-white rounded-2xl border border-gray-100 p-5">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            上传数据
          </h3>

          <!-- Drop zone -->
          <div
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleDrop"
            :class="['border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer', isDragging ? 'border-primary bg-primary-50' : 'border-gray-200 hover:border-primary/40 hover:bg-gray-50']"
            @click="triggerUpload"
          >
            <!-- File input hidden under the drop zone -->
            <input ref="fileInput" type="file" class="hidden" accept=".csv,.xlsx,.xls" multiple @change="handleFiles" />
            <div class="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <svg v-if="isUploading" class="w-6 h-6 text-primary animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
              <svg v-else class="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <p class="text-sm text-gray-600 font-medium">{{ isUploading ? '正在上传中...' : '拖拽文件到此处' }}</p>
            <p v-if="!isUploading" class="text-xs text-gray-400 mt-1">或点击选择文件</p>
            <p class="text-xs text-gray-300 mt-2">{{ uploadHintText }}</p>
          </div>

          <div class="mt-4 rounded-xl border border-amber-200 bg-amber-50/80 p-3">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="min-w-0 flex-1">
                <p class="text-xs font-semibold text-amber-900">{{ currentPlanLabel }}上传规则</p>
                <p class="mt-1 text-[11px] leading-5 text-amber-800">{{ uploadLimitDescription }}</p>
              </div>
              <router-link
                v-if="!isPaidPlan"
                to="/account/billing"
                class="inline-flex h-10 shrink-0 items-center justify-center self-start rounded-lg border border-amber-200 bg-white px-4 text-sm font-semibold leading-none text-amber-900 transition-colors hover:bg-amber-100 sm:self-center"
              >
                去升级
              </router-link>
            </div>
          </div>

          <div v-if="isUploading" class="mt-4 rounded-xl border border-primary/20 bg-primary-50/50 p-3">
            <div class="flex items-center justify-between gap-3">
              <p class="text-xs text-gray-600 truncate">正在上传：{{ uploadCurrentFile || '文件' }}</p>
              <p class="text-xs font-semibold text-primary">{{ Math.round(uploadProgress) }}%</p>
            </div>
            <div class="mt-2 h-1.5 w-full rounded-full bg-white overflow-hidden">
              <div
                class="h-full rounded-full bg-primary transition-all duration-200"
                :style="{ width: `${uploadProgress}%` }"
              ></div>
            </div>
            <p class="mt-2 text-[10px] text-gray-400">第 {{ uploadBatchIndex }}/{{ uploadBatchTotal }} 个文件</p>
          </div>

          <!-- Uploaded files list -->
          <div v-if="uploadedFiles.length" class="mt-4 space-y-2">
            <div v-for="file in uploadedFiles" :key="file.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
              <div class="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-900 truncate">{{ file.name }}</p>
                <p class="text-[10px] text-gray-400">{{ file.size }}</p>
              </div>
              <button
                @click="selectFile(file)"
                :disabled="isDatasetListLoading || isUploading"
                :class="['text-xs px-2.5 py-1 rounded-lg transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed', selectedFile?.id === file.id ? 'bg-primary text-white' : 'bg-white text-gray-500 hover:text-primary border border-gray-200']"
              >
                预览
              </button>
              <button
                class="w-8 h-8 rounded-lg border border-gray-200 bg-white text-gray-400 hover:text-red-500 hover:border-red-200 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                :disabled="deletingDatasetId === file.id || isUploading || isDatasetListLoading"
                @click.stop="handleDelete(file)"
                title="删除"
              >
                <svg v-if="deletingDatasetId === file.id" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
                <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Data Preview -->
      <div class="xl:col-span-8">
        <div class="space-y-6">
          <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <svg class="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                {{ selectedFile ? selectedFile.name : '数据预览' }}
              </h3>
              <span class="text-xs text-gray-400" v-if="selectedFile">
                {{ previewTotalRows ?? selectedFile.row_count ?? '未知' }} 行 × {{ previewTotalColumns ?? selectedFile.column_count ?? '未知' }} 列 (预览仅显示前10行)
              </span>
            </div>

            <div v-if="selectedFile && !previewLoading && !previewError" class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gray-50">
                    <th v-for="col in previewColumns" :key="col" class="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in previewRows" :key="i" class="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td v-for="col in previewColumns" :key="col" class="px-4 py-2.5 text-xs text-gray-600 whitespace-nowrap">{{ row[col] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="selectedFile && previewLoading" class="flex items-center justify-center py-16 text-gray-400 text-sm">
              正在加载数据预览...
            </div>

            <div v-else-if="selectedFile && previewError" class="flex items-center justify-center py-16 text-red-500 text-sm">
              {{ previewError }}
            </div>

            <!-- Empty state -->
            <div v-else class="flex flex-col items-center justify-center py-20">
              <div class="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mb-4">
                <svg class="w-8 h-8 text-gray-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
              </div>
              <p class="text-gray-400 text-sm">左侧点击数据集"预览"查看数据</p>
            </div>
          </div>

          <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-4">
              <div>
                <h3 class="text-sm font-semibold text-gray-900">基础统计面板</h3>
                <p class="mt-1 text-xs text-gray-400">自动识别变量类型、缺失情况与连续变量范围，便于快速做数据质量检查。</p>
              </div>
              <span
                v-if="datasetSummary"
                class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-medium text-emerald-700"
              >
                {{ datasetSummary.total_columns }} 个变量已完成基础画像
              </span>
            </div>

            <div v-if="selectedFile && summaryLoading" class="flex items-center justify-center py-20 text-gray-400 text-sm">
              正在生成基础统计摘要...
            </div>

            <div v-else-if="selectedFile && summaryError" class="flex items-center justify-center py-20 text-red-500 text-sm">
              {{ summaryError }}
            </div>

            <div v-else-if="selectedFile && datasetSummary" class="p-4 space-y-3">
              <div class="grid grid-cols-2 gap-2 xl:grid-cols-4">
                <div
                  v-for="item in summaryCards"
                  :key="item.label"
                  :class="['flex items-center gap-2 rounded-lg border px-2.5 py-2', item.cardClass]"
                >
                  <svg :class="['h-3.5 w-3.5 shrink-0', item.iconClass]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="item.icon"></svg>
                  <p class="text-base font-heading font-semibold text-gray-900 leading-none">{{ item.value }}</p>
                  <div class="min-w-0">
                    <p class="text-[11px] font-medium text-gray-500 truncate">{{ item.label }}</p>
                    <p class="text-[10px] text-gray-400 truncate">{{ item.description }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-lg border border-gray-100 bg-gradient-to-r from-slate-50 via-white to-emerald-50/40 px-3 py-2">
                <div class="flex flex-wrap items-center gap-1.5">
                  <span
                    v-for="item in qualitySignals"
                    :key="item.label"
                    class="inline-flex items-center gap-1.5 rounded-full border border-white/80 bg-white px-2.5 py-1 text-[11px] text-gray-600 shadow-sm"
                  >
                    <span class="font-medium text-gray-900">{{ item.label }}</span>
                    <span>{{ item.value }}</span>
                  </span>
                </div>
              </div>

              <div class="overflow-hidden rounded-lg border border-gray-100">
                <div class="overflow-x-auto">
                  <table class="w-full min-w-[800px]">
                    <thead class="bg-slate-50/80">
                      <tr>
                        <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">变量</th>
                        <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">类型</th>
                        <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">缺失情况</th>
                        <th class="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">关键统计</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="column in datasetSummary.columns"
                        :key="column.name"
                        class="border-t border-gray-50 align-middle transition-colors hover:bg-slate-50/60"
                      >
                        <td class="px-3 py-1.5">
                          <p class="text-[13px] font-semibold text-gray-900 leading-tight">{{ column.name }}</p>
                        </td>
                        <td class="px-3 py-1.5">
                          <div v-if="isEditableKind(column.kind)" class="space-y-0.5">
                            <div class="inline-flex overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                              <button
                                type="button"
                                class="inline-flex items-center justify-center gap-1 px-2 py-1 text-[10px] font-semibold transition-colors"
                                :class="column.kind === 'categorical' ? 'bg-sky-50 text-sky-700' : 'text-slate-500 hover:bg-slate-50'"
                                :disabled="updatingColumnKind === column.name"
                                @click="handleColumnKindChange(column, 'categorical')"
                              >
                                <span class="rounded bg-white/80 px-1 py-px text-[9px] tracking-wider">CAT</span>
                                <span>分类</span>
                              </button>
                              <button
                                type="button"
                                class="inline-flex items-center justify-center gap-1 border-l border-slate-200 px-2 py-1 text-[10px] font-semibold transition-colors"
                                :class="column.kind === 'numeric' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-500 hover:bg-slate-50'"
                                :disabled="updatingColumnKind === column.name"
                                @click="handleColumnKindChange(column, 'numeric')"
                              >
                                <span class="rounded bg-white/80 px-1 py-px text-[9px] tracking-wider">CON</span>
                                <span>连续</span>
                              </button>
                            </div>
                            <div class="flex items-center gap-1.5 text-[9px] text-gray-400">
                              <span>{{ column.kind_source === 'manual' ? '已手动指定' : '自动识别' }}</span>
                              <button
                                v-if="column.kind_source === 'manual'"
                                type="button"
                                class="text-primary hover:text-primary-600"
                                :disabled="updatingColumnKind === column.name"
                                @click="resetColumnKind(column)"
                              >
                                恢复自动
                              </button>
                            </div>
                          </div>
                          <span v-else :class="['inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-[10px] font-medium', kindBadgeClass(column.kind)]">
                            <span :class="['inline-flex h-4 min-w-4 items-center justify-center rounded px-0.5 text-[9px] font-semibold tracking-wider', kindMarkerClass(column.kind)]">
                              {{ kindShortLabel(column.kind) }}
                            </span>
                            <span>{{ kindLabel(column.kind) }}</span>
                          </span>
                        </td>
                        <td class="px-3 py-1.5">
                          <div class="min-w-[120px]">
                            <div class="flex items-center justify-between gap-2">
                              <span class="text-[13px] font-medium text-gray-900">{{ formatPercent(column.missing_rate) }}</span>
                              <span class="text-[10px] text-gray-400">{{ column.missing_count }} / {{ datasetSummary.total_rows }}</span>
                            </div>
                            <div class="mt-1 h-1 overflow-hidden rounded-full bg-gray-100">
                              <div
                                class="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600 transition-all"
                                :style="{ width: `${Math.min(100, column.missing_rate * 100)}%` }"
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td class="px-3 py-1.5">
                          <p class="text-[13px] text-gray-700 leading-tight">{{ formatColumnPrimaryStat(column) }}</p>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div v-else class="flex flex-col items-center justify-center py-20">
              <div class="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mb-4">
                <svg class="w-8 h-8 text-gray-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 19h16"/><path d="M7 16V8"/><path d="M12 16V5"/><path d="M17 16v-3"/>
                </svg>
              </div>
              <p class="text-sm text-gray-400">选择一个数据集后，这里会展示变量分布、范围和缺失情况。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  deleteDataset,
  getDatasetPreview,
  getDatasetSummary,
  getDatasets,
  getProjects,
  updateDatasetColumnKind,
  uploadDataset,
  type DatasetColumnSummary,
  type DatasetItem,
  type DatasetSummaryResponse,
} from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

interface UploadedFileItem {
  id: string
  name: string
  size: string
  row_count: number | null
  column_count: number | null
}

const SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
const SUPPORTED_EXTENSION_SET = new Set(SUPPORTED_EXTENSIONS)
const PAID_SUBSCRIPTIONS = new Set(['basic', 'pro', 'enterprise'])
const FREE_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
const PAID_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
const FREE_MAX_ROW_COUNT = 200

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const projects = ref<any[]>([])
const selectedProjectId = ref('')
const isLoadingProjects = ref(true)

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<UploadedFileItem | null>(null)

const uploadedFiles = ref<UploadedFileItem[]>([])
const isUploading = ref(false)
const deletingDatasetId = ref('')
const uploadProgress = ref(0)
const uploadCurrentFile = ref('')
const uploadBatchIndex = ref(0)
const uploadBatchTotal = ref(0)
const isDatasetListLoading = ref(false)

const previewColumns = ref<string[]>([])
const previewRows = ref<Record<string, string | number | boolean | null>[]>([])
const previewTotalRows = ref<number | null>(null)
const previewTotalColumns = ref<number | null>(null)
const previewLoading = ref(false)
const previewError = ref('')
const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const summaryLoading = ref(false)
const summaryError = ref('')
const updatingColumnKind = ref('')

const currentSubscription = computed(() => authStore.user?.subscription || 'free')
const isPaidPlan = computed(() => PAID_SUBSCRIPTIONS.has(currentSubscription.value))
const currentPlanLabel = computed(() => (isPaidPlan.value ? '付费版' : '免费版'))
const activeFileSizeLimit = computed(() => (isPaidPlan.value ? PAID_MAX_FILE_SIZE_BYTES : FREE_MAX_FILE_SIZE_BYTES))
const uploadHintText = computed(() => {
  if (isPaidPlan.value) {
    return '支持 CSV / XLSX / XLS，单文件最大 50MB'
  }
  return `支持 CSV / XLSX / XLS，免费版单文件最大 5MB，最多 ${FREE_MAX_ROW_COUNT} 行`
})
const uploadLimitDescription = computed(() => {
  if (isPaidPlan.value) {
    return '当前账号已解锁付费上传额度，支持 CSV / XLSX / XLS，单文件最大 50MB。'
  }
  return `当前免费版单文件最大 5MB，且数据行数不能超过 ${FREE_MAX_ROW_COUNT} 行。升级后可上传更大数据集。`
})
const summaryCards = computed(() => {
  if (!datasetSummary.value) return []
  const summary = datasetSummary.value
  return [
    {
      label: '总变量',
      value: summary.total_columns.toLocaleString(),
      description: `${summary.total_rows.toLocaleString()} 行可用于后续分析`,
      cardClass: 'border-slate-200 bg-slate-50/80',
      iconClass: 'text-slate-500',
      icon: '<path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/>',
    },
    {
      label: '连续变量',
      value: summary.numeric_columns.toLocaleString(),
      description: `日期 ${summary.datetime_columns} · 布尔 ${summary.boolean_columns}`,
      cardClass: 'border-emerald-200 bg-emerald-50/70',
      iconClass: 'text-emerald-500',
      icon: '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
    },
    {
      label: '分类变量',
      value: summary.categorical_columns.toLocaleString(),
      description: '适合先检查编码统一性和频数分布',
      cardClass: 'border-sky-200 bg-sky-50/70',
      iconClass: 'text-sky-500',
      icon: '<path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"/><path d="m15 9 6-6"/>',
    },
    {
      label: '缺失单元',
      value: formatPercent(summary.missing_rate),
      description: `${summary.missing_cells.toLocaleString()} 个单元格为空`,
      cardClass: 'border-amber-200 bg-amber-50/70',
      iconClass: 'text-amber-500',
      icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    },
  ]
})
const qualitySignals = computed(() => {
  if (!datasetSummary.value) return []
  const summary = datasetSummary.value
  return [
    { label: '完整观测', value: `${summary.complete_rows.toLocaleString()} 行` },
    { label: '重复行', value: `${summary.duplicate_rows.toLocaleString()} 行` },
    { label: '平均非空率', value: formatPercent(1 - summary.missing_rate) },
    { label: '字段密度', value: `${summary.total_rows.toLocaleString()} × ${summary.total_columns.toLocaleString()}` },
  ]
})

function resetPreviewState() {
  previewColumns.value = []
  previewRows.value = []
  previewTotalRows.value = null
  previewTotalColumns.value = null
  previewError.value = ''
}

function resetSummaryState() {
  datasetSummary.value = null
  summaryError.value = ''
}

async function loadDatasetPreview(datasetId: string) {
  previewLoading.value = true
  previewError.value = ''
  try {
    const res = await getDatasetPreview(datasetId, 10)
    previewColumns.value = res.columns
    previewRows.value = res.rows
    previewTotalRows.value = res.total_rows
    previewTotalColumns.value = res.total_columns
  } catch (err: any) {
    console.error('Failed to load dataset preview', err)
    resetPreviewState()
    previewError.value = err?.response?.data?.detail || '预览加载失败'
  } finally {
    previewLoading.value = false
  }
}

async function loadDatasetSummary(datasetId: string) {
  summaryLoading.value = true
  summaryError.value = ''
  try {
    datasetSummary.value = await getDatasetSummary(datasetId)
  } catch (err: any) {
    console.error('Failed to load dataset summary', err)
    datasetSummary.value = null
    summaryError.value = err?.response?.data?.detail || '统计摘要加载失败'
  } finally {
    summaryLoading.value = false
  }
}

async function loadDatasetDetails(datasetId: string) {
  await Promise.all([
    loadDatasetPreview(datasetId),
    loadDatasetSummary(datasetId),
  ])
}

async function selectFile(file: UploadedFileItem) {
  selectedFile.value = file
  await loadDatasetDetails(file.id)
}

const loadDatasets = async (preferredDatasetId?: string, resetView = false) => {
  if (!selectedProjectId.value) return
  if (resetView) {
    uploadedFiles.value = []
    selectedFile.value = null
    resetPreviewState()
    resetSummaryState()
  }

  isDatasetListLoading.value = true
  try {
    const data = await getDatasets(selectedProjectId.value)
    const nextFiles = data.map((d: DatasetItem) => ({
      id: d.id,
      name: d.name,
      size: formatFileSize(d.file_size),
      row_count: d.row_count,
      column_count: d.column_count,
    }))
    uploadedFiles.value = nextFiles

    if (!nextFiles.length) {
      selectedFile.value = null
      resetPreviewState()
      resetSummaryState()
      return
    }

    const previousSelectedId = selectedFile.value?.id
    const target =
      (preferredDatasetId && nextFiles.find((item) => item.id === preferredDatasetId)) ||
      (previousSelectedId && nextFiles.find((item) => item.id === previousSelectedId)) ||
      nextFiles[0]

    if (target) {
      selectedFile.value = target
      if (
        target.id !== previousSelectedId ||
        !previewColumns.value.length ||
        !datasetSummary.value
      ) {
        await loadDatasetDetails(target.id)
      }
    }
  } catch (err) {
    console.error('Failed to load datasets', err)
  } finally {
    isDatasetListLoading.value = false
  }
}

async function handleProjectChange() {
  await loadDatasets(undefined, true)
}

onMounted(async () => {
  if (authStore.token && !authStore.user) {
    try {
      await authStore.loadProfile()
    } catch (err) {
      console.error('Failed to load profile', err)
    }
  }

  try {
    projects.value = await getProjects()
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id
      await loadDatasets(undefined, true)
    }
  } catch (err) {
    console.error('Failed to load projects', err)
  } finally {
    isLoadingProjects.value = false
  }
})

function formatFileSize(bytes: number | null | undefined) {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatPercent(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '-'
  return `${(value * 100).toFixed(1)}%`
}

function formatNumber(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '-'
  if (Number.isInteger(value)) return value.toLocaleString()
  return value.toFixed(2)
}

function kindLabel(kind: DatasetColumnSummary['kind']) {
  const labels: Record<DatasetColumnSummary['kind'], string> = {
    numeric: 'Continuous',
    categorical: 'Categorical',
    datetime: 'Datetime',
    boolean: 'Boolean',
  }
  return labels[kind]
}

function isEditableKind(kind: DatasetColumnSummary['kind']) {
  return kind === 'numeric' || kind === 'categorical'
}

function kindShortLabel(kind: DatasetColumnSummary['kind']) {
  const labels: Record<DatasetColumnSummary['kind'], string> = {
    numeric: 'CON',
    categorical: 'CAT',
    datetime: 'DAT',
    boolean: 'BOOL',
  }
  return labels[kind]
}

function kindBadgeClass(kind: DatasetColumnSummary['kind']) {
  const classes: Record<DatasetColumnSummary['kind'], string> = {
    numeric: 'border-emerald-100 bg-emerald-50/60 text-emerald-800',
    categorical: 'border-sky-100 bg-sky-50/60 text-sky-800',
    datetime: 'border-violet-100 bg-violet-50/60 text-violet-800',
    boolean: 'border-amber-100 bg-amber-50/60 text-amber-800',
  }
  return classes[kind]
}

function kindMarkerClass(kind: DatasetColumnSummary['kind']) {
  const classes: Record<DatasetColumnSummary['kind'], string> = {
    numeric: 'bg-emerald-100 text-emerald-700',
    categorical: 'bg-sky-100 text-sky-700',
    datetime: 'bg-violet-100 text-violet-700',
    boolean: 'bg-amber-100 text-amber-700',
  }
  return classes[kind]
}

function formatColumnPrimaryStat(column: DatasetColumnSummary) {
  if (column.kind === 'numeric') {
    return `${formatNumber(column.numeric_mean)} ± ${formatNumber(column.numeric_std)}`
  }
  if (column.kind === 'datetime') {
    return `${column.datetime_min || '-'} 至 ${column.datetime_max || '-'}`
  }
  if (column.top_values?.length) {
    return column.top_values
      .slice(0, 4)
      .map((item) => `${item.value} ${formatPercent(item.ratio)}`)
      .join(' · ')
  }
  return `去重值 ${column.unique_count.toLocaleString()} 个`
}

function formatColumnSecondaryStat(column: DatasetColumnSummary) {
  if (column.kind === 'numeric') {
    return `中位数 ${formatNumber(column.numeric_median)} (Q1 ${formatNumber(column.numeric_q1)}, Q3 ${formatNumber(column.numeric_q3)})`
  }
  if (column.kind === 'datetime') {
    return `非空 ${column.non_null_count.toLocaleString()} · 去重 ${column.unique_count.toLocaleString()}`
  }
  if (column.top_values?.length) {
    return `最多展示前 ${Math.min(column.top_values.length, 4)} 类 · 去重 ${column.unique_count.toLocaleString()}`
  }
  return `非空 ${column.non_null_count.toLocaleString()} · 去重 ${column.unique_count.toLocaleString()}`
}

function formatColumnFootnote(column: DatasetColumnSummary) {
  return `非空 ${column.non_null_count.toLocaleString()} · 去重 ${column.unique_count.toLocaleString()}`
}

async function handleColumnKindChange(column: DatasetColumnSummary, kind: 'numeric' | 'categorical') {
  if (!selectedFile.value || updatingColumnKind.value || column.kind === kind) return
  updatingColumnKind.value = column.name
  try {
    await updateDatasetColumnKind(selectedFile.value.id, column.name, { kind })
    await loadDatasetSummary(selectedFile.value.id)
    notificationStore.success(
      '变量类型已更新',
      `${column.name} 已改为${kind === 'numeric' ? '连续变量' : '分类变量'}，后续统计会按新类型处理。`,
    )
  } catch (error: any) {
    console.error('Failed to update column kind', error)
    notificationStore.error('类型更新失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    updatingColumnKind.value = ''
  }
}

async function resetColumnKind(column: DatasetColumnSummary) {
  if (!selectedFile.value || updatingColumnKind.value) return
  updatingColumnKind.value = column.name
  try {
    await updateDatasetColumnKind(selectedFile.value.id, column.name, { kind: 'auto' })
    await loadDatasetSummary(selectedFile.value.id)
    notificationStore.success('已恢复自动识别', `${column.name} 将重新按照系统推断的类型参与后续统计。`)
  } catch (error: any) {
    console.error('Failed to reset column kind', error)
    notificationStore.error('恢复失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    updatingColumnKind.value = ''
  }
}

function triggerUpload() {
  if (isUploading.value) return
  if (!selectedProjectId.value) {
    notificationStore.warning('请先选择项目', '上传前请先在顶部切换到目标项目。')
    return
  }
  fileInput.value?.click()
}

async function handleFiles(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    await processUploads(target.files)
  }
  isDragging.value = false
  if (fileInput.value) fileInput.value.value = ''
}

async function handleDrop(e: DragEvent) {
  if (isUploading.value) return
  isDragging.value = false
  if (!selectedProjectId.value) {
    notificationStore.warning('请先选择项目', '上传前请先在顶部切换到目标项目。')
    return
  }
  if (e.dataTransfer?.files) {
    await processUploads(e.dataTransfer.files)
  }
}

function summarizeFileNames(files: File[]) {
  if (files.length === 0) return ''
  const names = files.slice(0, 2).map((file) => file.name)
  return files.length > 2 ? `${names.join('、')} 等 ${files.length} 个文件` : names.join('、')
}

function getFileExtension(fileName: string) {
  const dotIndex = fileName.lastIndexOf('.')
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : ''
}

function validateUploads(selectedFiles: File[]) {
  const unsupportedFiles = selectedFiles.filter((file) => !SUPPORTED_EXTENSION_SET.has(getFileExtension(file.name)))
  if (unsupportedFiles.length) {
    notificationStore.error(
      '不支持的文件格式',
      `${summarizeFileNames(unsupportedFiles)} 格式不受支持，仅支持 CSV、XLSX、XLS。`,
    )
  }

  const oversizedFiles = selectedFiles.filter((file) => file.size > activeFileSizeLimit.value)
  if (oversizedFiles.length) {
    notificationStore.warning(
      '文件超出上传限制',
      isPaidPlan.value
        ? `${summarizeFileNames(oversizedFiles)} 超过 50MB，请拆分后重试。`
        : `${summarizeFileNames(oversizedFiles)} 超过免费版 5MB 限制，且免费版最多支持 ${FREE_MAX_ROW_COUNT} 行数据。`,
    )
  }

  return selectedFiles.filter((file) => {
    const isSupported = SUPPORTED_EXTENSION_SET.has(getFileExtension(file.name))
    const isWithinSize = file.size <= activeFileSizeLimit.value
    return isSupported && isWithinSize
  })
}

async function processUploads(files: FileList) {
  const validFiles = validateUploads(Array.from(files))
  if (!validFiles.length) {
    return
  }

  isUploading.value = true
  uploadBatchTotal.value = validFiles.length
  uploadBatchIndex.value = 0
  uploadProgress.value = 0
  uploadCurrentFile.value = ''
  try {
    let lastUploadedId = ''
    const totalBytes = validFiles.reduce((sum, file) => sum + Math.max(file.size, 0), 0)
    let uploadedBytesBeforeCurrent = 0

    for (let i = 0; i < validFiles.length; i++) {
      const currentFile = validFiles[i]
      uploadBatchIndex.value = i + 1
      uploadCurrentFile.value = currentFile.name

      const formData = new FormData()
      formData.append('file', currentFile)
      formData.append('project_id', selectedProjectId.value)
      const uploaded = await uploadDataset(formData, (loaded, total) => {
        // Scale per-request progress back to pure file bytes, then aggregate by total upload bytes.
        const currentFileBytes = Math.max(currentFile.size, 0)
        let loadedCurrentFileBytes = Math.min(Math.max(loaded, 0), currentFileBytes)
        if (total && total > 0 && currentFileBytes > 0) {
          loadedCurrentFileBytes = Math.min(currentFileBytes, (loaded / total) * currentFileBytes)
        }

        const overallLoadedBytes = uploadedBytesBeforeCurrent + loadedCurrentFileBytes
        if (totalBytes > 0) {
          uploadProgress.value = Math.min(100, (overallLoadedBytes / totalBytes) * 100)
        }
      })
      lastUploadedId = uploaded.id
      uploadedBytesBeforeCurrent += Math.max(currentFile.size, 0)
      if (totalBytes > 0) {
        uploadProgress.value = Math.min(100, (uploadedBytesBeforeCurrent / totalBytes) * 100)
      }
    }
    await loadDatasets(lastUploadedId || undefined)
    notificationStore.success(
      '上传成功',
      validFiles.length === 1 ? `${validFiles[0].name} 已上传完成。` : `已成功上传 ${validFiles.length} 个文件。`,
    )
  } catch (error: any) {
    console.error('Upload failed', error)
    await loadDatasets(selectedFile.value?.id || undefined)
    notificationStore.error('上传失败', error.response?.data?.detail || error.message || '请稍后重试。')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
    uploadCurrentFile.value = ''
    uploadBatchIndex.value = 0
    uploadBatchTotal.value = 0
  }
}

async function handleDelete(file: UploadedFileItem) {
  if (!selectedProjectId.value) return

  const previousFiles = [...uploadedFiles.value]
  const previousSelectedId = selectedFile.value?.id
  const removedIndex = previousFiles.findIndex((item) => item.id === file.id)
  deletingDatasetId.value = file.id

  const nextFiles = previousFiles.filter((item) => item.id !== file.id)
  uploadedFiles.value = nextFiles

  if (previousSelectedId === file.id) {
    if (!nextFiles.length) {
      selectedFile.value = null
      resetPreviewState()
    } else {
      const nextIndex = removedIndex >= nextFiles.length ? nextFiles.length - 1 : removedIndex
      const fallback = nextFiles[Math.max(nextIndex, 0)]
      await selectFile(fallback)
    }
  }

  try {
    await deleteDataset(file.id)
    const preferredId = selectedFile.value?.id
    await loadDatasets(preferredId)
  } catch (err: any) {
    console.error('Delete dataset failed', err)
    uploadedFiles.value = previousFiles
    if (previousSelectedId) {
      const restored = previousFiles.find((item) => item.id === previousSelectedId)
      if (restored) {
        selectedFile.value = restored
        await loadDatasetDetails(restored.id)
      }
    }
    notificationStore.error('删除失败', err?.response?.data?.detail || err?.message || '未知错误')
  } finally {
    deletingDatasetId.value = ''
  }
}
</script>
