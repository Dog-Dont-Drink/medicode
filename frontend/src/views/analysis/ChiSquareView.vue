<template>
  <div class="space-y-6">
    <div class="panel-card bg-gradient-to-r from-slate-50 via-white to-amber-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">卡方检验</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        适用于 2 到 4 组独立样本的分类变量比较。系统会先构建列联表并检查期望频数；若不满足 Pearson 卡方检验前提，会自动切换到 Fisher 精确概率法，并继续返回可直接阅读的分布结果。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">检验配置</h2>
            <p class="mt-1 text-xs text-gray-400">先选择数据集和分组变量，再勾选要比较的分类变量。</p>
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
              <label class="mb-1.5 block text-xs font-medium text-gray-500">分组变量</label>
              <select v-model="groupVariable" :disabled="!groupVariableOptions.length" @change="handleGroupVariableChange" class="tool-input">
                <option value="">请选择 2-4 组变量</option>
                <option v-for="column in groupVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">卡方检验支持 2 到 4 组分组变量。</p>
            </div>

            <div class="panel-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">分类变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">期望频数不足时会自动切换到 Fisher 精确概率法。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllCategorical">
                  {{ selectedCategoricalVariables.length === categoricalVariableOptions.length && categoricalVariableOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="panel-card-tight mt-3 border-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ describeSelection(selectedCategoricalVariables, categoricalVariableOptions.length, '分类变量') }}</p>
                <div class="mt-2 grid max-h-48 grid-cols-2 gap-2 overflow-y-auto pr-1">
                  <label v-for="column in categoricalVariableOptions" :key="column.name" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                    <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="selectedCategoricalVariables.includes(column.name)" @change="toggleVariable(column.name)" />
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
              {{ isRunning ? '检验中...' : '运行卡方检验' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">前提检查</h2>
            <p class="mt-1 text-xs text-gray-400">这里会显示当前分组结构、已检验变量数以及卡方/Fisher 的判断依据。</p>
          </div>

          <div v-if="chiSquareResult" class="mt-5 space-y-4">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <div class="panel-card border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
                <p class="mt-2 text-sm font-semibold text-gray-900">{{ chiSquareResult.dataset_name }}</p>
                <p class="mt-1 text-xs text-gray-500">分组变量：{{ chiSquareResult.group_variable }}</p>
              </div>
              <div class="panel-card border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">组别</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ chiSquareResult.group_levels.length }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ chiSquareResult.group_levels.join(' / ') }}</p>
              </div>
              <div class="panel-card border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">已检验变量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ chiSquareResult.variables.length }}</p>
                <p class="mt-1 text-xs text-gray-500">alpha = {{ chiSquareResult.alpha }}</p>
              </div>
            </div>

            <div class="panel-subtle p-4">
              <div class="grid gap-2">
                <div v-for="(item, index) in chiSquareResult.assumptions" :key="index" class="flex items-start gap-2 text-sm text-gray-600">
                  <span class="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-primary"></span>
                  <span>{{ item }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行卡方检验后，系统会在这里总结当前数据是否满足卡方前提。
          </div>
        </div>

        <div class="panel-card p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">检验结果</h2>
              <p class="mt-1 text-xs text-gray-400">结果按三线表汇总呈现；列联表分布和方法备注放在表格下方的小字说明中。</p>
            </div>
            <button
              v-if="chiSquareResult"
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

          <div v-if="chiSquareResult" class="mt-5 space-y-4">
            <div class="overflow-x-auto">
              <table class="result-table min-w-full text-sm">
                <thead>
                  <tr>
                    <th>变量</th>
                    <th>水平</th>
                    <th v-for="group in chiSquareResult.group_levels" :key="`head-${group}`">{{ group }}</th>
                    <th>执行方法</th>
                    <th>最小期望频数</th>
                    <th>统计量</th>
                    <th>自由度</th>
                    <th>P 值</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="item in chiSquareResult.variables" :key="item.variable">
                    <tr v-for="(row, rowIndex) in item.level_rows" :key="`${item.variable}-${row.level}`">
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length" class="font-semibold text-slate-900">{{ item.variable }}</td>
                      <td>{{ row.level }}</td>
                      <td v-for="(value, valueIndex) in row.group_values" :key="`${item.variable}-${row.level}-${valueIndex}`">{{ value }}</td>
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length">{{ item.executed_test }}</td>
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length">{{ formatNumber(item.minimum_expected_count) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length">{{ formatNumber(item.statistic) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length">{{ formatNumber(item.df) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="item.level_rows.length">{{ formatP(item.p_value) }}</td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <div class="space-y-1.5 text-[12px] leading-6 text-slate-500">
              <p v-for="item in chiSquareResult.variables" :key="`${item.variable}-note`">
                <span class="font-medium text-slate-700">{{ item.variable }}</span>：
                {{ item.note }}
              </p>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行后，这里会逐变量展示 Pearson 卡方或 Fisher 精确检验结果。
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
  runChiSquare,
  type ChiSquareResponse,
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
const selectedCategoricalVariables = ref<string[]>([])
const alpha = ref(0.05)
const loadingDatasets = ref(true)
const isRunning = ref(false)
const chiSquareResult = ref<ChiSquareResponse | null>(null)
const copiedResult = ref(false)
let copyFeedbackTimer: number | null = null

const groupVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => (column.kind === 'categorical' || column.kind === 'boolean') && column.unique_count >= 2 && column.unique_count <= 4,
  ),
)

const categoricalVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => (column.kind === 'categorical' || column.kind === 'boolean') && column.name !== groupVariable.value,
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

function buildResultTableText() {
  if (!chiSquareResult.value) return ''
  const headers = ['变量', '水平', ...chiSquareResult.value.group_levels, '执行方法', '最小期望频数', '统计量', '自由度', 'P 值']
  const rows = chiSquareResult.value.variables.flatMap((item) =>
    item.level_rows.map((row, rowIndex) =>
      [
        rowIndex === 0 ? item.variable : '',
        row.level,
        ...row.group_values,
        rowIndex === 0 ? item.executed_test : '',
        rowIndex === 0 ? formatNumber(item.minimum_expected_count) : '',
        rowIndex === 0 ? formatNumber(item.statistic) : '',
        rowIndex === 0 ? formatNumber(item.df) : '',
        rowIndex === 0 ? formatP(item.p_value) : '',
      ].join('\t'),
    ),
  )
  const notes = chiSquareResult.value.variables.map((item) => `${item.variable}: ${item.note}`)
  return [headers.join('\t'), ...rows, '', '备注', ...notes].join('\n')
}

async function copyResultTable() {
  if (!chiSquareResult.value) return
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
    console.error('Failed to copy chi-square table', err)
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
    selectedCategoricalVariables.value = selectedCategoricalVariables.value.filter((name) =>
      datasetSummary.value?.columns.some((column) => column.name === name && (column.kind === 'categorical' || column.kind === 'boolean')),
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
    notificationStore.error('数据集加载失败', '无法加载卡方检验所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  groupVariable.value = ''
  selectedCategoricalVariables.value = []
  chiSquareResult.value = null
  void loadSummary()
}

function handleGroupVariableChange() {
  selectedCategoricalVariables.value = selectedCategoricalVariables.value.filter((name) => name !== groupVariable.value)
  chiSquareResult.value = null
}

function toggleVariable(variable: string) {
  chiSquareResult.value = null
  if (selectedCategoricalVariables.value.includes(variable)) {
    selectedCategoricalVariables.value = selectedCategoricalVariables.value.filter((name) => name !== variable)
    return
  }
  selectedCategoricalVariables.value = [...selectedCategoricalVariables.value, variable]
}

function toggleAllCategorical() {
  chiSquareResult.value = null
  if (selectedCategoricalVariables.value.length === categoricalVariableOptions.value.length) {
    selectedCategoricalVariables.value = []
    return
  }
  selectedCategoricalVariables.value = categoricalVariableOptions.value.map((column) => column.name)
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !groupVariable.value) {
    notificationStore.warning('缺少必要配置', '请先选择数据集和分组变量。')
    return
  }
  if (!selectedCategoricalVariables.value.length) {
    notificationStore.warning('请选择分类变量', '至少选择一个分类变量进行卡方检验。')
    return
  }
  isRunning.value = true
  try {
    chiSquareResult.value = await runChiSquare({
      dataset_id: selectedDatasetId.value,
      group_variable: groupVariable.value,
      categorical_variables: selectedCategoricalVariables.value,
      alpha: alpha.value,
      confirm_independence: true,
    })
    notificationStore.success('卡方检验已完成', '列联表与检验结果已准备完成。')
  } catch (error: any) {
    console.error('Failed to run chi-square test', error)
    notificationStore.error('卡方检验失败', error.response?.data?.detail || '请稍后重试。')
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
