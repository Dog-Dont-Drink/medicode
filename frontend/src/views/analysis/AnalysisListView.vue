<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-heading font-bold text-gray-900">分析列表</h1>
        <p class="text-gray-500 mt-1">查看和管理统计分析任务</p>
      </div>
      <button class="btn-primary">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        创建分析
      </button>
    </div>

    <div class="space-y-4">
      <div v-for="analysis in analyses" :key="analysis.id" class="card-hover">
        <div class="flex items-start gap-4">
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0', analysis.bgColor]">
            <svg class="w-5 h-5" :class="analysis.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="analysis.icon"></svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="text-base font-medium text-gray-900">{{ analysis.name }}</h3>
              <span :class="['badge', analysis.statusClass]">{{ analysis.status }}</span>
            </div>
            <p class="text-sm text-gray-500 mt-1">{{ analysis.method }} · {{ analysis.variables }}</p>
            <div class="flex items-center gap-4 mt-3 text-xs text-gray-400">
              <span>创建于 {{ analysis.createdAt }}</span>
              <span>耗时 {{ analysis.duration }}</span>
              <span>资源: {{ analysis.tokens }}</span>
            </div>
          </div>
          <button class="btn-ghost btn-sm flex-shrink-0">查看结果</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const analyses = [
  { id: 1, name: '基线特征描述统计', method: '描述统计', variables: '28个变量', status: '已完成', statusClass: 'badge-success', bgColor: 'bg-green-50', iconColor: 'text-green-500', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>', createdAt: '2天前', duration: '12秒', tokens: '50' },
  { id: 2, name: '治疗方案与预后的关联', method: 'Cox比例风险回归', variables: 'treatment → outcome', status: '进行中', statusClass: 'badge-primary', bgColor: 'bg-primary-50', iconColor: 'text-primary', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>', createdAt: '1天前', duration: '运行中...', tokens: '120' },
  { id: 3, name: 'BMI与HbA1c相关性', method: '线性回归', variables: 'bmi → hba1c', status: '已完成', statusClass: 'badge-success', bgColor: 'bg-blue-50', iconColor: 'text-blue-500', icon: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>', createdAt: '3天前', duration: '8秒', tokens: '40' },
  { id: 4, name: '亚组分析：性别差异', method: '亚组分析', variables: 'gender分层', status: '待审核', statusClass: 'badge-warning', bgColor: 'bg-amber-50', iconColor: 'text-amber-500', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>', createdAt: '5天前', duration: '25秒', tokens: '80' },
]
</script>
