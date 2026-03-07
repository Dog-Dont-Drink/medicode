<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/60 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h1 class="text-lg font-heading font-semibold text-slate-900">用户管理</h1>
        <p class="mt-1 text-sm text-slate-500">集中维护用户余额、套餐、角色、验证状态和启停状态。</p>
      </div>
      <div class="flex flex-col gap-3 sm:flex-row">
        <input v-model="searchTerm" type="text" class="input-field min-w-[240px]" placeholder="搜索邮箱、姓名、机构" />
        <select v-model="statusFilter" class="input-field min-w-[150px]">
          <option value="all">全部状态</option>
          <option value="active">仅启用</option>
          <option value="inactive">仅停用</option>
          <option value="admin">仅管理员</option>
        </select>
      </div>
    </div>

    <div v-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <section class="rounded-3xl border border-slate-200 bg-white shadow-sm shadow-slate-200/60">
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="border-b border-slate-200 bg-slate-50">
              <tr class="text-left text-slate-500">
                <th class="px-5 py-4 font-medium">用户</th>
                <th class="px-5 py-4 font-medium">套餐</th>
                <th class="px-5 py-4 font-medium">余额</th>
                <th class="px-5 py-4 font-medium">状态</th>
                <th class="px-5 py-4 font-medium">本月消耗</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                class="cursor-pointer border-b border-slate-100 transition hover:bg-slate-50"
                :class="selectedUser?.id === user.id ? 'bg-emerald-50/70' : ''"
                @click="selectUser(user)"
              >
                <td class="px-5 py-4 align-top">
                  <p class="font-medium text-slate-900">{{ user.name }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ user.email }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ user.institution || '未填写机构' }}</p>
                </td>
                <td class="px-5 py-4 align-top">
                  <span class="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {{ user.role === 'admin' ? '管理员' : user.subscription }}
                  </span>
                </td>
                <td class="px-5 py-4 align-top font-medium text-slate-900">{{ user.token_balance.toLocaleString() }}</td>
                <td class="px-5 py-4 align-top">
                  <div class="flex flex-wrap gap-2">
                    <span :class="badgeClass(user.is_active ? 'active' : 'inactive')">{{ user.is_active ? '启用' : '停用' }}</span>
                    <span :class="badgeClass(user.is_verified ? 'verified' : 'pending')">{{ user.is_verified ? '已验证' : '未验证' }}</span>
                  </div>
                </td>
                <td class="px-5 py-4 align-top text-slate-600">
                  <p>{{ user.billed_tokens_this_month.toLocaleString() }}</p>
                  <p class="mt-1 text-xs text-slate-400">实际 {{ user.actual_tokens_this_month.toLocaleString() }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/60">
        <div v-if="selectedUser" class="space-y-5">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">编辑用户</p>
            <h2 class="mt-2 text-xl font-heading font-semibold text-slate-900">{{ selectedUser.name }}</h2>
            <p class="mt-1 text-sm text-slate-500">{{ selectedUser.email }}</p>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">姓名</label>
              <input v-model="editForm.name" class="input-field" type="text" />
            </div>
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">邮箱</label>
              <input v-model="editForm.email" class="input-field" type="email" />
            </div>
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">角色</label>
              <select v-model="editForm.role" class="input-field">
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </div>
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">套餐</label>
              <select v-model="editForm.subscription" class="input-field">
                <option value="free">free</option>
                <option value="basic">basic</option>
                <option value="pro">pro</option>
                <option value="enterprise">enterprise</option>
              </select>
            </div>
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">Token 余额</label>
              <input v-model.number="editForm.token_balance" class="input-field" type="number" min="0" />
            </div>
            <div>
              <label class="mb-2 block text-xs font-medium text-slate-500">职称</label>
              <input v-model="editForm.title" class="input-field" type="text" />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-2 block text-xs font-medium text-slate-500">机构</label>
              <input v-model="editForm.institution" class="input-field" type="text" />
            </div>
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            <label class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>启用账号</span>
              <input v-model="editForm.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary" />
            </label>
            <label class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <span>邮箱已验证</span>
              <input v-model="editForm.is_verified" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary" />
            </label>
          </div>

          <div class="rounded-2xl bg-slate-50 px-4 py-4 text-sm text-slate-600">
            <div class="flex items-center justify-between">
              <span>项目数</span>
              <span>{{ selectedUser.project_count }}</span>
            </div>
            <div class="mt-2 flex items-center justify-between">
              <span>数据集数</span>
              <span>{{ selectedUser.dataset_count }}</span>
            </div>
            <div class="mt-2 flex items-center justify-between">
              <span>上次登录</span>
              <span>{{ selectedUser.last_login_at ? formatDate(selectedUser.last_login_at) : '从未登录' }}</span>
            </div>
          </div>

          <button
            type="button"
            :disabled="isSaving"
            class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0f9f6e] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#0b8a60] disabled:cursor-not-allowed disabled:opacity-60"
            @click="saveUser"
          >
            <svg v-if="isSaving" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            <span>{{ isSaving ? '保存中...' : '保存用户修改' }}</span>
          </button>
        </div>

        <div v-else class="flex min-h-[420px] items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400">
          从左侧选择一个用户开始编辑
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { getAdminUsers, updateAdminUser, type AdminUserItem } from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const users = ref<AdminUserItem[]>([])
const selectedUser = ref<AdminUserItem | null>(null)
const searchTerm = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive' | 'admin'>('all')
const isSaving = ref(false)
const errorMessage = ref('')

const editForm = reactive({
  name: '',
  email: '',
  role: 'user' as 'user' | 'admin',
  subscription: 'free',
  token_balance: 0,
  is_active: true,
  is_verified: false,
  institution: '',
  title: '',
})

const filteredUsers = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  return users.value.filter((user) => {
    const matchesTerm = !term || [user.name, user.email, user.institution || '', user.title || '']
      .some((value) => value.toLowerCase().includes(term))

    if (!matchesTerm) return false
    if (statusFilter.value === 'active') return user.is_active
    if (statusFilter.value === 'inactive') return !user.is_active
    if (statusFilter.value === 'admin') return user.role === 'admin'
    return true
  })
})

function badgeClass(kind: 'active' | 'inactive' | 'verified' | 'pending') {
  const styles = {
    active: 'bg-emerald-50 text-emerald-700',
    inactive: 'bg-rose-50 text-rose-700',
    verified: 'bg-sky-50 text-sky-700',
    pending: 'bg-amber-50 text-amber-700',
  }
  return ['inline-flex rounded-full px-2.5 py-1 text-xs font-medium', styles[kind]]
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function selectUser(user: AdminUserItem) {
  selectedUser.value = user
  editForm.name = user.name
  editForm.email = user.email
  editForm.role = user.role
  editForm.subscription = user.subscription
  editForm.token_balance = user.token_balance
  editForm.is_active = user.is_active
  editForm.is_verified = user.is_verified
  editForm.institution = user.institution || ''
  editForm.title = user.title || ''
}

async function loadUsers() {
  try {
    users.value = await getAdminUsers()
    if (users.value.length && !selectedUser.value) {
      selectUser(users.value[0])
    } else if (selectedUser.value) {
      const updated = users.value.find((item) => item.id === selectedUser.value?.id)
      if (updated) selectUser(updated)
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || error.message || '用户列表加载失败'
  }
}

async function saveUser() {
  if (!selectedUser.value) return
  isSaving.value = true
  try {
    const updatedUser = await updateAdminUser(selectedUser.value.id, { ...editForm })
    const index = users.value.findIndex((item) => item.id === updatedUser.id)
    if (index >= 0) {
      users.value[index] = updatedUser
    }
    selectUser(updatedUser)
    notificationStore.success('用户已更新', '用户资料和运营字段已保存。')
  } catch (error: any) {
    notificationStore.error('保存失败', error.response?.data?.detail || error.message || '请稍后重试')
  } finally {
    isSaving.value = false
  }
}

onMounted(async () => {
  await loadUsers()
})
</script>
