<template>
  <div>
    <!-- Header row -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-heading font-bold text-gray-900">我的项目</h1>
        <p class="text-sm text-gray-500 mt-1">管理您的研究项目与分析任务</p>
      </div>
      <button @click="showCreatePanel = !showCreatePanel" class="btn-primary cursor-pointer">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        {{ showCreatePanel ? '取消' : '新建项目' }}
      </button>
    </div>

    <!-- Inline Create Panel -->
    <transition name="slide-down">
      <div v-if="showCreatePanel" class="mb-6 p-6 bg-white rounded-2xl border border-gray-100 shadow-sm">
        <h3 class="text-lg font-heading font-semibold text-gray-900 mb-4">新建研究项目</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">项目名称</label>
            <input v-model="newProject.name" type="text" placeholder="例如：糖尿病预后因素研究" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">研究类型</label>
            <select v-model="newProject.type" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all bg-white cursor-pointer">
              <option value="">选择类型</option>
              <option value="cohort">队列研究</option>
              <option value="rct">随机对照试验</option>
              <option value="case-control">病例对照研究</option>
              <option value="cross-sectional">横断面研究</option>
              <option value="meta">Meta 分析</option>
            </select>
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">简要描述</label>
            <textarea v-model="newProject.description" rows="2" placeholder="描述您的研究目的与方法..." class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-4">
          <button @click="showCreatePanel = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors cursor-pointer">取消</button>
          <button @click="createProject" class="btn-primary btn-sm cursor-pointer">创建项目</button>
        </div>
      </div>
    </transition>

    <!-- Search & Filter -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-5">
      <div class="relative flex-1 w-full">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="search" type="text" placeholder="搜索项目名称..." class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
      </div>
      <div class="flex gap-1 bg-gray-100 rounded-xl p-1">
        <button v-for="f in ['全部', '进行中', '已完成']" :key="f" @click="filter = f" :class="['px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all cursor-pointer', filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']">{{ f }}</button>
      </div>
    </div>

    <!-- Project Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="project in filteredProjects" :key="project.id"
        class="group bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-card hover:border-primary/10 transition-all duration-300 cursor-pointer"
        @click="$router.push(`/projects/${project.id}`)"
      >
        <div class="flex items-start justify-between mb-3">
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-primary to-primary-600']">
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
          </div>
          <span :class="['px-2.5 py-1 text-xs font-medium rounded-full', project.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500']">
            {{ project.status === 'active' ? '进行中' : '已完成' }}
          </span>
        </div>
        <h3 class="text-base font-semibold text-gray-900 group-hover:text-primary transition-colors">{{ project.name }}</h3>
        <p class="text-sm text-gray-500 mt-1 line-clamp-2">{{ project.description }}</p>
        <div class="flex items-center gap-4 mt-4 pt-3 border-t border-gray-50 text-xs text-gray-400">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            {{ project.dataset_count || 0 }} 数据集
          </span>
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            {{ project.analysis_count || 0 }} 分析
          </span>
          <span class="ml-auto">{{ new Date(project.updated_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredProjects.length === 0" class="text-center py-16">
      <div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
      </div>
      <p class="text-gray-400 text-sm">暂无项目，点击上方按钮创建</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getProjects, createProject as apiCreateProject } from '@/services/api'

const showCreatePanel = ref(false)
const search = ref('')
const filter = ref('全部')
const newProject = ref({ name: '', type: '', description: '' })

const projects = ref<any[]>([])

const fetchProjects = async () => {
  try {
    projects.value = await getProjects()
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}

onMounted(() => {
  fetchProjects()
})

const filteredProjects = computed(() => {
  let list = projects.value
  if (filter.value === '进行中') list = list.filter(p => p.status === 'active')
  if (filter.value === '已完成') list = list.filter(p => p.status === 'completed')
  if (search.value) list = list.filter(p => p.name.includes(search.value))
  return list
})

async function createProject() {
  if (!newProject.value.name) return
  
  try {
    await apiCreateProject({
      name: newProject.value.name,
      study_type: newProject.value.type,
      description: newProject.value.description
    })
    
    // Refresh list after creation
    await fetchProjects()
    
    newProject.value = { name: '', type: '', description: '' }
    showCreatePanel.value = false
  } catch (error) {
    console.error('Failed to create project:', error)
  }
}
</script>

<style scoped>
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
}
.slide-down-enter-to, .slide-down-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
