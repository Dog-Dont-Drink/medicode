<template>
  <div class="max-w-2xl">
    <h1 class="text-2xl font-heading font-bold text-gray-900">个人设置</h1>
    <p class="text-sm text-gray-500 mt-1">管理您的个人资料和账户信息</p>

    <!-- Avatar -->
    <div class="mt-8 flex items-center gap-5">
      <div class="w-20 h-20 bg-gradient-to-br from-primary to-primary-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-sm">
        {{ form.name ? form.name[0].toUpperCase() : 'U' }}
      </div>
      <div>
        <button class="px-4 py-2 text-sm font-medium text-primary bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors cursor-pointer">更换头像</button>
        <p class="text-xs text-gray-400 mt-1.5">JPG, PNG 格式，≤ 2MB</p>
      </div>
    </div>

    <!-- Form -->
    <form class="mt-8 space-y-5" @submit.prevent="handleSave">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label class="form-label">姓名</label>
          <input v-model="form.name" type="text" class="form-input" placeholder="您的姓名" />
        </div>
        <div>
          <label class="form-label">邮箱</label>
          <input v-model="form.email" type="email" class="form-input" placeholder="your@email.com" />
        </div>
        <div>
          <label class="form-label">手机号码</label>
          <input v-model="form.phone" type="tel" class="form-input" placeholder="138 xxxx xxxx" />
        </div>
        <div>
          <label class="form-label">职称</label>
          <select v-model="form.title" class="form-input bg-white cursor-pointer">
            <option value="">请选择</option>
            <option value="professor">教授 / 主任医师</option>
            <option value="associate">副教授 / 副主任医师</option>
            <option value="lecturer">讲师 / 主治医师</option>
            <option value="resident">住院医师</option>
            <option value="student">研究生 / 博士后</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>

      <div>
        <label class="form-label">所属机构</label>
        <input v-model="form.institution" type="text" class="form-input" placeholder="医院 / 大学 / 研究所名称" />
      </div>

      <div>
        <label class="form-label">研究方向</label>
        <input v-model="form.researchField" type="text" class="form-input" placeholder="例如：心血管内科、肿瘤流行病学" />
      </div>

      <div>
        <label class="form-label">个人简介</label>
        <textarea v-model="form.bio" rows="3" class="form-input resize-none" placeholder="简要介绍您的研究经历和兴趣方向..."></textarea>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 pt-2">
        <button type="submit" class="btn-primary cursor-pointer">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          保存修改
        </button>
        <span v-if="saved" class="text-sm text-green-500 animate-fade-in">已保存</span>
      </div>
    </form>

    <!-- 修改密码区域 -->
    <div class="border-t border-gray-100 mt-8 pt-6">
      <h3 class="text-lg font-heading font-semibold text-gray-900 mb-1">修改密码</h3>
      <p class="text-sm text-gray-500 mb-5">修改密码需要先通过邮箱验证</p>

      <!-- Step 1: 发送验证码 -->
      <div v-if="pwdStep === 'idle'" class="space-y-4">
        <p class="text-sm text-gray-600">验证码将发送至 <span class="font-medium text-gray-800">{{ form.email }}</span></p>
        <button @click="sendPasswordCode" :disabled="pwdLoading" class="btn-primary btn-sm cursor-pointer">
          {{ pwdLoading ? '发送中...' : '发送验证码' }}
        </button>
      </div>

      <!-- Step 2: 输入验证码 + 新密码 -->
      <div v-if="pwdStep === 'verify'" class="space-y-4">
        <div>
          <label class="form-label">邮箱验证码</label>
          <div class="flex gap-2">
            <input
              v-for="(_, i) in 6" :key="i"
              :ref="el => { if (el) pwdCodeInputs[i] = el as HTMLInputElement }"
              v-model="pwdCodeDigits[i]"
              type="text" maxlength="1" inputmode="numeric"
              :class="['w-10 h-11 text-center text-lg font-bold rounded-lg border-2 transition-all outline-none', pwdCodeDigits[i] ? 'border-primary bg-primary-50 text-primary' : 'border-gray-200 focus:border-primary']"
              @input="handlePwdCodeInput(i)"
              @keydown="handlePwdCodeKeydown(i, $event)"
            />
          </div>
          <div class="mt-2">
            <button @click="resendPasswordCode" :disabled="pwdCooldown > 0" class="text-xs cursor-pointer disabled:cursor-not-allowed" :class="pwdCooldown > 0 ? 'text-gray-400' : 'text-primary hover:text-primary-600'">
              {{ pwdCooldown > 0 ? `重新发送 (${pwdCooldown}s)` : '重新发送验证码' }}
            </button>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="form-label">当前密码</label>
            <input v-model="pwdForm.currentPassword" type="password" class="form-input" placeholder="••••••••" />
          </div>
          <div>
            <label class="form-label">新密码</label>
            <input v-model="pwdForm.newPassword" type="password" class="form-input" placeholder="至少 8 位字符" />
          </div>
        </div>
        <p v-if="pwdError" class="text-sm text-red-500">{{ pwdError }}</p>
        <div class="flex gap-3">
          <button @click="pwdStep = 'idle'" class="btn-ghost text-sm cursor-pointer">取消</button>
          <button @click="handleChangePassword" :disabled="pwdLoading || pwdFullCode.length < 6" class="btn-primary btn-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            {{ pwdLoading ? '提交中...' : '确认修改' }}
          </button>
        </div>
      </div>

      <!-- Step 3: 修改成功 -->
      <div v-if="pwdStep === 'done'" class="flex items-center gap-2 text-green-600 text-sm font-medium">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        密码修改成功
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUserProfile, updateUserProfile, changePassword as apiChangePassword } from '@/services/api'

const authStore = useAuthStore()

const saved = ref(false)

const form = reactive({
  name: '',
  email: '',
  phone: '',
  title: '',
  institution: '',
  researchField: '',
  bio: '',
})

onMounted(async () => {
  try {
    const profile = await getUserProfile()
    Object.assign(form, {
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      title: profile.title || '',
      institution: profile.institution || '',
      researchField: profile.research_field || '',
      bio: profile.bio || '',
    })
  } catch (error) {
    console.error('Failed to load profile:', error)
  }
})

async function handleSave() {
  try {
    await updateUserProfile({
      name: form.name,
      phone: form.phone,
      title: form.title,
      institution: form.institution,
      research_field: form.researchField,
      bio: form.bio,
    })
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
    
    // Also update the store if name changed
    if (authStore.user) {
      authStore.user.name = form.name
    }
  } catch (error) {
    console.error('Failed to save profile:', error)
  }
}

// ====== 修改密码（需邮箱验证） ======
const pwdStep = ref<'idle' | 'verify' | 'done'>('idle')
const pwdLoading = ref(false)
const pwdError = ref('')
const pwdForm = reactive({ currentPassword: '', newPassword: '' })
const pwdCodeDigits = ref<string[]>(['', '', '', '', '', ''])
const pwdCodeInputs = ref<HTMLInputElement[]>([])
const pwdFullCode = computed(() => pwdCodeDigits.value.join(''))
const pwdCooldown = ref(0)
let pwdTimer: ReturnType<typeof setInterval> | null = null

async function sendPasswordCode() {
  pwdLoading.value = true
  const result = await authStore.sendCode(form.email, 'change-password')
  pwdLoading.value = false
  if (result.success) {
    pwdStep.value = 'verify'
    startPwdCooldown()
    setTimeout(() => pwdCodeInputs.value[0]?.focus(), 100)
  }
}

function resendPasswordCode() {
  authStore.sendCode(form.email, 'change-password')
  startPwdCooldown()
}

function handlePwdCodeInput(index: number) {
  pwdError.value = ''
  pwdCodeDigits.value[index] = pwdCodeDigits.value[index].replace(/\D/g, '')
  if (pwdCodeDigits.value[index] && index < 5) {
    pwdCodeInputs.value[index + 1]?.focus()
  }
}

function handlePwdCodeKeydown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !pwdCodeDigits.value[index] && index > 0) {
    pwdCodeInputs.value[index - 1]?.focus()
  }
}

async function handleChangePassword() {
  if (pwdFullCode.value.length < 6) return
  if (!pwdForm.currentPassword || !pwdForm.newPassword) {
    pwdError.value = '请填写当前密码和新密码'
    return
  }
  if (pwdForm.newPassword.length < 8) {
    pwdError.value = '新密码至少 8 位字符'
    return
  }

  pwdLoading.value = true
  pwdError.value = ''

  // 先验证验证码
  const verifyResult = await authStore.verifyCode(form.email, pwdFullCode.value, 'change-password')
  if (!verifyResult.success) {
    pwdError.value = verifyResult.error || '验证码错误或已过期'
    pwdLoading.value = false
    return
  }

  // Real API call for POST /api/v1/users/change-password
  try {
    await apiChangePassword({
      email: form.email,
      code: pwdFullCode.value,
      current_password: pwdForm.currentPassword,
      new_password: pwdForm.newPassword
    })
    pwdLoading.value = false
    pwdStep.value = 'done'
    setTimeout(() => { pwdStep.value = 'idle' }, 3000)
  } catch (error: any) {
    pwdError.value = error.response?.data?.detail || '修改密码失败，请重试'
    pwdLoading.value = false
  }
}

function startPwdCooldown() {
  pwdCooldown.value = 60
  pwdTimer = setInterval(() => {
    pwdCooldown.value--
    if (pwdCooldown.value <= 0 && pwdTimer) { clearInterval(pwdTimer); pwdTimer = null }
  }, 1000)
}

onUnmounted(() => { if (pwdTimer) clearInterval(pwdTimer) })
</script>

<style scoped>
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  color: #111827;
  transition: all 0.15s;
}
.form-input:focus {
  outline: none;
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.08);
}
.form-input::placeholder {
  color: #d1d5db;
}
</style>
