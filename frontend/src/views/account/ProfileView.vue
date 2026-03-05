<template>
  <div class="max-w-3xl mx-auto space-y-6 animate-fade-in">
    <h1 class="text-2xl font-heading font-bold text-gray-900">个人资料</h1>
    <div class="card space-y-6">
      <div class="flex items-center gap-5">
        <div class="w-20 h-20 overflow-hidden bg-gradient-to-br from-primary to-accent rounded-2xl flex items-center justify-center shadow-card">
          <img v-if="avatarUrl" :src="avatarUrl" alt="头像" class="w-full h-full object-cover" />
          <span v-else class="text-2xl font-bold text-white">{{ userInitial }}</span>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900">{{ profile.name }}</h2>
          <p class="text-gray-500">{{ profile.email }}</p>
          <router-link to="/account/settings" class="text-sm text-primary hover:underline mt-1 inline-block cursor-pointer">前往设置修改头像</router-link>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">姓名</label><input type="text" :value="profile.name" class="input-field" disabled /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">邮箱</label><input type="email" :value="profile.email" class="input-field" disabled /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">所属机构</label><input type="text" :value="profile.institution" class="input-field" disabled /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">职称</label><input type="text" :value="profile.title" class="input-field" disabled /></div>
        <div class="md:col-span-2"><label class="block text-sm font-medium text-gray-700 mb-1.5">研究方向</label><input type="text" :value="profile.researchField" class="input-field" disabled /></div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">个人简介</label>
        <textarea :value="profile.bio" class="input-field min-h-28 resize-none" disabled />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUserProfile } from '@/services/api'

const authStore = useAuthStore()

const profile = reactive({
  name: '',
  email: '',
  title: '',
  institution: '',
  researchField: '',
  bio: '',
  avatarUrl: '',
})

const userInitial = computed(() => (profile.name?.[0] || 'U').toUpperCase())
const avatarUrl = computed(() => profile.avatarUrl)

onMounted(async () => {
  if (authStore.token && !authStore.user) {
    await authStore.loadProfile()
  }

  const userProfile = await getUserProfile()
  Object.assign(profile, {
    name: userProfile.name || '',
    email: userProfile.email || '',
    title: userProfile.title || '',
    institution: userProfile.institution || '',
    researchField: userProfile.research_field || '',
    bio: userProfile.bio || '',
    avatarUrl: userProfile.avatar_url || '',
  })
})
</script>
