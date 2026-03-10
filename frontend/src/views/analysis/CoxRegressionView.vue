<template>
  <div class="space-y-6">
    <div class="panel-card bg-gradient-to-r from-slate-50 via-white to-cyan-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">Cox 生存分析</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        选择生存时间、事件结局和候选协变量，后端完成 Cox 模型拟合，并返回 HR、95% CI 与简洁森林图。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">模型配置</h2>
            <p class="mt-1 text-xs text-gray-400">生存时间需为正数，事件变量需为二分类变量，自变量支持数值型与分类变量。</p>
          </div>

          <div class="mt-5 space-y-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">数据集</label>
              <select v-model="selectedDatasetId" :disabled="loadingDatasets" @change="handleDatasetChange" class="tool-input">
                <option value="">请选择数据集</option>
                <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} · {{ dataset.projectName }}
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">生存时间变量</label>
              <select v-model="timeVariable" :disabled="!timeOptions.length" @change="handleCoreVariableChange" class="tool-input">
                <option value="">请选择生存时间变量</option>
                <option v-for="column in timeOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · 数值型
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">事件变量</label>
              <select v-model="eventVariable" :disabled="!eventOptions.length" @change="handleCoreVariableChange" class="tool-input">
                <option value="">请选择事件变量</option>
                <option v-for="column in eventOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ eventOptionLabel(column) }}
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">支持 0/1 数值型或双水平分类变量。</p>
            </div>

            <div class="panel-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">协变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">分类变量会自动在 R 中展开为虚拟变量并进入 Cox 模型。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllPredictors">
                  {{ selectedPredictors.length === predictorOptions.length && predictorOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="panel-card-tight mt-3 border-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ predictorSelectionText }}</p>
                <div class="mt-2 grid max-h-52 grid-cols-2 gap-2 overflow-y-auto pr-1">
                  <label
                    v-for="column in predictorOptions"
                    :key="column.name"
                    class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600"
                  >
                    <input
                      type="checkbox"
                      class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                      :checked="selectedPredictors.includes(column.name)"
                      @change="togglePredictor(column.name)"
                    />
                    <span class="truncate">{{ column.name }}</span>
                  </label>
                </div>
              </div>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">显著性水平</label>
              <select v-model.number="alpha" class="tool-input">
                <option :value="0.05">0.05</option>
                <option :value="0.01">0.01</option>
              </select>
            </div>

            <button
              @click="runAnalysis"
              :disabled="isRunning || !selectedDatasetId || !timeVariable || !eventVariable || !selectedPredictors.length"
              class="tool-btn-primary w-full px-4 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isRunning ? '模型运行中...' : '运行 Cox 生存分析' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="panel-card p-5">
          <div v-if="!result">
            <h2 class="text-sm font-semibold text-gray-900">Cox 比例风险模型结果</h2>
            <p class="mt-1 text-xs text-gray-400">展示 Cox 比例风险模型的 HR、95% CI、Z 值和 P 值。</p>
          </div>

          <div v-if="result" class="mt-5 space-y-5">
            <div class="inline-flex rounded-2xl border border-emerald-100 bg-emerald-50/80 p-1">
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeResultTab === 'table' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeResultTab = 'table'"
              >
                结果三线表
              </button>
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeResultTab === 'forest' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeResultTab = 'forest'"
              >
                森林图
              </button>
            </div>

            <div v-if="activeResultTab === 'table'" class="analysis-tab-panel space-y-4">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">Cox 比例风险模型结果</h2>
                <p class="mt-1 text-xs text-gray-400">展示 Cox 回归单因素与多因素结果，重点查看 HR、95% CI 和 P 值。</p>
              </div>

              <div class="overflow-x-auto">
                <table class="result-table min-w-full text-sm">
                  <thead>
                    <tr>
                      <th rowspan="2">项</th>
                      <th colspan="5" class="text-center">单因素</th>
                      <th colspan="5" class="text-center">多因素</th>
                    </tr>
                    <tr>
                      <th>系数</th>
                      <th>SE</th>
                      <th>HR</th>
                      <th>95% CI</th>
                      <th>P 值</th>
                      <th>系数</th>
                      <th>SE</th>
                      <th>HR</th>
                      <th>95% CI</th>
                      <th>P 值</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in combinedCoxRows" :key="item.term">
                      <td class="font-semibold text-slate-900">{{ item.term }}</td>
                      <td>{{ item.univariateCoefficient }}</td>
                      <td>{{ item.univariateSe }}</td>
                      <td>{{ item.univariateValue }}</td>
                      <td>{{ item.univariateInterval }}</td>
                      <td>{{ item.univariateP }}</td>
                      <td>{{ item.multivariateCoefficient }}</td>
                      <td>{{ item.multivariateSe }}</td>
                      <td>{{ item.multivariateValue }}</td>
                      <td>{{ item.multivariateInterval }}</td>
                      <td>{{ item.multivariateP }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="flex flex-wrap gap-2 text-[11px] text-slate-600">
                <span class="inline-flex rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1">样本量 {{ result.sample_size }}</span>
                <span class="inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-emerald-700">事件数 {{ result.event_count }}</span>
                <span class="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-cyan-700">事件水平 {{ result.event_level }}</span>
                <span class="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1">参考水平 {{ result.reference_level }}</span>
              </div>
            </div>

            <div v-else class="analysis-tab-panel space-y-4">

              <div v-if="result.plots.length" class="grid gap-4 lg:grid-cols-1">
                <div v-for="plot in result.plots" :key="plot.filename" class="panel-card overflow-hidden border-emerald-100 shadow-sm shadow-emerald-100/40">
                  <div class="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-100 bg-emerald-50/70 px-4 py-3">
                    <div>
                      <p class="text-sm font-semibold text-slate-900">{{ plot.name }}</p>
                    </div>
                    <div class="flex items-center gap-2">
                      <button
                        type="button"
                        class="tool-btn px-3 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
                        @click="downloadPlot(plot)"
                      >
                        下载 PNG
                      </button>
                      <button
                        type="button"
                        class="tool-btn border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60"
                        :disabled="downloadingPdfPlot === plot.filename"
                        @click="downloadPlotPdf(plot)"
                      >
                        <span>{{ downloadingPdfPlot === plot.filename ? '导出中...' : '下载 PDF' }}</span>
                        <span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 drop-shadow-[0_0_10px_rgba(16,185,129,0.45)]">
                          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>
                          1
                        </span>
                      </button>
                    </div>
                  </div>
                  <div class="bg-white p-4 sm:p-6">
                    <img :src="plotDataUri(plot)" :alt="plot.name" class="w-full bg-white object-contain" />
                  </div>
                </div>
              </div>

              <div v-else class="panel-card border-dashed border-emerald-200 bg-emerald-50/40 px-4 py-5 text-sm text-emerald-800">
                当前结果未生成森林图，请重新运行 Cox 生存分析后再查看。
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">运行模型后，这里会展示回归结果表和森林图。</div>

          <InsightActionPanel
            v-if="result"
            class="mt-5"
            :language="interpretationLanguage"
            :is-interpreting="isInterpreting"
            :is-downloading="isDownloading"
            :content="interpretationContent"
            :copied="copiedInterpretation"
            :charged-resources="interpretationChargedTokens"
            :remaining-resources="interpretationRemainingBalance"
            :saved-at="interpretationSavedAt"
            description="基于当前回归结果生成论文级结果说明。"
            loading-description="根据当前回归结果提炼论文式 Results 段落，请稍候。"
            empty-text="模型结果生成后，可在此调用 AI结果解读，输出适合论文 Results 部分的描述段落。"
            :interpret-disabled="isInterpreting"
            :download-disabled="isDownloading"
            @language-change="setInterpretationLanguage"
            @interpret="interpretResult"
            @download="downloadExcel"
            @copy="copyInterpretation"
          />
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import InsightActionPanel from '@/components/analysis/InsightActionPanel.vue'
import {
  downloadCoxPlotPdf,
  getDatasetSummary,
  getDatasets,
  getProjects,
  getSavedRegressionInterpretation,
  interpretRegression,
  downloadRegressionExcel,
  runCoxRegression,
  type CoxRegressionResponse,
  type DatasetColumnSummary,
  type DatasetItem,
  type DatasetSummaryResponse,
  type LassoPlotPayload,
} from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

interface ProjectItem {
  id: string
  name: string
}

interface DatasetOption extends DatasetItem {
  projectId: string
  projectName: string
}

interface PersistedCoxViewState {
  selectedDatasetId: string
  timeVariable: string
  eventVariable: string
  selectedPredictors: string[]
  alpha: number
  interpretationLanguage?: 'zh' | 'en'
  result: CoxRegressionResponse | null
  interpretationContent?: string
  interpretationChargedTokens?: number
  interpretationRemainingBalance?: number | null
  interpretationSavedAt?: string
}

interface CombinedCoxTableRow {
  term: string
  univariateCoefficient: string
  univariateSe: string
  univariateValue: string
  univariateInterval: string
  univariateP: string
  multivariateCoefficient: string
  multivariateSe: string
  multivariateValue: string
  multivariateInterval: string
  multivariateP: string
}

type CoxResultTab = 'table' | 'forest'

const COX_STATE_KEY = 'cox_regression_state_v1'

const notificationStore = useNotificationStore()
const authStore = useAuthStore()

const loadingDatasets = ref(false)
const isRunning = ref(false)
const isInterpreting = ref(false)
const isDownloading = ref(false)
const downloadingPdfPlot = ref<string | null>(null)
const activeResultTab = ref<CoxResultTab>('table')
const datasetOptions = ref<DatasetOption[]>([])
const datasetSummary = ref<DatasetSummaryResponse | null>(null)

const selectedDatasetId = ref('')
const timeVariable = ref('')
const eventVariable = ref('')
const selectedPredictors = ref<string[]>([])
const alpha = ref(0.05)
const result = ref<CoxRegressionResponse | null>(null)

const interpretationLanguage = ref<'zh' | 'en'>('zh')
const interpretationContent = ref('')
const interpretationChargedTokens = ref(0)
const interpretationRemainingBalance = ref<number | null>(null)
const interpretationSavedAt = ref('')
const copiedInterpretation = ref(false)

let restoringState = false

const PAID_SUBSCRIPTIONS = new Set(['basic', 'pro', 'enterprise'])
const canUseAiInterpretation = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))
const canDownloadPremiumPdf = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))

const timeOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter((column) => column.kind === 'numeric' && column.unique_count >= 2),
)

const eventOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter((column) => column.name !== timeVariable.value && isBinaryColumn(column)),
)

const predictorOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) =>
      column.name !== timeVariable.value &&
      column.name !== eventVariable.value &&
      column.kind !== 'datetime' &&
      column.unique_count >= 2,
  ),
)

const predictorSelectionText = computed(() => {
  if (!predictorOptions.value.length) return '当前暂无可选协变量'
  if (!selectedPredictors.value.length) return '当前未选择协变量'
  if (selectedPredictors.value.length <= 3) return `已选择 ${selectedPredictors.value.join('、')}`
  return `已选择 ${selectedPredictors.value.length} 个协变量`
})
const combinedCoxRows = computed<CombinedCoxTableRow[]>(() =>
  mergeComparisonRows(
    result.value?.univariate_coefficients || [],
    result.value?.coefficients || [],
    (item) => formatNumber(item.hazard_ratio),
    (item) => formatInterval(item.conf_low, item.conf_high),
    (item) => formatP(item.p_value),
  ),
)

function isBinaryColumn(column: DatasetColumnSummary) {
  return (column.kind === 'categorical' || column.kind === 'boolean' || column.kind === 'numeric') && column.unique_count === 2
}

function eventOptionLabel(column: DatasetColumnSummary) {
  if (column.kind === 'numeric') return '0/1 二分类'
  if (column.kind === 'boolean') return '布尔/二分类'
  return `${column.unique_count} 水平`
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return value.toFixed(3)
}

function formatP(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  if (value < 0.001) return '<0.001'
  return value.toFixed(3)
}

function formatInterval(low: number | null | undefined, high: number | null | undefined) {
  if (low === null || low === undefined || high === null || high === undefined) return '-'
  return `${low.toFixed(3)} ~ ${high.toFixed(3)}`
}

function mergeComparisonRows<T extends { term: string; coefficient?: number | null; std_error?: number | null }>(
  univariateRows: T[],
  multivariateRows: T[],
  formatValue: (row: T) => string,
  formatCi: (row: T) => string,
  formatPValue: (row: T) => string,
): CombinedCoxTableRow[] {
  const order: string[] = []
  const univariateMap = new Map<string, T>()
  const multivariateMap = new Map<string, T>()

  for (const row of univariateRows) {
    if (!order.includes(row.term)) order.push(row.term)
    univariateMap.set(row.term, row)
  }
  for (const row of multivariateRows) {
    if (!order.includes(row.term)) order.push(row.term)
    multivariateMap.set(row.term, row)
  }

  return order.map((term) => {
    const univariateRow = univariateMap.get(term)
    const multivariateRow = multivariateMap.get(term)
    return {
      term,
      univariateCoefficient: univariateRow ? formatNumber(univariateRow.coefficient) : '-',
      univariateSe: univariateRow ? formatNumber(univariateRow.std_error) : '-',
      univariateValue: univariateRow ? formatValue(univariateRow) : '-',
      univariateInterval: univariateRow ? formatCi(univariateRow) : '-',
      univariateP: univariateRow ? formatPValue(univariateRow) : '-',
      multivariateCoefficient: multivariateRow ? formatNumber(multivariateRow.coefficient) : '-',
      multivariateSe: multivariateRow ? formatNumber(multivariateRow.std_error) : '-',
      multivariateValue: multivariateRow ? formatValue(multivariateRow) : '-',
      multivariateInterval: multivariateRow ? formatCi(multivariateRow) : '-',
      multivariateP: multivariateRow ? formatPValue(multivariateRow) : '-',
    }
  })
}

function resetResult() {
  result.value = null
  activeResultTab.value = 'table'
  interpretationContent.value = ''
  interpretationChargedTokens.value = 0
  interpretationRemainingBalance.value = null
  interpretationSavedAt.value = ''
}

function buildCoxInterpretPayload() {
  if (!result.value) return null
  return {
    dataset_name: result.value.dataset_name,
    time_variable: result.value.time_variable,
    event_variable: result.value.event_variable,
    event_level: result.value.event_level,
    reference_level: result.value.reference_level,
    sample_size: result.value.sample_size,
    event_count: result.value.event_count,
    excluded_rows: result.value.excluded_rows,
    coefficients: result.value.coefficients.map((item) => ({
      term: item.term,
      hazard_ratio: item.hazard_ratio,
      conf_low: item.conf_low,
      conf_high: item.conf_high,
      p_value: item.p_value,
    })),
  }
}

function buildPersistedState(): PersistedCoxViewState {
  return {
    selectedDatasetId: selectedDatasetId.value,
    timeVariable: timeVariable.value,
    eventVariable: eventVariable.value,
    selectedPredictors: [...selectedPredictors.value],
    alpha: alpha.value,
    interpretationLanguage: interpretationLanguage.value,
    result: result.value,
    interpretationContent: interpretationContent.value,
    interpretationChargedTokens: interpretationChargedTokens.value,
    interpretationRemainingBalance: interpretationRemainingBalance.value,
    interpretationSavedAt: interpretationSavedAt.value,
  }
}

function persistState() {
  if (restoringState) return
  window.sessionStorage.setItem(COX_STATE_KEY, JSON.stringify(buildPersistedState()))
}

function loadPersistedState() {
  const raw = window.sessionStorage.getItem(COX_STATE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as PersistedCoxViewState
  } catch (error) {
    console.error('Failed to parse cox regression view state', error)
    return null
  }
}

async function loadSummary() {
  if (!selectedDatasetId.value) {
    datasetSummary.value = null
    return
  }
  try {
    datasetSummary.value = await getDatasetSummary(selectedDatasetId.value)
    selectedPredictors.value = selectedPredictors.value.filter((name) => datasetSummary.value?.columns.some((column) => column.name === name))
  } catch (error: any) {
    datasetSummary.value = null
    notificationStore.error('数据摘要加载失败', error.response?.data?.detail || '请稍后重试')
  }
}

async function loadAllDatasets() {
  loadingDatasets.value = true
  try {
    const savedState = loadPersistedState()
    const projects = (await getProjects()) as ProjectItem[]
    const groups = await Promise.all(
      projects.map(async (project) => {
        const datasets = await getDatasets(project.id)
        return datasets.map((dataset) => ({
          ...dataset,
          projectId: project.id,
          projectName: project.name,
        }))
      }),
    )
    datasetOptions.value = groups.flat().sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
    if (!datasetOptions.value.length) return

    selectedDatasetId.value = datasetOptions.value.some((dataset) => dataset.id === savedState?.selectedDatasetId)
      ? savedState?.selectedDatasetId || datasetOptions.value[0].id
      : datasetOptions.value[0].id
    await loadSummary()

    restoringState = true
    alpha.value = savedState?.alpha ?? 0.05
    const canRestoreExactState = !!savedState && savedState.selectedDatasetId === selectedDatasetId.value

    timeVariable.value = canRestoreExactState && timeOptions.value.some((column) => column.name === savedState?.timeVariable)
      ? savedState?.timeVariable || ''
      : ''
    eventVariable.value = canRestoreExactState && eventOptions.value.some((column) => column.name === savedState?.eventVariable)
      ? savedState?.eventVariable || ''
      : ''
    selectedPredictors.value = canRestoreExactState
      ? (savedState?.selectedPredictors || []).filter((name) => predictorOptions.value.some((column) => column.name === name))
      : []
    result.value = canRestoreExactState ? savedState?.result || null : null
    interpretationLanguage.value = savedState?.interpretationLanguage || 'zh'
    interpretationContent.value = canRestoreExactState ? savedState?.interpretationContent || '' : ''
    interpretationChargedTokens.value = canRestoreExactState ? savedState?.interpretationChargedTokens || 0 : 0
    interpretationRemainingBalance.value = canRestoreExactState ? (savedState?.interpretationRemainingBalance ?? null) : null
    interpretationSavedAt.value = canRestoreExactState ? savedState?.interpretationSavedAt || '' : ''

    restoringState = false
    persistState()
  } catch (error) {
    console.error('Failed to load datasets for cox regression', error)
    notificationStore.error('数据集加载失败', '无法加载 Cox 生存分析所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  timeVariable.value = ''
  eventVariable.value = ''
  selectedPredictors.value = []
  resetResult()
  void loadSummary()
}

function handleCoreVariableChange() {
  selectedPredictors.value = selectedPredictors.value.filter(
    (name) => name !== timeVariable.value && name !== eventVariable.value,
  )
  resetResult()
}

function togglePredictor(name: string) {
  resetResult()
  if (selectedPredictors.value.includes(name)) {
    selectedPredictors.value = selectedPredictors.value.filter((item) => item !== name)
    return
  }
  selectedPredictors.value = [...selectedPredictors.value, name]
}

function toggleAllPredictors() {
  resetResult()
  if (selectedPredictors.value.length === predictorOptions.value.length) {
    selectedPredictors.value = []
    return
  }
  selectedPredictors.value = predictorOptions.value.map((column) => column.name)
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !timeVariable.value || !eventVariable.value || !selectedPredictors.value.length) {
    notificationStore.warning('缺少必要配置', '请先选择数据集、生存时间、事件变量和至少一个协变量。')
    return
  }

  isRunning.value = true
  resetResult()
  try {
    result.value = await runCoxRegression({
      dataset_id: selectedDatasetId.value,
      time_variable: timeVariable.value,
      event_variable: eventVariable.value,
      predictor_variables: selectedPredictors.value,
      alpha: alpha.value,
    })
    notificationStore.success('Cox 生存分析已完成', '结果表与森林图已生成。')
    void loadSavedInterpretation()
  } catch (error: any) {
    console.error('Failed to run cox regression', error)
    notificationStore.error('Cox 生存分析失败', error.response?.data?.detail || '请稍后重试。')
  } finally {
    isRunning.value = false
  }
}

function setInterpretationLanguage(lang: 'zh' | 'en') {
  interpretationLanguage.value = lang
  if (result.value) {
    void loadSavedInterpretation()
  }
}

async function loadSavedInterpretation() {
  const payload = buildCoxInterpretPayload()
  if (!selectedDatasetId.value || !payload) return
  try {
    const res = await getSavedRegressionInterpretation({
      dataset_id: selectedDatasetId.value,
      analysis_kind: 'cox',
      language: interpretationLanguage.value,
      payload,
    })
    if (res.found && res.content) {
      interpretationContent.value = res.content
      interpretationChargedTokens.value = res.charged_resources || res.charged_tokens
      interpretationRemainingBalance.value = null
      interpretationSavedAt.value = res.saved_at || ''
    } else {
      interpretationContent.value = ''
      interpretationChargedTokens.value = 0
      interpretationRemainingBalance.value = null
      interpretationSavedAt.value = ''
    }
  } catch (error) {
    console.error('Failed to load saved cox interpretation', error)
  }
}

async function interpretResult() {
  const payload = buildCoxInterpretPayload()
  if (!payload || !selectedDatasetId.value) return

  if (!canUseAiInterpretation.value) {
    notificationStore.warning('当前不可用', '升级到付费套餐后可使用 AI 结果解读。')
    return
  }

  isInterpreting.value = true
  interpretationContent.value = ''
  try {
    const res = await interpretRegression({
      dataset_id: selectedDatasetId.value,
      analysis_kind: 'cox',
      language: interpretationLanguage.value,
      payload,
    })
    interpretationContent.value = res.content
    interpretationChargedTokens.value = res.charged_resources || res.charged_tokens
    interpretationRemainingBalance.value = res.remaining_resources ?? res.remaining_balance
    interpretationSavedAt.value = res.saved_at || ''
    if (authStore.user) {
      authStore.user.tokenBalance = res.remaining_resources ?? res.remaining_balance
    }
    notificationStore.success('AI解读已生成', '结果已同步保存，刷新后可自动恢复。')
  } catch (error: any) {
    console.error('Failed to interpret cox result', error)
    notificationStore.error('AI解读失败', error.response?.data?.detail || '请稍后重试。')
  } finally {
    isInterpreting.value = false
  }
}

function copyInterpretation() {
  if (!interpretationContent.value) return
  navigator.clipboard.writeText(interpretationContent.value)
    .then(() => {
      copiedInterpretation.value = true
      setTimeout(() => { copiedInterpretation.value = false }, 2000)
    })
    .catch((err) => {
      console.error('Copy failed:', err)
      notificationStore.error('复制失败', '请手动选中后复制。')
    })
}

async function downloadExcel() {
  if (!result.value) return

  isDownloading.value = true
  try {
    const exportPayload = {
      ...result.value,
      plots: [],
    }
    const blob = await downloadRegressionExcel({
      analysis_kind: 'cox',
      payload: exportPayload as unknown as Record<string, unknown>,
    })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${result.value.dataset_name || 'regression'}_cox_regression.xlsx`
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    window.URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('Failed to download regression excel', error)
    notificationStore.error('下载失败', error?.response?.data?.detail || 'Excel 下载失败，请稍后重试。')
  } finally {
    isDownloading.value = false
  }
}

function plotDataUri(plot: LassoPlotPayload) {
  return `data:${plot.media_type};base64,${plot.content_base64}`
}

function downloadPlot(plot: LassoPlotPayload) {
  const link = document.createElement('a')
  link.href = plotDataUri(plot)
  link.download = plot.filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function downloadPlotPdf(plot: LassoPlotPayload) {
  if (!selectedDatasetId.value) return

  if (!canDownloadPremiumPdf.value) {
    notificationStore.warning('当前不可用', '升级到付费套餐后可导出 PDF 高清图像。')
    return
  }

  downloadingPdfPlot.value = plot.filename
  try {
    const pdf = await downloadCoxPlotPdf({
      dataset_id: selectedDatasetId.value,
      plot,
    })
    const url = window.URL.createObjectURL(pdf.blob)
    const link = document.createElement('a')
    link.href = url
    const pdfFilename = plot.filename.replace(/\.[^/.]+$/, '') + '.pdf'
    link.setAttribute('download', pdfFilename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    if (authStore.user && pdf.remainingResources !== null) {
      authStore.user.tokenBalance = pdf.remainingResources
    }
  } catch (error: any) {
    console.error('Failed to download PDF', error)
    let errorMessage = '无法导出 PDF，请稍后重试'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        const json = JSON.parse(text)
        if (json.detail) errorMessage = json.detail
      } catch (e) {
        // ignore JSON parse error
      }
    }
    notificationStore.error('PDF导出失败', errorMessage)
  } finally {
    downloadingPdfPlot.value = null
  }
}

watch(
  [selectedDatasetId, timeVariable, eventVariable, selectedPredictors, alpha, result, interpretationLanguage, interpretationContent],
  () => {
    persistState()
  },
  { deep: true },
)

onMounted(async () => {
  await loadAllDatasets()
})
</script>

<style scoped>
.result-table {
  border-top: 1.5px solid #0f172a;
  border-bottom: 1.5px solid #0f172a;
  border-collapse: collapse;
}

.result-table thead tr {
  border-bottom: 1px solid #cbd5e1;
}

.result-table th,
.result-table td {
  padding: 12px 10px;
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid #eef2f7;
  line-height: 1.55;
}

.result-table tbody tr:last-child td {
  border-bottom: none;
}

.result-table th {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.result-table td {
  color: #334155;
}

.analysis-tab-panel {
  min-height: 24rem;
  align-content: start;
}

@media (min-width: 1280px) {
  .analysis-tab-panel {
    min-height: 38rem;
  }
}
</style>
