<template>
  <div class="space-y-6 animate-fade-in">
    <div class="rounded-2xl border border-emerald-100 bg-emerald-50/70 px-5 py-4">
      <p class="text-sm font-semibold text-emerald-900">上传前请先完成数据脱敏</p>
      <p class="mt-1 text-sm leading-6 text-emerald-800">
        为保护患者隐私，建议您在上传前隐藏或提前删除姓名、身份证号、手机号、住址、住院号等可直接识别个人身份的关键信息，
        并尽量避免上传能够反向定位患者身份的敏感字段。平台会对您上传的数据严格保密，仅用于您授权的分析处理。
      </p>
    </div>

    <div class="card">
      <!-- Project Selection -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">选择关联项目 <span class="text-danger">*</span></label>
        <select v-model="selectedProjectId" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all bg-white cursor-pointer" :disabled="isLoadingProjects">
          <option value="">请选择项目...</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name }} - {{ project.study_type || '无类型' }}
          </option>
        </select>
      </div>

      <!-- Upload Zone -->
      <div
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="handleDrop"
        :class="['border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer', isDragging ? 'border-primary bg-primary-50/50' : 'border-gray-300 hover:border-primary/50 hover:bg-gray-50']"
        @click="triggerFileInput"
      >
        <input ref="fileInput" type="file" accept=".csv,.xlsx,.xls,.sav,.dta" class="hidden" @change="handleFileSelect" multiple />
        <div class="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <p class="text-gray-700 font-medium">拖拽文件到此处，或点击选择</p>
        <p class="text-sm text-gray-400 mt-2">支持 CSV, Excel (.xlsx/.xls), SPSS (.sav), Stata (.dta)</p>
        <p class="text-xs text-gray-400 mt-1">最大文件大小：100MB</p>
      </div>

      <!-- Uploaded Files -->
      <div v-if="files.length > 0" class="mt-6 space-y-3">
        <h3 class="text-sm font-semibold text-gray-700">已选择文件</h3>
        <div v-for="(file, index) in files" :key="index" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ file.name }}</p>
            <p class="text-xs text-gray-400">{{ formatFileSize(file.size) }}</p>
          </div>
          <button @click="removeFile(index)" class="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-danger transition-colors cursor-pointer">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <button @click="startUpload" :disabled="files.length === 0 || !selectedProjectId || isUploading" class="btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
          <svg v-if="isUploading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
          <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ isUploading ? '上传中...' : '开始上传' }}
        </button>
        <p v-if="uploadMessage" :class="['text-sm mt-2 text-center', uploadSuccess ? 'text-green-500' : 'text-danger']">{{ uploadMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getProjects, uploadDataset } from '@/services/api'

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<File[]>([])

const projects = ref<any[]>([])
const selectedProjectId = ref('')
const isLoadingProjects = ref(true)

const isUploading = ref(false)
const uploadMessage = ref('')
const uploadSuccess = ref(false)

onMounted(async () => {
  try {
    projects.value = await getProjects()
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id
    }
  } catch (err) {
    console.error('Failed to load projects', err)
  } finally {
    isLoadingProjects.value = false
  }
})

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    files.value.push(...Array.from(input.files))
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files) {
    files.value.push(...Array.from(e.dataTransfer.files))
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function startUpload() {
  if (files.value.length === 0 || !selectedProjectId.value) return
  
  isUploading.value = true
  uploadMessage.value = ''
  
  try {
    for (const file of files.value) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', selectedProjectId.value)
      
      await uploadDataset(formData)
    }
    uploadSuccess.value = true
    uploadMessage.value = '全部文件上传成功'
    files.value = [] // Clear after success
  } catch (error: any) {
    uploadSuccess.value = false
    uploadMessage.value = '上传失败: ' + (error.response?.data?.detail || error.message)
    console.error('Upload failed', error)
  } finally {
    isUploading.value = false
  }
}
</script>
