<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Project Header -->
    <div class="card bg-gradient-to-r from-primary-50 to-white">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-heading font-bold text-gray-900">糖尿病患者预后分析</h1>
            <p class="text-sm text-gray-500 mt-0.5">回顾性队列研究 · 创建于 2026年2月15日</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="badge-primary">进行中</span>
          <button class="btn-ghost btn-sm">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09"/>
            </svg>
            设置
          </button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 border-b border-gray-200">
      <button v-for="tab in tabs" :key="tab.id"
        @click="activeTab = tab.id"
        :class="['px-4 py-3 text-sm font-medium border-b-2 transition-colors cursor-pointer', activeTab === tab.id ? 'text-primary border-primary' : 'text-gray-500 border-transparent hover:text-gray-700']"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content: Overview -->
    <div v-if="activeTab === 'overview'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="card">
          <h2 class="text-lg font-heading font-semibold text-gray-900 mb-3">项目描述</h2>
          <p class="text-gray-600 leading-relaxed">基于2,450例2型糖尿病患者的回顾性队列研究，评估不同口服降糖药物方案对HbA1c控制、心血管事件和全因死亡率的长期影响。</p>
        </div>

        <div class="card">
          <h2 class="text-lg font-heading font-semibold text-gray-900 mb-4">最近活动</h2>
          <div class="space-y-4">
            <div v-for="activity in activities" :key="activity.id" class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg class="w-4 h-4 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="activity.icon"></svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-gray-900">{{ activity.text }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ activity.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="card">
          <h3 class="text-sm font-semibold text-gray-900 mb-3">项目统计</h3>
          <div class="space-y-3">
            <div class="flex justify-between text-sm"><span class="text-gray-500">数据集</span><span class="font-medium text-gray-900">3</span></div>
            <div class="flex justify-between text-sm"><span class="text-gray-500">分析任务</span><span class="font-medium text-gray-900">5</span></div>
            <div class="flex justify-between text-sm"><span class="text-gray-500">已生成报告</span><span class="font-medium text-gray-900">2</span></div>
            <div class="flex justify-between text-sm"><span class="text-gray-500">Token 消耗</span><span class="font-medium text-gray-900">320</span></div>
          </div>
        </div>

        <div class="card">
          <h3 class="text-sm font-semibold text-gray-900 mb-3">团队成员</h3>
          <div class="space-y-2">
            <div v-for="member in members" :key="member.name" class="flex items-center gap-3">
              <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium', member.bg]">{{ member.initial }}</div>
              <div>
                <p class="text-sm font-medium text-gray-900">{{ member.name }}</p>
                <p class="text-xs text-gray-400">{{ member.role }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Content: Data -->
    <div v-if="activeTab === 'data'" class="card text-center py-12">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-600">数据管理</h3>
      <p class="text-gray-400 mt-1">上传和管理项目数据集</p>
      <button class="btn-primary mt-4">上传数据</button>
    </div>

    <!-- Tab Content: Analysis -->
    <div v-if="activeTab === 'analysis'" class="card text-center py-12">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-600">统计分析</h3>
      <p class="text-gray-400 mt-1">创建和管理分析任务</p>
      <button class="btn-primary mt-4">创建分析</button>
    </div>

    <!-- Tab Content: Reports -->
    <div v-if="activeTab === 'reports'" class="card text-center py-12">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-600">报告中心</h3>
      <p class="text-gray-400 mt-1">生成和导出分析报告</p>
      <button class="btn-primary mt-4">生成报告</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('overview')

const tabs = [
  { id: 'overview', label: '概览' },
  { id: 'data', label: '数据管理' },
  { id: 'analysis', label: '统计分析' },
  { id: 'reports', label: '报告' },
]

const activities = [
  { id: 1, text: '完成了 Cox回归分析 任务', time: '2小时前', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
  { id: 2, text: '上传了数据集 patient_followup_2026.csv', time: '5小时前', icon: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>' },
  { id: 3, text: '更新了数据字典', time: '昨天', icon: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>' },
  { id: 4, text: '生成了描述统计报告', time: '2天前', icon: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>' },
]

const members = [
  { name: '张医生', role: '项目负责人', initial: '张', bg: 'bg-primary' },
  { name: '李研究员', role: '数据分析', initial: '李', bg: 'bg-secondary' },
  { name: '王助理', role: '数据录入', initial: '王', bg: 'bg-amber-500' },
]
</script>
