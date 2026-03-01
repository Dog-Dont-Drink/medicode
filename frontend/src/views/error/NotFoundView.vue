<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gray-50">
    <div class="text-center animate-fade-in">
      <div class="w-24 h-24 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-12 h-12 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
      </div>
      <h1 class="text-6xl font-heading font-bold text-gray-900">404</h1>
      <p class="text-xl text-gray-600 mt-3">页面未找到</p>
      <p class="text-gray-400 mt-2 max-w-md mx-auto">抱歉，您访问的页面不存在或已被移除</p>
      <router-link to="/dashboard" class="btn-primary mt-8 inline-flex cursor-pointer">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
        </svg>
        返回首页
      </router-link>
    </div>
  </div>
</template>
<script setup lang="ts"></script>
