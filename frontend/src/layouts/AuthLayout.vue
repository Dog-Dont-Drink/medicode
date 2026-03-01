<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent/5 flex items-center justify-center p-4">
    <!-- Decorative background elements -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-secondary/5 rounded-full blur-3xl"></div>
      <div class="absolute top-1/4 left-1/4 w-64 h-64 bg-accent/3 rounded-full blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <router-link to="/" class="inline-flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-primary to-primary-600 rounded-xl flex items-center justify-center shadow-card">
            <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <span class="text-2xl font-heading font-bold text-gray-900">MediCode</span>
        </router-link>
      </div>

      <!-- Card container -->
      <div class="bg-white/80 backdrop-blur-xl rounded-2xl shadow-elevated border border-white/60 p-8">
        <router-view />
      </div>

      <!-- Footer -->
      <p class="text-center text-sm text-gray-400 mt-6">
        © 2026 MediCode. 专业医学统计分析平台
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
