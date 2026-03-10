<template>
  <div class="max-w-3xl mx-auto space-y-6 animate-fade-in">
    <div>
      <h1 class="text-2xl font-heading font-bold text-gray-900">创建分析</h1>
      <p class="text-gray-500 mt-1">选择统计分析方法并配置参数</p>
    </div>

    <!-- Step indicator -->
    <div class="flex items-center gap-2 px-4">
      <div v-for="(step, i) in steps" :key="i" class="flex items-center gap-2 flex-1">
        <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium', currentStep >= i ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500']">{{ i + 1 }}</div>
        <span :class="['text-sm hidden sm:block', currentStep >= i ? 'text-gray-900 font-medium' : 'text-gray-400']">{{ step }}</span>
        <div v-if="i < steps.length - 1" class="flex-1 h-px bg-gray-200 mx-2"></div>
      </div>
    </div>

    <!-- Step 1: Select Method -->
    <div v-if="currentStep === 0" class="card space-y-4">
      <h2 class="text-lg font-heading font-semibold text-gray-900">选择分析方法</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button v-for="method in methods" :key="method.id"
          @click="selectedMethod = method.id; currentStep = 1"
          :class="['text-left p-4 rounded-xl border transition-all cursor-pointer', selectedMethod === method.id ? 'border-primary bg-primary-50' : 'border-gray-200 hover:border-primary/30 hover:bg-gray-50']"
        >
          <div :class="['w-8 h-8 rounded-lg flex items-center justify-center mb-2', method.bgColor]">
            <svg class="w-4 h-4" :class="method.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="method.icon"></svg>
          </div>
          <p class="text-sm font-medium text-gray-900">{{ method.name }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ method.desc }}</p>
        </button>
      </div>
    </div>

    <!-- Step 2: Configure Variables -->
    <div v-if="currentStep === 1" class="card space-y-4">
      <h2 class="text-lg font-heading font-semibold text-gray-900">配置变量</h2>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">因变量 (Y)</label>
        <select class="input-field">
          <option value="">选择因变量...</option>
          <option>outcome</option><option>hba1c</option><option>follow_up_months</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">自变量 (X)</label>
        <div class="flex flex-wrap gap-2">
          <button v-for="v in ['age', 'gender', 'bmi', 'treatment', 'hba1c']" :key="v"
            @click="toggleVar(v)"
            :class="['px-3 py-1.5 rounded-lg text-sm transition-all cursor-pointer', selectedVars.includes(v) ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']"
          >{{ v }}</button>
        </div>
      </div>
      <div class="flex justify-between pt-4">
        <button @click="currentStep = 0" class="btn-ghost">上一步</button>
        <button @click="currentStep = 2" class="btn-primary">下一步</button>
      </div>
    </div>

    <!-- Step 3: Confirm & Run -->
    <div v-if="currentStep === 2" class="card space-y-4">
      <h2 class="text-lg font-heading font-semibold text-gray-900">确认并运行</h2>
      <div class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
        <div class="flex justify-between"><span class="text-gray-500">分析方法</span><span class="font-medium text-gray-900">{{ methods.find(m => m.id === selectedMethod)?.name }}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">自变量</span><span class="font-medium text-gray-900">{{ selectedVars.join(', ') || '未选择' }}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">会员功能扣费</span><span class="font-medium text-primary">AI解读 / PDF 导出各扣 1 资源</span></div>
      </div>
      <div class="flex justify-between pt-4">
        <button @click="currentStep = 1" class="btn-ghost">上一步</button>
        <button class="btn-primary">开始分析</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const currentStep = ref(0)
const selectedMethod = ref('')
const selectedVars = ref<string[]>([])
const steps = ['选择方法', '配置变量', '确认运行']

function toggleVar(v: string) {
  const idx = selectedVars.value.indexOf(v)
  if (idx >= 0) selectedVars.value.splice(idx, 1)
  else selectedVars.value.push(v)
}

const methods = [
  { id: 'descriptive', name: '描述统计', desc: '均值、中位数、标准差等', bgColor: 'bg-green-50', iconColor: 'text-green-500', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { id: 'ttest', name: '假设检验', desc: 'T检验、卡方检验等', bgColor: 'bg-blue-50', iconColor: 'text-blue-500', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
  { id: 'regression', name: '回归分析', desc: '线性、Logistic回归', bgColor: 'bg-purple-50', iconColor: 'text-purple-500', icon: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>' },
  { id: 'survival', name: '生存分析', desc: 'KM曲线、Cox回归', bgColor: 'bg-primary-50', iconColor: 'text-primary', icon: '<path d="M3 17l6-6 4 4 8-8"/><polyline points="14 7 21 7 21 14"/>' },
  { id: 'prediction', name: '预测模型', desc: 'ROC、校准曲线', bgColor: 'bg-amber-50', iconColor: 'text-amber-500', icon: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>' },
  { id: 'diagnostic', name: '诊断试验', desc: '灵敏度、特异度', bgColor: 'bg-rose-50', iconColor: 'text-rose-500', icon: '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' },
]
</script>
