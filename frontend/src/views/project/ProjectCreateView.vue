<template>
  <div class="max-w-2xl mx-auto space-y-6 animate-fade-in">
    <div>
      <h1 class="text-2xl font-heading font-bold text-gray-900">创建新项目</h1>
      <p class="text-gray-500 mt-1">填写项目基本信息以开始您的统计分析</p>
    </div>

    <form @submit.prevent="handleCreate" class="card space-y-6">
      <!-- Project Name -->
      <div>
        <label for="project-name" class="block text-sm font-medium text-gray-700 mb-1.5">项目名称 <span class="text-danger">*</span></label>
        <input id="project-name" v-model="form.name" type="text" required placeholder="例如：糖尿病预后分析" class="input-field" />
      </div>

      <!-- Description -->
      <div>
        <label for="project-desc" class="block text-sm font-medium text-gray-700 mb-1.5">项目描述</label>
        <textarea id="project-desc" v-model="form.description" rows="4" placeholder="简要描述研究目的和方法..." class="input-field resize-none"></textarea>
      </div>

      <!-- Study Type -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">研究类型 <span class="text-danger">*</span></label>
        <div class="grid grid-cols-2 gap-3">
          <label v-for="type in studyTypes" :key="type.value"
            :class="['flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all', form.studyType === type.value ? 'border-primary bg-primary-50' : 'border-gray-200 hover:border-gray-300']"
          >
            <input type="radio" v-model="form.studyType" :value="type.value" class="sr-only" />
            <div :class="['w-4 h-4 rounded-full border-2 flex items-center justify-center', form.studyType === type.value ? 'border-primary' : 'border-gray-300']">
              <div v-if="form.studyType === type.value" class="w-2 h-2 rounded-full bg-primary"></div>
            </div>
            <span class="text-sm" :class="form.studyType === type.value ? 'text-primary font-medium' : 'text-gray-600'">{{ type.label }}</span>
          </label>
        </div>
      </div>

      <!-- Tags -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1.5">标签</label>
        <div class="flex flex-wrap gap-2">
          <button v-for="tag in availableTags" :key="tag" type="button"
            @click="toggleTag(tag)"
            :class="['px-3 py-1.5 rounded-full text-sm transition-all cursor-pointer', form.tags.includes(tag) ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']"
          >
            {{ tag }}
          </button>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
        <router-link to="/projects" class="btn-ghost">取消</router-link>
        <button type="submit" :disabled="loading" class="btn-primary">
          <svg v-if="loading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
          {{ loading ? '创建中...' : '创建项目' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createProject } from '@/services/api'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  name: '',
  description: '',
  studyType: '',
  tags: [] as string[],
})

const studyTypes = [
  { label: '回顾性研究', value: 'retrospective' },
  { label: '前瞻性研究', value: 'prospective' },
  { label: '横断面研究', value: 'cross-sectional' },
  { label: '随机对照试验', value: 'rct' },
  { label: 'Meta分析', value: 'meta' },
  { label: '其他', value: 'other' },
]

const availableTags = ['肿瘤', '心血管', '糖尿病', '呼吸', '神经', '儿科', '传染病', '公共卫生']

function toggleTag(tag: string) {
  const idx = form.tags.indexOf(tag)
  if (idx >= 0) form.tags.splice(idx, 1)
  else form.tags.push(tag)
}

async function handleCreate() {
  loading.value = true
  try {
    await createProject({
      name: form.name,
      study_type: form.studyType,
      description: form.description
    })
    router.push('/projects')
  } catch (error) {
    console.error('Failed to create project:', error)
  } finally {
    loading.value = false
  }
}
</script>
