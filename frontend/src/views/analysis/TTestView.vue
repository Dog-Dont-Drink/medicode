<template>
  <div class="space-y-6">
    <div class="panel-card bg-gradient-to-r from-slate-50 via-white to-sky-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">两组间连续变量统计</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        适用于两组独立样本的连续变量比较。系统会先检查二分类分组、正态性和方差齐性，再自动判断应使用 Student t-test、Welch t-test 或给出非参数替代结果，因此这里展示的是“两组连续变量比较结果”，不局限于单一 t 检验。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">检验配置</h2>
            <p class="mt-1 text-xs text-gray-400">先选择数据集和二分类分组变量，再勾选要检验的连续变量。</p>
          </div>

          <div class="mt-5 space-y-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">数据集</label>
              <select v-model="selectedDatasetId" @change="handleDatasetChange" :disabled="loadingDatasets" class="tool-input">
                <option value="">请选择数据集</option>
                <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} · {{ dataset.projectName }}
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">二分类分组变量</label>
              <select v-model="groupVariable" @change="handleGroupVariableChange" :disabled="!groupVariableOptions.length" class="tool-input">
                <option value="">请选择二分类变量</option>
                <option v-for="column in groupVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">T 检验只接受恰好 2 组的分组变量。</p>
            </div>

            <div class="panel-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">连续变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">系统会逐变量做每组正态性检验，并检查方差齐性。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllContinuous">
                  {{ selectedContinuousVariables.length === continuousVariableOptions.length && continuousVariableOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="panel-card-tight mt-3 border-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ describeSelection(selectedContinuousVariables, continuousVariableOptions.length) }}</p>
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
              <select v-model.number="alpha" class="tool-input">
                <option :value="0.05">0.05</option>
                <option :value="0.01">0.01</option>
              </select>
            </div>

            <button @click="runAnalysis" :disabled="isRunning || !selectedDatasetId || !groupVariable" class="tool-btn-primary w-full px-4 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50">
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isRunning ? '检验中...' : '运行两组比较' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">前提检查</h2>
            <p class="mt-1 text-xs text-gray-400">T 检验的核心要求会集中显示在这里，方便你判断当前数据是否适合使用。</p>
          </div>

          <div v-if="ttestResult" class="mt-5 space-y-4">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <div class="panel-card border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
                <p class="mt-2 text-sm font-semibold text-gray-900">{{ ttestResult.dataset_name }}</p>
                <p class="mt-1 text-xs text-gray-500">分组变量：{{ ttestResult.group_variable }}</p>
              </div>
              <div class="panel-card border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">组别</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ ttestResult.group_levels.join(' / ') }}</p>
                <p class="mt-1 text-xs text-gray-500">必须为 2 组</p>
              </div>
              <div class="panel-card border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">已检验变量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ ttestResult.variables.length }}</p>
                <p class="mt-1 text-xs text-gray-500">alpha = {{ ttestResult.alpha }}</p>
              </div>
            </div>

            <div class="panel-subtle p-4">
              <div class="grid gap-2">
                <div v-for="(item, index) in ttestResult.assumptions" :key="index" class="flex items-start gap-2 text-sm text-gray-600">
                  <span class="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-primary"></span>
                  <span>{{ item }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行两组比较后，系统会在这里总结当前数据是否满足对应检验前提。
          </div>
        </div>

        <div class="panel-card p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">检验结果</h2>
              <p class="mt-1 text-xs text-gray-400">结果按三线表汇总呈现；检验前提和备注放在表格下方的小字说明中。</p>
            </div>
            <button
              v-if="ttestResult"
              type="button"
              class="tool-btn h-9 w-9 p-0 text-slate-500 hover:text-primary"
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

          <div v-if="ttestResult" class="mt-5 space-y-4">
            <div class="overflow-x-auto">
              <table class="result-table min-w-full text-sm">
                <thead>
                  <tr>
                    <th>变量</th>
                    <th>{{ getGroupHeader(0) }}</th>
                    <th>{{ getGroupHeader(1) }}</th>
                    <th>执行方法</th>
                    <th>统计量</th>
                    <th>自由度</th>
                    <th>差值 / 95% CI</th>
                    <th>P 值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in ttestResult.variables" :key="item.variable">
                    <td class="font-semibold text-slate-900">{{ item.variable }}</td>
                    <td>{{ renderTTestGroupCell(item, 0) }}</td>
                    <td>{{ renderTTestGroupCell(item, 1) }}</td>
                    <td>{{ item.executed_test }}</td>
                    <td>{{ formatNumber(item.statistic) }}</td>
                    <td>{{ formatNumber(item.df) }}</td>
                    <td>{{ formatNumber(item.estimate) }} / {{ formatInterval(item.conf_low, item.conf_high) }}</td>
                    <td>{{ formatP(item.p_value) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="space-y-1.5 text-[12px] leading-6 text-slate-500">
              <p v-for="item in ttestResult.variables" :key="`${item.variable}-note`">
                <span class="font-medium text-slate-700">{{ item.variable }}</span>：
                {{ renderTTestNotes(item) }}
              </p>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行后，这里会逐变量展示两组间连续变量比较结果。
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
  runTTest,
  type DatasetItem,
  type DatasetSummaryResponse,
  type TTestResponse,
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
const ttestResult = ref<TTestResponse | null>(null)
const copiedResult = ref(false)
let copyFeedbackTimer: number | null = null

const groupVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => (column.kind === 'categorical' || column.kind === 'boolean') && column.unique_count === 2,
  ),
)

const continuousVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.kind === 'numeric' && column.name !== groupVariable.value,
  ),
)

function describeSelection(selected: string[], total: number) {
  if (!total) return '当前暂无可选连续变量'
  if (!selected.length) return '当前未选择连续变量'
  if (selected.length <= 2) return `已选择 ${selected.join('、')}`
  return `已选择 ${selected.length} 个连续变量`
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

function formatInterval(low: number | null, high: number | null) {
  if (low === null || high === null) return '-'
  return `${low.toFixed(3)} ~ ${high.toFixed(3)}`
}

function getGroupHeader(index: number) {
  return ttestResult.value?.group_levels[index] || `第${index + 1}组`
}

function renderTTestGroupCell(item: TTestResponse['variables'][number], index: number) {
  const group = item.group_summaries[index]
  if (!group) return '-'
  return `${formatMeanSd(group.mean, group.sd)}；${formatMedianIqr(group.median, group.q1, group.q3)}`
}

function renderTTestNotes(item: TTestResponse['variables'][number]) {
  const normality = item.normality_checks
    .map((check) => `${check.group} ${check.method} P=${formatP(check.p_value)}`)
    .join('；')
  const variance = `${item.variance_test_name} P=${formatP(item.variance_p_value)}`
  return `${normality}；${variance}；${item.note}`
}

function buildResultTableText() {
  if (!ttestResult.value) return ''
  const headers = ['变量', getGroupHeader(0), getGroupHeader(1), '执行方法', '统计量', '自由度', '差值 / 95% CI', 'P 值']
  const rows = ttestResult.value.variables.map((item) =>
    [
      item.variable,
      renderTTestGroupCell(item, 0),
      renderTTestGroupCell(item, 1),
      item.executed_test,
      formatNumber(item.statistic),
      formatNumber(item.df),
      `${formatNumber(item.estimate)} / ${formatInterval(item.conf_low, item.conf_high)}`,
      formatP(item.p_value),
    ].join('\t'),
  )
  const notes = ttestResult.value.variables.map((item) => `${item.variable}: ${renderTTestNotes(item)}`)
  return [headers.join('\t'), ...rows, '', '备注', ...notes].join('\n')
}

async function copyResultTable() {
  if (!ttestResult.value) return
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
    console.error('Failed to copy t test table', err)
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
    notificationStore.error('数据集加载失败', '无法加载 T 检验所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  groupVariable.value = ''
  selectedContinuousVariables.value = []
  ttestResult.value = null
  void loadSummary()
}

function handleGroupVariableChange() {
  selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) => name !== groupVariable.value)
  ttestResult.value = null
}

function toggleVariable(variable: string) {
  ttestResult.value = null
  if (selectedContinuousVariables.value.includes(variable)) {
    selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) => name !== variable)
    return
  }
  selectedContinuousVariables.value = [...selectedContinuousVariables.value, variable]
}

function toggleAllContinuous() {
  ttestResult.value = null
  if (selectedContinuousVariables.value.length === continuousVariableOptions.value.length) {
    selectedContinuousVariables.value = []
    return
  }
  selectedContinuousVariables.value = continuousVariableOptions.value.map((column) => column.name)
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !groupVariable.value) {
    notificationStore.warning('缺少必要配置', '请先选择数据集和二分类分组变量。')
    return
  }
  if (!selectedContinuousVariables.value.length) {
    notificationStore.warning('请选择连续变量', '至少选择一个连续变量进行 T 检验。')
    return
  }
  isRunning.value = true
  try {
    ttestResult.value = await runTTest({
      dataset_id: selectedDatasetId.value,
      group_variable: groupVariable.value,
      continuous_variables: selectedContinuousVariables.value,
      alpha: alpha.value,
      confirm_independence: true,
    })
    notificationStore.success('T 检验已完成', '前提检查和检验结果已准备完成。')
  } catch (error: any) {
    console.error('Failed to run t test', error)
    notificationStore.error('T 检验失败', error.response?.data?.detail || '请稍后重试。')
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
