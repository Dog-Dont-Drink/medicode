<template>
  <div class="animate-fade-in">
    <div class="text-center mb-8">
      <h1 class="text-2xl font-heading font-bold text-gray-900">欢迎回来</h1>
      <p class="text-gray-500 mt-2">登录您的 MediCode 账户</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-5">
      <!-- Email -->
      <div>
        <label for="login-email" class="block text-sm font-medium text-gray-700 mb-1.5">邮箱地址</label>
        <div class="relative">
          <div class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <input
            id="login-email"
            v-model="form.email"
            type="email"
            required
            placeholder="请输入邮箱"
            :class="['input-field pl-11', errors.email ? 'input-error' : '']"
          />
        </div>
        <p v-if="errors.email" class="text-sm text-danger mt-1">{{ errors.email }}</p>
      </div>

      <!-- Password -->
      <div>
        <div class="flex items-center justify-between mb-1.5">
          <label for="login-password" class="block text-sm font-medium text-gray-700">密码</label>
          <router-link to="/auth/forgot-password" class="text-sm text-primary hover:text-primary-600 transition-colors cursor-pointer">忘记密码?</router-link>
        </div>
        <div class="relative">
          <div class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
          </div>
          <input
            id="login-password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            required
            placeholder="请输入密码"
            :class="['input-field pl-11 pr-11', errors.password ? 'input-error' : '']"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
          >
            <svg v-if="showPassword" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
            <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
        <p v-if="errors.password" class="text-sm text-danger mt-1">{{ errors.password }}</p>
      </div>

      <!-- Remember me -->
      <div class="flex items-center gap-2">
        <input
          id="remember"
          v-model="form.remember"
          type="checkbox"
          class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary/20 cursor-pointer"
        />
        <label for="remember" class="text-sm text-gray-600 cursor-pointer">记住我</label>
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="loading"
        class="btn-primary w-full py-3 text-base"
      >
        <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <span>{{ loading ? '登录中...' : '登录' }}</span>
      </button>

      <!-- Error message -->
      <div v-if="loginError" class="alert-danger text-sm">
        {{ loginError }}
      </div>

      <!-- 邮箱未验证提示 -->
      <div v-if="needVerify" class="p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <p class="text-sm text-amber-700 mb-2">您的邮箱尚未验证，请先完成验证后再登录。</p>
        <button @click="goVerify" class="text-sm font-medium text-primary hover:text-primary-600 cursor-pointer">去验证 →</button>
      </div>
    </form>



    <!-- Register link -->
    <p class="text-center text-sm text-gray-500 mt-6">
      还没有账户？
      <router-link to="/auth/register" class="text-primary font-medium hover:text-primary-600 transition-colors cursor-pointer">立即注册</router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: '',
  remember: false,
})

const errors = reactive({
  email: '',
  password: '',
})

const showPassword = ref(false)
const loading = ref(false)
const loginError = ref('')
const needVerify = ref(false)

function goVerify() {
  router.push({ name: 'VerifyEmail', query: { email: form.email, purpose: 'register' } })
}

async function handleLogin() {
  errors.email = ''
  errors.password = ''
  loginError.value = ''
  needVerify.value = false

  if (!form.email) {
    errors.email = '请输入邮箱地址'
    return
  }
  if (!form.password) {
    errors.password = '请输入密码'
    return
  }

  loading.value = true
  const result = await authStore.login(form.email, form.password)
  loading.value = false

  if (result.success) {
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } else if ((result as any).needVerify) {
    needVerify.value = true
    loginError.value = ''
  } else {
    loginError.value = result.error || '登录失败，请检查邮箱和密码'
  }
}
</script>
