<template>
  <!-- Mobile overlay -->
  <transition name="fade">
    <div v-if="open" class="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden" @click="$emit('close')"></div>
  </transition>

  <!-- Sidebar -->
  <aside
    :class="[
      'fixed top-0 left-0 bottom-0 w-[240px] z-40',
      'bg-white border-r border-gray-100',
      'flex flex-col',
      'transform transition-transform duration-300 ease-in-out',
      open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-2.5 px-5 h-16 border-b border-gray-100">
      <div class="w-8 h-8 bg-gradient-to-br from-primary to-primary-600 rounded-lg flex items-center justify-center">
        <svg class="w-4.5 h-4.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
      </div>
      <span class="text-base font-heading font-bold text-gray-900">MediCode</span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-3 px-3 scrollbar-hide">
      <!-- Main -->
      <div class="space-y-0.5">
        <router-link to="/dashboard" :class="linkClass('/dashboard')" @click="$emit('close')">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
          <span>工作台</span>
        </router-link>

        <router-link to="/projects" :class="linkClass('/projects')" @click="$emit('close')">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
          <span>我的项目</span>
        </router-link>

        <div
          class="group space-y-0.5"
          @mouseenter="hoveredSection = 'data'"
          @mouseleave="hoveredSection = null"
        >
          <router-link to="/data" :class="linkClass('/data')" @click="$emit('close')">
            <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            <span>数据管理</span>
          </router-link>
          <div :class="['ml-[26px] mt-1 pl-3 border-l border-gray-100 space-y-0.5', isSectionExpanded('data') ? 'block' : 'hidden']">
            <router-link to="/data" :class="subLinkClass('/data', true)" @click="$emit('close')">
              数据上传
            </router-link>
            <router-link to="/data/cleaning" :class="subLinkClass('/data/cleaning', true)" @click="$emit('close')">
              数据清洗
            </router-link>
          </div>
        </div>
      </div>

      <!-- Divider + Section label -->
      <div class="mt-5 mb-2 px-2">
        <p class="text-[11px] font-medium text-gray-400 tracking-wide">统计分析</p>
      </div>

      <div class="space-y-0.5">
        <!-- Collapsible: 基础统计 -->
        <div class="group space-y-0.5" @mouseenter="hoveredSection = 'basic'" @mouseleave="hoveredSection = null">
        <button class="nav-group-btn" type="button">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          <span class="flex-1 text-left">基础统计</span>
          <svg :class="['w-3.5 h-3.5 text-gray-300 transition-transform duration-200', isSectionExpanded('basic') && 'rotate-90']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <div v-if="isSectionExpanded('basic')" class="ml-[26px] pl-3 border-l border-gray-100 space-y-0.5 pb-1">
          <router-link to="/analysis/descriptive" :class="subLinkClass('/analysis/descriptive', true)" @click="$emit('close')">
            描述统计
          </router-link>
          <router-link to="/analysis/t-test" :class="subLinkClass('/analysis/t-test', true)" @click="$emit('close')">
            两组间连续变量统计
          </router-link>
          <router-link to="/analysis/anova" :class="subLinkClass('/analysis/anova', true)" @click="$emit('close')">
            多组间连续变量统计
          </router-link>
          <router-link to="/analysis/repeated-measures-anova" :class="subLinkClass('/analysis/repeated-measures-anova', true)" @click="$emit('close')">
            重复测量方差分析
          </router-link>
          <router-link to="/analysis/chi-square" :class="subLinkClass('/analysis/chi-square', true)" @click="$emit('close')">
            卡方检验
          </router-link>
        </div>
        </div>

        <!-- 回归分析 -->
        <div class="group space-y-0.5" @mouseenter="hoveredSection = 'regression'" @mouseleave="hoveredSection = null">
        <button class="nav-group-btn" type="button">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
          <span class="flex-1 text-left">回归分析</span>
          <svg :class="['w-3.5 h-3.5 text-gray-300 transition-transform duration-200', isSectionExpanded('regression') && 'rotate-90']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <div v-if="isSectionExpanded('regression')" class="ml-[26px] pl-3 border-l border-gray-100 space-y-0.5 pb-1">
          <a v-for="s in regressionItems" :key="s" class="sub-link">{{ s }}</a>
        </div>
        </div>

        <!-- 生存分析 -->
        <div class="group space-y-0.5" @mouseenter="hoveredSection = 'survival'" @mouseleave="hoveredSection = null">
        <button class="nav-group-btn" type="button">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><polyline points="14 7 21 7 21 14"/></svg>
          <span class="flex-1 text-left">生存分析</span>
          <svg :class="['w-3.5 h-3.5 text-gray-300 transition-transform duration-200', isSectionExpanded('survival') && 'rotate-90']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <div v-if="isSectionExpanded('survival')" class="ml-[26px] pl-3 border-l border-gray-100 space-y-0.5 pb-1">
          <a v-for="s in survivalItems" :key="s" class="sub-link">{{ s }}</a>
        </div>
        </div>

        <!-- 高级分析 -->
        <div class="group space-y-0.5" @mouseenter="hoveredSection = 'advanced'" @mouseleave="hoveredSection = null">
        <button class="nav-group-btn" type="button">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12c0-5.52 4.48-10 10-10"/></svg>
          <span class="flex-1 text-left">高级分析</span>
          <svg :class="['w-3.5 h-3.5 text-gray-300 transition-transform duration-200', isSectionExpanded('advanced') && 'rotate-90']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <div v-if="isSectionExpanded('advanced')" class="ml-[26px] pl-3 border-l border-gray-100 space-y-0.5 pb-1">
          <a v-for="s in advancedItems" :key="s" class="sub-link">{{ s }}</a>
        </div>
        </div>
      </div>

      <!-- Divider -->
      <div class="mt-5 mb-2 px-2">
        <p class="text-[11px] font-medium text-gray-400 tracking-wide">其他</p>
      </div>

      <div class="space-y-0.5">
        <router-link to="/reports" :class="linkClass('/reports')" @click="$emit('close')">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <span>报告中心</span>
        </router-link>

        <router-link to="/account/billing" :class="linkClass('/account/billing')" @click="$emit('close')">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/></svg>
          <span>Token 充值</span>
        </router-link>
      </div>
    </nav>

    <!-- Bottom -->
    <div class="p-3 border-t border-gray-100">
      <router-link to="/account/settings" :class="linkClass('/account')" @click="$emit('close')">
        <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09"/></svg>
        <span>设置</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

const route = useRoute()
const hoveredSection = ref<string | null>(null)

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function isSectionExpanded(id: string) {
  return hoveredSection.value === id
}

function linkClass(path: string) {
  return [
    'flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 cursor-pointer',
    isActive(path)
      ? 'bg-primary-50 text-primary'
      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
  ]
}

function subLinkClass(path: string, exact = false) {
  return [
    'block px-2.5 py-1.5 rounded-md text-[12px] transition-all duration-150 cursor-pointer',
    (exact ? route.path === path : isActive(path))
      ? 'bg-primary-50 text-primary font-medium'
      : 'text-gray-400 hover:text-primary hover:bg-primary-50/70'
  ]
}

const regressionItems = ['线性回归', 'Logistic 回归', '多元回归', '岭回归 / LASSO']
const survivalItems = ['KM 生存曲线', 'Cox 回归', 'Log-rank 检验', '竞争风险模型']
const advancedItems = ['ROC 曲线', 'Meta 分析', '倾向评分匹配', '亚组分析', '诊断试验']
</script>

<style scoped>
.nav-group-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
  background: none;
  border: none;
}
.nav-group-btn:hover {
  color: #111827;
  background: #f9fafb;
}
</style>
