<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-50 via-white to-cyan-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">混合设计重复测量方差分析</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        适用于长表数据。你可以指定 ID 变量、可选的组间分组变量、时间变量，以及一个或多个连续变量；系统会自动给出时间主效应、组间主效应与交互效应，并在需要时采用球形性校正。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">检验配置</h2>
            <p class="mt-1 text-xs text-gray-400">请按长表结构依次指定 ID、组间分组、时间变量和连续变量。</p>
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
              <label class="mb-1.5 block text-xs font-medium text-gray-500">ID 变量</label>
              <select v-model="subjectVariable" :disabled="!subjectVariableOptions.length" @change="handleStructureChange" class="input-field py-2.5 text-sm">
                <option value="">请选择 ID 变量</option>
                <option v-for="column in subjectVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 个唯一值
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">同一受试者在不同时间点应复用同一个 ID。</p>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">组间分组变量（可选）</label>
              <select v-model="betweenVariable" :disabled="!betweenVariableOptions.length" @change="handleStructureChange" class="input-field py-2.5 text-sm">
                <option value="">不设置组间分组变量</option>
                <option v-for="column in betweenVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">例如治疗组/对照组。若留空，则只分析时间主效应。</p>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">时间变量</label>
              <select v-model="timeVariable" :disabled="!timeVariableOptions.length" @change="handleStructureChange" class="input-field py-2.5 text-sm">
                <option value="">请选择时间变量</option>
                <option v-for="column in timeVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 个水平
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">例如 baseline / month1 / month3，或 visit1 / visit2 / visit3。</p>
            </div>

            <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">连续变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">每个变量会单独拟合混合设计重复测量方差分析模型。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllContinuous">
                  {{ selectedContinuousVariables.length === continuousVariableOptions.length && continuousVariableOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="mt-3 rounded-lg border border-white bg-white p-2.5">
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
              <select v-model.number="alpha" class="input-field py-2.5 text-sm">
                <option :value="0.05">0.05</option>
                <option :value="0.01">0.01</option>
              </select>
            </div>

            <button @click="runAnalysis" :disabled="isRunning || !selectedDatasetId || !subjectVariable || !timeVariable" class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50">
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isRunning ? '检验中...' : '运行重复测量方差分析' }}
            </button>
          </div>
        </div>
      </div>

      <div class="xl:col-span-8">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex flex-col gap-3 border-b border-slate-200 pb-4">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">结果报告</h2>
                <p class="mt-1 text-xs text-gray-400">三线表主体聚焦时间点指标分布；统计过程、效应检验和假设检查统一放在表格下方小字备注。</p>
              </div>
              <div class="flex items-center gap-2">
                <span v-if="analysisResult" class="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-600">
                  {{ analysisResult.dataset_name }} · 时间 {{ analysisResult.time_variable }}
                </span>
                <button
                  v-if="analysisResult"
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
            </div>

            <div v-if="analysisResult" class="flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-slate-500">
              <span>ID：{{ analysisResult.subject_variable }}</span>
              <span>组间变量：{{ analysisResult.between_variable || '未设置' }}</span>
              <span>时间水平：{{ analysisResult.time_levels.join(' / ') }}</span>
              <span v-if="analysisResult.between_levels.length">组别：{{ analysisResult.between_levels.join(' / ') }}</span>
            </div>
          </div>

          <div v-if="analysisResult" class="mt-4 overflow-x-auto">
            <table class="rm-table min-w-full text-sm">
              <thead>
                <tr>
                  <th rowspan="2">项目</th>
                  <th rowspan="2">组别</th>
                  <th rowspan="2">n</th>
                  <th :colspan="analysisResult.time_levels.length">时间点</th>
                  <th colspan="2">时间</th>
                  <th v-if="analysisResult.between_variable" colspan="2">组间</th>
                  <th v-if="analysisResult.between_variable" colspan="2">时间 × 组间</th>
                </tr>
                <tr>
                  <th v-for="timeLevel in analysisResult.time_levels" :key="`time-${timeLevel}`">{{ timeLevel }}</th>
                  <th>F 值</th>
                  <th>P 值</th>
                  <template v-if="analysisResult.between_variable">
                    <th>F 值</th>
                    <th>P 值</th>
                    <th>F 值</th>
                    <th>P 值</th>
                  </template>
                </tr>
              </thead>
              <tbody>
                <template v-for="item in analysisResult.variables" :key="item.variable">
                  <tr v-for="(groupLevel, rowIndex) in getDisplayGroups()" :key="`${item.variable}-${groupLevel}`">
                    <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length" class="font-semibold text-slate-900">{{ item.variable }}</td>
                    <td>{{ groupLevel }}</td>
                    <td>{{ getGroupN(item, groupLevel) }}</td>
                    <td v-for="timeLevel in analysisResult.time_levels" :key="`${item.variable}-${groupLevel}-${timeLevel}`">
                      {{ renderTimeCell(item, timeLevel, groupLevel) }}
                    </td>
                    <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatEffectStatistic(item.time_effect) }}</td>
                    <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatP(item.time_effect?.p_value ?? null) }}</td>
                    <template v-if="analysisResult.between_variable">
                      <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatEffectStatistic(item.between_effect) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatP(item.between_effect?.p_value ?? null) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatEffectStatistic(item.interaction_effect) }}</td>
                      <td v-if="rowIndex === 0" :rowspan="getDisplayGroups().length">{{ formatP(item.interaction_effect?.p_value ?? null) }}</td>
                    </template>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            运行后，这里会以三线表形式紧凑展示混合设计重复测量方差分析结果。
          </div>

          <div v-if="analysisResult" class="mt-4 border-t border-slate-200 pt-3 space-y-2 text-[12px] leading-6 text-slate-500">
            <p v-for="item in analysisResult.variables" :key="`${item.variable}-note`">
              <span class="font-medium text-slate-700">{{ item.variable }}</span>：
              {{ renderResultNotes(item) }}
            </p>
            <div class="pt-1 text-[11px] text-slate-400">
              <p v-for="(item, index) in analysisResult.assumptions" :key="`assumption-${index}`">{{ item }}</p>
            </div>
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
  runRepeatedMeasuresAnova,
  type DatasetItem,
  type DatasetSummaryResponse,
  type RepeatedMeasuresEffectResult,
  type RepeatedMeasuresResponse,
  type RepeatedMeasuresVariableResult,
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
const subjectVariable = ref('')
const betweenVariable = ref('')
const timeVariable = ref('')
const selectedContinuousVariables = ref<string[]>([])
const alpha = ref(0.05)
const loadingDatasets = ref(true)
const isRunning = ref(false)
const analysisResult = ref<RepeatedMeasuresResponse | null>(null)
const copiedResult = ref(false)
let copyFeedbackTimer: number | null = null

const subjectVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.name !== betweenVariable.value && column.name !== timeVariable.value && column.kind !== 'datetime' && column.unique_count >= 2,
  ),
)

const betweenVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) =>
      column.name !== subjectVariable.value &&
      column.name !== timeVariable.value &&
      (column.kind === 'categorical' || column.kind === 'boolean') &&
      column.unique_count >= 2 &&
      column.unique_count <= 4,
  ),
)

const timeVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) =>
      column.name !== subjectVariable.value &&
      column.name !== betweenVariable.value &&
      ['categorical', 'boolean', 'datetime'].includes(column.kind) &&
      column.unique_count >= 2 &&
      column.unique_count <= 6,
  ),
)

const continuousVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) =>
      column.kind === 'numeric' &&
      column.name !== subjectVariable.value &&
      column.name !== betweenVariable.value &&
      column.name !== timeVariable.value,
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

function formatMeanSdOnly(mean: number | null, sd: number | null) {
  if (mean === null) return '-'
  if (sd === null) return mean.toFixed(1)
  return `${mean.toFixed(1)} ± ${sd.toFixed(1)}`
}

function renderEffect(effect: RepeatedMeasuresEffectResult | null | undefined) {
  if (!effect || effect.p_value === null || effect.p_value === undefined) return '-'
  const statistic = effect.statistic === null || effect.statistic === undefined ? '-' : effect.statistic.toFixed(3)
  const df1 = effect.df_effect === null || effect.df_effect === undefined ? '-' : effect.df_effect.toFixed(2)
  const df2 = effect.df_error === null || effect.df_error === undefined ? '-' : effect.df_error.toFixed(2)
  const suffix = effect.corrected ? ' · GG校正' : ''
  return `F=${statistic}; df=${df1},${df2}; P=${formatP(effect.p_value)}${suffix}`
}

function renderNormality(item: RepeatedMeasuresVariableResult) {
  const status = item.residual_normality_passed ? '通过' : '未通过'
  return `${status}; P=${formatP(item.residual_normality_p_value)}`
}

function renderSphericity(item: RepeatedMeasuresVariableResult) {
  const timePart =
    item.time_sphericity_p_value === null || item.time_sphericity_p_value === undefined
      ? '时间: -'
      : `时间: ${formatP(item.time_sphericity_p_value)}`
  if (!analysisResult.value?.between_variable) {
    return timePart
  }
  const interactionPart =
    item.interaction_sphericity_p_value === null || item.interaction_sphericity_p_value === undefined
      ? '交互: -'
      : `交互: ${formatP(item.interaction_sphericity_p_value)}`
  return `${timePart}; ${interactionPart}`
}

function getTimeCellSummaries(item: RepeatedMeasuresVariableResult, timeLevel: string) {
  return item.time_summaries.filter((summary) => summary.time_level === timeLevel)
}

function getDisplayGroups() {
  if (analysisResult.value?.between_levels.length) {
    return analysisResult.value.between_levels
  }
  return ['总体']
}

function getGroupSummaries(item: RepeatedMeasuresVariableResult, groupLevel: string) {
  if (!analysisResult.value?.between_variable) {
    return item.time_summaries.filter((summary) => !summary.group_level)
  }
  return item.time_summaries.filter((summary) => summary.group_level === groupLevel)
}

function getGroupN(item: RepeatedMeasuresVariableResult, groupLevel: string) {
  const firstSummary = getGroupSummaries(item, groupLevel)[0]
  if (!firstSummary) return '-'
  return firstSummary.n
}

function renderTimeCell(item: RepeatedMeasuresVariableResult, timeLevel: string, groupLevel: string) {
  const summary = getGroupSummaries(item, groupLevel).find((entry) => entry.time_level === timeLevel)
  if (!summary) return '-'
  return formatMeanSdOnly(summary.mean, summary.sd)
}

function formatEffectStatistic(effect: RepeatedMeasuresEffectResult | null | undefined) {
  if (!effect || effect.statistic === null || effect.statistic === undefined) return '-'
  return effect.statistic.toFixed(2)
}

function renderDfNote(label: string, effect: RepeatedMeasuresEffectResult | null | undefined) {
  if (!effect || effect.df_effect === null || effect.df_effect === undefined || effect.df_error === null || effect.df_error === undefined) {
    return `${label}df=-`
  }
  return `${label}df=${formatNumber(effect.df_effect)},${formatNumber(effect.df_error)}`
}

function renderResultNotes(item: RepeatedMeasuresVariableResult) {
  const parts = [
    `${item.executed_test}`,
    `完整受试者 ${item.complete_subject_count}，剔除 ${item.excluded_subject_count}，重复记录取均值 ${item.duplicate_pair_count}`,
    `残差正态性 ${renderNormality(item)}`,
    `球形性 ${renderSphericity(item)}`,
    renderDfNote('时间', item.time_effect),
  ]
  if (analysisResult.value?.between_variable) {
    parts.push(renderDfNote('组间', item.between_effect))
    parts.push(renderDfNote('交互', item.interaction_effect))
  }
  if (item.note) {
    parts.push(item.note)
  }
  return parts.join('；')
}

function buildResultTableText() {
  if (!analysisResult.value) return ''
  const headers = [
    '项目',
    '组别',
    'n',
    ...analysisResult.value.time_levels,
    '时间 F值',
    '时间 P值',
    ...(analysisResult.value.between_variable ? ['组间 F值', '组间 P值', '时间×组间 F值', '时间×组间 P值'] : []),
  ]
  const rows = analysisResult.value.variables.flatMap((item) =>
    getDisplayGroups().map((groupLevel, rowIndex) =>
      [
        rowIndex === 0 ? item.variable : '',
        groupLevel,
        String(getGroupN(item, groupLevel)),
        ...analysisResult.value!.time_levels.map((timeLevel) => renderTimeCell(item, timeLevel, groupLevel)),
        rowIndex === 0 ? formatEffectStatistic(item.time_effect) : '',
        rowIndex === 0 ? formatP(item.time_effect?.p_value ?? null) : '',
        ...(analysisResult.value!.between_variable
          ? [
              rowIndex === 0 ? formatEffectStatistic(item.between_effect) : '',
              rowIndex === 0 ? formatP(item.between_effect?.p_value ?? null) : '',
              rowIndex === 0 ? formatEffectStatistic(item.interaction_effect) : '',
              rowIndex === 0 ? formatP(item.interaction_effect?.p_value ?? null) : '',
            ]
          : []),
      ].join('\t'),
    ),
  )
  const notes = analysisResult.value.variables.map((item) => `${item.variable}: ${renderResultNotes(item)}`)
  return [headers.join('\t'), ...rows, '', '备注', ...notes].join('\n')
}

async function copyResultTable() {
  if (!analysisResult.value) return
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
    console.error('Failed to copy repeated measures table', err)
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
    notificationStore.error('数据集加载失败', '无法加载混合设计重复测量分析所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  subjectVariable.value = ''
  betweenVariable.value = ''
  timeVariable.value = ''
  selectedContinuousVariables.value = []
  analysisResult.value = null
  void loadSummary()
}

function handleStructureChange() {
  selectedContinuousVariables.value = selectedContinuousVariables.value.filter(
    (name) => name !== subjectVariable.value && name !== betweenVariable.value && name !== timeVariable.value,
  )
  analysisResult.value = null
}

function toggleVariable(variable: string) {
  analysisResult.value = null
  if (selectedContinuousVariables.value.includes(variable)) {
    selectedContinuousVariables.value = selectedContinuousVariables.value.filter((name) => name !== variable)
    return
  }
  selectedContinuousVariables.value = [...selectedContinuousVariables.value, variable]
}

function toggleAllContinuous() {
  analysisResult.value = null
  if (selectedContinuousVariables.value.length === continuousVariableOptions.value.length) {
    selectedContinuousVariables.value = []
    return
  }
  selectedContinuousVariables.value = continuousVariableOptions.value.map((column) => column.name)
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !subjectVariable.value || !timeVariable.value) {
    notificationStore.warning('缺少必要配置', '请先选择数据集、ID 变量和时间变量。')
    return
  }
  if (!selectedContinuousVariables.value.length) {
    notificationStore.warning('请选择连续变量', '至少选择一个连续变量进行重复测量分析。')
    return
  }
  isRunning.value = true
  try {
    analysisResult.value = await runRepeatedMeasuresAnova({
      dataset_id: selectedDatasetId.value,
      subject_variable: subjectVariable.value,
      between_variable: betweenVariable.value || null,
      time_variable: timeVariable.value,
      continuous_variables: selectedContinuousVariables.value,
      alpha: alpha.value,
      confirm_repeated_design: true,
    })
    notificationStore.success('重复测量分析已完成', '已生成紧凑的结果表格。')
  } catch (error: any) {
    console.error('Failed to run repeated measures anova', error)
    notificationStore.error('重复测量分析失败', error.response?.data?.detail || '请稍后重试。')
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
.rm-table {
  border-top: 1.5px solid #0f172a;
  border-bottom: 1.5px solid #0f172a;
  border-collapse: collapse;
}

.rm-table thead tr {
  border-bottom: 1px solid #cbd5e1;
}

.rm-table th,
.rm-table td {
  padding: 12px 10px;
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid #eef2f7;
}

.rm-table tbody tr:last-child td {
  border-bottom: none;
}

.rm-table th {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.rm-table td {
  color: #334155;
  line-height: 1.55;
}
</style>
