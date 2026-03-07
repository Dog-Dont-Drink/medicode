<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-50 via-white to-emerald-50/50 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">基线特征</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">
        自动生成基线特征表。系统会按分组变量自动选择组间比较方法，并输出符合 SCI 阅读习惯的三线表预览，同时支持导出 Excel。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">分析配置</h2>
            <p class="mt-1 text-xs text-gray-400">先选数据集和分组变量，再勾选需要进入基线表的变量。</p>
          </div>

          <div class="mt-5 space-y-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">数据集</label>
              <select v-model="selectedDatasetId" @change="handleDatasetChange" :disabled="loadingDatasets" class="input-field py-2.5 text-sm">
                <option value="">请选择数据集</option>
                <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} · {{ dataset.projectName }}
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">分组变量</label>
              <select v-model="groupVariable" @change="handleGroupVariableChange" :disabled="!datasetSummary || !groupVariableOptions.length" class="input-field py-2.5 text-sm">
                <option value="">请选择分组变量</option>
                <option v-for="column in groupVariableOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ column.unique_count }} 组
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">仅支持 2 到 4 组的分组变量。</p>
            </div>

            <div class="grid grid-cols-1 gap-4">
              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold text-gray-700">连续变量</p>
                    <p class="mt-1 text-[11px] text-gray-400">正态变量用 t 检验 / 方差分析，非正态变量按组数自动匹配非参数检验。</p>
                  </div>
                  <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllContinuous">
                    {{ selectedContinuousVariables.length === continuousVariableOptions.length && continuousVariableOptions.length ? '清空' : '全选' }}
                  </button>
                </div>
                <div class="mt-3 rounded-lg border border-white bg-white p-2.5">
                  <p class="text-[11px] text-gray-500">{{ describeSelection(selectedContinuousVariables, continuousVariableOptions.length, '连续变量') }}</p>
                  <div class="mt-2 grid max-h-40 grid-cols-2 gap-2 overflow-y-auto pr-1">
                    <label v-for="column in continuousVariableOptions" :key="column.name" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                      <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="selectedContinuousVariables.includes(column.name)" @change="toggleVariable('continuous', column.name)" />
                      <span class="truncate">{{ column.name }}</span>
                    </label>
                  </div>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold text-gray-700">分类变量</p>
                    <p class="mt-1 text-[11px] text-gray-400">低期望频数时自动切换精确检验，RxC 由 R 的 fisher.test 计算。</p>
                  </div>
                  <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllCategorical">
                    {{ selectedCategoricalVariables.length === categoricalVariableOptions.length && categoricalVariableOptions.length ? '清空' : '全选' }}
                  </button>
                </div>
                <div class="mt-3 rounded-lg border border-white bg-white p-2.5">
                  <p class="text-[11px] text-gray-500">{{ describeSelection(selectedCategoricalVariables, categoricalVariableOptions.length, '分类变量') }}</p>
                  <div class="mt-2 grid max-h-40 grid-cols-2 gap-2 overflow-y-auto pr-1">
                    <label v-for="column in categoricalVariableOptions" :key="column.name" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                      <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="selectedCategoricalVariables.includes(column.name)" @change="toggleVariable('categorical', column.name)" />
                      <span class="truncate">{{ column.name }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">保留小数位</label>
              <select v-model.number="decimals" @change="markPreviewStale" class="input-field py-2.5 text-sm">
                <option :value="1">1 位</option>
                <option :value="2">2 位</option>
                <option :value="3">3 位</option>
              </select>
            </div>

            <button @click="generatePreview" :disabled="isGenerating || !selectedDatasetId || !groupVariable" class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50">
              <svg v-if="isGenerating" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isGenerating ? '生成中...' : '生成基线特征' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">分析摘要</h2>
            <p class="mt-1 text-xs text-gray-400">自动识别分组数量、正态性和比较方法，适合直接整理进论文基线表。</p>
          </div>

          <div v-if="tableOneResult" class="mt-5 space-y-4">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
                <p class="mt-2 text-sm font-semibold text-gray-900">{{ tableOneResult.dataset_name }}</p>
                <p class="mt-1 text-xs text-gray-500">分组变量：{{ tableOneResult.group_variable }}</p>
              </div>
              <div class="rounded-2xl border border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">组别</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ tableOneResult.group_levels.length }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ tableOneResult.group_levels.join(' / ') }}</p>
              </div>
              <div class="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">连续变量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ tableOneResult.continuous_variables.length }}</p>
                <p class="mt-1 text-xs text-gray-500">非正态 {{ tableOneResult.nonnormal_variables.length }} 个</p>
              </div>
              <div class="rounded-2xl border border-amber-200 bg-amber-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">分类变量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ tableOneResult.categorical_variables.length }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ selectedVariableCount }} 个变量进入基线表</p>
              </div>
            </div>

            <div class="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
              <div class="flex flex-wrap gap-2">
                <span class="inline-flex rounded-full border border-white bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm">
                  正态性检验：{{ tableOneResult.normality_method }}
                </span>
                <span class="inline-flex rounded-full border border-white bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm">
                  正态连续变量：Welch t 检验 / 单因素方差分析
                </span>
                <span class="inline-flex rounded-full border border-white bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm">
                  非正态连续变量：2 组用 Mann-Whitney U，3-4 组用 Kruskal-Wallis
                </span>
                <span class="inline-flex rounded-full border border-white bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm">
                  分类变量：卡方检验；低期望频数时 2x2 / RxC 均用 Fisher 精确检验
                </span>
              </div>
              <p v-if="tableOneResult.nonnormal_variables.length" class="mt-3 text-xs text-gray-500">
                非正态变量：{{ tableOneResult.nonnormal_variables.join('、') }}
              </p>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            选择数据集、分组变量和统计变量后，系统会在这里生成基线特征摘要。
          </div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">基线特征预览</h2>
              <p class="mt-1 text-xs text-gray-400">按论文三线表风格展示，可直接用于论文基线特征整理。</p>
            </div>
          </div>

          <div v-if="tableOneResult" class="mt-5">
            <div class="overflow-x-auto">
              <table class="three-line-table min-w-full text-sm">
                <thead>
                  <tr>
                    <th v-for="header in tableOneResult.headers" :key="header" class="px-3 py-2.5 text-left font-semibold text-gray-700">
                      {{ header }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in tableOneResult.rows" :key="rowIndex">
                    <td
                      v-for="(cell, cellIndex) in row"
                      :key="`${rowIndex}-${cellIndex}`"
                      :class="[
                        'px-3 py-2 align-top text-gray-700',
                        cellIndex === 0 ? 'font-medium text-gray-900' : '',
                        cellIndex === 1 && cell ? 'pl-6 text-gray-500' : '',
                      ]"
                    >
                      {{ cell }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
              <div class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 px-3 py-2">
                <div class="relative inline-flex rounded-full bg-white p-1 shadow-sm">
                  <span
                    class="absolute top-1 h-8 w-[4.75rem] rounded-full bg-emerald-500 transition-transform duration-200"
                    :class="interpretationLanguage === 'zh' ? 'translate-x-0' : 'translate-x-[4.75rem]'"
                  />
                  <button
                    type="button"
                    class="relative z-10 inline-flex h-8 w-[4.75rem] items-center justify-center rounded-full text-xs font-semibold transition-colors"
                    :class="interpretationLanguage === 'zh' ? 'text-white' : 'text-slate-500'"
                    @click="setInterpretationLanguage('zh')"
                  >
                    中文
                  </button>
                  <button
                    type="button"
                    class="relative z-10 inline-flex h-8 w-[4.75rem] items-center justify-center rounded-full text-xs font-semibold transition-colors"
                    :class="interpretationLanguage === 'en' ? 'text-white' : 'text-slate-500'"
                    @click="setInterpretationLanguage('en')"
                  >
                    English
                  </button>
                </div>

                <button
                  @click="interpretResult"
                  :disabled="isInterpreting"
                  class="inline-flex h-10 items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 text-sm font-semibold text-amber-700 transition-colors hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3L13.8 8.2L19 10L13.8 11.8L12 17L10.2 11.8L5 10L10.2 8.2L12 3Z" />
                    <path d="M19 16L19.9 18.1L22 19L19.9 19.9L19 22L18.1 19.9L16 19L18.1 18.1L19 16Z" />
                  </svg>
                  {{ isInterpreting ? '解读中...' : 'AI结果解读' }}
                </button>
              </div>

              <button
                @click="downloadExcel"
                :disabled="isDownloading"
                class="inline-flex h-10 items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 text-sm font-semibold text-emerald-700 transition-colors hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 3V15" />
                  <path d="M7 10L12 15L17 10" />
                  <path d="M5 21H19" />
                </svg>
                {{ isDownloading ? '下载中...' : '下载 Excel' }}
              </button>
            </div>

            <div class="mt-4 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-semibold text-slate-900">AI结果解读</p>
                    <span class="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                      高级功能
                    </span>
                  </div>
                  <p class="mt-1 text-xs leading-5 text-slate-500">
                    依据当前三线表自动生成论文级结果段落，适合直接作为 Results 初稿。
                  </p>
                </div>
                <p class="text-[11px] text-slate-400">
                  {{ interpretationLanguage === 'zh' ? '输出语言：中文' : 'Output: English' }}
                </p>
              </div>

              <div
                v-if="isInterpreting"
                class="mt-4 rounded-2xl border border-white bg-white/90 px-4 py-4 shadow-sm"
              >
                <div class="flex items-center gap-3">
                  <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                    <svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                      <path d="M21 12a9 9 0 1 1-3.47-7.09" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-slate-900">AI 正在整理结果描述</p>
                    <p class="mt-1 text-xs text-slate-500">根据当前基线特征提炼论文式 Results 段落，请稍候。</p>
                  </div>
                </div>
                <div class="mt-4 space-y-2.5">
                  <div class="h-3 w-full animate-pulse rounded-full bg-slate-100"></div>
                  <div class="h-3 w-11/12 animate-pulse rounded-full bg-slate-100"></div>
                  <div class="h-3 w-10/12 animate-pulse rounded-full bg-slate-100"></div>
                  <div class="h-3 w-8/12 animate-pulse rounded-full bg-slate-100"></div>
                </div>
              </div>
              <div v-else-if="interpretationContent" class="mt-4 rounded-2xl border border-white bg-white/90 px-4 py-3 shadow-sm">
                <div class="relative">
                  <p class="whitespace-pre-line pr-12 text-sm leading-7 text-slate-700">{{ interpretationContent }}</p>
                  <button
                    type="button"
                    class="absolute bottom-0 right-0 inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 transition-colors hover:border-primary/30 hover:text-primary"
                    @click="copyInterpretation"
                    :aria-label="copiedInterpretation ? '已复制结果解读' : '复制结果解读'"
                    :title="copiedInterpretation ? '已复制' : '复制到剪切板'"
                  >
                    <svg v-if="copiedInterpretation" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 6L9 17L4 12" />
                    </svg>
                    <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <path d="M5 15V6a2 2 0 0 1 2-2h9" />
                    </svg>
                  </button>
                </div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span v-if="interpretationBilledTokens" class="inline-flex rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] text-emerald-700">
                    本次消耗 {{ interpretationBilledTokens }} tokens
                  </span>
                  <span v-if="interpretationRemainingBalance !== null" class="inline-flex rounded-full bg-amber-50 px-2.5 py-1 text-[11px] text-amber-700">
                    剩余 {{ interpretationRemainingBalance }} tokens
                  </span>
                  <span v-if="interpretationSavedAt" class="inline-flex rounded-full bg-sky-50 px-2.5 py-1 text-[11px] text-sky-700">
                    已保存 {{ new Date(interpretationSavedAt).toLocaleString() }}
                  </span>
                </div>
                
              </div>
              <div v-else class="mt-4 rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-5 text-sm text-slate-400">
                生成基线特征后，可在此调用 AI结果解读，输出适合论文 Results 部分的描述段落。
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            生成基线特征后，这里会显示三线表预览。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  downloadTableOneExcel,
  generateTableOne,
  getSavedTableOneInterpretation,
  getDatasetSummary,
  getDatasets,
  getProjects,
  interpretTableOne,
  type DatasetItem,
  type DatasetSummaryResponse,
  type TableOneResponse,
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

const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const PAID_SUBSCRIPTIONS = new Set(['basic', 'pro', 'enterprise'])
const TABLEONE_STATE_KEY = 'descriptive_table1_state_v1'

const datasetOptions = ref<DatasetOption[]>([])
const selectedDatasetId = ref('')
const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const groupVariable = ref('')
const selectedContinuousVariables = ref<string[]>([])
const selectedCategoricalVariables = ref<string[]>([])
const decimals = ref(1)
const tableOneResult = ref<TableOneResponse | null>(null)
const interpretationLanguage = ref<'zh' | 'en'>('zh')
const interpretationContent = ref('')
const interpretationModel = ref('')
const interpretationActualTokens = ref(0)
const interpretationBilledTokens = ref(0)
const interpretationRemainingBalance = ref<number | null>(null)
const interpretationSavedAt = ref('')
const copiedInterpretation = ref(false)

const loadingDatasets = ref(true)
const isGenerating = ref(false)
const isDownloading = ref(false)
const isInterpreting = ref(false)

let copyFeedbackTimer: number | null = null

const selectedVariableCount = computed(
  () => selectedContinuousVariables.value.length + selectedCategoricalVariables.value.length,
)
const canUseAiInterpretation = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))

const groupVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.kind !== 'datetime' && column.unique_count >= 2 && column.unique_count <= 4,
  ),
)

const continuousVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.kind === 'numeric' && column.name !== groupVariable.value,
  ),
)

const categoricalVariableOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) =>
      (column.kind === 'categorical' || column.kind === 'boolean') &&
      column.name !== groupVariable.value &&
      column.unique_count >= 2 &&
      column.unique_count <= 20 &&
      (!column.non_null_count || column.unique_count / column.non_null_count < 0.5),
  ),
)

function describeSelection(selected: string[], total: number, label: string) {
  if (!total) return `当前暂无可选${label}`
  if (!selected.length) return `当前未选择${label}`
  if (selected.length <= 2) return `已选择 ${selected.join('、')}`
  return `已选择 ${selected.length} 个${label}`
}

function markPreviewStale() {
  tableOneResult.value = null
  interpretationContent.value = ''
  interpretationModel.value = ''
  interpretationActualTokens.value = 0
  interpretationBilledTokens.value = 0
  interpretationRemainingBalance.value = null
  interpretationSavedAt.value = ''
  copiedInterpretation.value = false
  persistViewState()
}

function toggleVariable(kind: 'continuous' | 'categorical', variable: string) {
  markPreviewStale()
  const target = kind === 'continuous' ? selectedContinuousVariables : selectedCategoricalVariables
  if (target.value.includes(variable)) {
    target.value = target.value.filter((item) => item !== variable)
    persistViewState()
    return
  }
  target.value = [...target.value, variable]
  persistViewState()
}

function toggleAllContinuous() {
  markPreviewStale()
  if (selectedContinuousVariables.value.length === continuousVariableOptions.value.length) {
    selectedContinuousVariables.value = []
    persistViewState()
    return
  }
  selectedContinuousVariables.value = continuousVariableOptions.value.map((column) => column.name)
  persistViewState()
}

function toggleAllCategorical() {
  markPreviewStale()
  if (selectedCategoricalVariables.value.length === categoricalVariableOptions.value.length) {
    selectedCategoricalVariables.value = []
    persistViewState()
    return
  }
  selectedCategoricalVariables.value = categoricalVariableOptions.value.map((column) => column.name)
  persistViewState()
}

function resetSelections() {
  groupVariable.value = ''
  selectedContinuousVariables.value = []
  selectedCategoricalVariables.value = []
  tableOneResult.value = null
  interpretationContent.value = ''
  interpretationModel.value = ''
  interpretationActualTokens.value = 0
  interpretationBilledTokens.value = 0
  interpretationRemainingBalance.value = null
  interpretationSavedAt.value = ''
  copiedInterpretation.value = false
}

function persistViewState() {
  window.sessionStorage.setItem(
    TABLEONE_STATE_KEY,
    JSON.stringify({
      selectedDatasetId: selectedDatasetId.value,
      groupVariable: groupVariable.value,
      selectedContinuousVariables: selectedContinuousVariables.value,
      selectedCategoricalVariables: selectedCategoricalVariables.value,
      decimals: decimals.value,
      interpretationLanguage: interpretationLanguage.value,
    }),
  )
}

function loadPersistedViewState() {
  const raw = window.sessionStorage.getItem(TABLEONE_STATE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as {
      selectedDatasetId?: string
      groupVariable?: string
      selectedContinuousVariables?: string[]
      selectedCategoricalVariables?: string[]
      decimals?: number
      interpretationLanguage?: 'zh' | 'en'
    }
  } catch {
    return null
  }
}

function syncSelections() {
  const continuousNames = continuousVariableOptions.value.map((column) => column.name)
  const categoricalNames = categoricalVariableOptions.value.map((column) => column.name)
  selectedContinuousVariables.value = selectedContinuousVariables.value.filter((column) => continuousNames.includes(column))
  selectedCategoricalVariables.value = selectedCategoricalVariables.value.filter((column) => categoricalNames.includes(column))
}

async function loadSummary() {
  if (!selectedDatasetId.value) {
    datasetSummary.value = null
    return
  }

  try {
    datasetSummary.value = await getDatasetSummary(selectedDatasetId.value)
    syncSelections()
  } catch (err: any) {
    datasetSummary.value = null
    notificationStore.error('数据摘要加载失败', err?.response?.data?.detail || '请稍后重试')
  }
}

async function loadAllDatasets() {
  loadingDatasets.value = true
  try {
    const savedState = loadPersistedViewState()
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

    datasetOptions.value = groups
      .flat()
      .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())

    if (datasetOptions.value.length) {
      const savedDatasetId = savedState?.selectedDatasetId || ''
      selectedDatasetId.value = datasetOptions.value.some((dataset) => dataset.id === savedDatasetId)
        ? savedDatasetId
        : datasetOptions.value[0].id
      await loadSummary()

      if (savedState) {
        groupVariable.value = savedState.groupVariable || ''
        selectedContinuousVariables.value = savedState.selectedContinuousVariables || []
        selectedCategoricalVariables.value = savedState.selectedCategoricalVariables || []
        decimals.value = savedState.decimals || 1
        interpretationLanguage.value = savedState.interpretationLanguage || 'zh'
        syncSelections()
        persistViewState()

        if (groupVariable.value && (selectedContinuousVariables.value.length || selectedCategoricalVariables.value.length)) {
          await generatePreview(true)
        }
      }
    }
  } catch (err) {
    console.error('Failed to load datasets', err)
    notificationStore.error('数据集加载失败', '无法加载描述统计所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

async function handleDatasetChange() {
  resetSelections()
  persistViewState()
  await loadSummary()
}

function handleGroupVariableChange() {
  markPreviewStale()
  syncSelections()
  persistViewState()
}

function buildRequestPayload() {
  return {
    dataset_id: selectedDatasetId.value,
    group_variable: groupVariable.value,
    variables: [...selectedContinuousVariables.value, ...selectedCategoricalVariables.value],
    decimals: decimals.value,
  }
}

function setInterpretationLanguage(language: 'zh' | 'en') {
  if (interpretationLanguage.value !== language) {
    interpretationContent.value = ''
    interpretationModel.value = ''
    interpretationActualTokens.value = 0
    interpretationBilledTokens.value = 0
    interpretationRemainingBalance.value = null
    interpretationSavedAt.value = ''
    copiedInterpretation.value = false
  }
  interpretationLanguage.value = language
  persistViewState()
  if (tableOneResult.value && selectedDatasetId.value) {
    void loadSavedInterpretation()
  }
}

async function loadSavedInterpretation() {
  if (!tableOneResult.value || !selectedDatasetId.value) {
    return
  }

  try {
    const saved = await getSavedTableOneInterpretation({
      dataset_id: selectedDatasetId.value,
      language: interpretationLanguage.value,
      table: tableOneResult.value,
    })
    if (!saved.found) {
      interpretationContent.value = ''
      interpretationModel.value = ''
      interpretationActualTokens.value = 0
      interpretationBilledTokens.value = 0
      interpretationRemainingBalance.value = null
      interpretationSavedAt.value = ''
      copiedInterpretation.value = false
      return
    }

    interpretationContent.value = saved.content || ''
    interpretationModel.value = saved.model || ''
    interpretationActualTokens.value = saved.llm_tokens_used || saved.actual_tokens || 0
    interpretationBilledTokens.value = saved.charged_tokens || saved.billed_tokens || 0
    interpretationRemainingBalance.value = null
    interpretationSavedAt.value = saved.saved_at || ''
    copiedInterpretation.value = false
  } catch (err) {
    console.error('Failed to load saved interpretation', err)
  }
}

async function generatePreview(silent = false) {
  if (!selectedDatasetId.value || !groupVariable.value) {
    if (!silent) {
      notificationStore.warning('缺少必要配置', '请先选择数据集和分组变量。')
    }
    return
  }

  if (!selectedVariableCount.value) {
    if (!silent) {
      notificationStore.warning('请选择统计变量', '至少需要选择一个连续变量或分类变量。')
    }
    return
  }

  isGenerating.value = true
  try {
    tableOneResult.value = await generateTableOne(buildRequestPayload())
    interpretationContent.value = ''
    interpretationModel.value = ''
    interpretationActualTokens.value = 0
    interpretationBilledTokens.value = 0
    interpretationRemainingBalance.value = null
    interpretationSavedAt.value = ''
    copiedInterpretation.value = false
    persistViewState()
    await loadSavedInterpretation()
    if (!silent) {
      notificationStore.success('基线特征已生成', '基线表预览已准备完成。')
    }
  } catch (err: any) {
    console.error('Failed to generate table one', err)
    if (!silent) {
      notificationStore.error('生成失败', err?.response?.data?.detail || '基线特征生成失败，请稍后重试。')
    }
  } finally {
    isGenerating.value = false
  }
}

async function interpretResult() {
  if (!tableOneResult.value || !selectedDatasetId.value) {
    notificationStore.warning('缺少结果表格', '请先生成基线特征。')
    return
  }

  if (!canUseAiInterpretation.value) {
    notificationStore.warning('请升级套餐', 'AI结果解读为高级功能，升级后即可使用。')
    return
  }

  isInterpreting.value = true
  copiedInterpretation.value = false
  try {
    const result = await interpretTableOne({
      dataset_id: selectedDatasetId.value,
      language: interpretationLanguage.value,
      table: tableOneResult.value,
    })
    interpretationContent.value = result.content
    interpretationModel.value = result.model
    interpretationActualTokens.value = result.llm_tokens_used || result.actual_tokens || 0
    interpretationBilledTokens.value = result.charged_tokens || result.billed_tokens || 0
    interpretationRemainingBalance.value = result.remaining_balance
    interpretationSavedAt.value = result.saved_at || ''
    if (authStore.user) {
      authStore.user.tokenBalance = result.remaining_balance
    }
    persistViewState()
    notificationStore.success('AI解读已生成', '结果已同步保存到项目结果，刷新后可自动恢复。')
  } catch (err: any) {
    console.error('Failed to interpret table one', err)
    notificationStore.error('AI解读失败', err?.response?.data?.detail || '请稍后重试。')
  } finally {
    isInterpreting.value = false
  }
}

async function copyInterpretation() {
  if (!interpretationContent.value) return

  try {
    await navigator.clipboard.writeText(interpretationContent.value)
    copiedInterpretation.value = true
    if (copyFeedbackTimer !== null) {
      window.clearTimeout(copyFeedbackTimer)
    }
    copyFeedbackTimer = window.setTimeout(() => {
      copiedInterpretation.value = false
      copyFeedbackTimer = null
    }, 1800)
    notificationStore.success('已复制结果解读', '内容已写入剪切板。')
  } catch (err) {
    console.error('Failed to copy interpretation', err)
    notificationStore.error('复制失败', '当前环境不支持写入剪切板。')
  }
}

async function downloadExcel() {
  if (!tableOneResult.value) return

  isDownloading.value = true
  try {
    const blob = await downloadTableOneExcel(buildRequestPayload())
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${tableOneResult.value.dataset_name.replace(/\.[^.]+$/, '')}_table1.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    console.error('Failed to download table one', err)
    notificationStore.error('下载失败', err?.response?.data?.detail || 'Excel 下载失败，请稍后重试。')
  } finally {
    isDownloading.value = false
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
.three-line-table {
  border-top: 2px solid #111827;
  border-bottom: 2px solid #111827;
  border-collapse: collapse;
}

.three-line-table thead th {
  border-bottom: 1px solid #111827;
}

.three-line-table td,
.three-line-table th {
  white-space: nowrap;
}
</style>
