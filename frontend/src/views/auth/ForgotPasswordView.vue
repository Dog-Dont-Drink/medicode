<template>
  <div class="animate-fade-in">
    <div class="text-center mb-8">
      <div class="w-12 h-12 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
      </div>
      <h1 class="text-2xl font-heading font-bold text-gray-900">{{ stepTitle }}</h1>
      <p class="text-gray-500 mt-2">{{ stepDesc }}</p>
    </div>

    <!-- Step 1: 输入邮箱 -->
    <form v-if="step === 'email'" @submit.prevent="handleSendCode" class="space-y-5">
      <div>
        <label for="forgot-email" class="block text-sm font-medium text-gray-700 mb-1.5">邮箱地址</label>
        <div class="relative">
          <div class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <input id="forgot-email" v-model="form.email" type="email" required placeholder="请输入注册邮箱" class="input-field pl-11" />
        </div>
      </div>

      <button type="submit" :disabled="loading" class="btn-primary w-full py-3 text-base cursor-pointer">
        <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <span>{{ loading ? '发送中...' : '发送验证码' }}</span>
      </button>
    </form>

    <!-- Step 2: 输入验证码 -->
    <div v-if="step === 'code'" class="space-y-5">
      <p class="text-sm text-gray-600 text-center">验证码已发送至 <span class="font-medium text-gray-800">{{ form.email }}</span></p>
      <div class="flex gap-2 justify-center">
        <input
          v-for="(_, i) in 6" :key="i"
          :ref="el => { if (el) codeInputs[i] = el as HTMLInputElement }"
          v-model="codeDigits[i]"
          type="text" maxlength="1" inputmode="numeric" pattern="[0-9]"
          :class="['w-11 h-13 text-center text-xl font-bold rounded-xl border-2 transition-all outline-none', codeDigits[i] ? 'border-primary bg-primary-50 text-primary' : 'border-gray-200 focus:border-primary']"
          @input="handleCodeInput(i)"
          @keydown="handleCodeKeydown(i, $event)"
          @paste="handleCodePaste"
        />
      </div>
      <p v-if="error" class="text-sm text-red-500 text-center">{{ error }}</p>

      <button @click="handleVerifyCode" :disabled="loading || fullCode.length < 6" class="btn-primary w-full py-3 text-base cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
        <span>{{ loading ? '验证中...' : '验证' }}</span>
      </button>

      <div class="text-center">
        <button @click="resendCode" :disabled="cooldown > 0" class="text-sm cursor-pointer disabled:cursor-not-allowed" :class="cooldown > 0 ? 'text-gray-400' : 'text-primary hover:text-primary-600'">
          {{ cooldown > 0 ? `重新发送 (${cooldown}s)` : '重新发送验证码' }}
        </button>
      </div>
    </div>

    <!-- Step 3: 设置新密码 -->
    <form v-if="step === 'reset'" @submit.prevent="handleResetPassword" class="space-y-5">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">新密码</label>
        <input v-model="form.newPassword" type="password" required minlength="8" placeholder="至少 8 位字符" class="input-field" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">确认新密码</label>
        <input v-model="form.confirmPassword" type="password" required placeholder="请再次输入新密码" class="input-field" />
        <p v-if="form.confirmPassword && form.newPassword !== form.confirmPassword" class="text-sm text-red-500 mt-1">两次输入的密码不一致</p>
      </div>

      <button type="submit" :disabled="loading || form.newPassword !== form.confirmPassword" class="btn-primary w-full py-3 text-base cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
        <span>{{ loading ? '重置中...' : '重置密码' }}</span>
      </button>
    </form>

    <!-- Step 4: 成功 -->
    <div v-if="step === 'done'" class="text-center space-y-4">
      <div class="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto">
        <svg class="w-8 h-8 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-gray-900">密码重置成功</h2>
      <p class="text-sm text-gray-500">正在为您登录并跳转到控制台...</p>
      <button @click="goDashboard" class="btn-primary inline-block px-6 py-2.5 cursor-pointer">立即进入控制台</button>
    </div>

    <!-- Back link -->
    <p v-if="step !== 'done'" class="text-center text-sm text-gray-500 mt-6">
      <router-link to="/auth/login" class="text-primary font-medium hover:text-primary-600 transition-colors cursor-pointer flex items-center justify-center gap-1">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
        </svg>
        返回登录
      </router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const step = ref<'email' | 'code' | 'reset' | 'done'>('email')
const form = reactive({ email: '', newPassword: '', confirmPassword: '' })
const loading = ref(false)
const error = ref('')

// 验证码相关
const codeDigits = ref<string[]>(['', '', '', '', '', ''])
const codeInputs = ref<HTMLInputElement[]>([])
const fullCode = computed(() => codeDigits.value.join(''))
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null
let redirectTimer: ReturnType<typeof setTimeout> | null = null

const stepTitle = computed(() => {
  if (step.value === 'email') return '忘记密码'
  if (step.value === 'code') return '输入验证码'
  if (step.value === 'reset') return '设置新密码'
  return '重置成功'
})
const stepDesc = computed(() => {
  if (step.value === 'email') return '输入您的注册邮箱，我们将发送验证码'
  if (step.value === 'code') return '请输入 6 位数字验证码'
  if (step.value === 'reset') return '请设置您的新密码'
  return ''
})

async function handleSendCode() {
  loading.value = true
  const result = await authStore.sendCode(form.email, 'reset-password')
  loading.value = false
  if (result.success) {
    step.value = 'code'
    startCooldown()
    setTimeout(() => codeInputs.value[0]?.focus(), 100)
  }
}

function handleCodeInput(index: number) {
  error.value = ''
  codeDigits.value[index] = codeDigits.value[index].replace(/\D/g, '')
  if (codeDigits.value[index] && index < 5) {
    codeInputs.value[index + 1]?.focus()
  }
}

function handleCodeKeydown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !codeDigits.value[index] && index > 0) {
    codeInputs.value[index - 1]?.focus()
  }
}

function handleCodePaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text')?.replace(/\D/g, '').slice(0, 6) || ''
  for (let i = 0; i < 6; i++) codeDigits.value[i] = text[i] || ''
  if (text.length > 0) codeInputs.value[Math.min(text.length, 5)]?.focus()
}

async function handleVerifyCode() {
  if (fullCode.value.length < 6) return
  loading.value = true
  error.value = ''
  const result = await authStore.verifyCode(form.email, fullCode.value, 'reset-password')
  loading.value = false
  if (result.success) {
    step.value = 'reset'
  } else {
    error.value = result.error || '验证码错误或已过期'
  }
}

async function handleResetPassword() {
  if (form.newPassword !== form.confirmPassword) return
  loading.value = true
  error.value = ''
  const result = await authStore.resetPassword(form.email, fullCode.value, form.newPassword)
  if (result.success) {
    const loginResult = await authStore.login(form.email, form.newPassword)
    loading.value = false

    if (loginResult.success) {
      step.value = 'done'
      redirectTimer = setTimeout(() => {
        router.push('/dashboard')
      }, 1200)
      return
    }

    error.value = loginResult.error || '自动登录失败，请手动登录'
    router.push({ name: 'Login', query: { email: form.email } })
    return
  }

  loading.value = false
  error.value = result.error || '重置密码失败'
}

function goDashboard() {
  router.push('/dashboard')
}

function resendCode() {
  authStore.sendCode(form.email, 'reset-password')
  startCooldown()
}

function startCooldown() {
  cooldown.value = 60
  timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0 && timer) { clearInterval(timer); timer = null }
  }, 1000)
}

onMounted(() => {
  // 支持从 EmailVerifyView 跳过来设置新密码
  if (route.query.step === 'reset' && route.query.email) {
    form.email = route.query.email as string
    step.value = 'reset'
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (redirectTimer) clearTimeout(redirectTimer)
})
</script>
