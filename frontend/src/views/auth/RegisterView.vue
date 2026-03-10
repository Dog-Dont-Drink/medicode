<template>
  <div class="animate-fade-in">
    <div class="text-center mb-5">
      <h1 class="text-xl font-heading font-bold text-gray-900">创 建 账 户</h1>
      <p class="text-gray-400 text-xs mt-1">注册即可开始使用 MediCode</p>
    </div>

    <form @submit.prevent="handleRegister" class="space-y-3.5">
      <!-- Name -->
      <div>
        <label for="reg-name" class="reg-label">用户名</label>
        <input id="reg-name" v-model="form.name" type="text" required placeholder="请输入姓名" class="reg-input" />
      </div>

      <!-- Email + Send Code -->
      <div>
        <label for="reg-email" class="reg-label">邮箱地址</label>
        <div class="flex gap-2">
          <input id="reg-email" v-model="form.email" type="email" required placeholder="请输入邮箱" class="reg-input flex-1" :disabled="emailVerified" />
          <button
            type="button" @click="handleSendCode"
            :disabled="codeCooldown > 0 || !form.email || sendingCode || emailVerified"
            class="shrink-0 px-4 h-[38px] text-xs font-medium rounded-lg transition-all cursor-pointer disabled:cursor-not-allowed whitespace-nowrap"
            :class="emailVerified
              ? 'bg-green-50 text-green-600 border border-green-200'
              : codeCooldown > 0
                ? 'bg-gray-50 text-gray-400 border border-gray-200'
                : 'bg-primary text-white hover:bg-primary-600'"
          >
            <template v-if="emailVerified"><span class="flex items-center gap-1"><svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>已验证</span></template>
            <template v-else-if="sendingCode">发送中...</template>
            <template v-else-if="codeCooldown > 0">{{ codeCooldown }}s</template>
            <template v-else-if="codeSent">重新发送</template>
            <template v-else>发送验证码</template>
          </button>
        </div>
      </div>

      <!-- Verification code (inline) -->
      <div v-if="codeSent && !emailVerified" class="space-y-1.5">
        <label class="reg-label">邮箱验证码</label>
        <div class="flex gap-1.5 items-center">
          <input
            v-for="(_, i) in 6" :key="i"
            :ref="el => { if (el) codeInputs[i] = el as HTMLInputElement }"
            v-model="codeDigits[i]"
            type="text" maxlength="1" inputmode="numeric" pattern="[0-9]"
            :class="['w-9 h-10 text-center text-base font-bold rounded-lg border-2 transition-all outline-none',
              codeDigits[i] ? 'border-primary bg-primary-50 text-primary' : 'border-gray-200 focus:border-primary']"
            @input="handleCodeInput(i)"
            @keydown="handleCodeKeydown(i, $event)"
            @paste="handleCodePaste"
          />
          <button
            type="button" @click="handleVerifyCode"
            :disabled="fullCode.length < 6 || verifying"
            class="ml-1 shrink-0 px-3 py-2 text-xs font-medium bg-primary text-white rounded-lg hover:bg-primary-600 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >{{ verifying ? '验证中' : '验证' }}</button>
        </div>
        <p v-if="codeError" class="text-xs text-red-500">{{ codeError }}</p>
        <p v-else class="text-[11px] text-gray-400">请输入发送至邮箱的 6 位验证码</p>
      </div>

      <!-- Email verified badge -->
      <div v-if="emailVerified" class="flex items-center gap-1.5 text-xs text-green-600 bg-green-50 border border-green-100 rounded-lg px-3 py-2">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        邮箱验证通过
      </div>

      <!-- Password -->
      <div>
        <label for="reg-password" class="reg-label">密码</label>
        <div class="relative">
          <input
            id="reg-password" v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            required minlength="8" placeholder="至少 8 位字符"
            class="reg-input pr-9"
          />
          <button type="button" @click="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer">
            <svg v-if="showPassword" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
            <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
        <!-- Password strength -->
        <div v-if="form.password" class="mt-1.5 flex gap-1">
          <div v-for="i in 4" :key="i" :class="['h-0.5 flex-1 rounded-full transition-colors', i <= passwordStrength ? strengthColors[passwordStrength] : 'bg-gray-200']"></div>
        </div>
        <p v-if="passwordStrength > 0" class="text-[10px] mt-0.5" :class="strengthTextColors[passwordStrength]">{{ strengthLabels[passwordStrength] }}</p>
      </div>

      <!-- Confirm password -->
      <div>
        <label for="reg-confirm" class="reg-label">确认密码</label>
        <input
          id="reg-confirm" v-model="form.confirmPassword"
          :type="showPassword ? 'text' : 'password'"
          required placeholder="请再次输入密码"
          :class="['reg-input', form.confirmPassword && form.password !== form.confirmPassword ? 'border-red-300 focus:border-red-400' : '']"
        />
        <p v-if="form.confirmPassword && form.password !== form.confirmPassword" class="text-[11px] text-red-500 mt-0.5">两次输入的密码不一致</p>
      </div>

      <!-- Terms -->
      <div class="flex items-start gap-2">
        <input id="terms" v-model="form.agreeTerms" type="checkbox" required class="w-3.5 h-3.5 mt-0.5 rounded border-gray-300 text-primary focus:ring-primary/20 cursor-pointer" />
        <label for="terms" class="text-xs text-gray-500 cursor-pointer leading-relaxed">
          我已阅读并同意 <a href="#" class="text-primary hover:underline">服务条款</a> 和 <a href="#" class="text-primary hover:underline">隐私政策</a>
        </label>
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="loading || !form.agreeTerms || !emailVerified"
        class="btn-primary w-full py-2.5 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg v-if="loading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <span>{{ loading ? '注册中...' : '创建账户' }}</span>
      </button>
    </form>

    <!-- Login link -->
    <p class="text-center text-xs text-gray-400 mt-4">
      已有账户？
      <router-link to="/auth/login" class="text-primary font-medium hover:text-primary-600 transition-colors cursor-pointer">立即登录</router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false,
})

const showPassword = ref(false)
const loading = ref(false)

// --- Email verification ---
const codeSent = ref(false)
const sendingCode = ref(false)
const emailVerified = ref(false)
const verifying = ref(false)
const codeError = ref('')
const codeCooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

const codeDigits = ref<string[]>(['', '', '', '', '', ''])
const codeInputs = ref<HTMLInputElement[]>([])
const fullCode = computed(() => codeDigits.value.join(''))

async function handleSendCode() {
  if (!form.email) return
  sendingCode.value = true
  const result = await authStore.sendCode(form.email, 'register')
  sendingCode.value = false
  if (result.success) {
    codeSent.value = true
    codeError.value = ''
    startCooldown()
    setTimeout(() => codeInputs.value[0]?.focus(), 100)
  } else {
    codeError.value = result.error || '验证码发送失败，请重试'
  }
}

function handleCodeInput(index: number) {
  codeError.value = ''
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
  verifying.value = true
  codeError.value = ''
  const result = await authStore.verifyCode(form.email, fullCode.value, 'register')
  verifying.value = false
  if (result.success) {
    emailVerified.value = true
  } else {
    codeError.value = result.error || '验证码错误或已过期'
  }
}

function startCooldown() {
  codeCooldown.value = 60
  cooldownTimer = setInterval(() => {
    codeCooldown.value--
    if (codeCooldown.value <= 0 && cooldownTimer) { clearInterval(cooldownTimer); cooldownTimer = null }
  }, 1000)
}

// --- Password strength ---
const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return 0
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  return score
})

const strengthColors: Record<number, string> = { 0: 'bg-gray-200', 1: 'bg-red-400', 2: 'bg-amber-400', 3: 'bg-blue-400', 4: 'bg-green-400' }
const strengthTextColors: Record<number, string> = { 0: 'text-gray-400', 1: 'text-red-500', 2: 'text-amber-500', 3: 'text-blue-500', 4: 'text-green-500' }
const strengthLabels: Record<number, string> = { 0: '', 1: '弱', 2: '中等', 3: '强', 4: '非常强' }

// --- Register ---
async function handleRegister() {
  if (form.password !== form.confirmPassword) return
  if (!emailVerified.value) return
  loading.value = true
  const result = await authStore.register(form.name, form.email, form.password, fullCode.value)
  loading.value = false
  if (result.success) {
    router.push('/dashboard')
  }
}

onUnmounted(() => { if (cooldownTimer) clearInterval(cooldownTimer) })
</script>

<style scoped>
.reg-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 4px;
}
.reg-input {
  display: block;
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  color: #111827;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.reg-input:focus {
  outline: none;
  border-color: #059669;
  box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.08);
}
.reg-input::placeholder {
  color: #c9cdd4;
  font-weight: 400;
}
.reg-input:disabled {
  background: #f9fafb;
  color: #6b7280;
}
</style>
