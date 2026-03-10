<template>
  <div class="min-h-screen bg-white">
    <!-- ===== Navbar ===== -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <router-link to="/" class="flex items-center gap-2.5 cursor-pointer">
            <div class="w-9 h-9 bg-gradient-to-br from-primary to-primary-600 rounded-xl flex items-center justify-center shadow-sm">
              <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <span class="text-xl font-heading font-bold text-gray-900">MediCode</span>
          </router-link>

          <!-- Desktop Nav -->
          <div class="hidden md:flex items-center gap-8">
            <a href="#features" class="text-sm text-gray-600 hover:text-primary transition-colors cursor-pointer">功能特色</a>
            <a href="#stats" class="text-sm text-gray-600 hover:text-primary transition-colors cursor-pointer">数据实力</a>
            <a href="#workflow" class="text-sm text-gray-600 hover:text-primary transition-colors cursor-pointer">工作流程</a>
            <a href="#pricing" class="text-sm text-gray-600 hover:text-primary transition-colors cursor-pointer">价格方案</a>
          </div>

          <div class="flex items-center gap-3">
            <router-link to="/auth/login" class="text-sm font-medium text-gray-700 hover:text-primary transition-colors cursor-pointer hidden sm:block">登录</router-link>
            <router-link to="/auth/register" class="btn-primary btn-sm">免费开始</router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- ===== Hero Section ===== -->
    <section class="relative pt-32 pb-20 lg:pt-40 lg:pb-28 overflow-hidden">
      <!-- Background decorations -->
      <div class="absolute inset-0 pointer-events-none overflow-hidden">
        <div class="absolute -top-24 -right-24 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl"></div>
        <div class="absolute top-1/2 -left-32 w-[400px] h-[400px] bg-secondary/5 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-1/3 w-[300px] h-[300px] bg-accent/5 rounded-full blur-3xl"></div>
        <!-- Grid background -->
        <div class="absolute inset-0 opacity-[0.03]" style="background-image: radial-gradient(circle, #059669 1px, transparent 1px); background-size: 32px 32px;"></div>
      </div>

      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-10 items-center">
          <!-- Text Content -->
          <div class="lg:col-span-7 text-center lg:text-left animate-fade-in">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 bg-primary-50 text-primary text-sm font-medium rounded-full mb-6">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              专业级医学统计分析
            </div>

            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold text-gray-900 leading-tight">
              让医学数据
              <span class="text-gradient bg-gradient-to-r from-primary via-accent to-secondary">
                说话
              </span>
            </h1>

            <p class="mt-6 text-lg lg:text-xl text-gray-600 leading-relaxed max-w-xl mx-auto lg:mx-0">
              无需编程，零代码实现专业统计分析。从描述统计到生存分析，一站式覆盖临床研究全流程。
            </p>

            <div class="mt-8 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <router-link to="/auth/register" class="btn-primary btn-lg shadow-card hover:shadow-elevated transition-shadow">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                免费注册使用
              </router-link>
              <a href="#features" class="btn-ghost btn-lg group">
                了解更多
                <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                </svg>
              </a>
            </div>

            <!-- Trust signals -->
            <div class="mt-10 flex items-center gap-6 justify-center lg:justify-start text-sm text-gray-400">
              <div class="flex items-center gap-1.5">
                <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                HIPAA 合规
              </div>
              <div class="flex items-center gap-1.5">
                <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                数据加密
              </div>
              <div class="flex items-center gap-1.5">
                <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                可复现脚本
              </div>
            </div>
          </div>

          <!-- Hero Visual -->
          <div class="lg:col-span-5 relative animate-slide-up flex justify-center">
            <div class="relative max-w-md w-full">
              <!-- Image with no white edge -->
              <div class="relative w-full aspect-[4/3] rounded-2xl overflow-hidden" style="background: linear-gradient(135deg, #e0f7fa 0%, #e8f5e9 100%);">
                <img src="/hero-image.png" alt="MediCode 医学统计分析平台" class="absolute inset-0 w-full h-full object-cover" />
              </div>
              <!-- Floating cards -->
              <div class="absolute -bottom-3 -left-3 bg-white rounded-xl shadow-elevated py-2.5 px-3 animate-pulse-soft hidden sm:block">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center">
                    <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-gray-900">分析完成</p>
                    <p class="text-[10px] text-gray-500">P < 0.001 · 显著差异</p>
                  </div>
                </div>
              </div>
              <div class="absolute -top-3 -right-3 bg-white rounded-xl shadow-elevated py-2.5 px-3 hidden sm:block">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center">
                    <svg class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-gray-900">AUC = 0.89</p>
                    <p class="text-[10px] text-gray-500">模型预测性能优秀</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Stats Bar ===== -->
    <section id="stats" class="relative py-16 bg-gradient-to-r from-primary-50/50 via-white to-primary-50/50 border-y border-gray-100 overflow-hidden">
      <!-- 3D Decorative Icons -->
      <div class="absolute inset-0 pointer-events-none">
        <svg class="absolute top-4 left-[8%] w-10 h-10 text-primary/10 animate-bounce" style="animation-duration:3s" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        <svg class="absolute bottom-4 right-[12%] w-8 h-8 text-secondary/10 animate-bounce" style="animation-duration:4s" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
        <svg class="absolute top-6 right-[25%] w-6 h-6 text-accent/10 animate-bounce" style="animation-duration:2.5s" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="3"/></svg>
        <svg class="absolute bottom-6 left-[20%] w-7 h-7 text-primary/8 animate-bounce" style="animation-duration:3.5s" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        <svg class="absolute top-1/2 left-[45%] w-5 h-5 text-secondary/8 animate-bounce" style="animation-duration:5s" viewBox="0 0 24 24" fill="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          <div v-for="stat in platformStats" :key="stat.label" class="relative p-4 rounded-2xl bg-white/60 backdrop-blur-sm border border-white/80 shadow-sm">
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 w-10 h-10 rounded-xl flex items-center justify-center shadow-sm" :class="stat.iconBg">
              <svg class="w-5 h-5" :class="stat.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="stat.icon"></svg>
            </div>
            <p class="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mt-4">{{ stat.value }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Features Section ===== -->
    <section id="features" class="py-20 lg:py-28">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <span class="text-sm font-medium text-primary uppercase tracking-wider">功能特色</span>
          <h2 class="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mt-3">覆盖临床研究全流程</h2>
          <p class="text-lg text-gray-500 mt-4">从数据导入到报告生成，每个环节都经过精心打磨</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="feature in features" :key="feature.title"
            class="group p-6 rounded-2xl border border-gray-100 hover:border-primary/20 hover:shadow-card bg-white transition-all duration-300 cursor-pointer"
          >
            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-colors duration-300', feature.bgColor, 'group-hover:' + feature.bgColorHover]">
              <svg class="w-6 h-6" :class="feature.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="feature.icon"></svg>
            </div>
            <h3 class="text-lg font-heading font-semibold text-gray-900 group-hover:text-primary transition-colors">{{ feature.title }}</h3>
            <p class="text-gray-500 mt-2 leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Workflow Section ===== -->
    <section id="workflow" class="py-20 lg:py-28 bg-gray-50/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <span class="text-sm font-medium text-primary uppercase tracking-wider">工作流程</span>
          <h2 class="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mt-3">四步完成专业分析</h2>
          <p class="text-lg text-gray-500 mt-4">无需统计学背景，像使用表格一样简单</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div v-for="(step, i) in workflowSteps" :key="step.title" class="relative text-center">
            <!-- Connector line -->
            <div v-if="i < workflowSteps.length - 1" class="hidden lg:block absolute top-8 left-[60%] w-[80%] h-px bg-gradient-to-r from-primary/30 to-primary/10"></div>
            <div class="relative inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-primary-600 text-white text-2xl font-heading font-bold shadow-card mb-5">
              {{ i + 1 }}
            </div>
            <h3 class="text-lg font-heading font-semibold text-gray-900">{{ step.title }}</h3>
            <p class="text-gray-500 mt-2 text-sm leading-relaxed">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Analysis Methods ===== -->
    <section class="py-20 lg:py-28">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <span class="text-sm font-medium text-primary uppercase tracking-wider">分析方法</span>
          <h2 class="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mt-3">支持的统计分析类型</h2>
          <p class="text-lg text-gray-500 mt-4">全面覆盖医学研究常用统计方法</p>
        </div>

        <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
          <div v-for="method in analysisMethods" :key="method.name"
            class="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-white border border-gray-100 hover:border-primary/30 hover:shadow-sm transition-all duration-200 cursor-pointer text-center"
          >
            <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', method.bgColor]">
              <svg class="w-4 h-4" :class="method.iconColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="method.icon"></svg>
            </div>
            <span class="text-xs font-medium text-gray-600 leading-tight">{{ method.name }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Pricing Section ===== -->
    <section id="pricing" class="py-20 lg:py-28 bg-gray-50/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <span class="text-sm font-medium text-primary uppercase tracking-wider">价格方案</span>
          <h2 class="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mt-3">灵活的资源套餐</h2>
          <p class="text-lg text-gray-500 mt-4">按分析量付费，无月费负担</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div v-for="plan in plans" :key="plan.name"
            @mouseenter="activePlan = plan.name"
            @click="activePlan = plan.name"
            :class="['rounded-2xl p-8 text-center transition-all duration-300 cursor-pointer', activePlan === plan.name ? 'bg-gradient-to-b from-primary to-primary-600 text-white shadow-float scale-105 ring-4 ring-primary/20' : 'bg-white border border-gray-200 hover:border-primary/30 hover:shadow-card']"
          >
            <span v-if="plan.badge" class="inline-block px-3 py-1 text-xs font-semibold rounded-full mb-4" :class="activePlan === plan.name ? 'bg-white/20 text-white' : 'bg-primary/10 text-primary'">{{ plan.badge }}</span>
            <h3 :class="['text-xl font-heading font-bold', activePlan === plan.name ? 'text-white' : 'text-gray-900']">{{ plan.name }}</h3>
            <div class="mt-4">
              <span :class="['text-4xl font-heading font-bold', activePlan === plan.name ? 'text-white' : 'text-gray-900']">¥{{ plan.price }}</span>
            </div>
            <p :class="['text-sm mt-1', activePlan === plan.name ? 'text-white/70' : 'text-gray-500']">{{ plan.tokens }} 资源</p>
            <ul class="mt-6 space-y-3 text-left">
              <li v-for="feat in plan.features" :key="feat" class="flex items-center gap-2 text-sm" :class="activePlan === plan.name ? 'text-white/90' : 'text-gray-600'">
                <svg class="w-4 h-4 flex-shrink-0" :class="activePlan === plan.name ? 'text-white' : 'text-green-500'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feat }}
              </li>
            </ul>
            <router-link to="/account/billing"
              :class="['w-full mt-8 inline-block py-3 rounded-lg font-medium transition-all cursor-pointer text-center', activePlan === plan.name ? 'bg-white text-primary hover:bg-gray-50' : 'btn-secondary']"
            >
              立即购买
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== CTA Section ===== -->
    <section class="py-20 lg:py-28">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="relative bg-gradient-to-br from-primary via-primary-600 to-primary-700 rounded-3xl p-12 lg:p-16 overflow-hidden shadow-float">
          <!-- Decorative elements -->
          <div class="absolute inset-0 pointer-events-none overflow-hidden">
            <div class="absolute -top-20 -right-20 w-60 h-60 bg-white/10 rounded-full blur-2xl"></div>
            <div class="absolute -bottom-16 -left-16 w-48 h-48 bg-secondary/20 rounded-full blur-2xl"></div>
          </div>

          <div class="relative">
            <h2 class="text-3xl sm:text-4xl font-heading font-bold text-white">准备好开始分析了吗？</h2>
            <p class="text-lg text-white/80 mt-4 max-w-2xl mx-auto">注册即赠 200 资源，免费体验全部统计分析功能</p>
            <div class="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
              <router-link to="/auth/register" class="inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-white text-primary font-semibold rounded-xl hover:bg-gray-50 transition-all shadow-lg cursor-pointer">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                免费注册
              </router-link>
              <router-link to="/auth/login" class="inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all border border-white/20 cursor-pointer">
                已有账号，直接登录
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Footer ===== -->
    <footer class="border-t border-gray-100 py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div class="col-span-2 md:col-span-1">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 bg-gradient-to-br from-primary to-primary-600 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
              </div>
              <span class="text-lg font-heading font-bold text-gray-900">MediCode</span>
            </div>
            <p class="text-sm text-gray-500 leading-relaxed">专业的医学统计分析平台，<br/>助力科研数据分析。</p>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-900 mb-3">产品</h4>
            <ul class="space-y-2">
              <li><a href="#features" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">功能特色</a></li>
              <li><a href="#pricing" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">价格方案</a></li>
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">更新日志</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-900 mb-3">资源</h4>
            <ul class="space-y-2">
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">文档中心</a></li>
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">API 文档</a></li>
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">教程视频</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-sm font-semibold text-gray-900 mb-3">支持</h4>
            <ul class="space-y-2">
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">帮助中心</a></li>
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">联系我们</a></li>
              <li><a href="#" class="text-sm text-gray-500 hover:text-primary transition-colors cursor-pointer">隐私政策</a></li>
            </ul>
          </div>
        </div>
        <div class="mt-8 pt-8 border-t border-gray-100 text-center text-sm text-gray-400">
          © 2026 MediCode. All rights reserved.
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const platformStats = [
  { value: '50,000+', label: '已完成分析', iconBg: 'bg-primary-50', iconColor: 'text-primary', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { value: '3,200+', label: '活跃研究者', iconBg: 'bg-blue-50', iconColor: 'text-blue-500', icon: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>' },
  { value: '120+', label: '合作医院', iconBg: 'bg-green-50', iconColor: 'text-green-500', icon: '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>' },
  { value: '99.9%', label: '服务可用率', iconBg: 'bg-amber-50', iconColor: 'text-amber-500', icon: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
]

const features = [
  { title: '智能数据清洗', desc: '自动检测缺失值、异常值，支持多种填补策略，确保分析数据质量。', bgColor: 'bg-primary-50', bgColorHover: 'bg-primary-100', iconColor: 'text-primary', icon: '<path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>' },
  { title: '一键统计分析', desc: '描述统计、T检验、方差分析、卡方检验等，点击即可完成，结果即时呈现。', bgColor: 'bg-blue-50', bgColorHover: 'bg-blue-100', iconColor: 'text-blue-500', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { title: '高级回归模型', desc: '线性回归、Logistic回归、Cox比例风险模型，自动生成森林图和系数表。', bgColor: 'bg-purple-50', bgColorHover: 'bg-purple-100', iconColor: 'text-purple-500', icon: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>' },
  { title: '生存分析', desc: 'Kaplan-Meier 曲线、Log-rank 检验，支持多组比较和分层分析。', bgColor: 'bg-green-50', bgColorHover: 'bg-green-100', iconColor: 'text-green-500', icon: '<path d="M3 17l6-6 4 4 8-8"/><polyline points="14 7 21 7 21 14"/>' },
  { title: '可复现 R 脚本', desc: '每次分析自动生成完整 R 脚本，确保研究的可复现性和审计追踪。', bgColor: 'bg-amber-50', bgColorHover: 'bg-amber-100', iconColor: 'text-amber-500', icon: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>' },
  { title: '专业报告导出', desc: '一键生成符合期刊要求的统计报告，支持 PDF、Word 和 HTML 格式。', bgColor: 'bg-rose-50', bgColorHover: 'bg-rose-100', iconColor: 'text-rose-500', icon: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>' },
]

const workflowSteps = [
  { title: '上传数据', desc: '支持 CSV、Excel、SPSS、Stata 格式，拖拽即可上传' },
  { title: '选择方法', desc: '智能推荐最适合您数据的统计分析方法' },
  { title: '自动分析', desc: '后台高性能计算引擎，秒级返回结果' },
  { title: '导出报告', desc: '专业图表和统计表格，直接用于论文发表' },
]

const analysisMethods = [
  { name: '描述统计', bgColor: 'bg-primary-50', iconColor: 'text-primary', icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { name: 'T 检验', bgColor: 'bg-blue-50', iconColor: 'text-blue-500', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
  { name: '方差分析', bgColor: 'bg-purple-50', iconColor: 'text-purple-500', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { name: '卡方检验', bgColor: 'bg-green-50', iconColor: 'text-green-500', icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>' },
  { name: '线性回归', bgColor: 'bg-amber-50', iconColor: 'text-amber-500', icon: '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>' },
  { name: 'Logistic 回归', bgColor: 'bg-rose-50', iconColor: 'text-rose-500', icon: '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' },
  { name: 'Cox 回归', bgColor: 'bg-indigo-50', iconColor: 'text-indigo-500', icon: '<path d="M3 17l6-6 4 4 8-8"/><polyline points="14 7 21 7 21 14"/>' },
  { name: 'KM 生存曲线', bgColor: 'bg-teal-50', iconColor: 'text-teal-500', icon: '<path d="M3 3v18h18"/><path d="M3 12h4l3-6 4 10 3-4h4"/>' },
  { name: 'ROC 曲线', bgColor: 'bg-cyan-50', iconColor: 'text-cyan-500', icon: '<circle cx="12" cy="12" r="10"/><path d="M2 12c0-5.52 4.48-10 10-10"/>' },
  { name: 'Meta 分析', bgColor: 'bg-orange-50', iconColor: 'text-orange-500', icon: '<rect x="2" y="7" width="20" height="2"/><rect x="4" y="11" width="16" height="2"/><rect x="6" y="15" width="12" height="2"/>' },
  { name: '倾向评分匹配', bgColor: 'bg-pink-50', iconColor: 'text-pink-500', icon: '<circle cx="8" cy="12" r="3"/><circle cx="16" cy="12" r="3"/><line x1="11" y1="12" x2="13" y2="12"/>' },
  { name: '亚组分析', bgColor: 'bg-lime-50', iconColor: 'text-lime-600', icon: '<path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><path d="M12 11l4 4-4 4"/>' },
]

const activePlan = ref('专业版')

const plans = [
  {
    name: '基础版',
    price: '49',
    tokens: '500',
    badge: '',
    features: ['描述统计分析', '基础图表生成', '数据导入导出', 'CSV/Excel 格式', '邮件支持'],
  },
  {
    name: '专业版',
    price: '199',
    tokens: '2,500',
    badge: '最受欢迎',
    features: ['全部分析方法', '可复现 R 脚本', '专业报告导出', '协作团队功能', '优先技术支持'],
  },
  {
    name: '企业版',
    price: '499',
    tokens: '8,000',
    badge: '',
    features: ['无限分析方法', '定制分析模块', '专属技术顾问', 'API 集成接口', 'SLA 保障'],
  },
]
</script>
