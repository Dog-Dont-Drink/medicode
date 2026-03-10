<template>
  <div class="mx-auto max-w-3xl">
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div>
        <h1 class="text-lg font-heading font-bold text-gray-900">我的项目</h1>
        <p class="text-xs text-gray-400 mt-0.5">管理您的研究项目</p>
      </div>
      <button @click="showCreatePanel = !showCreatePanel" class="btn-primary btn-sm cursor-pointer">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        {{ showCreatePanel ? '取消' : '新建项目' }}
      </button>
    </div>

    <!-- Inline Create Panel -->
    <transition name="slide-down">
      <div v-if="showCreatePanel" class="mb-5 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
        <h3 class="text-sm font-semibold text-gray-900 mb-3">新建研究项目</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">项目名称</label>
            <input v-model="newProject.name" type="text" placeholder="例如：糖尿病预后因素研究" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">研究类型</label>
            <select v-model="newProject.type" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all bg-white cursor-pointer">
              <option value="">选择类型</option>
              <option value="cohort">队列研究</option>
              <option value="rct">随机对照试验</option>
              <option value="case-control">病例对照研究</option>
              <option value="cross-sectional">横断面研究</option>
              <option value="meta">Meta 分析</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-500 mb-1">简要描述</label>
            <textarea v-model="newProject.description" rows="2" placeholder="描述您的研究目的与方法..." class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-3">
          <button @click="showCreatePanel = false" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors cursor-pointer">取消</button>
          <button @click="createProject" class="btn-primary btn-sm cursor-pointer">创建项目</button>
        </div>
      </div>
    </transition>

    <!-- Search & Filter -->
    <div class="flex items-center gap-2 mb-4">
      <div class="relative flex-1">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="search" type="text" placeholder="搜索项目..." class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
      </div>
      <div class="flex gap-0.5 bg-gray-100 rounded-lg p-0.5">
        <button v-for="f in ['全部', '进行中', '已完成']" :key="f" @click="filter = f" :class="['px-3 py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer', filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']">{{ f }}</button>
      </div>
    </div>

    <!-- Project List -->
    <div class="space-y-2">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="group rounded-xl border border-gray-100 bg-white transition-all duration-200 hover:shadow-sm hover:border-primary/10"
      >
        <!-- View mode -->
        <div v-if="editingId !== project.id" class="flex items-center gap-4 px-4 py-3.5">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center shrink-0">
            <svg class="w-4.5 h-4.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
          </div>
          <div class="min-w-0 flex-1 cursor-pointer" @click="$router.push(`/projects/${project.id}`)">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-semibold text-gray-900 truncate group-hover:text-primary transition-colors">{{ project.name }}</h3>
              <span :class="['shrink-0 px-2 py-0.5 text-[10px] font-medium rounded-full', project.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400']">
                {{ project.status === 'active' ? '进行中' : '已完成' }}
              </span>
            </div>
            <p class="text-xs text-gray-400 mt-0.5 truncate">{{ project.description || '暂无描述' }}</p>
          </div>
          <div class="flex items-center gap-3 shrink-0 text-xs text-gray-400">
            <span class="flex items-center gap-1" title="数据集">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
              {{ project.dataset_count || 0 }}
            </span>
            <span class="flex items-center gap-1" title="分析">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              {{ project.analysis_count || 0 }}
            </span>
            <span class="hidden sm:inline text-gray-300">{{ formatDate(project.updated_at) }}</span>
          </div>
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
            <button class="p-1.5 rounded-md text-gray-400 hover:text-primary hover:bg-primary-50 transition-colors cursor-pointer" title="编辑" @click.stop="startEdit(project)">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4Z"/></svg>
            </button>
            <button class="p-1.5 rounded-md text-gray-400 hover:text-rose-500 hover:bg-rose-50 transition-colors cursor-pointer" title="删除" @click.stop="confirmDelete(project)">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg>
            </button>
          </div>
        </div>

        <!-- Edit mode -->
        <div v-else class="px-4 py-3.5 space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">项目名称</label>
              <input v-model="editDraft.name" type="text" class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">状态</label>
              <select v-model="editDraft.status" class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white cursor-pointer">
                <option value="active">进行中</option>
                <option value="completed">已完成</option>
              </select>
            </div>
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-500 mb-1">描述</label>
              <textarea v-model="editDraft.description" rows="2" class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"></textarea>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button @click="editingId = null" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer">取消</button>
            <button @click="saveEdit(project.id)" class="btn-primary btn-sm cursor-pointer">保存</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredProjects.length === 0 && !showCreatePanel" class="text-center py-16">
      <div class="w-14 h-14 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-3">
        <svg class="w-7 h-7 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
      </div>
      <p class="text-gray-400 text-sm">暂无项目，点击上方按钮创建</p>
    </div>

    <!-- Delete confirm dialog -->
    <teleport to="body">
      <transition name="fade">
        <div v-if="deletingProject" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deletingProject = null">
          <div class="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900">确认删除</h3>
            <p class="mt-2 text-xs text-gray-500">确定要删除项目「{{ deletingProject.name }}」吗？此操作不可恢复，关联数据将一并删除。</p>
            <div class="mt-4 flex justify-end gap-2">
              <button @click="deletingProject = null" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer">取消</button>
              <button @click="doDelete" class="px-3 py-1.5 text-xs font-medium text-white bg-rose-500 hover:bg-rose-600 rounded-lg transition-colors cursor-pointer">删除</button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getProjects, createProject as apiCreateProject, updateProject as apiUpdateProject, deleteProject as apiDeleteProject } from '@/services/api'

const showCreatePanel = ref(false)
const search = ref('')
const filter = ref('全部')
const newProject = ref({ name: '', type: '', description: '' })

const projects = ref<any[]>([])
const editingId = ref<string | null>(null)
const editDraft = ref({ name: '', description: '', status: '' })
const deletingProject = ref<any>(null)

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

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const m = d.getMonth() + 1
  const day = d.getDate()
  return `${m}/${day}`
}

async function createProject() {
  if (!newProject.value.name) return
  try {
    await apiCreateProject({
      name: newProject.value.name,
      study_type: newProject.value.type,
      description: newProject.value.description,
    })
    await fetchProjects()
    newProject.value = { name: '', type: '', description: '' }
    showCreatePanel.value = false
  } catch (error) {
    console.error('Failed to create project:', error)
  }
}

function startEdit(project: any) {
  editingId.value = project.id
  editDraft.value = {
    name: project.name || '',
    description: project.description || '',
    status: project.status || 'active',
  }
}

async function saveEdit(projectId: string) {
  try {
    await apiUpdateProject(projectId, {
      name: editDraft.value.name,
      description: editDraft.value.description,
      status: editDraft.value.status,
    })
    await fetchProjects()
    editingId.value = null
  } catch (error) {
    console.error('Failed to update project:', error)
  }
}

function confirmDelete(project: any) {
  deletingProject.value = project
}

async function doDelete() {
  if (!deletingProject.value) return
  try {
    await apiDeleteProject(deletingProject.value.id)
    await fetchProjects()
    deletingProject.value = null
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}
</script>

<style scoped>
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.2s ease;
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
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
