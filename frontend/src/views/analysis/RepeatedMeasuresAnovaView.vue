<template>
  <div class="space-y-6">
    <div class="panel-card bg-gradient-to-r from-slate-50 via-white to-cyan-50/60 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">混合设计重复测量方差分析</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        适用于长表数据。你可以指定 ID 变量、可选的组间分组变量、时间变量，以及一个或多个连续变量；系统会自动给出时间主效应、组间主效应与交互效应，并在需要时采用球形性校正。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">检验配置</h2>
            <p class="mt-1 text-xs text-gray-400">请按长表结构依次指定 ID、组间分组、时间变量和连续变量。</p>
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
              <label class="mb-1.5 block text-xs font-medium text-gray-500">ID 变量</label>
              <select v-model="subjectVariable" :disabled="!subjectVariableOptions.length" @change="handleStructureChange" class="tool-input">
                <option value="">请选择 ID 变量</option>
                <option v-for="column in subjectVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 个唯一值
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">同一受试者在不同时间点应复用同一个 ID。</p>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">组间分组变量（可选）</label>
              <select v-model="betweenVariable" :disabled="!betweenVariableOptions.length" @change="handleStructureChange" class="tool-input">
                <option value="">不设置组间分组变量</option>
                <option v-for="column in betweenVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">例如治疗组/对照组。若留空，则只分析时间主效应。</p>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">时间变量</label>
              <select v-model="timeVariable" :disabled="!timeVariableOptions.length" @change="handleStructureChange" class="tool-input">
                <option value="">请选择时间变量</option>
                <option v-for="column in timeVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 个水平
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">例如 baseline / month1 / month3，或 visit1 / visit2 / visit3。</p>
            </div>

            <div class="panel-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">连续变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">每个变量会单独拟合混合设计重复测量方差分析模型。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllContinuous">
                  {{ selectedContinuousVariables.length === continuousVariableOptions.length && continuousVariableOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="panel-card-tight mt-3 border-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ describeSelection(selectedContinuousVariables, continuousVariableOptions.length) }}</p>
                <div class="mt-2 grid max-h-48 grid-cols-2 gap-2 overflow-y-auto pr-1">
                  <label
                    v-for="column in continuousVariableOptions"
                    :key="column.name"
                    class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600"
                  >
                    <input
                      type="checkbox"
                      class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary"
                      :checked="selectedContinuousVariables.includes(column.name)"
                      @change="toggleVariable(column.name)"
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
              :disabled="isRunning || !selectedDatasetId || !subjectVariable || !timeVariable"
              class="tool-btn-primary w-full px-4 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
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
        <div class="panel-card p-5">
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

          <div v-if="analysisResult" class="mt-4 space-y-3 border-t border-slate-200 pt-3 text-[12px] leading-6 text-slate-500">
            <div
              v-for="item in analysisResult.variables"
              :key="`${item.variable}-note`"
              class="panel-subtle px-3 py-2.5"
            >
              <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span class="font-semibold text-slate-800">{{ item.variable }}</span>
                <span class="rounded-full bg-white px-2 py-0.5 text-[11px] text-slate-500">{{ item.executed_test }}</span>
              </div>
              <div class="mt-2 space-y-1.5">
                <p><span class="font-medium text-slate-700">样本处理：</span>{{ renderSampleSummary(item) }}</p>
                <p><span class="font-medium text-slate-700">残差正态性：</span>{{ renderResidualSummary(item) }}</p>
                <p><span class="font-medium text-slate-700">球形性检验：</span>{{ renderSphericitySummary(item) }}</p>
                <p><span class="font-medium text-slate-700">时间效应：</span>{{ renderEffectDetail(item.time_effect) }}</p>
                <p v-if="analysisResult.between_variable"><span class="font-medium text-slate-700">组间效应：</span>{{ renderEffectDetail(item.between_effect) }}</p>
                <p v-if="analysisResult.between_variable"><span class="font-medium text-slate-700">交互效应：</span>{{ renderEffectDetail(item.interaction_effect) }}</p>
                <p v-if="item.note"><span class="font-medium text-slate-700">说明：</span>{{ item.note }}</p>
              </div>
            </div>
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

function formatMeanSdOnly(mean: number | null, sd: number | null) {
  if (mean === null) return '-'
  if (sd === null) return mean.toFixed(1)
  return `${mean.toFixed(1)} ± ${sd.toFixed(1)}`
}

function renderResidualSummary(item: RepeatedMeasuresVariableResult) {
  const status = item.residual_normality_passed ? '通过' : '未通过'
  const statistic =
    item.residual_normality_statistic === null || item.residual_normality_statistic === undefined
      ? 'W=-'
      : `W=${formatNumber(item.residual_normality_statistic)}`
  return `${item.residual_normality_method}；${statistic}；P=${formatP(item.residual_normality_p_value)}；结果=${status}`
}

function renderSingleSphericity(
  label: string,
  statistic: number | null | undefined,
  pValue: number | null | undefined,
  passed: boolean | null | undefined,
  gg: number | null | undefined,
  hf: number | null | undefined,
) {
  if (pValue === null || pValue === undefined) {
    return `${label} 未提供检验结果`
  }

  const status = passed === null || passed === undefined ? '未判定' : passed ? '通过' : '未通过'
  const parts = [
    `${label} W=${formatNumber(statistic ?? null)}`,
    `P=${formatP(pValue)}`,
    `结果=${status}`,
  ]
  if (gg !== null && gg !== undefined) {
    parts.push(`GG ε=${formatNumber(gg)}`)
  }
  if (hf !== null && hf !== undefined) {
    parts.push(`HF ε=${formatNumber(hf)}`)
  }
  return parts.join('；')
}

function renderSphericitySummary(item: RepeatedMeasuresVariableResult) {
  const parts = [
    renderSingleSphericity(
      '时间',
      item.time_sphericity_statistic,
      item.time_sphericity_p_value,
      item.time_sphericity_passed,
      item.time_gg_epsilon,
      item.time_hf_epsilon,
    ),
  ]
  if (analysisResult.value?.between_variable) {
    parts.push(
      renderSingleSphericity(
        '时间×组间',
        item.interaction_sphericity_statistic,
        item.interaction_sphericity_p_value,
        item.interaction_sphericity_passed,
        item.interaction_gg_epsilon,
        item.interaction_hf_epsilon,
      ),
    )
  }
  return parts.join('； ')
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

function renderSampleSummary(item: RepeatedMeasuresVariableResult) {
  return `完整受试者 ${item.complete_subject_count}，剔除 ${item.excluded_subject_count}，重复记录均值处理 ${item.duplicate_pair_count} 次`
}

function renderEffectDetail(effect: RepeatedMeasuresEffectResult | null | undefined) {
  if (!effect) return '-'
  const statistic = effect.statistic === null || effect.statistic === undefined ? 'F=-' : `F=${formatNumber(effect.statistic)}`
  const df =
    effect.df_effect === null || effect.df_effect === undefined || effect.df_error === null || effect.df_error === undefined
      ? 'df=-'
      : `df=${formatNumber(effect.df_effect)}, ${formatNumber(effect.df_error)}`
  const correction = effect.corrected ? '；已采用 GG 校正' : ''
  return `${statistic}；${df}；P=${formatP(effect.p_value ?? null)}${correction}`
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

  const notes = analysisResult.value.variables.map(
    (item) =>
      `${item.variable}: 样本处理=${renderSampleSummary(item)} | 残差正态性=${renderResidualSummary(item)} | 球形性检验=${renderSphericitySummary(item)} | 时间效应=${renderEffectDetail(item.time_effect)}${analysisResult.value?.between_variable ? ` | 组间效应=${renderEffectDetail(item.between_effect)} | 交互效应=${renderEffectDetail(item.interaction_effect)}` : ''}${item.note ? ` | 说明=${item.note}` : ''}`,
  )

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
