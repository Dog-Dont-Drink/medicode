<template>
  <div class="mx-auto max-w-3xl animate-fade-in">
    <!-- Back link -->
    <button class="mb-4 flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors cursor-pointer" @click="$router.push('/projects')">
      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      返回项目列表
    </button>

    <div v-if="!project" class="text-center py-16">
      <p class="text-sm text-gray-400">加载中...</p>
    </div>

    <div v-else class="space-y-4">
      <!-- Project card -->
      <div class="rounded-xl border border-gray-100 bg-white p-5">
        <!-- View mode -->
        <div v-if="!isEditing">
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-primary-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
              </div>
              <div>
                <h1 class="text-base font-heading font-bold text-gray-900">{{ project.name }}</h1>
                <div class="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
                  <span v-if="project.study_type">{{ studyTypeLabel(project.study_type) }}</span>
                  <span v-if="project.study_type">·</span>
                  <span>创建于 {{ formatDate(project.created_at) }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span :class="['px-2 py-0.5 text-[10px] font-medium rounded-full', project.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400']">
                {{ project.status === 'active' ? '进行中' : '已完成' }}
              </span>
              <button class="p-1.5 rounded-md text-gray-400 hover:text-primary hover:bg-primary-50 transition-colors cursor-pointer" title="编辑项目" @click="startEdit">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4Z"/></svg>
              </button>
            </div>
          </div>
          <p v-if="project.description" class="mt-3 text-sm text-gray-500 leading-relaxed">{{ project.description }}</p>
          <p v-else class="mt-3 text-xs text-gray-300 italic">暂无描述</p>
        </div>

        <!-- Edit mode -->
        <div v-else class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">项目名称</label>
              <input v-model="editDraft.name" type="text" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">状态</label>
              <select v-model="editDraft.status" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white cursor-pointer">
                <option value="active">进行中</option>
                <option value="completed">已完成</option>
              </select>
            </div>
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-500 mb-1">描述</label>
              <textarea v-model="editDraft.description" rows="3" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"></textarea>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button @click="isEditing = false" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer">取消</button>
            <button @click="saveEdit" class="btn-primary btn-sm cursor-pointer">保存</button>
          </div>
        </div>
      </div>

      <!-- Quick stats row -->
      <div class="grid grid-cols-3 gap-3">
        <div class="rounded-xl border border-gray-100 bg-white px-4 py-3 text-center">
          <p class="text-lg font-bold text-gray-900">{{ project.dataset_count || 0 }}</p>
          <p class="text-[11px] text-gray-400 mt-0.5">数据集</p>
        </div>
        <div class="rounded-xl border border-gray-100 bg-white px-4 py-3 text-center">
          <p class="text-lg font-bold text-gray-900">{{ project.analysis_count || 0 }}</p>
          <p class="text-[11px] text-gray-400 mt-0.5">分析任务</p>
        </div>
        <div class="rounded-xl border border-gray-100 bg-white px-4 py-3 text-center">
          <p class="text-lg font-bold text-gray-900">{{ formatDate(project.updated_at) }}</p>
          <p class="text-[11px] text-gray-400 mt-0.5">最近更新</p>
        </div>
      </div>

      <!-- Saved workflows -->
      <div class="rounded-xl border border-gray-100 bg-white p-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide">临床预测流程</h3>
            <p class="mt-1 text-[11px] text-gray-400">保存的画布流程可在这里快速打开继续编辑。</p>
          </div>
          <button
            class="btn-primary btn-sm cursor-pointer"
            type="button"
            @click="openWorkflowBuilder()"
          >
            新建流程
          </button>
        </div>

        <div v-if="isLoadingWorkflows" class="mt-3 text-xs text-gray-400">加载中...</div>
        <div v-else-if="workflowError" class="mt-3 text-xs text-rose-500">{{ workflowError }}</div>
        <div v-else-if="!clinicalWorkflows.length" class="mt-3 rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-3 text-xs text-gray-400">
          暂无已保存流程。你可以在临床模型画布里点击“保存流程”，然后回到这里查看。
        </div>
        <div v-else class="mt-3 space-y-2">
          <div
            v-for="wf in clinicalWorkflows"
            :key="wf.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-gray-100 px-3 py-2.5 hover:border-primary/20 hover:bg-primary-50/40 transition-colors"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-gray-900">{{ wf.name }}</p>
              <p class="mt-0.5 text-[11px] text-gray-400">
                {{ wf.node_count }} 节点 · {{ wf.connection_count }} 连线 · 更新于 {{ formatDateTime(wf.updated_at) }}
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-primary border border-primary/20 rounded-lg hover:bg-primary-50 transition-colors cursor-pointer"
                type="button"
                @click="openWorkflowBuilder(wf.id)"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 3h7v7"/><path d="M10 14L21 3"/><path d="M21 14v7h-7"/><path d="M3 10V3h7"/><path d="M3 14v7h7"/>
                </svg>
                打开
              </button>
              <button
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-rose-600 border border-rose-200 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer"
                type="button"
                @click="confirmDeleteWorkflow(wf)"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 16h10l1-16"/><path d="M10 11v6"/><path d="M14 11v6"/>
                </svg>
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="rounded-xl border border-gray-100 bg-white p-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">快捷操作</h3>
        <div class="grid grid-cols-3 gap-2">
          <router-link to="/data" class="flex flex-col items-center gap-1.5 rounded-lg border border-gray-100 px-3 py-3 text-gray-500 hover:border-primary/20 hover:text-primary hover:bg-primary-50/50 transition-all cursor-pointer">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            <span class="text-xs font-medium">数据管理</span>
          </router-link>
          <router-link to="/analysis/descriptive" class="flex flex-col items-center gap-1.5 rounded-lg border border-gray-100 px-3 py-3 text-gray-500 hover:border-primary/20 hover:text-primary hover:bg-primary-50/50 transition-all cursor-pointer">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            <span class="text-xs font-medium">统计分析</span>
          </router-link>
          <router-link to="/reports" class="flex flex-col items-center gap-1.5 rounded-lg border border-gray-100 px-3 py-3 text-gray-500 hover:border-primary/20 hover:text-primary hover:bg-primary-50/50 transition-all cursor-pointer">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-xs font-medium">报告中心</span>
          </router-link>
        </div>
      </div>

      <!-- Danger zone -->
      <div class="rounded-xl border border-gray-100 bg-white p-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-xs font-semibold text-gray-900">删除项目</h3>
            <p class="text-[11px] text-gray-400 mt-0.5">删除后不可恢复，关联数据将一并移除</p>
          </div>
          <button @click="confirmDelete" class="px-3 py-1.5 text-xs font-medium text-rose-500 border border-rose-200 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer">删除项目</button>
        </div>
      </div>
    </div>

    <!-- Delete confirm dialog -->
    <teleport to="body">
      <transition name="fade">
        <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="showDeleteConfirm = false">
          <div class="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900">确认删除</h3>
            <p class="mt-2 text-xs text-gray-500">确定要删除项目「{{ project?.name }}」吗？此操作不可恢复。</p>
            <div class="mt-4 flex justify-end gap-2">
              <button @click="showDeleteConfirm = false" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer">取消</button>
              <button @click="doDelete" class="px-3 py-1.5 text-xs font-medium text-white bg-rose-500 hover:bg-rose-600 rounded-lg transition-colors cursor-pointer">删除</button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <!-- Workflow delete confirm dialog -->
    <teleport to="body">
      <transition name="fade">
        <div
          v-if="showWorkflowDeleteConfirm"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
          @click.self="showWorkflowDeleteConfirm = false"
        >
          <div class="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
            <h3 class="text-sm font-semibold text-gray-900">删除流程</h3>
            <p class="mt-2 text-xs text-gray-500">
              确定要删除流程「{{ workflowToDelete?.name || '-' }}」吗？此操作不可恢复。
            </p>
            <div class="mt-4 flex justify-end gap-2">
              <button
                class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 cursor-pointer"
                type="button"
                :disabled="isDeletingWorkflow"
                @click="showWorkflowDeleteConfirm = false"
              >
                取消
              </button>
              <button
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-rose-500 hover:bg-rose-600 rounded-lg transition-colors cursor-pointer disabled:opacity-70"
                type="button"
                :disabled="isDeletingWorkflow || !workflowToDelete"
                @click="doDeleteWorkflow()"
              >
                <svg v-if="isDeletingWorkflow" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 16h10l1-16"/><path d="M10 11v6"/><path d="M14 11v6"/>
                </svg>
                确认删除
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, updateProject as apiUpdateProject, deleteProject as apiDeleteProject, deleteClinicalWorkflow, listClinicalWorkflows } from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId as string
const notificationStore = useNotificationStore()

const project = ref<any>(null)
const isEditing = ref(false)
const editDraft = ref({ name: '', description: '', status: '' })
const showDeleteConfirm = ref(false)
const clinicalWorkflows = ref<any[]>([])
const isLoadingWorkflows = ref(false)
const workflowError = ref('')
const showWorkflowDeleteConfirm = ref(false)
const workflowToDelete = ref<any | null>(null)
const isDeletingWorkflow = ref(false)

onMounted(async () => {
  try {
    project.value = await getProject(projectId)
  } catch (error) {
    console.error('Failed to load project:', error)
  }

  await loadClinicalWorkflows()
})

const studyTypeMap: Record<string, string> = {
  cohort: '队列研究',
  rct: '随机对照试验',
  'case-control': '病例对照研究',
  'cross-sectional': '横断面研究',
  meta: 'Meta 分析',
}

function studyTypeLabel(type: string) {
  return studyTypeMap[type] || type
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

async function loadClinicalWorkflows() {
  workflowError.value = ''
  isLoadingWorkflows.value = true
  try {
    // Only list workflows created by the clinical prediction canvas.
    clinicalWorkflows.value = await listClinicalWorkflows(projectId, 'clinical_prediction')
  } catch (error: any) {
    workflowError.value = error?.response?.data?.detail || '流程列表加载失败'
    clinicalWorkflows.value = []
  } finally {
    isLoadingWorkflows.value = false
  }
}

function openWorkflowBuilder(workflowId?: string) {
  router.push({
    name: 'ClinicalModelBuilder',
    query: {
      projectId,
      workflowId: workflowId || undefined,
    },
  })
}

function confirmDeleteWorkflow(workflow: any) {
  workflowToDelete.value = workflow
  showWorkflowDeleteConfirm.value = true
}

async function doDeleteWorkflow() {
  if (!workflowToDelete.value || isDeletingWorkflow.value) return
  isDeletingWorkflow.value = true
  try {
    await deleteClinicalWorkflow(workflowToDelete.value.id)
    notificationStore.success('流程已删除', workflowToDelete.value.name || '')
    showWorkflowDeleteConfirm.value = false
    workflowToDelete.value = null
    await loadClinicalWorkflows()
  } catch (error: any) {
    notificationStore.error('删除失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    isDeletingWorkflow.value = false
  }
}

function startEdit() {
  editDraft.value = {
    name: project.value.name || '',
    description: project.value.description || '',
    status: project.value.status || 'active',
  }
  isEditing.value = true
}

async function saveEdit() {
  try {
    project.value = await apiUpdateProject(projectId, {
      name: editDraft.value.name,
      description: editDraft.value.description,
      status: editDraft.value.status,
    })
    isEditing.value = false
  } catch (error) {
    console.error('Failed to update project:', error)
  }
}

function confirmDelete() {
  showDeleteConfirm.value = true
}

async function doDelete() {
  try {
    await apiDeleteProject(projectId)
    router.push('/projects')
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
