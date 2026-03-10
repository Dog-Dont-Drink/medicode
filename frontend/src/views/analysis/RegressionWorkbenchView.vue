<template>
  <div class="space-y-6">
    <div class="panel-card bg-gradient-to-r from-slate-50 via-white to-fuchsia-50/40 px-5 py-4">
      <p class="text-sm font-semibold text-slate-900">{{ pageTitle }}</p>
      <p class="mt-1 text-sm leading-6 text-slate-600">{{ pageDescription }}</p>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-12">
      <div class="xl:col-span-4">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">模型配置</h2>
            <p class="mt-1 text-xs text-gray-400">先选择数据集、因变量，再勾选候选自变量。</p>
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
              <label class="mb-1.5 block text-xs font-medium text-gray-500">因变量</label>
              <select v-model="outcomeVariable" :disabled="!outcomeOptions.length" @change="handleOutcomeChange" class="tool-input">
                <option value="">请选择因变量</option>
                <option v-for="column in outcomeOptions" :key="column.name" :value="column.name">
                  {{ column.name }} · {{ outcomeOptionLabel(column) }}
                </option>
              </select>
              <p class="mt-1 text-[11px] text-gray-400">{{ outcomeHint }}</p>
            </div>

            <div class="panel-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold text-gray-700">自变量</p>
                  <p class="mt-1 text-[11px] text-gray-400">支持数值型和分类变量；分类变量会在 R 中自动展开为虚拟变量。</p>
                </div>
                <button type="button" class="text-[11px] font-medium text-primary" @click="toggleAllPredictors">
                  {{ selectedPredictors.length === predictorOptions.length && predictorOptions.length ? '清空' : '全选' }}
                </button>
              </div>
              <div class="panel-card-tight mt-3 border-white p-2.5">
                <p class="text-[11px] text-gray-500">{{ predictorSelectionText }}</p>
                <div class="mt-2 grid max-h-48 grid-cols-2 gap-2 overflow-y-auto pr-1">
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

            <div v-if="props.mode === 'lasso'">
              <label class="mb-1.5 block text-xs font-medium text-gray-500">交叉验证折数</label>
              <select v-model.number="nfolds" class="tool-input">
                <option v-for="value in [5, 10]" :key="value" :value="value">{{ value }}</option>
              </select>
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
              :disabled="isRunning || !selectedDatasetId || !outcomeVariable || !selectedPredictors.length"
              class="tool-btn-primary w-full px-4 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg v-if="isRunning" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 3L10 14" />
                <path d="M21 3L14 21L10 14L3 10L21 3Z" />
              </svg>
              {{ isRunning ? '模型运行中...' : runButtonText }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-6 xl:col-span-8">
        <div class="panel-card p-5">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">模型摘要</h2>
            <p class="mt-1 text-xs text-gray-400">
              {{ props.mode === 'logistic' || props.mode === 'linear' ? '保留关键建模信息，其余细节放入结果表与图形结果查看。' : '先看样本量、拟合度和模型说明，再进入系数表和图形结果。' }}
            </p>
          </div>

          <div v-if="linearResult" class="panel-subtle mt-4 px-4 py-3 text-xs leading-6 text-slate-500">
            <p>
              数据集 {{ linearResult.dataset_name }}，因变量 {{ linearResult.outcome_variable }}；样本量 {{ linearResult.sample_size }}，剔除 {{ linearResult.excluded_rows }} 行缺失记录；
              R² {{ formatNumber(linearResult.r_squared) }}，Adjusted R² {{ formatNumber(linearResult.adjusted_r_squared) }}，
              模型 P {{ formatP(linearResult.model_p_value) }}。
            </p>
            <p class="mt-1">
              残差正态性 {{ linearResult.residual_normality_method || '未提供' }} P={{ formatP(linearResult.residual_normality_p_value) }}；
              同方差性 {{ linearResult.homoscedasticity_test_method || '未提供' }} P={{ formatP(linearResult.homoscedasticity_p_value) }}。
            </p>
            <p class="mt-1">模型采用完整案例拟合，建议结合残差图、拟合图、异常值和共线性进一步判断模型稳健性。</p>
            <p v-if="resultNote" class="mt-1">{{ resultNote }}</p>
          </div>

          <div v-else-if="logisticResult" class="panel-subtle mt-4 px-4 py-3 text-xs leading-6 text-slate-500">
            <p>
              数据集 {{ logisticResult.dataset_name }}，因变量 {{ logisticResult.outcome_variable }}；样本量 {{ logisticResult.sample_size }}，剔除 {{ logisticResult.excluded_rows }} 行缺失记录；
              事件水平 {{ logisticResult.event_level }}，参考水平 {{ logisticResult.reference_level }}；Pseudo R² {{ formatNumber(logisticResult.pseudo_r_squared) }}，
              AIC {{ formatNumber(logisticResult.aic) }}，模型 P {{ formatP(logisticResult.model_p_value) }}。
            </p>
            <p class="mt-1">模型采用完整案例拟合，OR &gt; 1 表示事件发生优势升高，OR &lt; 1 表示优势降低。</p>
            <p v-if="resultNote" class="mt-1">{{ resultNote }}</p>
          </div>

          <template v-else-if="hasResult">
            <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div class="panel-card border-slate-200 bg-slate-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">数据集</p>
                <p class="mt-2 text-sm font-semibold text-gray-900">{{ resultDatasetName }}</p>
                <p class="mt-1 text-xs text-gray-500">因变量：{{ outcomeVariable }}</p>
              </div>
              <div class="panel-card border-sky-200 bg-sky-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">样本量</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ resultSampleSize }}</p>
                <p class="mt-1 text-xs text-gray-500">剔除 {{ resultExcludedRows }} 行缺失记录</p>
              </div>
              <div class="panel-card border-emerald-200 bg-emerald-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">核心指标</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ modelMetricValue }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ modelMetricHint }}</p>
              </div>
              <div class="panel-card border-amber-200 bg-amber-50/80 p-4">
                <p class="text-[11px] uppercase tracking-[0.18em] text-gray-500">模型检验</p>
                <p class="mt-2 text-xl font-semibold text-gray-900">{{ modelPValueText }}</p>
                <p class="mt-1 text-xs text-gray-500">{{ modelFormulaText }}</p>
              </div>
            </div>

            <div class="panel-subtle mt-4 p-4">
              <div class="grid gap-2">
                <div v-for="(item, index) in assumptions" :key="index" class="flex items-start gap-2 text-sm text-gray-600">
                  <span class="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-primary"></span>
                  <span>{{ item }}</span>
                </div>
              </div>
              <p v-if="resultNote" class="mt-3 text-xs text-gray-500">{{ resultNote }}</p>
            </div>
          </template>

          <div v-else class="py-16 text-center text-sm text-gray-400">运行模型后，这里会展示摘要和建模说明。</div>
        </div>

        <div class="panel-card p-5">
          <div v-if="!linearResult && !logisticResult && !lassoResult">
            <h2 class="text-sm font-semibold text-gray-900">结果表</h2>
            <p class="mt-1 text-xs text-gray-400">{{ resultTableDescription }}</p>
          </div>

          <div v-if="linearResult" class="mt-5 space-y-5">
            <div class="inline-flex rounded-2xl border border-emerald-100 bg-emerald-50/80 p-1">
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeLinearTab === 'table' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeLinearTab = 'table'"
              >
                结果三线表
              </button>
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeLinearTab === 'diagnostics' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeLinearTab = 'diagnostics'"
              >
                残差图与拟合图
              </button>
            </div>

            <div v-if="activeLinearTab === 'table'" class="analysis-tab-panel space-y-4">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">结果表</h2>
                <p class="mt-1 text-xs text-gray-400">展示线性回归结果三线表。</p>
              </div>

              <div class="overflow-x-auto">
                <table class="result-table min-w-full text-sm">
                  <thead>
                    <tr>
                      <th>项</th>
                      <th>Estimate</th>
                      <th>SE</th>
                      <th>t</th>
                      <th>95% CI</th>
                      <th>P 值</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in linearResult.coefficients" :key="item.term">
                      <td class="font-semibold text-slate-900">{{ item.term }}</td>
                      <td>{{ formatNumber(item.estimate) }}</td>
                      <td>{{ formatNumber(item.std_error) }}</td>
                      <td>{{ formatNumber(item.statistic) }}</td>
                      <td>{{ formatInterval(item.conf_low, item.conf_high) }}</td>
                      <td>{{ formatP(item.p_value) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else class="analysis-tab-panel space-y-5">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">残差图与拟合图</h2>
                <p class="mt-1 text-xs text-gray-400">查看线性回归残差检验结果，以及残差诊断图和拟合值对比图。</p>
              </div>

              <!-- <div class="flex flex-wrap gap-3">
                <div class="inline-flex items-center gap-3 rounded-full border border-emerald-100 bg-emerald-50/80 px-4 py-2 text-sm text-slate-700">
                  <span class="font-semibold text-emerald-700">残差正态性</span>
                  <span class="font-semibold text-slate-900">{{ linearResult.residual_normality_passed ? '通过' : '未通过 / 未执行' }}</span>
                  <span>{{ linearResult.residual_normality_method || '未提供' }}</span>
                  <span>P={{ formatP(linearResult.residual_normality_p_value) }}</span>
                </div>
                <div class="inline-flex items-center gap-3 rounded-full border border-emerald-100 bg-emerald-50/80 px-4 py-2 text-sm text-slate-700">
                  <span class="font-semibold text-emerald-700">同方差性</span>
                  <span class="font-semibold text-slate-900">{{ linearResult.homoscedasticity_passed ? '通过' : '未通过 / 未执行' }}</span>
                  <span>{{ linearResult.homoscedasticity_test_method || '未提供' }}</span>
                  <span>P={{ formatP(linearResult.homoscedasticity_p_value) }}</span>
                </div>
              </div> -->

              <div class="grid gap-4 xl:grid-cols-2">
                <div
                  v-for="plot in linearResult.plots"
                  :key="plot.filename"
                  class="panel-card overflow-hidden border-emerald-100 shadow-sm shadow-emerald-100/40"
                >
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
                        @click="downloadLinearPlotPdfAction(plot)"
                      >
                        <span>{{ downloadingPdfPlot === plot.filename ? '导出中...' : '下载 PDF' }}</span>
                        <span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 drop-shadow-[0_0_10px_rgba(16,185,129,0.45)]">
                          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>
                          1
                        </span>
                      </button>
                    </div>
                  </div>
                  <img :src="plotDataUri(plot)" :alt="plot.name" class="linear-diagnostic-image" />
                </div>
              </div>

              <div v-if="!linearResult.plots?.length" class="panel-card border-dashed border-emerald-200 bg-emerald-50/40 px-4 py-5 text-sm text-emerald-800">
                当前结果未生成诊断图，请重新运行线性回归后再查看。
              </div>
            </div>
          </div>

          <div v-else-if="logisticResult" class="mt-5 overflow-x-auto">
            <div class="space-y-5">
              <div class="inline-flex rounded-2xl border border-emerald-100 bg-emerald-50/80 p-1">
                <button
                  type="button"
                  class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                  :class="activeLogisticTab === 'table' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                  @click="activeLogisticTab = 'table'"
                >
                  结果三线表
                </button>
                <button
                  type="button"
                  class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                  :class="activeLogisticTab === 'forest' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                  @click="activeLogisticTab = 'forest'"
                >
                  森林图
                </button>
              </div>

              <div v-if="activeLogisticTab === 'table'" class="analysis-tab-panel space-y-4">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">结果表</h2>
                  <p class="mt-1 text-xs text-gray-400">展示 Logistic 回归单因素与多因素结果，重点查看 OR、95% CI 和 P 值。</p>
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
                        <th>OR</th>
                        <th>95% CI</th>
                        <th>P 值</th>
                        <th>系数</th>
                        <th>SE</th>
                        <th>OR</th>
                        <th>95% CI</th>
                        <th>P 值</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in logisticCombinedRows" :key="item.term">
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
              </div>

              <div v-else class="analysis-tab-panel space-y-4">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">森林图</h2>
                  <p class="mt-1 text-xs text-gray-400">查看 Logistic 回归 OR 森林图，支持 PNG 下载与高清 PDF 导出。</p>
                </div>

                <div v-if="logisticResult.plots.length" class="grid gap-4 lg:grid-cols-1">
                  <div
                    v-for="plot in logisticResult.plots"
                    :key="plot.filename"
                    class="panel-card overflow-hidden border-emerald-100 shadow-sm shadow-emerald-100/40"
                  >
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
                          @click="downloadLogisticPlotPdfAction(plot)"
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
                  当前结果未生成森林图，请重新运行 Logistic 回归后再查看。
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="lassoResult" class="mt-5 space-y-5">
            <div class="inline-flex rounded-2xl border border-emerald-100 bg-emerald-50/80 p-1">
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeLassoTab === 'table' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeLassoTab = 'table'"
              >
                结果三线表
              </button>
              <button
                type="button"
                class="rounded-xl px-4 py-2 text-sm font-semibold transition-colors"
                :class="activeLassoTab === 'plots' ? 'bg-emerald-500 text-white shadow-sm' : 'text-emerald-800 hover:bg-white/80'"
                @click="activeLassoTab = 'plots'"
              >
                图形结果
              </button>
            </div>

            <div v-if="activeLassoTab === 'table'" class="analysis-tab-panel space-y-4">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">结果表</h2>
                <p class="mt-1 text-xs text-gray-400">展示 LASSO 筛选变量的系数结果，以及在 lambda.min 与 lambda.1se 下的入选情况。</p>
              </div>

              <div class="overflow-x-auto">
                <table class="result-table min-w-full text-sm">
                  <thead>
                    <tr>
                      <th>变量</th>
                      <th>lambda.min 系数</th>
                      <th>lambda.1se 系数</th>
                      <th>lambda.min 入选</th>
                      <th>lambda.1se 入选</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in lassoResult.selected_features" :key="item.term">
                      <td class="font-semibold text-slate-900">{{ item.term }}</td>
                      <td>{{ formatNumber(item.coefficient_lambda_min) }}</td>
                      <td>{{ formatNumber(item.coefficient_lambda_1se) }}</td>
                      <td>{{ item.selected_at_lambda_min ? '是' : '否' }}</td>
                      <td>{{ item.selected_at_lambda_1se ? '是' : '否' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else class="analysis-tab-panel space-y-4">
              <div>
                <h2 class="text-sm font-semibold text-gray-900">交叉验证曲线与系数路径图</h2>
                <p class="mt-1 text-xs text-gray-400">查看 LASSO 的交叉验证曲线和系数路径图，支持 PNG 下载与高清 PDF 导出。</p>
              </div>

              <div class="grid gap-4 xl:grid-cols-2">
                <div
                  v-for="plot in lassoResult.plots"
                  :key="plot.filename"
                  class="panel-card overflow-hidden border-emerald-100 shadow-sm shadow-emerald-100/40"
                >
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
                  <img :src="plotDataUri(plot)" :alt="plot.name" class="w-full bg-white object-contain" />
                </div>
              </div>

              <div v-if="!lassoResult.plots?.length" class="panel-card border-dashed border-emerald-200 bg-emerald-50/40 px-4 py-5 text-sm text-emerald-800">
                当前结果未生成图形，请重新运行 LASSO 回归后再查看。
              </div>
            </div>
          </div>

          <InsightActionPanel
            v-if="hasResult"
            class="mt-5"
            :language="interpretationLanguage"
            :is-interpreting="isInterpreting"
            :is-downloading="isDownloading"
            :content="interpretationContent"
            :copied="copiedInterpretation"
            :charged-resources="interpretationChargedTokens"
            :remaining-resources="interpretationRemainingBalance"
            :saved-at="interpretationSavedAt"
            description="基于当前结果生成论文级结果说明。"
            loading-description="根据当前回归结果提炼论文式 Results 段落，请稍候。"
            empty-text="模型结果生成后，可在此调用 AI结果解读，输出适合论文 Results 部分的描述段落。"
            :interpret-disabled="isInterpreting"
            :download-disabled="isDownloading"
            @language-change="setInterpretationLanguage"
            @interpret="interpretResult"
            @download="downloadExcel"
            @copy="copyInterpretation"
          />

          <div v-else class="py-16 text-center text-sm text-gray-400">运行模型后，这里会展示回归结果表。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import InsightActionPanel from '@/components/analysis/InsightActionPanel.vue'
import {
  downloadLogisticPlotPdf,
  downloadLinearPlotPdf,
  downloadLassoPlotPdf,
  downloadRegressionExcel,
  getDatasetSummary,
  getDatasets,
  getProjects,
  getSavedRegressionInterpretation,
  interpretRegression,
  runLassoRegression,
  runLinearRegression,
  runLogisticRegression,
  type DatasetColumnSummary,
  type DatasetItem,
  type DatasetSummaryResponse,
  type LassoPlotPayload,
  type LassoRegressionResponse,
  type LinearRegressionResponse,
  type LogisticRegressionResponse,
} from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps<{ mode: 'linear' | 'lasso' | 'logistic' }>()

interface ProjectItem {
  id: string
  name: string
}

interface DatasetOption extends DatasetItem {
  projectId: string
  projectName: string
}

interface PersistedRegressionViewState {
  selectedDatasetId?: string
  outcomeVariable?: string
  selectedPredictors?: string[]
  alpha?: number
  nfolds?: number
  interpretationLanguage?: 'zh' | 'en'
  linearResult?: LinearRegressionResponse | null
  logisticResult?: LogisticRegressionResponse | null
  lassoResult?: LassoRegressionResponse | null
  interpretationContent?: string
  interpretationChargedTokens?: number
  interpretationRemainingBalance?: number | null
  interpretationSavedAt?: string
}

interface CombinedRegressionTableRow {
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

type LinearResultTab = 'table' | 'diagnostics'
type LogisticResultTab = 'table' | 'forest'
type LassoResultTab = 'table' | 'plots'

const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const PAID_SUBSCRIPTIONS = new Set(['basic', 'pro', 'enterprise'])
const REGRESSION_STATE_KEY = `regression_workbench_state_${props.mode}_v1`

const datasetOptions = ref<DatasetOption[]>([])
const selectedDatasetId = ref('')
const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const outcomeVariable = ref('')
const selectedPredictors = ref<string[]>([])
const alpha = ref(0.05)
const nfolds = ref(10)
const loadingDatasets = ref(true)
const isRunning = ref(false)
const isInterpreting = ref(false)
const isDownloading = ref(false)
const downloadingPdfPlot = ref('')
const activeLinearTab = ref<LinearResultTab>('table')
const activeLogisticTab = ref<LogisticResultTab>('table')
const activeLassoTab = ref<LassoResultTab>('table')
const interpretationLanguage = ref<'zh' | 'en'>('zh')
const interpretationContent = ref('')
const interpretationChargedTokens = ref(0)
const interpretationRemainingBalance = ref<number | null>(null)
const interpretationSavedAt = ref('')
const copiedInterpretation = ref(false)
let copyFeedbackTimer: number | null = null
let restoringState = false

const linearResult = ref<LinearRegressionResponse | null>(null)
const logisticResult = ref<LogisticRegressionResponse | null>(null)
const lassoResult = ref<LassoRegressionResponse | null>(null)

const pageTitle = computed(() => {
  if (props.mode === 'linear') return '线性回归'
  if (props.mode === 'logistic') return 'Logistic 回归'
  return 'LASSO 回归'
})

const pageDescription = computed(() => {
  if (props.mode === 'linear') return '适用于连续结局变量，输出回归系数、95% CI、模型拟合度，并提供残差诊断图与拟合值对比图。'
  if (props.mode === 'logistic') return '适用于二分类结局变量，输出经典三线表 OR 结果、模型检验和 AI 解读。'
  return '执行 LASSO，返回筛选变量结果以及交叉验证曲线、系数路径图。'
})

const outcomeHint = computed(() => {
  if (props.mode === 'linear') return '线性回归要求因变量为连续数值型。'
  if (props.mode === 'logistic') return 'Logistic 回归要求因变量为二分类变量。'
  return 'LASSO 当前支持连续结局或二分类结局。'
})

const runButtonText = computed(() => {
  if (props.mode === 'linear') return '运行线性回归'
  if (props.mode === 'logistic') return '运行 Logistic 回归'
  return '运行 LASSO 回归'
})

const resultTableDescription = computed(() => {
  if (props.mode === 'linear') return '使用 Tab 查看线性回归结果三线表，以及残差诊断图和拟合值对比图。'
  if (props.mode === 'logistic') return '使用 Tab 查看 Logistic 回归结果三线表，以及 OR 森林图。'
  return '展示 LASSO 筛选到的变量，并提供两张经典图的 PNG 下载。'
})

const hasResult = computed(() => !!linearResult.value || !!logisticResult.value || !!lassoResult.value)
const canUseAiInterpretation = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))
const canDownloadPremiumPdf = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))
const resultDatasetName = computed(() => linearResult.value?.dataset_name || logisticResult.value?.dataset_name || lassoResult.value?.dataset_name || '')
const resultSampleSize = computed(() => linearResult.value?.sample_size || logisticResult.value?.sample_size || lassoResult.value?.sample_size || 0)
const resultExcludedRows = computed(() => linearResult.value?.excluded_rows || logisticResult.value?.excluded_rows || lassoResult.value?.excluded_rows || 0)
const assumptions = computed(() => linearResult.value?.assumptions || logisticResult.value?.assumptions || lassoResult.value?.assumptions || [])
const resultNote = computed(() => linearResult.value?.note || logisticResult.value?.note || lassoResult.value?.note || '')
const modelFormulaText = computed(() => linearResult.value?.formula || logisticResult.value?.formula || (lassoResult.value ? `family=${lassoResult.value.family}` : '-'))
const modelPValueText = computed(() => {
  if (linearResult.value) return formatP(linearResult.value.model_p_value)
  if (logisticResult.value) return formatP(logisticResult.value.model_p_value)
  if (lassoResult.value) return `min=${formatNumber(lassoResult.value.lambda_min)}`
  return '-'
})
const modelMetricValue = computed(() => {
  if (linearResult.value) return formatNumber(linearResult.value.r_squared)
  if (logisticResult.value) return formatNumber(logisticResult.value.pseudo_r_squared)
  if (lassoResult.value) return `${lassoResult.value.nonzero_count_lambda_min}/${lassoResult.value.nonzero_count_lambda_1se}`
  return '-'
})
const modelMetricHint = computed(() => {
  if (linearResult.value) return `Adjusted R² ${formatNumber(linearResult.value.adjusted_r_squared)}`
  if (logisticResult.value) return `AIC ${formatNumber(logisticResult.value.aic)}`
  if (lassoResult.value) return 'nonzero(lambda.min / 1se)'
  return '-'
})
const logisticCombinedRows = computed<CombinedRegressionTableRow[]>(() =>
  mergeComparisonRows(
    logisticResult.value?.univariate_coefficients || [],
    logisticResult.value?.coefficients || [],
    (item) => formatNumber(item.odds_ratio),
    (item) => formatInterval(item.conf_low, item.conf_high),
    (item) => formatP(item.p_value),
  ),
)
const predictorSelectionText = computed(() => {
  if (!predictorOptions.value.length) return '当前暂无可选自变量'
  if (!selectedPredictors.value.length) return '当前未选择自变量'
  if (selectedPredictors.value.length <= 3) return `已选择 ${selectedPredictors.value.join('、')}`
  return `已选择 ${selectedPredictors.value.length} 个自变量`
})

const outcomeOptions = computed(() => {
  const columns = datasetSummary.value?.columns || []
  if (props.mode === 'linear') {
    return columns.filter((column) => column.kind === 'numeric')
  }
  if (props.mode === 'logistic') {
    return columns.filter((column) => isBinaryColumn(column))
  }
  return columns.filter((column) => column.kind === 'numeric' || isBinaryColumn(column))
})

const predictorOptions = computed(() =>
  (datasetSummary.value?.columns || []).filter(
    (column) => column.name !== outcomeVariable.value && column.kind !== 'datetime' && column.unique_count >= 2,
  ),
)

function isBinaryColumn(column: DatasetColumnSummary) {
  return (column.kind === 'categorical' || column.kind === 'boolean' || column.kind === 'numeric') && column.unique_count === 2
}

function outcomeOptionLabel(column: DatasetColumnSummary) {
  if (column.kind === 'numeric') {
    return column.unique_count === 2 ? '数值/二分类' : '数值型'
  }
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
): CombinedRegressionTableRow[] {
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

function resetResults() {
  linearResult.value = null
  logisticResult.value = null
  lassoResult.value = null
  activeLinearTab.value = 'table'
  activeLogisticTab.value = 'table'
  activeLassoTab.value = 'table'
  interpretationContent.value = ''
  interpretationChargedTokens.value = 0
  interpretationRemainingBalance.value = null
  interpretationSavedAt.value = ''
  copiedInterpretation.value = false
}

function buildPersistedViewState(): PersistedRegressionViewState {
  return {
    selectedDatasetId: selectedDatasetId.value,
    outcomeVariable: outcomeVariable.value,
    selectedPredictors: [...selectedPredictors.value],
    alpha: alpha.value,
    nfolds: nfolds.value,
    interpretationLanguage: interpretationLanguage.value,
    linearResult: linearResult.value,
    logisticResult: logisticResult.value,
    lassoResult: lassoResult.value,
    interpretationContent: interpretationContent.value,
    interpretationChargedTokens: interpretationChargedTokens.value,
    interpretationRemainingBalance: interpretationRemainingBalance.value,
    interpretationSavedAt: interpretationSavedAt.value,
  }
}

function persistViewState() {
  if (restoringState) return

  const state = buildPersistedViewState()
  try {
    window.sessionStorage.setItem(REGRESSION_STATE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('Failed to persist regression view state, retrying without embedded plots', error)
    try {
      const fallbackState: PersistedRegressionViewState = {
        ...state,
        linearResult: state.linearResult
          ? {
              ...state.linearResult,
              plots: [],
            }
          : state.linearResult,
        logisticResult: state.logisticResult
          ? {
              ...state.logisticResult,
              plots: [],
            }
          : state.logisticResult,
        lassoResult: state.lassoResult
          ? {
              ...state.lassoResult,
              plots: [],
            }
          : state.lassoResult,
      }
      window.sessionStorage.setItem(REGRESSION_STATE_KEY, JSON.stringify(fallbackState))
    } catch (fallbackError) {
      console.error('Failed to persist regression view state fallback', fallbackError)
    }
  }
}

function loadPersistedViewState() {
  const raw = window.sessionStorage.getItem(REGRESSION_STATE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as PersistedRegressionViewState
  } catch (error) {
    console.error('Failed to parse regression view state', error)
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
    datasetOptions.value = groups.flat().sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
    if (datasetOptions.value.length) {
      selectedDatasetId.value = datasetOptions.value.some((dataset) => dataset.id === savedState?.selectedDatasetId)
        ? savedState?.selectedDatasetId || datasetOptions.value[0].id
        : datasetOptions.value[0].id
      await loadSummary()

      restoringState = true
      alpha.value = savedState?.alpha ?? 0.05
      nfolds.value = savedState?.nfolds ?? 10
      interpretationLanguage.value = savedState?.interpretationLanguage || 'zh'

      const canRestoreExactState = !!savedState && savedState.selectedDatasetId === selectedDatasetId.value
      outcomeVariable.value = canRestoreExactState && outcomeOptions.value.some((column) => column.name === savedState?.outcomeVariable)
        ? savedState?.outcomeVariable || ''
        : ''
      selectedPredictors.value = canRestoreExactState
        ? (savedState?.selectedPredictors || []).filter((name) => predictorOptions.value.some((column) => column.name === name))
        : []

      linearResult.value = props.mode === 'linear' && canRestoreExactState ? savedState?.linearResult || null : null
      logisticResult.value = props.mode === 'logistic' && canRestoreExactState ? savedState?.logisticResult || null : null
      lassoResult.value = props.mode === 'lasso' && canRestoreExactState ? savedState?.lassoResult || null : null
      interpretationContent.value = canRestoreExactState ? savedState?.interpretationContent || '' : ''
      interpretationChargedTokens.value = canRestoreExactState ? savedState?.interpretationChargedTokens || 0 : 0
      interpretationRemainingBalance.value = canRestoreExactState ? savedState?.interpretationRemainingBalance ?? null : null
      interpretationSavedAt.value = canRestoreExactState ? savedState?.interpretationSavedAt || '' : ''
      copiedInterpretation.value = false
      restoringState = false
      persistViewState()
    }
  } catch (error) {
    console.error('Failed to load datasets', error)
    notificationStore.error('数据集加载失败', '无法加载回归分析所需的数据集。')
  } finally {
    loadingDatasets.value = false
  }
}

function handleDatasetChange() {
  outcomeVariable.value = ''
  selectedPredictors.value = []
  resetResults()
  void loadSummary()
}

function handleOutcomeChange() {
  selectedPredictors.value = selectedPredictors.value.filter((name) => name !== outcomeVariable.value)
  resetResults()
}

function togglePredictor(name: string) {
  resetResults()
  if (selectedPredictors.value.includes(name)) {
    selectedPredictors.value = selectedPredictors.value.filter((item) => item !== name)
    return
  }
  selectedPredictors.value = [...selectedPredictors.value, name]
}

function toggleAllPredictors() {
  resetResults()
  if (selectedPredictors.value.length === predictorOptions.value.length) {
    selectedPredictors.value = []
    return
  }
  selectedPredictors.value = predictorOptions.value.map((column) => column.name)
}

function buildInterpretPayload() {
  const current = linearResult.value || logisticResult.value || lassoResult.value
  if (!current) return null
  const payload = JSON.parse(JSON.stringify(current)) as Record<string, unknown>
  delete payload.plots
  return payload
}

async function downloadExcel() {
  const payload = buildInterpretPayload()
  if (!payload) return

  isDownloading.value = true
  try {
    const blob = await downloadRegressionExcel({
      analysis_kind: props.mode,
      payload,
    })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${resultDatasetName.value || 'regression'}_${props.mode}_regression.xlsx`
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

async function loadSavedInterpretation() {
  const payload = buildInterpretPayload()
  if (!payload || !selectedDatasetId.value || !canUseAiInterpretation.value) return

  try {
    const saved = await getSavedRegressionInterpretation({
      dataset_id: selectedDatasetId.value,
      analysis_kind: props.mode,
      language: interpretationLanguage.value,
      payload,
    })
    if (!saved.found) {
      interpretationContent.value = ''
      interpretationChargedTokens.value = 0
      interpretationRemainingBalance.value = null
      interpretationSavedAt.value = ''
      copiedInterpretation.value = false
      return
    }
    interpretationContent.value = saved.content || ''
    interpretationChargedTokens.value = saved.charged_resources || saved.charged_tokens || 0
    interpretationRemainingBalance.value = null
    interpretationSavedAt.value = saved.saved_at || ''
    copiedInterpretation.value = false
  } catch (error) {
    console.error('Failed to load saved regression interpretation', error)
  }
}

async function runAnalysis() {
  if (!selectedDatasetId.value || !outcomeVariable.value || !selectedPredictors.value.length) {
    notificationStore.warning('缺少必要配置', '请先选择数据集、因变量和至少一个自变量。')
    return
  }

  isRunning.value = true
  resetResults()
  try {
    if (props.mode === 'linear') {
      linearResult.value = await runLinearRegression({
        dataset_id: selectedDatasetId.value,
        outcome_variable: outcomeVariable.value,
        predictor_variables: selectedPredictors.value,
        alpha: alpha.value,
      })
    } else if (props.mode === 'logistic') {
      logisticResult.value = await runLogisticRegression({
        dataset_id: selectedDatasetId.value,
        outcome_variable: outcomeVariable.value,
        predictor_variables: selectedPredictors.value,
        alpha: alpha.value,
      })
    } else {
      lassoResult.value = await runLassoRegression({
        dataset_id: selectedDatasetId.value,
        outcome_variable: outcomeVariable.value,
        predictor_variables: selectedPredictors.value,
        alpha: alpha.value,
        nfolds: nfolds.value,
      })
    }
    await loadSavedInterpretation()
    notificationStore.success(`${pageTitle.value}已完成`, '结果表和模型摘要已生成。')
  } catch (error: any) {
    console.error('Failed to run regression', error)
    notificationStore.error(`${pageTitle.value}失败`, error.response?.data?.detail || '请稍后重试。')
  } finally {
    isRunning.value = false
  }
}

async function interpretResult() {
  const payload = buildInterpretPayload()
  if (!payload || !selectedDatasetId.value) return
  if (!canUseAiInterpretation.value) {
    notificationStore.warning('当前不可用', '升级到付费套餐后可使用 AI 回归解读。')
    return
  }

  isInterpreting.value = true
  copiedInterpretation.value = false
  try {
    const result = await interpretRegression({
      dataset_id: selectedDatasetId.value,
      analysis_kind: props.mode,
      language: interpretationLanguage.value,
      payload,
    })
    interpretationContent.value = result.content
    interpretationChargedTokens.value = result.charged_resources || result.charged_tokens
    interpretationRemainingBalance.value = result.remaining_resources ?? result.remaining_balance
    interpretationSavedAt.value = result.saved_at || ''
    if (authStore.user) {
      authStore.user.tokenBalance = result.remaining_resources ?? result.remaining_balance
    }
    notificationStore.success('AI解读已生成', '结果已同步保存到项目结果，刷新后可自动恢复。')
  } catch (error: any) {
    console.error('Failed to interpret regression', error)
    notificationStore.error('AI解读失败', error.response?.data?.detail || '请稍后重试。')
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
  } catch (error) {
    console.error('Failed to copy regression interpretation', error)
    notificationStore.error('复制失败', '当前环境不支持写入剪切板。')
  }
}

function setInterpretationLanguage(language: 'zh' | 'en') {
  if (interpretationLanguage.value === language) return
  interpretationContent.value = ''
  interpretationChargedTokens.value = 0
  interpretationRemainingBalance.value = null
  interpretationSavedAt.value = ''
  copiedInterpretation.value = false
  interpretationLanguage.value = language
  void loadSavedInterpretation()
}

function plotDataUri(plot: LassoPlotPayload) {
  return `data:${plot.media_type};base64,${plot.content_base64}`
}

function downloadPlot(plot: LassoPlotPayload) {
  const anchor = document.createElement('a')
  anchor.href = plotDataUri(plot)
  anchor.download = plot.filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
}

async function downloadPlotPdf(plot: LassoPlotPayload) {
  if (!selectedDatasetId.value) return
  if (!canDownloadPremiumPdf.value) {
    notificationStore.warning('请升级套餐', 'LASSO 图 PDF 导出为付费会员功能，PNG 下载仍可免费使用。')
    return
  }

  downloadingPdfPlot.value = plot.filename
  try {
    const pdf = await downloadLassoPlotPdf({
      dataset_id: selectedDatasetId.value,
      plot,
    })
    const url = window.URL.createObjectURL(pdf.blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = plot.filename.replace(/\.[^.]+$/, '') + '.pdf'
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    window.URL.revokeObjectURL(url)
    if (authStore.user && pdf.remainingResources !== null) {
      authStore.user.tokenBalance = pdf.remainingResources
    }
  } catch (error: any) {
    console.error('Failed to download lasso plot pdf', error)
    notificationStore.error('PDF 下载失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    downloadingPdfPlot.value = ''
  }
}

async function downloadLinearPlotPdfAction(plot: LassoPlotPayload) {
  if (!selectedDatasetId.value) return
  if (!canDownloadPremiumPdf.value) {
    notificationStore.warning('请升级套餐', '线性回归高清 PDF 导出为付费会员功能，PNG 下载仍可免费使用。')
    return
  }

  downloadingPdfPlot.value = plot.filename
  try {
    const pdf = await downloadLinearPlotPdf({
      dataset_id: selectedDatasetId.value,
      plot,
    })
    const url = window.URL.createObjectURL(pdf.blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = plot.filename.replace(/\.[^.]+$/, '') + '.pdf'
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    window.URL.revokeObjectURL(url)
    if (authStore.user && pdf.remainingResources !== null) {
      authStore.user.tokenBalance = pdf.remainingResources
    }
  } catch (error: any) {
    console.error('Failed to download linear plot pdf', error)
    notificationStore.error('PDF 下载失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    downloadingPdfPlot.value = ''
  }
}

async function downloadLogisticPlotPdfAction(plot: LassoPlotPayload) {
  if (!selectedDatasetId.value) return
  if (!canDownloadPremiumPdf.value) {
    notificationStore.warning('请升级套餐', 'Logistic 回归森林图高清 PDF 导出为付费会员功能，PNG 下载仍可免费使用。')
    return
  }

  downloadingPdfPlot.value = plot.filename
  try {
    const pdf = await downloadLogisticPlotPdf({
      dataset_id: selectedDatasetId.value,
      plot,
    })
    const url = window.URL.createObjectURL(pdf.blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = plot.filename.replace(/\.[^.]+$/, '') + '.pdf'
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    window.URL.revokeObjectURL(url)
    if (authStore.user && pdf.remainingResources !== null) {
      authStore.user.tokenBalance = pdf.remainingResources
    }
  } catch (error: any) {
    console.error('Failed to download logistic plot pdf', error)
    notificationStore.error('PDF 下载失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    downloadingPdfPlot.value = ''
  }
}

watch(
  [
    selectedDatasetId,
    outcomeVariable,
    selectedPredictors,
    alpha,
    nfolds,
    interpretationLanguage,
    linearResult,
    logisticResult,
    lassoResult,
    interpretationContent,
    interpretationChargedTokens,
    interpretationRemainingBalance,
    interpretationSavedAt,
  ],
  () => {
    persistViewState()
  },
  { deep: true },
)

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

.linear-diagnostic-image {
  width: 100%;
  background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 18%);
  object-fit: contain;
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
