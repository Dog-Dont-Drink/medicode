<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gray-50">
    <div class="text-center animate-fade-in">
      <div class="w-24 h-24 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-12 h-12 text-danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h1 class="text-6xl font-heading font-bold text-gray-900">403</h1>
      <p class="text-xl text-gray-600 mt-3">访问被拒绝</p>
      <p class="text-gray-400 mt-2 max-w-md mx-auto">您没有权限访问此页面，请联系管理员</p>
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
