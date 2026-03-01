<template>
  <div class="space-y-8 animate-fade-in" id="dashboard-view">
    <!-- Welcome Section -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 class="text-2xl md:text-3xl font-heading font-bold text-gray-900">
          你好，{{ userName }} 👋
        </h1>
        <p class="text-gray-500 mt-1">欢迎回到 MediCode，以下是您的工作概览</p>
      </div>
      <router-link to="/projects/new" class="btn-primary">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        新建项目
      </router-link>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <div v-for="stat in stats" :key="stat.title" class="card-hover group">
        <div class="flex items-start justify-between">
          <div :class="['w-11 h-11 rounded-xl flex items-center justify-center', stat.bgColor]">
            <svg class="w-5 h-5" :class="stat.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="stat.iconPath"></svg>
          </div>
          <div :class="['flex items-center gap-1 text-sm font-medium', stat.changeColor]">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline :points="stat.changeUp ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/>
            </svg>
            {{ stat.change }}
          </div>
        </div>
        <div class="mt-4">
          <p class="text-3xl font-heading font-bold text-gray-900">{{ stat.value }}</p>
          <p class="text-sm text-gray-500 mt-1">{{ stat.title }}</p>
        </div>
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent Projects (2/3) -->
      <div class="lg:col-span-2 card">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-heading font-semibold text-gray-900">最近项目</h2>
          <router-link to="/projects" class="text-sm text-primary hover:text-primary-600 transition-colors cursor-pointer">
            查看全部
          </router-link>
        </div>

        <div class="space-y-3">
          <div v-for="project in recentProjects" :key="project.id"
            class="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50/80 transition-colors cursor-pointer group"
          >
            <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', project.bgColor]">
              <svg class="w-5 h-5" :class="project.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate group-hover:text-primary transition-colors">{{ project.name }}</p>
              <p class="text-xs text-gray-500 mt-0.5">{{ project.description }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <span :class="['badge', project.statusClass]">{{ project.status }}</span>
              <p class="text-xs text-gray-400 mt-1">{{ project.updatedAt }}</p>
            </div>
          </div>
        </div>

        <div v-if="recentProjects.length === 0" class="text-center py-12">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
          <p class="text-gray-500">暂无项目</p>
          <router-link to="/projects/new" class="text-sm text-primary hover:underline mt-1 inline-block cursor-pointer">创建第一个项目</router-link>
        </div>
      </div>

      <!-- Token Overview (1/3) -->
      <div class="card">
        <h2 class="text-lg font-heading font-semibold text-gray-900 mb-6">Token 概览</h2>

        <!-- Token Balance Circle -->
        <div class="flex flex-col items-center mb-6">
          <div class="relative w-32 h-32">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" stroke="#E2E8F0" stroke-width="8" fill="none"/>
              <circle cx="60" cy="60" r="52" stroke="url(#gradient)" stroke-width="8" fill="none"
                stroke-linecap="round" :stroke-dasharray="326.73" :stroke-dashoffset="326.73 * (1 - tokenUsagePercent / 100)"/>
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#059669"/>
                  <stop offset="100%" stop-color="#22C55E"/>
                </linearGradient>
              </defs>
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-2xl font-heading font-bold text-gray-900">{{ tokenBalance }}</span>
              <span class="text-xs text-gray-500">剩余 Token</span>
            </div>
          </div>
        </div>

        <!-- Token Details -->
        <div class="space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">本月已用</span>
            <span class="font-medium text-gray-900">{{ tokenUsed }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-500">总额度</span>
            <span class="font-medium text-gray-900">{{ tokenTotal }}</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2 mt-2">
            <div class="bg-gradient-to-r from-primary to-secondary rounded-full h-2 transition-all duration-500" :style="{ width: tokenUsagePercent + '%' }"></div>
          </div>
        </div>

        <router-link to="/account/billing" class="btn-secondary w-full mt-6 text-sm">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/>
          </svg>
          购买更多 Token
        </router-link>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card">
      <h2 class="text-lg font-heading font-semibold text-gray-900 mb-4">快速开始</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <router-link v-for="action in quickActions" :key="action.label" :to="action.route"
          class="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:border-primary/30 hover:bg-primary-50/30 transition-all duration-200 cursor-pointer group"
        >
          <div :class="['w-10 h-10 rounded-lg flex items-center justify-center transition-colors', action.bgColor, 'group-hover:' + action.bgColorHover]">
            <svg class="w-5 h-5" :class="action.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="action.iconPath"></svg>
          </div>
          <div class="text-left">
            <p class="text-sm font-medium text-gray-900">{{ action.label }}</p>
            <p class="text-xs text-gray-500">{{ action.desc }}</p>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const userName = computed(() => authStore.user?.name || '用户')
const tokenBalance = computed(() => '1,500')
const tokenUsed = computed(() => '500')
const tokenTotal = computed(() => '2,000')
const tokenUsagePercent = computed(() => 25)

const stats = [
  {
    title: '活跃项目',
    value: '12',
    change: '+2',
    changeUp: true,
    changeColor: 'text-green-600',
    bgColor: 'bg-primary-50',
    iconColor: 'text-primary',
    iconPath: '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>',
  },
  {
    title: '数据集',
    value: '36',
    change: '+5',
    changeUp: true,
    changeColor: 'text-green-600',
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
    iconPath: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  },
  {
    title: '分析任务',
    value: '8',
    change: '+3',
    changeUp: true,
    changeColor: 'text-green-600',
    bgColor: 'bg-purple-50',
    iconColor: 'text-purple-500',
    iconPath: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
  },
  {
    title: 'Token 余额',
    value: '1,500',
    change: '-120',
    changeUp: false,
    changeColor: 'text-amber-600',
    bgColor: 'bg-green-50',
    iconColor: 'text-green-500',
    iconPath: '<circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/>',
  },
]

const recentProjects = [
  {
    id: '1',
    name: '糖尿病患者预后分析',
    description: '回顾性队列研究 · 2,450 样本',
    status: '进行中',
    statusClass: 'badge-primary',
    updatedAt: '2小时前',
    bgColor: 'bg-primary-50',
    iconColor: 'text-primary',
  },
  {
    id: '2',
    name: '肺癌生存分析',
    description: 'Cox回归 · KM曲线 · 1,200 样本',
    status: '已完成',
    statusClass: 'badge-success',
    updatedAt: '昨天',
    bgColor: 'bg-green-50',
    iconColor: 'text-green-500',
  },
  {
    id: '3',
    name: '心血管风险预测模型',
    description: 'Logistic回归 · ROC分析 · 5,600 样本',
    status: '进行中',
    statusClass: 'badge-primary',
    updatedAt: '3天前',
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    id: '4',
    name: '临床试验数据清洗',
    description: '缺失值处理 · 异常值检测 · 800 样本',
    status: '待审核',
    statusClass: 'badge-warning',
    updatedAt: '1周前',
    bgColor: 'bg-amber-50',
    iconColor: 'text-amber-500',
  },
]

const quickActions = [
  {
    label: '上传数据',
    desc: '导入CSV/Excel',
    route: '/data',
    bgColor: 'bg-primary-50',
    bgColorHover: 'bg-primary-100',
    iconColor: 'text-primary',
    iconPath: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
  },
  {
    label: '创建分析',
    desc: '选择统计方法',
    route: '/analysis/new',
    bgColor: 'bg-purple-50',
    bgColorHover: 'bg-purple-100',
    iconColor: 'text-purple-500',
    iconPath: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  },
  {
    label: '生成报告',
    desc: '导出分析结果',
    route: '/reports',
    bgColor: 'bg-blue-50',
    bgColorHover: 'bg-blue-100',
    iconColor: 'text-blue-500',
    iconPath: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
  },
  {
    label: '购买Token',
    desc: '充值分析额度',
    route: '/account/billing',
    bgColor: 'bg-green-50',
    bgColorHover: 'bg-green-100',
    iconColor: 'text-green-500',
    iconPath: '<circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/>',
  },
]
</script>
