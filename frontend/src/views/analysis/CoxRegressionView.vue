<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-50 via-white to-cyan-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">Cox 生存分析</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        选择生存时间、事件结局和候选协变量，后端将通过 R 的 `survival::coxph` 完成比例风险模型拟合，并返回 HR、95% CI 与比例风险假设检验结果。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">模型配置</h2>
            <p class="mt-1 text-xs text-gray-400">生存时间需为正数，事件变量需为二分类变量，自变量支持数值型与分类变量。</p>
          </div>

          <div class="mt-5 space-y-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">数据集</label>
              <select v-model="selectedDatasetId" :disabled="loadingDatasets" @change="handleDatasetChange" class="input-field py-2.5 text-sm">
                <option value="">请选择数据集</option>
                <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} · {{ dataset.projectName }}
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">生存时间变量</label>
              <select v-model="timeVariable" :disabled="!timeOptions.length" @change="handleCoreVariableChange" class="input-field py-2.5 text-sm">
                <option value="">请选择生存时间变量</option>
                <option v-for="column in timeOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · 数值型
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">事件变量</label>
              <select v-model="eventVariable" :disabled="!eventOptions.length" @change="handleCoreVariableChange" class="input-field py-2.5 text-sm">
                <option value="">请选择事件变量</option>
                <option v-for="column in eventOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ eventOptionLabel(column) }}
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">支持 0/1 数值型或双水平分类变量。</p>
            </div>

            <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">协变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">分类变量会自动在 R 中展开为虚拟变量并进入 Cox 模型。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllPredictors">
                  {{ selectedPredictors.length === predictorOptions.length && predictorOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="mt-3 rounded-lg border border-white bg-white p-2.5">
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
              <select v-model.number="alpha" class="input-field py-2.5 text-sm">
                <option :value="0.05">0.05</option>
                <option :value="0.01">0.01</option>
              </select>
            </div>

            <button
              @click="runAnalysis"
              :disabled="isRunning || !selectedDatasetId || !timeVariable || !eventVariable || !selectedPredictors.length"
              class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
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
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">模型摘要</h2>
            <p class="mt-1 text-xs text-gray-400">重点查看样本量、事件数、C-index 和整体检验结果。</p>
          </div>

          <div v-if="result" class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
              <p class="mt-2 text-sm font-semibold text-gray-900">{{ result.dataset_name }}</p>
              <p class="mt-1 text-xs text-gray-500">时间：{{ result.time_variable }} / 事件：{{ result.event_variable }}</p>
            </div>
            <div class="rounded-2xl border border-sky-200 bg-sky-50/80 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">样本与事件</p>
              <p class="mt-2 text-xl font-semibold text-gray-900">{{ result.sample_size }}</p>
              <p class="mt-1 text-xs text-gray-500">事件 {{ result.event_count }}，剔除 {{ result.excluded_rows }} 行</p>
            </div>
            <div class="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">区分度</p>
              <p class="mt-2 text-xl font-semibold text-gray-900">{{ formatNumber(result.concordance) }}</p>
              <p class="mt-1 text-xs text-gray-500">C-index，SE {{ formatNumber(result.concordance_std_error) }}</p>
            </div>
            <div class="rounded-2xl border border-amber-200 bg-amber-50/80 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">PH 假设</p>
              <p class="mt-2 text-xl font-semibold text-gray-900">{{ formatP(result.global_ph_p_value) }}</p>
              <p class="mt-1 text-xs text-gray-500">全局 Schoenfeld 检验 P 值</p>
            </div>
          </div>

          <div v-if="result" class="mt-4 rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
            <div class="grid gap-2">
              <div v-for="(item, index) in result.assumptions" :key="index" class="flex items-start gap-2 text-sm text-gray-600">
                <span class="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-primary"></span>
                <span>{{ item }}</span>
              </div>
            </div>
            <p class="mt-3 text-xs text-gray-500">{{ result.note }}</p>
          </div>

          <div v-if="result" class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">Likelihood ratio</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatNumber(result.likelihood_ratio_statistic) }}</p>
              <p class="mt-1 text-xs text-gray-500">df {{ formatNumber(result.likelihood_ratio_df) }}，P {{ formatP(result.likelihood_ratio_p_value) }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">Wald</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatNumber(result.wald_statistic) }}</p>
              <p class="mt-1 text-xs text-gray-500">df {{ formatNumber(result.wald_df) }}，P {{ formatP(result.wald_p_value) }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">Score (log-rank)</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ formatNumber(result.score_statistic) }}</p>
              <p class="mt-1 text-xs text-gray-500">df {{ formatNumber(result.score_df) }}，P {{ formatP(result.score_p_value) }}</p>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">运行模型后，这里会展示 Cox 模型摘要、PH 假设检验和总体统计量。</div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">结果表</h2>
            <p class="mt-1 text-xs text-gray-400">展示 Cox 比例风险模型的 HR、95% CI、Z 值和 P 值。</p>
          </div>

          <div v-if="result" class="mt-5 overflow-x-auto">
            <table class="result-table min-w-full text-sm">
              <thead>
                <tr>
                  <th>项</th>
                  <th>HR</th>
                  <th>SE</th>
                  <th>Z</th>
                  <th>95% CI</th>
                  <th>P 值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in result.coefficients" :key="item.term">
                  <td class="font-semibold text-slate-900">{{ item.term }}</td>
                  <td>{{ formatNumber(item.hazard_ratio) }}</td>
                  <td>{{ formatNumber(item.std_error) }}</td>
                  <td>{{ formatNumber(item.z_value) }}</td>
                  <td>{{ formatInterval(item.conf_low, item.conf_high) }}</td>
                  <td>{{ formatP(item.p_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="py-12 text-center text-sm text-gray-400">模型运行完成后，这里会展示 Cox 三线表结果。</div>
        </div>

        <div v-if="result" class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">比例风险假设检验</h2>
              <p class="mt-1 text-xs text-gray-400">基于 Schoenfeld 残差的 `cox.zph` 结果。若某协变量或全局 P 值过小，需要进一步考虑 PH 假设是否成立。</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-right">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">Global P</p>
              <p class="mt-1 text-sm font-semibold text-slate-900">{{ formatP(result.global_ph_p_value) }}</p>
            </div>
          </div>

          <div v-if="result.proportional_hazards_tests.length" class="mt-5 overflow-x-auto">
            <table class="result-table min-w-full text-sm">
              <thead>
                <tr>
                  <th>项</th>
                  <th>Chi-square</th>
                  <th>df</th>
                  <th>P 值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in result.proportional_hazards_tests" :key="item.term">
                  <td class="font-semibold text-slate-900">{{ item.term }}</td>
                  <td>{{ formatNumber(item.statistic) }}</td>
                  <td>{{ formatNumber(item.df) }}</td>
                  <td>{{ formatP(item.p_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="mt-5 rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-8 text-center text-sm text-slate-400">
            当前模型未返回逐项 PH 检验结果，但已返回全局 PH 检验。
          </div>

          <div class="mt-5 rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3 text-xs text-slate-500">
            <p>公式：{{ result.formula }}</p>
            <p class="mt-1">事件水平：{{ result.event_level }}；参考水平：{{ result.reference_level }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import {
  getDatasetSummary,
  getDatasets,
  getProjects,
  runCoxRegression,
  type CoxRegressionResponse,
  type DatasetColumnSummary,
  type DatasetItem,
  type DatasetSummaryResponse,
} from '@/services/api'
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
  result: CoxRegressionResponse | null
}

const COX_STATE_KEY = 'cox_regression_state_v1'

const notificationStore = useNotificationStore()

const loadingDatasets = ref(false)
const isRunning = ref(false)
const datasetOptions = ref<DatasetOption[]>([])
const datasetSummary = ref<DatasetSummaryResponse | null>(null)

const selectedDatasetId = ref('')
const timeVariable = ref('')
const eventVariable = ref('')
const selectedPredictors = ref<string[]>([])
const alpha = ref(0.05)
const result = ref<CoxRegressionResponse | null>(null)

let restoringState = false

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

function resetResult() {
  result.value = null
}

function buildPersistedState(): PersistedCoxViewState {
  return {
    selectedDatasetId: selectedDatasetId.value,
    timeVariable: timeVariable.value,
    eventVariable: eventVariable.value,
    selectedPredictors: [...selectedPredictors.value],
    alpha: alpha.value,
    result: result.value,
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
    notificationStore.success('Cox 生存分析已完成', '结果表、整体检验和 PH 假设检验已生成。')
  } catch (error: any) {
    console.error('Failed to run cox regression', error)
    notificationStore.error('Cox 生存分析失败', error.response?.data?.detail || '请稍后重试。')
  } finally {
    isRunning.value = false
  }
}

watch(
  [selectedDatasetId, timeVariable, eventVariable, selectedPredictors, alpha, result],
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
</style>
