<template>
  <section class="space-y-5">
      <div v-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ errorMessage }}
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white shadow-sm shadow-slate-200/60">
        <div class="border-b border-slate-200 px-5 py-4">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-slate-400">{{ currentTable?.table_name || 'Table' }}</p>
              <h2 class="mt-2 text-xl font-heading font-semibold text-slate-900">{{ currentTableLabel }}</h2>
              <p class="mt-1 text-sm text-slate-500">鍏?{{ currentTable?.total || 0 }} 琛岋紝鐐瑰嚮浠绘剰涓€琛屽嵆鍙湪鍙充晶缂栬緫銆?/p>
            </div>
            <button
              type="button"
              class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:text-primary"
              @click="reloadCurrentTable"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-2.64-6.36" />
                <path d="M21 3v6h-6" />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="isLoadingTables" class="p-5">
          <div class="space-y-3">
            <div v-for="index in 5" :key="index" class="h-12 animate-pulse rounded-2xl bg-slate-100"></div>
          </div>
        </div>

        <div v-else-if="currentTable" class="grid gap-0 xl:grid-cols-[1.1fr_0.9fr]">
          <div class="overflow-x-auto border-b border-slate-200 xl:border-b-0 xl:border-r">
            <table class="min-w-full text-sm">
              <thead class="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th
                    v-for="column in currentTable.columns"
                    :key="column.name"
                    class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
                  >
                    {{ column.name }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in currentTable.rows"
                  :key="String(row[currentTable.primary_key])"
                  class="cursor-pointer border-b border-slate-100 transition hover:bg-slate-50"
                  :class="selectedRowId === String(row[currentTable.primary_key]) ? 'bg-emerald-50/70' : ''"
                  @click="selectRow(row)"
                >
                  <td
                    v-for="column in currentTable.columns"
                    :key="column.name"
                    class="max-w-[220px] truncate px-4 py-3 align-top text-slate-600"
                  >
                    {{ renderCell(row[column.name]) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="p-5">
            <div v-if="selectedRow" class="space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Row Editor</p>
                  <p class="mt-2 text-sm font-medium text-slate-900">涓婚敭 {{ selectedRowId }}</p>
                </div>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-3 py-2 text-sm text-rose-600 transition hover:bg-rose-50"
                  @click="removeRow"
                >
                  鍒犻櫎鏈
                </button>
              </div>

              <div class="grid gap-4">
                <div v-for="column in editableColumns" :key="column.name">
                  <label class="mb-2 block text-xs font-medium uppercase tracking-[0.15em] text-slate-400">
                    {{ column.name }}
                  </label>
                  <textarea
                    v-if="isLargeField(column.name)"
                    v-model="editBuffer[column.name]"
                    rows="4"
                    class="input-field min-h-[112px]"
                  />
                  <input
                    v-else
                    v-model="editBuffer[column.name]"
                    type="text"
                    class="input-field"
                  />
                </div>
              </div>

              <button
                type="button"
                :disabled="isSaving"
                class="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0f9f6e] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#0b8a60] disabled:cursor-not-allowed disabled:opacity-60"
                @click="saveRow"
              >
                <svg v-if="isSaving" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                <span>{{ isSaving ? '淇濆瓨涓?..' : '淇濆瓨褰撳墠琛? }}</span>
              </button>
            </div>

            <div v-else class="flex min-h-[360px] items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400">
              璇烽€夋嫨涓€琛屽紑濮嬬紪杈?
            </div>
          </div>
        </div>
      </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import {
  deleteAdminTableRow,
  getAdminTableRows,
  updateAdminTableRow,
  type AdminTableColumn,
  type AdminTableRowsResponse,
} from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const notificationStore = useNotificationStore()

const currentTable = ref<AdminTableRowsResponse | null>(null)
const selectedRow = ref<Record<string, any> | null>(null)
const selectedRowId = ref('')
const isLoadingTables = ref(true)
const isSaving = ref(false)
const errorMessage = ref('')
const editBuffer = reactive<Record<string, string>>({})

const currentTableLabel = computed(() => {
  const tableName = typeof route.params.tableName === 'string' ? route.params.tableName : ''
  const labelMap: Record<string, string> = {
    analyses: '鍒嗘瀽浠诲姟',
    analysis_results: '鍒嗘瀽缁撴灉',
    dataset_dictionary: '鏁版嵁瀛楀吀',
    datasets: '鏁版嵁闆?,
    orders: '璁㈠崟璁板綍',
    projects: '椤圭洰琛?,
    token_usage: 'Token 娑堣€?,
    users: '鐢ㄦ埛琛?,
    verification_codes: '楠岃瘉鐮?,
  }
  return labelMap[tableName] || tableName.replace(/_/g, ' ') || '数据表'description', 'bio', 'result_data', 'tables', 'charts', 'codebook', 'configuration', 'script_r', 'script_python'].includes(name)
}

function renderCell(value: any) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function fillEditBuffer(row: Record<string, any>) {
  Object.keys(editBuffer).forEach((key) => delete editBuffer[key])
  editableColumns.value.forEach((column: AdminTableColumn) => {
    const value = row[column.name]
    editBuffer[column.name] = value === null || value === undefined
      ? ''
      : typeof value === 'object'
        ? JSON.stringify(value, null, 2)
        : String(value)
  })
}

function normalizeValue(column: AdminTableColumn, value: string) {
  if (value === '') return null
  if (column.type.toUpperCase().includes('JSON')) {
    try {
      return JSON.parse(value)
    } catch {
      return value
    }
  }
  if (column.type.toUpperCase().includes('BOOLEAN')) {
    return ['true', '1', 'yes', 'on'].includes(value.trim().toLowerCase())
  }
  if (column.type.toUpperCase().includes('INTEGER')) {
    const parsed = Number.parseInt(value, 10)
    return Number.isNaN(parsed) ? value : parsed
  }
  if (column.type.toUpperCase().includes('NUMERIC') || column.type.toUpperCase().includes('FLOAT')) {
    const parsed = Number.parseFloat(value)
    return Number.isNaN(parsed) ? value : parsed
  }
  return value
}

async function loadCurrentTable() {
  try {
    const routeTable = typeof route.params.tableName === 'string' ? route.params.tableName : ''
    if (!routeTable) {
      errorMessage.value = '璇峰厛浠庡乏渚т富瀵艰埅閫夋嫨涓€涓暟鎹〃銆?
      currentTable.value = null
      return
    }
    errorMessage.value = ''
    selectedRow.value = null
    selectedRowId.value = ''
    currentTable.value = await getAdminTableRows(routeTable)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || error.message || '鏁版嵁琛ㄥ垪琛ㄥ姞杞藉け璐?
    currentTable.value = null
  } finally {
    isLoadingTables.value = false
  }
}

function selectRow(row: Record<string, any>) {
  selectedRow.value = row
  selectedRowId.value = String(row[currentTable.value?.primary_key || 'id'])
  fillEditBuffer(row)
}

async function reloadCurrentTable() {
  const routeTable = typeof route.params.tableName === 'string' ? route.params.tableName : ''
  if (!routeTable) return
  currentTable.value = await getAdminTableRows(routeTable)
  if (selectedRowId.value) {
    const row = currentTable.value.rows.find((item) => String(item[currentTable.value?.primary_key || 'id']) === selectedRowId.value)
    if (row) {
      selectRow(row)
    } else {
      selectedRow.value = null
      selectedRowId.value = ''
    }
  }
}

async function saveRow() {
  if (!currentTable.value || !selectedRowId.value) return
  isSaving.value = true
  try {
    const payload = Object.fromEntries(
      editableColumns.value.map((column) => [column.name, normalizeValue(column, editBuffer[column.name] ?? '')])
    )
    const result = await updateAdminTableRow(currentTable.value.table_name, selectedRowId.value, payload)
    const index = currentTable.value.rows.findIndex((row) => String(row[currentTable.value?.primary_key || 'id']) === selectedRowId.value)
    if (index >= 0) {
      currentTable.value.rows[index] = result.row
      selectRow(result.row)
    }
    notificationStore.success('鏁版嵁琛屽凡鏇存柊', `${currentTableLabel.value} 涓殑璁板綍宸蹭繚瀛樸€俙)
  } catch (error: any) {
    notificationStore.error('淇濆瓨澶辫触', error.response?.data?.detail || error.message || '璇风◢鍚庨噸璇?)
  } finally {
    isSaving.value = false
  }
}

async function removeRow() {
  if (!currentTable.value || !selectedRowId.value) return
  try {
    await deleteAdminTableRow(currentTable.value.table_name, selectedRowId.value)
    currentTable.value.rows = currentTable.value.rows.filter(
      (row) => String(row[currentTable.value?.primary_key || 'id']) !== selectedRowId.value,
    )
    currentTable.value.total -= 1
    selectedRow.value = null
    selectedRowId.value = ''
    notificationStore.success('鏁版嵁琛屽凡鍒犻櫎', '褰撳墠璁板綍宸蹭粠鏁版嵁搴撶Щ闄ゃ€?)
  } catch (error: any) {
    notificationStore.error('鍒犻櫎澶辫触', error.response?.data?.detail || error.message || '璇风◢鍚庨噸璇?)
  }
}

watch(
  () => route.params.tableName,
  async (nextValue) => {
    isLoadingTables.value = true
    if (typeof nextValue === 'string' && nextValue) {
      await loadCurrentTable()
      return
    }
    currentTable.value = null
    selectedRow.value = null
    selectedRowId.value = ''
    errorMessage.value = '璇峰厛浠庡乏渚т富瀵艰埅閫夋嫨涓€涓暟鎹〃銆?
    isLoadingTables.value = false
  },
)

onMounted(async () => {
  await loadCurrentTable()
})
</script>

