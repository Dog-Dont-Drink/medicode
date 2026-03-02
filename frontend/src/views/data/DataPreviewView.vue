<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-heading font-bold text-gray-900">数据预览</h1>
        <p class="text-gray-500 mt-1">patient_data_2026.csv · 2,450行 × 28列</p>
      </div>
      <div class="flex gap-2">
        <button class="btn-ghost btn-sm">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          导出
        </button>
        <button class="btn-primary btn-sm">编辑数据字典</button>
      </div>
    </div>

    <!-- Data Table Preview -->
    <div class="card p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-200">
              <th v-for="col in columns" :key="col" class="px-4 py-3 text-left font-semibold text-gray-700 whitespace-nowrap">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in rows" :key="i" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
              <td v-for="col in columns" :key="col" class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ row[col] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
        <p class="text-sm text-gray-500">显示 1-10 of 2,450 条记录</p>
        <div class="flex gap-1">
          <button class="px-3 py-1 text-sm rounded bg-primary text-white cursor-pointer">1</button>
          <button class="px-3 py-1 text-sm rounded hover:bg-gray-200 text-gray-600 cursor-pointer">2</button>
          <button class="px-3 py-1 text-sm rounded hover:bg-gray-200 text-gray-600 cursor-pointer">3</button>
          <span class="px-2 py-1 text-sm text-gray-400">...</span>
          <button class="px-3 py-1 text-sm rounded hover:bg-gray-200 text-gray-600 cursor-pointer">245</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const columns = ['patient_id', 'age', 'gender', 'bmi', 'hba1c', 'treatment', 'outcome', 'follow_up_months']

const rows: Record<string, any>[] = Array.from({ length: 10 }, (_, i) => ({
  patient_id: `P${String(1001 + i).padStart(4, '0')}`,
  age: Math.floor(Math.random() * 40 + 30),
  gender: Math.random() > 0.5 ? '男' : '女',
  bmi: (Math.random() * 15 + 20).toFixed(1),
  hba1c: (Math.random() * 5 + 5).toFixed(1),
  treatment: ['二甲双胍', '格列齐特', '联合用药', '胰岛素'][Math.floor(Math.random() * 4)],
  outcome: Math.random() > 0.7 ? '事件' : '无事件',
  follow_up_months: Math.floor(Math.random() * 60 + 12),
}))
</script>
