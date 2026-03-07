<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-50 via-white to-emerald-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">多组间连续变量统计</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        适用于 3 到 4 组独立样本的连续变量比较。系统会先逐组检查正态性，再判断方差齐性；只有满足前提时才使用 one-way ANOVA，否则自动切换到 Kruskal-Wallis 多组非参数检验。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">检验配置</h2>
            <p class="mt-1 text-xs text-gray-400">先选择数据集和 3 到 4 组分组变量，再勾选要比较的连续变量。</p>
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
              <label class="mb-1.5 block text-xs font-medium text-gray-500">多组分组变量</label>
              <select v-model="groupVariable" :disabled="!groupVariableOptions.length" @change="handleGroupVariableChange" class="input-field py-2.5 text-sm">
                <option value="">请选择 3-4 组变量</option>
                <option v-for="column in groupVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">方差分析仅接受 3 到 4 组分组变量。</p>
            </div>

            <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">连续变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">系统会自动检验正态性与 Bartlett 方差齐性。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllContinuous">
                  {{ selectedContinuousVariables.length === continuousVariableOptions.length && continuousVariableOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="mt-3 rounded-lg border border-white bg-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ describeSelection(selectedContinuousVariables, continuousVariableOptions.length, '连续变量') }}</p>
                <div class="mt-2 grid max-h-48 grid-cols-2 gap-2 overflow-y-auto pr-1">
                  <label v-for="column in continuousVariableOptions" :key="column.name" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                    <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="selectedContinuousVariables.includes(column.name)" @change="toggleVariable(column.name)" />
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

            <button @click="runAnalysis" :disabled="isRunning || !selectedDatasetId || !groupVariable" class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50">
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isRunning ? '检验中...' : '运行方差分析' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">前提检查</h2>
            <p class="mt-1 text-xs text-gray-400">系统会集中显示当前分组结构、已检验变量数，以及多组比较的关键前提。</p>
          </div>

          <div v-if="anovaResult" class="mt-5 space-y-4">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
                <p class="mt-2 text-sm font-semibold text-gray-900">{{ anovaResult.dataset_name }}</p>
                <p class="mt-1 text-xs text-gray-500">分组变量：{{ anovaResult.group_variable }}</p>
              </div>
              <div class="rounded-2xl border border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">组别</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ anovaResult.group_levels.length }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ anovaResult.group_levels.join(' / ') }}</p>
              </div>
              <div class="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">已检验变量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ anovaResult.variables.length }}</p>
                <p class="mt-1 text-xs text-gray-500">alpha = {{ anovaResult.alpha }}</p>
              </div>
            </div>

            <div class="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
              <div class="grid gap-2">
                <div v-for="(item, index) in anovaResult.assumptions" :key="index" class="flex items-start gap-2 text-sm text-gray-600">
                  <span class="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-primary"></span>
                  <span>{{ item }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行方差分析后，系统会在这里总结当前数据是否满足分析前提。
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">检验结果</h2>
              <p class="mt-1 text-xs text-gray-400">结果按三线表汇总呈现；前提检查和备注放在表格下方的小字说明中。</p>
            </div>
            <button
              v-if="anovaResult"
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 transition-colors hover:border-primary/30 hover:text-primary"
              @click="copyResultTable"
              :aria-label="copiedResult ? '已复制统计结果' : '复制统计结果'"
              :title="copiedResult ? '已复制' : '复制到剪切板'"
            >
              <svg v-if="copiedResult" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6L9 17L4 12" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="11" height="11" rx="2" />
                <path d="M5 15V6a2 2 0 0 1 2-2h9" />
              </svg>
            </button>
          </div>

          <div v-if="anovaResult" class="mt-5 space-y-4">
            <div class="overflow-x-auto">
              <table class="result-table min-w-full text-sm">
                <thead>
                  <tr>
                    <th>变量</th>
                    <th v-for="group in anovaResult.group_levels" :key="`head-${group}`">{{ group }}</th>
                    <th>执行方法</th>
                    <th>统计量</th>
                    <th>df 组间</th>
                    <th>df 组内</th>
                    <th>P 值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in anovaResult.variables" :key="item.variable">
                    <td class="font-semibold text-slate-900">{{ item.variable }}</td>
                    <td v-for="(_, index) in anovaResult.group_levels" :key="`${item.variable}-${index}`">
                      {{ renderAnovaGroupCell(item, index) }}
                    </td>
                    <td>{{ item.executed_test }}</td>
                    <td>{{ formatNumber(item.statistic) }}</td>
                    <td>{{ formatNumber(item.df_between) }}</td>
                    <td>{{ formatNumber(item.df_within) }}</td>
                    <td>{{ formatP(item.p_value) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="space-y-1.5 text-[12px] leading-6 text-slate-500">
              <p v-for="item in anovaResult.variables" :key="`${item.variable}-note`">
                <span class="font-medium text-slate-700">{{ item.variable }}</span>：
                {{ renderAnovaNotes(item) }}
              </p>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行后，这里会逐变量展示方差分析或 Kruskal-Wallis 结果。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import {
  getDatasetSummary,
  getDatasets,
  getProjects,
  runAnova,
  type AnovaResponse,
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

const notificationStore = useNotificationStore()

const datasetOptions = ref<DatasetOption[]>([])
const selectedDatasetId = ref('')
const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const groupVariable = ref('')
const selectedContinuousVariables = ref<string[]>([])
const alpha = ref(0.05)
const loadingDatasets = ref(true)
const isRunning = ref(false)
const anovaResult = ref<AnovaResponse | null>(null)
const copiedResult = ref(false)
let copyFeedbackTimer: number | null = null

const groupVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => (column.kind === 'categorical' || column.kind === 'boolean') && column.unique_count >= 3 && column.unique_count <= 4,
  ),
)

const continuousVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.kind === 'numeric' && column.name !== groupVariable.value,
  ),
)

function describeSelection(selected: string[], total: number, label: string) {
  if (!total) return `当前暂无可选${label}`
  if (!selected.length) return `当前未选择${label}`
  if (selected.length <= 2) return `已选择 ${selected.join('、')}`
  return `已选择 ${selected.length} 个${label}`
}

function formatNumber(value: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  return value.toFixed(3)
}

function formatP(value: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  if (value < 0.001) return '<0.001'
  return value.toFixed(3)
}

function formatMeanSd(mean: number | null, sd: number | null) {
  if (mean === null) return '-'
  if (sd === null) return mean.toFixed(2)
  return `${mean.toFixed(2)} ± ${sd.toFixed(2)}`
}

function formatMedianIqr(median: number | null, q1: number | null, q3: number | null) {
  if (median === null) return '-'
  if (q1 === null || q3 === null) return median.toFixed(2)
  return `${median.toFixed(2)} (${q1.toFixed(2)}, ${q3.toFixed(2)})`
}

function renderAnovaGroupCell(item: AnovaResponse['variables'][number], index: number) {
  const group = item.group_summaries[index]
  if (!group) return '-'
  return `${formatMeanSd(group.mean, group.sd)}；${formatMedianIqr(group.median, group.q1, group.q3)}`
}

function renderAnovaNotes(item: AnovaResponse['variables'][number]) {
  const normality = item.normality_checks
    .map((check) => `${check.group} ${check.method} P=${formatP(check.p_value)}`)
    .join('；')
  const variance = `${item.variance_test_name} P=${formatP(item.variance_p_value)}`
  return `${normality}；${variance}；${item.note}`
}

function buildResultTableText() {
  if (!anovaResult.value) return ''
  const headers = ['变量', ...anovaResult.value.group_levels, '执行方法', '统计量', 'df 组间', 'df 组内', 'P 值']
  const rows = anovaResult.value.variables.map((item) =>
    [
      item.variable,
      ...anovaResult.value!.group_levels.map((_, index) => renderAnovaGroupCell(item, index)),
      item.executed_test,
      formatNumber(item.statistic),
      formatNumber(item.df_between),
      formatNumber(item.df_within),
      formatP(item.p_value),
    ].join('\t'),
  )
  const notes = anovaResult.value.variables.map((item) => `${item.variable}: ${renderAnovaNotes(item)}`)
  return [headers.join('\t'), ...rows, '', '备注', ...notes].join('\n')
}

async function copyResultTable() {
  if (!anovaResult.value) return
  try {
    await navigator.clipboard.writeText(buildResultTableText())
    copiedResult.value = true
    if (copyFeedbackTimer !== null) {
      window.clearTimeout(copyFeedbackTimer)
    }
    copyFeedbackTimer = window.setTimeout(() => {
      copiedResult.value = false
      copyFeedbackTimer = null
    }, 1800)
    notificationStore.success('已复制统计结果', '三线表内容已写入剪切板。')
  } catch (err) {
    console.error('Failed to copy anova table', err)
    notificationStore.error('复制失败', '当前环境不支持写入剪切板。')
  }
}

async function loadSummary() {
  if (!selectedDatasetId.value) {
    datasetSummary.value = null
    return
  }

  try {
    datasetSummary.value = await getDatasetSummary(selectedDatasetId.value)
    selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) =>
      datasetSummary.value?.columns.some((column) => column.name === name && column.kind === 'numeric'),
    )
  } catch (error: any) {
    datasetSummary.value = null
    notificationStore.error('数据摘要加载失败', error.response?.data?.detail || '请稍后重试')
  }
}

async function loadAllDatasets() {
  loadingDatasets.value = true
  try {
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
    if (datasetOptions.value.length) {
      selectedDatasetId.value = datasetOptions.value[0].id
      await loadSummary()
    }
  } catch (error) {
    console.error('Failed to load datasets', error)
    notificationStore.error('数据集加载失败', '无法加载方差分析所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  groupVariable.value = ''
  selectedContinuousVariables.value = []
  anovaResult.value = null
  void loadSummary()
}

function handleGroupVariableChange() {
  selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) => name !== groupVariable.value)
  anovaResult.value = null
}

function toggleVariable(variable: string) {
  anovaResult.value = null
  if (selectedContinuousVariables.value.includes(variable)) {
    selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) => name !== variable)
    return
  }
  selectedContinuousVariables.value = [...selectedContinuousVariables.value, variable]
}

function toggleAllContinuous() {
  anovaResult.value = null
  if (selectedContinuousVariables.value.length === continuousVariableOptions.value.length) {
    selectedContinuousVariables.value = []
    return
  }
  selectedContinuousVariables.value = continuousVariableOptions.value.map((column) => column.name)
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !groupVariable.value) {
    notificationStore.warning('缺少必要配置', '请先选择数据集和多组分组变量。')
    return
  }
  if (!selectedContinuousVariables.value.length) {
    notificationStore.warning('请选择连续变量', '至少选择一个连续变量进行方差分析。')
    return
  }
  isRunning.value = true
  try {
    anovaResult.value = await runAnova({
      dataset_id: selectedDatasetId.value,
      group_variable: groupVariable.value,
      continuous_variables: selectedContinuousVariables.value,
      alpha: alpha.value,
      confirm_independence: true,
    })
    notificationStore.success('方差分析已完成', '前提检查和多组比较结果已准备完成。')
  } catch (error: any) {
    console.error('Failed to run anova', error)
    notificationStore.error('方差分析失败', error.response?.data?.detail || '请稍后重试。')
  } finally {
    isRunning.value = false
  }
}

onMounted(async () => {
  await loadAllDatasets()
})

onUnmounted(() => {
  if (copyFeedbackTimer !== null) {
    window.clearTimeout(copyFeedbackTimer)
  }
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
