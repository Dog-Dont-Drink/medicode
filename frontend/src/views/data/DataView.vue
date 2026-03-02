<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-heading font-bold text-gray-900">数据管理</h1>
        <p class="text-sm text-gray-500 mt-1">上传、预览和管理您的研究数据</p>
      </div>
      <!-- Project Selection -->
      <div class="flex items-center gap-3">
        <label class="text-sm text-gray-700">当前项目</label>
        <select v-model="selectedProjectId" @change="loadDatasets" class="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white min-w-[200px]" :disabled="isLoadingProjects">
          <option value="">请选择项目...</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <!-- Left: Upload area -->
      <div class="xl:col-span-4">
        <div class="bg-white rounded-2xl border border-gray-100 p-5">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            上传数据
          </h3>

          <!-- Drop zone -->
          <div
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleDrop"
            :class="['border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer', isDragging ? 'border-primary bg-primary-50' : 'border-gray-200 hover:border-primary/40 hover:bg-gray-50']"
            @click="triggerUpload"
          >
            <!-- File input hidden under the drop zone -->
            <input ref="fileInput" type="file" class="hidden" accept=".csv,.xlsx,.xls,.sav,.dta" multiple @change="handleFiles" />
            <div class="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <svg v-if="isUploading" class="w-6 h-6 text-primary animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
              <svg v-else class="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <p class="text-sm text-gray-600 font-medium">{{ isUploading ? '正在上传中...' : '拖拽文件到此处' }}</p>
            <p v-if="!isUploading" class="text-xs text-gray-400 mt-1">或点击选择文件</p>
            <p class="text-xs text-gray-300 mt-2">选定项目后可上传数据集</p>
          </div>

          <!-- Uploaded files list -->
          <div v-if="uploadedFiles.length" class="mt-4 space-y-2">
            <div v-for="(file, i) in uploadedFiles" :key="i" class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
              <div class="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-900 truncate">{{ file.name }}</p>
                <p class="text-[10px] text-gray-400">{{ file.size }}</p>
              </div>
              <button @click="selectFile(file)" :class="['text-xs px-2.5 py-1 rounded-lg transition-all cursor-pointer', selectedFile?.name === file.name ? 'bg-primary text-white' : 'bg-white text-gray-500 hover:text-primary border border-gray-200']">
                预览
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Data Preview -->
      <div class="xl:col-span-8">
        <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <svg class="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
              {{ selectedFile ? selectedFile.name : '数据预览' }}
            </h3>
            <span class="text-xs text-gray-400" v-if="selectedFile">
              {{ selectedFile.row_count || '未知' }} 行 × {{ mockColumns.length }} 列 (预览仅显示前5行)
            </span>
          </div>

          <div v-if="selectedFile" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-gray-50">
                  <th v-for="col in mockColumns" :key="col" class="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in mockData" :key="i" class="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <td v-for="col in mockColumns" :key="col" class="px-4 py-2.5 text-xs text-gray-600 whitespace-nowrap">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Empty state -->
          <div v-else class="flex flex-col items-center justify-center py-20">
            <div class="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mb-4">
              <svg class="w-8 h-8 text-gray-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
            </div>
            <p class="text-gray-400 text-sm">左侧点击数据集"预览"查看数据</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getProjects, getDatasets, uploadDataset } from '@/services/api'

const projects = ref<any[]>([])
const selectedProjectId = ref('')
const isLoadingProjects = ref(true)

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<any>(null)

const uploadedFiles = ref<any[]>([])
const isUploading = ref(false)

onMounted(async () => {
  try {
    projects.value = await getProjects()
    if (projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id
      await loadDatasets()
    }
  } catch (err) {
    console.error('Failed to load projects', err)
  } finally {
    isLoadingProjects.value = false
  }
})

const loadDatasets = async () => {
  if (!selectedProjectId.value) return
  uploadedFiles.value = []
  try {
    const data = await getDatasets(selectedProjectId.value)
    uploadedFiles.value = data.map((d: any) => ({
      id: d.id,
      name: d.filename,
      size: formatFileSize(d.size_bytes),
      row_count: d.row_count,
    }))
  } catch (err) {
    console.error('Failed to load datasets', err)
  }
}

function formatFileSize(bytes: number) {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const mockColumns = ['patient_id', 'age', 'gender', 'bmi', 'blood_pressure', 'glucose', 'outcome']
const mockData: Record<string, string | number>[] = [
  { patient_id: 'P001', age: 45, gender: '男', bmi: 24.5, blood_pressure: '130/85', glucose: 6.1, outcome: '好转' },
  { patient_id: 'P002', age: 58, gender: '女', bmi: 28.3, blood_pressure: '145/92', glucose: 7.8, outcome: '稳定' },
  { patient_id: 'P003', age: 33, gender: '男', bmi: 22.1, blood_pressure: '120/78', glucose: 5.2, outcome: '好转' },
  { patient_id: 'P004', age: 67, gender: '女', bmi: 31.0, blood_pressure: '158/98', glucose: 9.4, outcome: '恶化' },
  { patient_id: 'P005', age: 41, gender: '男', bmi: 25.7, blood_pressure: '135/88', glucose: 6.5, outcome: '好转' },
  { patient_id: 'P006', age: 55, gender: '女', bmi: 26.9, blood_pressure: '142/90', glucose: 7.2, outcome: '稳定' },
  { patient_id: 'P007', age: 72, gender: '男', bmi: 23.8, blood_pressure: '150/95', glucose: 8.1, outcome: '稳定' },
  { patient_id: 'P008', age: 29, gender: '女', bmi: 21.4, blood_pressure: '115/72', glucose: 4.9, outcome: '好转' },
]

function triggerUpload() {
  if (!selectedProjectId.value) {
    alert('请先在顶部选择一个项目')
    return
  }
  fileInput.value?.click()
}

async function handleFiles(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    await processUploads(target.files)
  }
  isDragging.value = false
  if (fileInput.value) fileInput.value.value = ''
}

async function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (!selectedProjectId.value) {
    alert('请先在顶部选择一个项目')
    return
  }
  if (e.dataTransfer?.files) {
    await processUploads(e.dataTransfer.files)
  }
}

async function processUploads(files: FileList) {
  isUploading.value = true
  try {
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData()
        formData.append('file', files[i])
        formData.append('project_id', selectedProjectId.value)
        await uploadDataset(formData)
    }
    await loadDatasets()
  } catch (error: any) {
    console.error('Upload failed', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    isUploading.value = false
  }
}

function selectFile(file: any) {
  selectedFile.value = file
}
</script>
