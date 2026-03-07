<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-sky-100 bg-sky-50/70 px-5 py-4">
      <p class="text-sm font-semibold text-sky-900">数据清洗工作台</p>
      <p class="mt-1 text-sm leading-6 text-sky-800">
        对已上传数据执行极端值处理、缺失值清理、归一化、中心化、哑变量编码和简化版多重插补。系统始终保留原始数据，并生成新的清洗后数据副本供下载。
      </p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-5">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">清洗策略</h2>
              <p class="mt-1 text-xs text-gray-400">直接选择数据集，再配置需要执行的统计处理。</p>
            </div>
            <span class="inline-flex rounded-full bg-gray-50 px-3 py-1 text-[11px] font-medium text-gray-500">
              输出为新的 CSV 数据集
            </span>
          </div>

          <div class="mt-5 space-y-4">
            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">数据集</label>
              <select
                v-model="selectedDatasetId"
                @change="handleDatasetChange"
                :disabled="loadingDatasets"
                class="input-field py-2.5 text-sm"
              >
                <option value="">请选择数据集</option>
                <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} · {{ dataset.projectName }}
                </option>
              </select>
            </div>

            <div
              v-if="selectedDataset"
              class="rounded-xl border border-slate-100 bg-slate-50/80 p-3"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-gray-900">{{ selectedDataset.name }}</p>
                  <p class="mt-1 text-[11px] text-gray-500">所属项目：{{ selectedDataset.projectName }}</p>
                </div>
                <span class="inline-flex rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600">
                  {{ selectedDataset.row_count ?? '未知' }} 行
                </span>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <label class="mb-1.5 block text-xs font-medium text-gray-500">极端值处理</label>
                <select v-model="form.outlier_strategy" class="input-field bg-white py-2.5 text-sm">
                  <option value="none">不处理</option>
                  <option value="clip_iqr">IQR 截尾</option>
                  <option value="remove_rows">IQR 删除观测行</option>
                </select>
                <div class="mt-2">
                  <label class="mb-1 block text-[11px] text-gray-400">IQR 系数</label>
                  <input
                    v-model.number="form.outlier_factor"
                    type="number"
                    min="0.5"
                    max="5"
                    step="0.1"
                    class="input-field bg-white py-2 text-sm"
                  />
                </div>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">作用变量</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('outlier_columns')">全部变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.outlier_columns, numericColumnOptions, '连续变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in numericColumnOptions" :key="`outlier-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.outlier_columns.includes(column)" @change="toggleSelectedColumn('outlier_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <div class="flex items-center justify-between gap-3">
                  <label class="text-xs font-medium text-gray-500">高缺失变量剔除</label>
                  <input
                    v-model="form.drop_high_missing_columns"
                    type="checkbox"
                    class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                </div>
                <div class="mt-2">
                  <label class="mb-1 block text-[11px] text-gray-400">缺失阈值</label>
                  <div class="relative">
                    <input
                      v-model.number="missingThresholdPercent"
                      type="number"
                      min="0"
                      max="100"
                      step="1"
                      class="input-field bg-white py-2 pr-10 text-sm"
                    />
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">%</span>
                  </div>
                </div>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">检测范围</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('missing_drop_columns')">全部变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.missing_drop_columns, allColumnOptions, '全部变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in allColumnOptions" :key="`missing-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.missing_drop_columns.includes(column)" @change="toggleSelectedColumn('missing_drop_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <label class="mb-1.5 block text-xs font-medium text-gray-500">数值缺失值</label>
                <select v-model="form.numeric_missing_strategy" class="input-field bg-white py-2.5 text-sm">
                  <option value="none">不填补</option>
                  <option value="mean">均值填补</option>
                  <option value="median">中位数填补</option>
                  <option value="multiple_imputation">简化多重插补</option>
                </select>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">填补变量</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('numeric_missing_columns')">全部连续变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.numeric_missing_columns, numericColumnOptions, '连续变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in numericColumnOptions" :key="`numeric-missing-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.numeric_missing_columns.includes(column)" @change="toggleSelectedColumn('numeric_missing_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <label class="mb-1.5 block text-xs font-medium text-gray-500">分类缺失值</label>
                <select v-model="form.categorical_missing_strategy" class="input-field bg-white py-2.5 text-sm">
                  <option value="none">不填补</option>
                  <option value="mode">众数填补</option>
                  <option value="unknown">填充 Unknown</option>
                </select>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">填补变量</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('categorical_missing_columns')">全部分类变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.categorical_missing_columns, categoricalColumnOptions, '分类变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in categoricalColumnOptions" :key="`cat-missing-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.categorical_missing_columns.includes(column)" @change="toggleSelectedColumn('categorical_missing_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <label class="mb-1.5 block text-xs font-medium text-gray-500">数值变换</label>
                <select v-model="form.scaling_strategy" class="input-field bg-white py-2.5 text-sm">
                  <option value="none">不处理</option>
                  <option value="normalize">归一化</option>
                  <option value="standardize">标准化</option>
                  <option value="center">中心化</option>
                </select>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">变换变量</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('scaling_columns')">全部连续变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.scaling_columns, numericColumnOptions, '连续变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in numericColumnOptions" :key="`scale-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.scaling_columns.includes(column)" @change="toggleSelectedColumn('scaling_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>

              <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                <label class="mb-1.5 block text-xs font-medium text-gray-500">分类编码</label>
                <select v-model="form.categorical_encoding" class="input-field bg-white py-2.5 text-sm">
                  <option value="none">不编码</option>
                  <option value="one_hot">哑变量处理</option>
                </select>
                <div v-if="datasetSummary" class="mt-3 rounded-lg border border-white bg-white/90 p-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-[11px] font-medium text-gray-500">编码变量</p>
                    <button type="button" class="text-[11px] text-primary" @click="resetSelectedColumns('encoding_columns')">全部分类变量</button>
                  </div>
                  <details class="mt-2">
                    <summary class="flex cursor-pointer list-none items-center gap-1 text-[11px] text-gray-600">
                      <span>{{ describeSelectedColumns(form.encoding_columns, categoricalColumnOptions, '分类变量') }}</span>
                      <svg class="h-3 w-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                      </svg>
                    </summary>
                    <div class="mt-2 grid max-h-32 grid-cols-2 gap-2 overflow-y-auto pr-1">
                      <label v-for="column in categoricalColumnOptions" :key="`encoding-${column}`" class="flex items-center gap-2 rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-gray-600">
                        <input type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary" :checked="form.encoding_columns.includes(column)" @change="toggleSelectedColumn('encoding_columns', column)" />
                        <span class="truncate">{{ column }}</span>
                      </label>
                    </div>
                  </details>
                </div>
              </div>
            </div>

            <div>
              <label class="mb-1.5 block text-xs font-medium text-gray-500">输出文件名</label>
              <input
                v-model="form.output_name"
                type="text"
                class="input-field py-2.5 text-sm"
                placeholder="例如: demodata_cleaned.csv"
              />
            </div>

            <div class="rounded-xl border border-emerald-100 bg-emerald-50/70 p-3">
              <p class="text-xs font-medium text-emerald-900">推荐组合</p>
              <p class="mt-1 text-[11px] leading-5 text-emerald-800">
                医学队列数据常用流程：高缺失变量剔除 10% + 数值中位数填补 + 分类众数填补 + 连续变量标准化 + 分类变量哑变量处理。
              </p>
            </div>

            <button
              @click="runCleaning"
              :disabled="!selectedDatasetId || isRunning"
              class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18" /><path d="M7 12h10" /><path d="M10 18h4" />
              </svg>
              {{ isRunning ? '清洗中...' : '执行数据清洗' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-7">
        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">原始数据概览</h2>
              <p class="mt-1 text-xs text-gray-400">用于快速确认当前数据规模和变量构成。</p>
            </div>
            <router-link to="/data" class="text-xs font-medium text-primary transition-colors hover:text-primary-600">
              返回数据上传
            </router-link>
          </div>

          <div v-if="summaryLoading" class="py-16 text-center text-sm text-gray-400">正在加载原始数据概览...</div>
          <div v-else-if="summaryError" class="py-16 text-center text-sm text-red-500">{{ summaryError }}</div>
          <div v-else-if="datasetSummary" class="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div v-for="card in sourceCards" :key="card.label" :class="['rounded-2xl border p-4', card.cardClass]">
              <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">{{ card.label }}</p>
              <p class="mt-2 text-2xl font-heading font-semibold text-gray-900">{{ card.value }}</p>
              <p class="mt-1 text-xs text-gray-500">{{ card.description }}</p>
            </div>
          </div>
          <div v-else class="py-16 text-center text-sm text-gray-400">请选择一个数据集以查看可清洗内容。</div>
        </div>

        <div class="rounded-2xl border border-gray-100 bg-white p-5">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">清洗结果</h2>
              <p class="mt-1 text-xs text-gray-400">系统不会覆盖原始数据，而是生成一个新的处理后数据集。</p>
            </div>
            <div class="flex items-center gap-2" v-if="cleaningResult">
              <button
                @click="handleDownload(cleaningResult.dataset.id, cleaningResult.dataset.name)"
                :disabled="isDownloading"
                class="inline-flex h-9 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 px-3 text-xs font-semibold text-emerald-700 transition-colors hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {{ isDownloading ? '下载中...' : '下载清洗结果' }}
              </button>
              <span class="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-medium text-emerald-700">
                {{ cleaningResult.dataset.name }}
              </span>
            </div>
          </div>

          <div v-if="cleaningResult" class="mt-5 space-y-5">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div class="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">观测变化</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ cleaningResult.original_rows }} → {{ cleaningResult.cleaned_rows }}</p>
                <p class="mt-1 text-xs text-gray-500">删除 {{ cleaningResult.removed_rows }} 行</p>
              </div>
              <div class="rounded-2xl border border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">变量变化</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ cleaningResult.original_columns }} → {{ cleaningResult.cleaned_columns }}</p>
                <p class="mt-1 text-xs text-gray-500">剔除 {{ cleaningResult.removed_columns }} 列</p>
              </div>
              <div class="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">插补单元</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ cleaningResult.numeric_imputed_cells + cleaningResult.categorical_imputed_cells }}</p>
                <p class="mt-1 text-xs text-gray-500">数值 {{ cleaningResult.numeric_imputed_cells }} · 分类 {{ cleaningResult.categorical_imputed_cells }}</p>
              </div>
              <div class="rounded-2xl border border-amber-200 bg-amber-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">编码新增列</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ cleaningResult.encoded_columns_added }}</p>
                <p class="mt-1 text-xs text-gray-500">哑变量展开后的新增特征数</p>
              </div>
            </div>

            <div class="rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <p class="text-xs font-medium text-gray-700">已执行操作</p>
                <button
                  @click="handleDownload(cleaningResult.dataset.id, cleaningResult.dataset.name)"
                  :disabled="isDownloading"
                  class="inline-flex items-center rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:border-emerald-200 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  另存下载
                </button>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="operation in cleaningResult.operations"
                  :key="operation"
                  class="inline-flex rounded-full border border-white bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm"
                >
                  {{ operation }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="py-16 text-center text-sm text-gray-400">
            执行清洗后，这里会展示新数据集名称、变量变化、插补数量，并提供下载入口。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  cleanDataset,
  downloadDataset,
  getDatasetSummary,
  getDatasets,
  getProjects,
  type DatasetCleaningResult,
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

const loadingDatasets = ref(true)
const summaryLoading = ref(false)
const isRunning = ref(false)
const isDownloading = ref(false)

const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const summaryError = ref('')
const cleaningResult = ref<DatasetCleaningResult | null>(null)

const form = reactive({
  outlier_strategy: 'clip_iqr' as 'none' | 'clip_iqr' | 'remove_rows',
  outlier_factor: 1.5,
  outlier_columns: [] as string[],
  drop_high_missing_columns: true,
  missing_column_threshold: 0.1,
  missing_drop_columns: [] as string[],
  numeric_missing_strategy: 'median' as 'none' | 'mean' | 'median' | 'multiple_imputation',
  numeric_missing_columns: [] as string[],
  categorical_missing_strategy: 'mode' as 'none' | 'mode' | 'unknown',
  categorical_missing_columns: [] as string[],
  scaling_strategy: 'standardize' as 'none' | 'normalize' | 'standardize' | 'center',
  scaling_columns: [] as string[],
  categorical_encoding: 'none' as 'none' | 'one_hot',
  encoding_columns: [] as string[],
  output_name: '',
})

const selectedDataset = computed(() =>
  datasetOptions.value.find((item) => item.id === selectedDatasetId.value) ?? null,
)

const missingThresholdPercent = computed({
  get: () => Math.round(form.missing_column_threshold * 100),
  set: (value: number) => {
    const normalized = Number.isFinite(value) ? value : 0
    form.missing_column_threshold = Math.min(1, Math.max(0, normalized / 100))
  },
})

const sourceCards = computed(() => {
  if (!datasetSummary.value) return []
  const summary = datasetSummary.value
  return [
    {
      label: '样本量',
      value: summary.total_rows.toLocaleString(),
      description: '当前数据集中可用观测行数',
      cardClass: 'border-slate-200 bg-slate-50/80',
    },
    {
      label: '变量数',
      value: summary.total_columns.toLocaleString(),
      description: `连续 ${summary.numeric_columns} · 分类 ${summary.categorical_columns}`,
      cardClass: 'border-sky-200 bg-sky-50/80',
    },
    {
      label: '缺失率',
      value: `${(summary.missing_rate * 100).toFixed(1)}%`,
      description: `${summary.missing_cells.toLocaleString()} 个单元格为空`,
      cardClass: 'border-amber-200 bg-amber-50/80',
    },
    {
      label: '重复行',
      value: summary.duplicate_rows.toLocaleString(),
      description: `${summary.complete_rows.toLocaleString()} 行为完整观测`,
      cardClass: 'border-emerald-200 bg-emerald-50/80',
    },
  ]
})

const allColumnOptions = computed(() =>
  (datasetSummary.value?.columns || []).map((column) => column.name),
)

const numericColumnOptions = computed(() =>
  (datasetSummary.value?.columns || [])
    .filter((column) => column.kind === 'numeric')
    .map((column) => column.name),
)

const categoricalColumnOptions = computed(() =>
  (datasetSummary.value?.columns || [])
    .filter((column) => column.kind === 'categorical')
    .map((column) => column.name),
)

type ColumnSelectionField =
  | 'outlier_columns'
  | 'missing_drop_columns'
  | 'numeric_missing_columns'
  | 'categorical_missing_columns'
  | 'scaling_columns'
  | 'encoding_columns'

function resetColumnSelections() {
  form.outlier_columns = []
  form.missing_drop_columns = []
  form.numeric_missing_columns = []
  form.categorical_missing_columns = []
  form.scaling_columns = []
  form.encoding_columns = []
}

function resetSelectedColumns(field: ColumnSelectionField) {
  form[field] = []
}

function toggleSelectedColumn(field: ColumnSelectionField, column: string) {
  const current = form[field]
  if (current.includes(column)) {
    form[field] = current.filter((item) => item !== column)
    return
  }
  form[field] = [...current, column]
}

function describeSelectedColumns(selected: string[], available: string[], fallbackLabel: string) {
  if (!available.length) {
    return '当前数据集中暂无可选变量'
  }
  if (!selected.length) {
    return `当前为全部${fallbackLabel}`
  }
  if (selected.length <= 2) {
    return `已选择 ${selected.join('、')}`
  }
  return `已选择 ${selected.length} 个变量`
}

function syncColumnSelectionsToCurrentSummary(summary: DatasetSummaryResponse | null) {
  if (!summary) {
    resetColumnSelections()
    return
  }

  const allColumns = summary.columns.map((column) => column.name)
  const numericColumns = summary.columns
    .filter((column) => column.kind === 'numeric')
    .map((column) => column.name)
  const categoricalColumns = summary.columns
    .filter((column) => column.kind === 'categorical')
    .map((column) => column.name)

  form.outlier_columns = form.outlier_columns.filter((column) => numericColumns.includes(column))
  form.missing_drop_columns = form.missing_drop_columns.filter((column) => allColumns.includes(column))
  form.numeric_missing_columns = form.numeric_missing_columns.filter((column) => numericColumns.includes(column))
  form.categorical_missing_columns = form.categorical_missing_columns.filter((column) => categoricalColumns.includes(column))
  form.scaling_columns = form.scaling_columns.filter((column) => numericColumns.includes(column))
  form.encoding_columns = form.encoding_columns.filter((column) => categoricalColumns.includes(column))
}

async function loadSummary() {
  if (!selectedDatasetId.value) {
    datasetSummary.value = null
    summaryError.value = ''
    return
  }

  summaryLoading.value = true
  summaryError.value = ''
  try {
    datasetSummary.value = await getDatasetSummary(selectedDatasetId.value)
    syncColumnSelectionsToCurrentSummary(datasetSummary.value)
  } catch (err: any) {
    datasetSummary.value = null
    syncColumnSelectionsToCurrentSummary(null)
    summaryError.value = err?.response?.data?.detail || '原始数据概览加载失败'
  } finally {
    summaryLoading.value = false
  }
}

async function loadAllDatasets(preferredId?: string) {
  loadingDatasets.value = true
  try {
    const projects = (await getProjects()) as ProjectItem[]
    const datasetGroups = await Promise.all(
      projects.map(async (project) => {
        const datasets = await getDatasets(project.id)
        return datasets.map((dataset) => ({
          ...dataset,
          projectId: project.id,
          projectName: project.name,
        }))
      }),
    )

    const merged = datasetGroups
      .flat()
      .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())

    datasetOptions.value = merged
    if (!merged.length) {
      selectedDatasetId.value = ''
      datasetSummary.value = null
      return
    }

    const targetId =
      preferredId && merged.find((item) => item.id === preferredId)
        ? preferredId
        : selectedDatasetId.value && merged.find((item) => item.id === selectedDatasetId.value)
          ? selectedDatasetId.value
          : merged[0].id

    selectedDatasetId.value = targetId
    await loadSummary()
  } catch (err) {
    console.error('Failed to load datasets', err)
    notificationStore.error('数据集加载失败', '无法加载当前账户下的数据集列表。')
  } finally {
    loadingDatasets.value = false
  }
}

async function handleDatasetChange() {
  cleaningResult.value = null
  resetColumnSelections()
  await loadSummary()
}

async function runCleaning() {
  if (!selectedDatasetId.value) {
    notificationStore.warning('请先选择数据集', '只有选中一个数据集后，才能执行数据清洗。')
    return
  }

  isRunning.value = true
  try {
    const result = await cleanDataset(selectedDatasetId.value, {
      ...form,
      output_name: form.output_name.trim() || undefined,
    })
    cleaningResult.value = result
    await loadAllDatasets(result.dataset.id)
    notificationStore.success('数据清洗完成', `已生成新的数据集：${result.dataset.name}`)
  } catch (err: any) {
    console.error('Cleaning failed', err)
    notificationStore.error('数据清洗失败', err?.response?.data?.detail || err?.message || '请稍后重试')
  } finally {
    isRunning.value = false
  }
}

async function handleDownload(datasetId: string, fileName: string) {
  isDownloading.value = true
  try {
    const blob = await downloadDataset(datasetId)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    console.error('Download failed', err)
    notificationStore.error('下载失败', err?.response?.data?.detail || '清洗结果下载失败，请稍后重试。')
  } finally {
    isDownloading.value = false
  }
}

onMounted(async () => {
  await loadAllDatasets()
})
</script>
