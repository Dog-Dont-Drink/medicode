<template>
  <div class="animate-fade-in text-center">
    <div class="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
      <svg class="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
      </svg>
    </div>

    <h1 class="text-2xl font-heading font-bold text-gray-900">验证您的邮箱</h1>
    <p class="text-gray-500 mt-3 max-w-sm mx-auto">
      我们已向 <span class="font-medium text-gray-700">{{ email }}</span> 发送了 6 位验证码，请输入验证码完成验证。
    </p>

    <!-- 验证码输入 -->
    <div class="mt-8 max-w-xs mx-auto">
      <div class="flex gap-2 justify-center">
        <input
          v-for="(_, i) in 6" :key="i"
          :ref="el => { if (el) codeInputs[i] = el as HTMLInputElement }"
          v-model="codeDigits[i]"
          type="text"
          maxlength="1"
          inputmode="numeric"
          pattern="[0-9]"
          :class="['w-11 h-13 text-center text-xl font-bold rounded-xl border-2 transition-all outline-none', codeDigits[i] ? 'border-primary bg-primary-50 text-primary' : 'border-gray-200 focus:border-primary']"
          @input="handleInput(i)"
          @keydown="handleKeydown(i, $event)"
          @paste="handlePaste"
        />
      </div>

      <!-- Error message -->
      <p v-if="error" class="text-sm text-red-500 mt-3">{{ error }}</p>

      <!-- Success -->
      <div v-if="verified" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-xl">
        <div class="flex items-center gap-2 justify-center text-green-600 text-sm font-medium">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          验证成功！正在跳转...
        </div>
      </div>

      <!-- Submit -->
      <button
        v-if="!verified"
        @click="handleVerify"
        :disabled="loading || fullCode.length < 6"
        class="btn-primary w-full py-3 mt-5 text-base disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      >
        <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <span>{{ loading ? '验证中...' : '确认验证' }}</span>
      </button>
    </div>

    <!-- Resend & back -->
    <div class="mt-6 space-y-3">
      <button
        @click="resendCode"
        :disabled="cooldown > 0"
        class="text-sm font-medium transition-colors cursor-pointer disabled:cursor-not-allowed"
        :class="cooldown > 0 ? 'text-gray-400' : 'text-primary hover:text-primary-600'"
      >
        {{ cooldown > 0 ? `重新发送 (${cooldown}s)` : '重新发送验证码' }}
      </button>

      <router-link to="/auth/login" class="block text-sm text-gray-500 hover:text-gray-700 transition-colors cursor-pointer">
        返回登录
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const email = computed(() => (route.query.email as string) || authStore.pendingEmail || '')
const purpose = computed(() => (route.query.purpose as string) || authStore.pendingPurpose || 'register')

const codeDigits = ref<string[]>(['', '', '', '', '', ''])
const codeInputs = ref<HTMLInputElement[]>([])
const fullCode = computed(() => codeDigits.value.join(''))

const loading = ref(false)
const verified = ref(false)
const error = ref('')
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

function handleInput(index: number) {
  error.value = ''
  // 只允许数字
  codeDigits.value[index] = codeDigits.value[index].replace(/\D/g, '')
  // 自动跳到下一个
  if (codeDigits.value[index] && index < 5) {
    codeInputs.value[index + 1]?.focus()
  }
}

function handleKeydown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !codeDigits.value[index] && index > 0) {
    codeInputs.value[index - 1]?.focus()
  }
}

function handlePaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text')?.replace(/\D/g, '').slice(0, 6) || ''
  for (let i = 0; i < 6; i++) {
    codeDigits.value[i] = text[i] || ''
  }
  if (text.length > 0) {
    const focusIdx = Math.min(text.length, 5)
    codeInputs.value[focusIdx]?.focus()
  }
}

async function handleVerify() {
  if (fullCode.value.length < 6) return
  loading.value = true
  error.value = ''

  const result = await authStore.verifyCode(email.value, fullCode.value, purpose.value)
  loading.value = false

  if (result.success) {
    verified.value = true
    setTimeout(() => {
      if (purpose.value === 'register') {
        router.push('/dashboard')
      } else if (purpose.value === 'reset-password') {
        router.push({ name: 'ForgotPassword', query: { step: 'reset', email: email.value } })
      } else {
        router.push('/auth/login')
      }
    }, 1500)
  } else {
    error.value = result.error || '验证码错误或已过期'
  }
}

function resendCode() {
  cooldown.value = 60
  authStore.sendCode(email.value, purpose.value)
  timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

onMounted(() => {
  // 自动聚焦第一个输入框
  setTimeout(() => codeInputs.value[0]?.focus(), 100)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
