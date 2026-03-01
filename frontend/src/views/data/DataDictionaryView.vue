<template>
  <div class="space-y-6 animate-fade-in">
    <div>
      <h1 class="text-2xl font-heading font-bold text-gray-900">数据字典</h1>
      <p class="text-gray-500 mt-1">定义和管理数据集中各变量的含义和类型</p>
    </div>
    <div class="card p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="bg-gray-50 border-b border-gray-200">
            <th class="px-4 py-3 text-left font-semibold text-gray-700">变量名</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">标签</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">类型</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">缺失值</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="v in variables" :key="v.name" class="border-b border-gray-50 hover:bg-gray-50/50">
              <td class="px-4 py-3 font-mono text-primary text-sm">{{ v.name }}</td>
              <td class="px-4 py-3 text-gray-700">{{ v.label }}</td>
              <td class="px-4 py-3"><span :class="['badge', v.typeClass]">{{ v.type }}</span></td>
              <td class="px-4 py-3 text-gray-500">{{ v.missing }}</td>
              <td class="px-4 py-3"><button class="text-primary text-sm hover:underline cursor-pointer">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const variables = [
  { name: 'patient_id', label: '患者编号', type: '字符串', typeClass: 'badge-primary', missing: '0 (0%)' },
  { name: 'age', label: '年龄', type: '连续', typeClass: 'badge-success', missing: '12 (0.5%)' },
  { name: 'gender', label: '性别', type: '分类', typeClass: 'badge-warning', missing: '0 (0%)' },
  { name: 'bmi', label: '体重指数', type: '连续', typeClass: 'badge-success', missing: '45 (1.8%)' },
  { name: 'hba1c', label: '糖化血红蛋白', type: '连续', typeClass: 'badge-success', missing: '23 (0.9%)' },
  { name: 'treatment', label: '治疗方案', type: '分类', typeClass: 'badge-warning', missing: '0 (0%)' },
  { name: 'outcome', label: '结局事件', type: '二分类', typeClass: 'badge-danger', missing: '5 (0.2%)' },
  { name: 'follow_up_months', label: '随访时间(月)', type: '连续', typeClass: 'badge-success', missing: '0 (0%)' },
]
</script>
