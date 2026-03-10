<template>
  <div class="space-y-4 animate-fade-in">
    <section class="grid gap-3 xl:grid-cols-[248px_minmax(0,1fr)]">
      <aside class="space-y-3">
        <div class="panel-card p-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-[13px] font-semibold text-slate-900">模块库</h2>
              <p class="mt-1 text-[10px] leading-5 text-slate-500">拖入或点击创建节点</p>
            </div>
            <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-600">{{ totalModules }} 个模块</span>
          </div>

          <div class="mt-3 grid gap-1">
            <label class="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">当前项目</label>
            <select v-model="selectedProjectId" class="tool-input h-9" title="选择项目">
              <option value="">选择项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
            </select>
          </div>

          <div class="module-library-scroll mt-3 space-y-1.5">
            <article v-for="group in moduleGroups" :key="group.id" class="panel-subtle p-2">
              <div class="flex items-center justify-between gap-2">
                <div class="flex min-w-0 items-center gap-2">
                  <span class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg" :class="group.iconClass" v-html="group.icon"></span>
                  <div class="min-w-0">
                    <h3 class="truncate text-[11px] font-semibold text-slate-900">{{ group.label }}</h3>
                    <p class="mt-0.5 line-clamp-1 text-[10px] leading-4 text-slate-500">{{ group.description }}</p>
                  </div>
                </div>
                <span class="rounded-full bg-white px-2 py-1 text-[9px] font-semibold text-slate-500">{{ group.modules.length }}</span>
              </div>

              <div class="mt-1.5 space-y-1">
                <button
                  v-for="module in group.modules"
                  :key="module.id"
                  draggable="true"
                  :class="['module-library-card', draggingLibraryModuleId === module.id && 'is-dragging']"
                  type="button"
                  :title="module.description"
                  @dragstart="onLibraryDragStart(module)"
                  @click="addNodeFromLibrary(module)"
                >
                  <div class="flex items-center gap-2.5">
                    <span class="module-library-card__icon" :class="group.iconClass" v-html="group.icon"></span>
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-[12px] font-semibold leading-[1.2] text-slate-800">{{ module.label }}</p>
                      <p class="mt-0.5 truncate text-[10px] leading-[1.2] text-slate-500">{{ module.description }}</p>
                    </div>
                  </div>
                </button>
              </div>
            </article>
          </div>
        </div>

        <div class="panel-card p-2.5">
          <div class="grid grid-cols-4 gap-2 text-center text-[10px] text-slate-500">
            <div class="rounded-xl bg-slate-50 px-2 py-2">
              <div class="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white text-slate-600">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11 4 16"/><path d="m4 16 5 5"/><path d="M15 13 20 8"/><path d="m20 8-5-5"/></svg>
              </div>
              拖拽
            </div>
            <div class="rounded-xl bg-slate-50 px-2 py-2">
              <div class="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white text-slate-600">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3"/></svg>
              </div>
              连线
            </div>
            <div class="rounded-xl bg-slate-50 px-2 py-2">
              <div class="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white text-slate-600">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="m7 5 11 7-11 7V5Z"/></svg>
              </div>
              运行
            </div>
            <div class="rounded-xl bg-slate-50 px-2 py-2">
              <div class="mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-lg bg-white text-slate-600">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3H5a2 2 0 0 0-2 2v7"/><path d="M19 21h-7a2 2 0 0 1-2-2v-7"/></svg>
              </div>
              面板
            </div>
          </div>
        </div>
      </aside>

      <main class="space-y-2">
        <section class="panel-card overflow-hidden p-0">
	          <div class="flex items-center justify-between gap-3 border-b border-slate-200/80 px-3 py-2.5">
	            <div class="flex min-w-0 items-center gap-3">
	              <div class="min-w-0">
	                <div v-if="isEditingWorkflowName" class="flex items-center gap-2">
	                  <input
	                    ref="workflowNameInputRef"
	                    v-model="workflowNameDraft"
	                    class="tool-input h-9 w-[240px] max-w-full"
	                    placeholder="Untitled"
	                    @blur="finishEditingWorkflowName"
	                    @keydown.enter.prevent="finishEditingWorkflowName"
	                    @keydown.esc.prevent="cancelEditingWorkflowName"
	                  />
	                  <button class="tool-btn px-2.5 py-1.5 text-[11px] font-semibold" type="button" @click="finishEditingWorkflowName">确定</button>
	                </div>
	                <button
	                  v-else
	                  class="group inline-flex max-w-full items-center gap-2 rounded-lg px-2 py-1 text-left transition hover:bg-white"
	                  type="button"
	                  title="点击重命名"
	                  @click="startEditingWorkflowName"
	                >
	                  <span class="truncate text-sm font-semibold text-slate-900">{{ workflowName || 'Untitled' }}</span>
	                  <svg class="h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
	                </button>
	              </div>
	            </div>

            <div class="flex flex-wrap items-center gap-2">
              <div class="panel-subtle inline-flex items-center gap-1.5 px-1.5 py-1.5">
                <button class="canvas-zoom-btn" type="button" title="缩小" @click="stepZoom(-0.1)">-</button>
                <input
                  v-model.number="zoomPercent"
                  class="h-1.5 w-24 accent-emerald-600"
                  type="range"
                  min="50"
                  max="160"
                  step="5"
                  @input="setZoom((zoomPercent || 100) / 100)"
                />
                <button class="canvas-zoom-btn" type="button" title="放大" @click="stepZoom(0.1)">+</button>
                <button class="rounded-md px-2 py-1 text-[11px] font-semibold text-slate-500 transition hover:bg-white hover:text-slate-700" type="button" title="重置缩放" @click="resetZoom">
                  {{ Math.round(canvasScale * 100) }}%
                </button>
              </div>
              <div class="flex flex-wrap gap-1.5 text-xs">
              <span class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600" title="节点数">
                <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="9" y="14" width="6" height="6" rx="1"/></svg>
                {{ canvasNodes.length }}
              </span>
              <span class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 font-medium text-emerald-700" title="连线数">
                <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3"/></svg>
                {{ connections.length }}
              </span>
              </div>
            </div>
          </div>

          <div class="node-canvas-shell">
            <div
              ref="canvasRef"
              :class="['node-canvas', panState && 'is-panning']"
              @mousedown="handleCanvasMouseDown"
              @dragover.prevent
              @drop.prevent="onCanvasDrop"
              @mousemove="handleCanvasMouseMove"
              @wheel="handleCanvasWheel"
              @contextmenu.prevent="handleCanvasContextMenu"
            >
            <div class="canvas-surface" :style="{ transform: `scale(${canvasScale})`, width: `${canvasSurfaceWidth}px`, height: `${canvasSurfaceHeight}px` }">
              <svg class="absolute inset-0 h-full w-full overflow-visible">
                <g v-for="connection in connectionPaths" :key="connection.id">
                  <path
                    :d="connection.d"
                    class="connection-hit-path"
                    stroke-linecap="round"
                    @click.stop="selectConnection(connection.id)"
                  />
                  <path
                    :d="connection.d"
                    class="fill-none stroke-[3] pointer-events-none"
                    :class="connection.isSelected ? 'stroke-emerald-500' : 'stroke-slate-300'"
                    stroke-linecap="round"
                  />
                </g>
                <path
                  v-if="temporaryConnectionPath"
                  :d="temporaryConnectionPath"
                  class="pointer-events-none fill-none stroke-[3] stroke-emerald-400/70"
                  stroke-linecap="round"
                  stroke-dasharray="8 8"
                />
                <rect
                  v-if="selectionBounds"
                  :x="selectionBounds.x"
                  :y="selectionBounds.y"
                  :width="selectionBounds.width"
                  :height="selectionBounds.height"
                  class="selection-marquee"
                  rx="18"
                />
              </svg>

              <div
                v-for="node in canvasNodes"
                :key="node.id"
                :style="{ transform: `translate(${node.x}px, ${node.y}px)` }"
                :class="[
                  'node-card absolute',
                  selectedNodeIds.includes(node.id) && 'is-selected',
                  isNodeRunning(node.id) && 'is-running',
                ]"
                @click="selectNode(node.id, $event)"
              >
                <button
                  class="node-port node-port-input"
                  :class="inputPortStateClass(node.id)"
                  type="button"
                  :title="inputPortTitle(node.id)"
                  @click.stop="completeConnection(node.id)"
                >
                  <span></span>
                </button>

                <div :class="['rounded-[10px] border bg-white shadow-[0_12px_28px_-24px_rgba(15,23,42,0.28)]', nodeExecutionCardClass(node.id)]">
	                  <div
	                    class="flex cursor-grab items-center justify-between gap-2.5 rounded-t-[10px] border-b border-slate-100 bg-white px-2.5 py-1.5 active:cursor-grabbing"
	                    @mousedown.stop="startNodeDrag($event, node.id)"
	                  >
	                    <div class="space-y-0.5">
	                      <div class="flex flex-nowrap items-center gap-1.5 whitespace-nowrap">
	                        <span class="shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase leading-none tracking-[0.16em]" :class="stageTagClass(node.stageId)">
	                          {{ shortStageLabel(node.stageId) }}
	                        </span>
	                        <span class="shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-semibold leading-none" :class="nodeStatusClass(node.id)">
	                          {{ nodeStatusLabel(node.id) }}
	                        </span>
	                        <span class="shrink-0 whitespace-nowrap text-[10px] font-medium leading-none text-slate-400">#{{ node.order }}</span>
	                      </div>
	                      <h3 class="text-sm font-semibold text-slate-900">{{ node.label }}</h3>
	                    </div>
	                    <div class="flex flex-nowrap items-center gap-1.5">
	                      <div v-if="nodeLastRunTime(node.id)" class="text-right">
	                        <p class="whitespace-nowrap text-[10px] font-medium leading-none text-slate-400 tabular-nums">{{ nodeLastRunTime(node.id) }}</p>
	                      </div>
	                      <button class="rounded-full p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-500" type="button" title="删除节点" @click.stop="removeNode(node.id)">
	                        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
	                      </button>
	                    </div>
	                  </div>

                  <div class="space-y-1.5 px-2.5 py-2">
                    <div class="flex flex-wrap gap-1">
	                      <span class="inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-600" :title="node.description">
	                        <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h1v4"/></svg>
	                        {{ nodeStatusLabel(node.id) }}
	                      </span>
                      <span v-for="item in summarizeNode(node).slice(0, 2)" :key="item" class="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-600">
                        {{ item }}
                      </span>
                    </div>

                    <p class="line-clamp-2 text-[11px] leading-4.5 text-slate-400">{{ nodeStatusMessage(node.id) }}</p>

                    <div v-if="nodePreviewItems(node.id).length" class="rounded-[8px] border border-slate-200 bg-white px-2 py-1.5">
                      <div class="mb-1 flex items-center justify-between gap-2">
                        <p class="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">预览</p>
                        <span class="text-[10px] text-slate-400">{{ nodePreview(node.id)?.title }}</span>
                      </div>
                      <div class="space-y-1">
                        <div v-for="item in nodePreviewItems(node.id)" :key="`${node.id}-${item.label}`" class="flex items-center justify-between gap-2 text-[11px]">
                          <span class="text-slate-500">{{ item.label }}</span>
                          <span class="rounded-full px-2 py-1 font-semibold" :class="previewToneClass(item.tone)">{{ item.value }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="flex items-center justify-between gap-2 pt-0">
                      <button
                        class="node-tool-btn"
                        type="button"
                        data-tooltip="设置参数"
                        aria-label="打开参数设置"
                        @click.stop="openNodeSettings(node.id)"
                      >
                        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3"/><path d="M12 19v3"/><path d="m4.93 4.93 2.12 2.12"/><path d="m16.95 16.95 2.12 2.12"/><path d="M2 12h3"/><path d="M19 12h3"/><path d="m4.93 19.07 2.12-2.12"/><path d="m16.95 7.05 2.12-2.12"/></svg>
                      </button>

                      <div class="flex items-center gap-2">
                        <button
                          :class="['node-tool-btn is-primary', isNodeRunning(node.id) && 'is-busy']"
                          type="button"
                          :data-tooltip="nodeRunActionTooltip(node.id)"
                          aria-label="运行当前节点"
                          @click.stop="runNodeOnly(node)"
                        >
                          <svg
                            v-if="isNodeRunning(node.id)"
                            class="h-3.5 w-3.5 animate-spin"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                          >
                            <circle cx="12" cy="12" r="9" class="opacity-25"></circle>
                            <path d="M21 12a9 9 0 0 0-9-9" stroke-linecap="round"></path>
                          </svg>
                          <svg v-else class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="m7 5 11 7-11 7V5Z"/></svg>
                        </button>

                        <button
                          :class="['node-tool-btn', hasNodeRunResult(node.id) ? 'is-result-ready' : 'is-muted']"
                          type="button"
                          data-tooltip="查看结果"
                          aria-label="查看运行结果"
                          @click.stop="openNodeResults(node.id)"
                        >
                          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <button
                  class="node-port node-port-output"
                  type="button"
                  :class="pendingConnectionFrom === node.id && 'is-armed'"
                  :title="pendingConnectionFrom === node.id ? '正在等待连接目标' : '点击开始连线'"
                  @click.stop="beginConnection(node.id)"
                >
                  <span></span>
                </button>
              </div>
            </div>

            <div v-if="!canvasNodes.length" class="absolute inset-0 flex items-center justify-center">
              <div class="max-w-md rounded-[12px] border border-dashed border-slate-300 bg-white/78 px-7 py-8 text-center backdrop-blur-sm">
                <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-[10px] border border-slate-200 bg-white text-slate-300">
                  <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
                </div>
                <h3 class="mt-4 text-base font-semibold text-slate-900">空白画布</h3>
                <p class="mt-2 text-sm leading-6 text-slate-500">
                  从左侧拖入第一个模块，或直接注入模板。
                </p>
                <div class="mt-5 grid gap-3 text-left sm:grid-cols-2">
                  <button
                    v-for="template in canvasTemplates"
                    :key="template.id"
                    class="rounded-[12px] border border-slate-200 bg-white px-4 py-4 shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_16px_30px_-24px_rgba(16,185,129,0.55)]"
                    type="button"
                    @click="injectTemplate(template.id)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="template.accentClass">
                        一键注入
                      </span>
                      <svg class="h-4 w-4 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                    </div>
                    <h4 class="mt-3 text-sm font-semibold text-slate-900">{{ template.label }}</h4>
                    <p class="mt-1 text-xs leading-5 text-slate-500">{{ template.description }}</p>
                  </button>
                </div>
              </div>
	            </div>
	            </div>

	            <div class="canvas-overlay-top">
	              <div class="canvas-dock">
                <button class="canvas-dock-btn" type="button" title="清空画布" data-tooltip="清空画布" @click="resetCanvas">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-square-icon lucide-square"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>
                </button>
                <button
                  v-if="selectedNodeIds.length"
                  class="canvas-dock-btn"
                  type="button"
                  title="删除所选"
                  data-tooltip="删除所选"
                  @click="deleteSelectedNodes"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash2-icon lucide-trash-2"><path d="M10 11v6"/><path d="M14 11v6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
                <button
                  v-if="hasMultiSelection"
                  class="canvas-dock-btn"
                  type="button"
                  title="左对齐"
                  data-tooltip="左对齐"
                  @click="alignSelectedNodes('left')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-align-start-vertical-icon lucide-align-start-vertical"><rect width="9" height="6" x="6" y="14" rx="2"/><rect width="16" height="6" x="6" y="4" rx="2"/><path d="M2 2v20"/></svg>
                </button>
                <button
                  v-if="hasMultiSelection"
                  class="canvas-dock-btn"
                  type="button"
                  title="横向分布"
                  data-tooltip="横向分布"
                  @click="distributeSelectedNodes('horizontal')"
                >
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-align-horizontal-space-around-icon lucide-align-horizontal-space-around"><rect width="6" height="10" x="9" y="7" rx="2"/><path d="M4 22V2"/><path d="M20 22V2"/></svg>
                </button>
                <button
                  v-if="hasMultiSelection"
                  class="canvas-dock-btn"
                  type="button"
                  title="纵向分布"
                  data-tooltip="纵向分布"
                  @click="distributeSelectedNodes('vertical')"
                >
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-align-vertical-space-around-icon lucide-align-vertical-space-around"><rect width="10" height="6" x="7" y="9" rx="2"/><path d="M22 20H2"/><path d="M22 4H2"/></svg>
                </button>
                <button class="canvas-dock-btn" type="button" :title="isTemplatePickerOpen ? '收起模板' : '插入模板'" :data-tooltip="isTemplatePickerOpen ? '收起模板' : '插入模板'" @click="isTemplatePickerOpen = !isTemplatePickerOpen">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-template-icon lucide-layout-template"><rect width="18" height="7" x="3" y="3" rx="1"/><rect width="9" height="7" x="3" y="14" rx="1"/><rect width="5" height="7" x="16" y="14" rx="1"/></svg>
                </button>
	                <button class="canvas-dock-btn is-primary" type="button" title="一键整理" data-tooltip="一键整理" @click="autoArrangeNodes">
	                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shelving-unit-icon lucide-shelving-unit"><path d="M12 12V9a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/><path d="M16 20v-3a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1v3"/><path d="M20 22V2"/><path d="M4 12h16"/><path d="M4 20h16"/><path d="M4 2v20"/><path d="M4 4h16"/></svg>
	                </button>
	                <button class="canvas-dock-btn" type="button" title="重置视角" data-tooltip="重置视角" @click="tidyCanvas">
	                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-binoculars-icon lucide-binoculars"><path d="M10 10h4"/><path d="M19 7V4a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1v3"/><path d="M20 21a2 2 0 0 0 2-2v-3.851c0-1.39-2-2.962-2-4.829V8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v11a2 2 0 0 0 2 2z"/><path d="M 22 16 L 2 16"/><path d="M4 21a2 2 0 0 1-2-2v-3.851c0-1.39 2-2.962 2-4.829V8a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v11a2 2 0 0 1-2 2z"/><path d="M9 7V4a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1v3"/></svg>
	                </button>
                <button class="canvas-dock-btn" type="button" title="撤销操作 (Ctrl+Z)" data-tooltip="撤销操作" :disabled="!undoStack.length" @click="undo">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-rotate-ccw-icon lucide-rotate-ccw"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                </button>
                <button class="canvas-dock-btn" type="button" :title="selectedConnectionId ? '删除连线' : '取消连线'" :data-tooltip="selectedConnectionId ? '删除连线' : '取消连线'" @click="cancelPendingConnection">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-scissors-icon lucide-scissors"><circle cx="6" cy="6" r="3"/><path d="M8.12 8.12 12 12"/><path d="M20 4 8.12 15.88"/><circle cx="6" cy="18" r="3"/><path d="M14.8 14.8 20 20"/></svg>
                </button>
                <button class="canvas-dock-btn" type="button" title="保存流程" data-tooltip="保存流程" :disabled="isSavingWorkflow || !selectedProjectId" @click="saveWorkflowToBackend">
                  <svg v-if="isSavingWorkflow" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save-icon lucide-save"><path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/></svg>
                </button>
              </div>
            </div>

            <div v-if="isTemplatePickerOpen" class="canvas-overlay-bottom">
              <div class="template-picker">
                <div class="grid gap-3 md:grid-cols-2">
                  <button
                    v-for="template in canvasTemplates"
                    :key="template.id"
                    class="rounded-[12px] border border-slate-200 bg-white px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_16px_30px_-24px_rgba(16,185,129,0.55)]"
                    type="button"
                    @click="injectTemplate(template.id)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="template.accentClass">
                        {{ template.label }}
                      </span>
                      <span class="text-[11px] font-medium text-slate-400">{{ template.nodes.length }} 节点</span>
                    </div>
                    <p class="mt-3 text-xs leading-5 text-slate-500">{{ template.description }}</p>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="panel-card p-3">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="flex min-w-0 flex-1 flex-wrap gap-2">
              <span v-for="item in graphSummary.slice(0, 3)" :key="item" class="rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-medium text-slate-600">
                {{ item }}
              </span>
            </div>
            <button class="tool-btn px-3 py-1.5 text-[11px] font-semibold" type="button" @click="clearLogs">
              清空日志
            </button>
          </div>
          <div class="mt-3 flex gap-2 overflow-x-auto pb-1">
            <div v-for="entry in logs.slice(0, 6)" :key="entry.id" class="min-w-[220px] rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
              <div class="flex items-center justify-between gap-3">
                <span class="text-[10px] font-semibold tracking-[0.12em] text-slate-400">{{ entry.time }}</span>
                <span class="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{{ entry.kind }}</span>
              </div>
              <p class="mt-1.5 line-clamp-2 text-[11px] leading-5 text-slate-600">{{ entry.message }}</p>
            </div>
          </div>
        </section>
      </main>


    </section>

    <div v-if="isSettingsDialogOpen && selectedNode" class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/35 p-6 backdrop-blur-sm" @click.self="closeNodeDialogs">
      <div class="max-h-[88vh] w-full max-w-3xl overflow-y-auto rounded-[14px] border border-white/60 bg-white shadow-[0_36px_120px_-70px_rgba(15,23,42,0.45)]">
        <div class="sticky top-0 z-10 flex items-center justify-between gap-2 border-b border-slate-200 bg-white/90 px-3.5 py-2.5 backdrop-blur">
          <div class="flex min-w-0 items-center gap-2">
            <p class="shrink-0 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-600">Settings</p>
            <h3 class="truncate text-[15px] font-semibold text-slate-900">{{ selectedNode.label }}</h3>
          </div>
          <button class="rounded-full p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700" type="button" @click="isSettingsDialogOpen = false">
            <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div class="settings-modal-body space-y-2 p-3">
          <div class="settings-card rounded-[10px] border border-slate-200 bg-white p-2">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <h3 class="truncate text-[15px] font-semibold text-slate-900">{{ selectedNode.label }}</h3>
                <p v-if="selectedNodeStatus" class="mt-0.5 line-clamp-1 text-[11px] leading-4 text-slate-400">{{ selectedNodeStatus.message }}</p>
              </div>
              <div class="flex items-center gap-2 pl-2">
                <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="nodeStatusClass(selectedNode.id)">
                  {{ selectedNodeStatus?.label }}
                </span>
                <button
                  :class="['node-run-inline-btn', isNodeRunning(selectedNode.id) && 'is-busy']"
                  type="button"
                  :data-tooltip="nodeRunActionTooltip(selectedNode.id)"
                  aria-label="运行当前节点"
                  @click="runNodeOnly(selectedNode)"
                >
                  <svg
                    v-if="isNodeRunning(selectedNode.id)"
                    class="h-3.5 w-3.5 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="9" class="opacity-25"></circle>
                    <path d="M21 12a9 9 0 0 0-9-9" stroke-linecap="round"></path>
                  </svg>
                  <svg v-else class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="m7 5 11 7-11 7V5Z"/></svg>
                  <span>{{ isNodeRunning(selectedNode.id) ? '运行中' : '运行' }}</span>
                </button>
              </div>
            </div>
          </div>

          <div class="settings-card rounded-[10px] border border-slate-200 bg-white p-2">
            <div class="flex items-center justify-between gap-2">
              <h4 class="text-sm font-semibold text-slate-900">输入</h4>
              <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-500">
                {{
                  selectedNodeIncomingNodes.length
                    ? `${selectedNodeIncomingNodes.length} 个上游`
                    : (showInputDatasetPicker ? '流程起点' : '需上游输入')
                }}
              </span>
            </div>

            <div v-if="selectedNodeIncomingNodes.length" class="mt-1.5 flex flex-wrap gap-1">
                <span
                  v-for="upstream in selectedNodeIncomingNodes"
                  :key="upstream.id"
                  class="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-slate-700 ring-1 ring-slate-200"
                >
                  {{ upstream.label }}
                </span>
            </div>

            <div v-else-if="showInputDatasetPicker" class="mt-1.5 space-y-1.5">
              <div class="grid gap-1 sm:grid-cols-[84px_minmax(0,1fr)] sm:items-center">
                <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">输入数据集</label>
                <select
                  v-model="selectedDatasetId"
                  class="tool-input"
                  :disabled="loadingDatasets"
                >
                  <option value="">{{ loadingDatasets ? '加载数据集...' : '选择数据集' }}</option>
                  <option v-for="dataset in datasetOptions" :key="dataset.id" :value="dataset.id">{{ dataset.name }}</option>
                </select>
              </div>

              <div v-if="selectedDatasetOption" class="grid gap-1 sm:grid-cols-2">
                <div class="rounded-[8px] border border-slate-200 bg-white px-2 py-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">当前数据源</p>
                  <p class="mt-0.5 truncate text-sm font-semibold text-slate-900">{{ selectedDatasetOption.name }}</p>
                </div>
                <div class="rounded-[8px] border border-slate-200 bg-white px-2 py-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">数据规模</p>
                  <p class="mt-0.5 text-sm font-semibold text-slate-900">{{ datasetShapeText(datasetSummary) }}</p>
                </div>
              </div>
            </div>

            <div v-else class="mt-1.5 rounded-[10px] border border-slate-200 bg-white px-3 py-2.5 text-[11px] leading-5 text-slate-500">
              该节点不能作为流程起点，请先连接上游模型节点（Logistic 或 Cox）后再运行。
            </div>
          </div>

          <div v-if="selectedNode.moduleId === 'field-mapping'" class="space-y-1.5">
            <div class="grid gap-1.5 sm:grid-cols-2">
              <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
                <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">ID 字段</label>
                <select class="tool-input" :value="selectedNode.values.idField || ''" @change="updateNodeValue(selectedNode.id, 'idField', ($event.target as HTMLSelectElement).value)">
                  <option value="">选择字段</option>
                  <option v-for="column in datasetColumnNames" :key="`modal-id-${column}`" :value="column">{{ column }}</option>
                </select>
              </div>
              <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
                <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">结局字段</label>
                <select class="tool-input" :value="selectedNode.values.outcomeField || ''" @change="updateNodeValue(selectedNode.id, 'outcomeField', ($event.target as HTMLSelectElement).value)">
                  <option value="">选择字段</option>
                  <option v-for="column in datasetColumnNames" :key="`modal-outcome-${column}`" :value="column">{{ column }}</option>
                </select>
              </div>
            </div>

            <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
              <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">时间字段</label>
              <select class="tool-input" :value="selectedNode.values.timeField || ''" @change="updateNodeValue(selectedNode.id, 'timeField', ($event.target as HTMLSelectElement).value)">
                <option value="">选择字段</option>
                <option v-for="column in datasetColumnNames" :key="`modal-time-${column}`" :value="column">{{ column }}</option>
              </select>
            </div>

            <div class="settings-card rounded-[10px] border border-slate-200 bg-white p-2">
              <div class="flex items-center justify-between gap-2">
                <div class="min-w-0">
                  <h4 class="text-sm font-semibold text-slate-900">候选变量字段</h4>
                  <p class="mt-0.5 text-[11px] leading-4 text-slate-400">后续建模的候选变量。</p>
                </div>
                <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-500">{{ selectedFieldMappingPredictors.length }} 个已选</span>
              </div>
              <div class="mt-1 flex flex-wrap gap-1">
                <button class="tool-btn px-2.5 py-1 text-[11px] font-semibold" type="button" @click="selectAllFieldMappingPredictors()">全选</button>
                <button class="tool-btn px-2.5 py-1 text-[11px] font-semibold" type="button" @click="clearFieldMappingPredictors()">清空</button>
              </div>
              <div v-if="fieldMappingCandidateColumns.length" class="mt-1.5 grid max-h-56 gap-1 overflow-y-auto pr-1 sm:grid-cols-2">
                <button
                  v-for="column in fieldMappingCandidateColumns"
                  :key="`modal-predictor-${column}`"
                  type="button"
                  :class="[
                    'rounded-xl border px-2.5 py-1 text-left text-[11px] font-medium transition',
                    selectedFieldMappingPredictors.includes(column)
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                  ]"
                  @click="toggleFieldMappingPredictor(column)"
                >
                  {{ column }}
                </button>
              </div>
            </div>
          </div>

          <div v-else-if="selectedNode.moduleId === 'split'" class="grid gap-1.5 sm:grid-cols-2">
            <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
              <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">划分比例</label>
              <select
                class="tool-input"
                :value="selectedNode.values.ratio || '7:3'"
                @change="updateNodeValue(selectedNode.id, 'ratio', ($event.target as HTMLSelectElement).value)"
              >
                <option value="7:3">7:3</option>
                <option value="8:2">8:2</option>
                <option value="6:2:2">6:2:2</option>
              </select>
            </div>
            <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
              <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">抽样方式</label>
              <select
                class="tool-input"
                :value="selectedNode.values.sampling || '随机划分'"
                @change="updateSplitSamplingValue(selectedNode.id, ($event.target as HTMLSelectElement).value)"
              >
                <option value="随机划分">随机划分</option>
                <option value="分层抽样">分层抽样</option>
                <option value="时间切分">时间切分</option>
              </select>
            </div>
            <div class="grid gap-1 sm:grid-cols-[72px_minmax(0,1fr)] sm:items-center">
              <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">随机种子</label>
              <input
                class="tool-input"
                :value="selectedNode.values.seed || '2026'"
                @input="updateNodeValue(selectedNode.id, 'seed', ($event.target as HTMLInputElement).value)"
              />
            </div>
            <div v-if="selectedNode.values.sampling === '分层抽样'" class="space-y-1">
              <div class="flex items-center justify-between gap-2">
                <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">分层变量</label>
                <button
                  v-if="splitSuggestedStratifyField(selectedNode) && splitSuggestedStratifyField(selectedNode) !== selectedNode.values.stratifyField"
                  class="text-[11px] font-semibold text-emerald-600"
                  type="button"
                  @click="updateNodeValue(selectedNode.id, 'stratifyField', splitSuggestedStratifyField(selectedNode))"
                >
                  用推荐项
                </button>
              </div>
              <select
                class="tool-input"
                :value="selectedNode.values.stratifyField || ''"
                @change="updateNodeValue(selectedNode.id, 'stratifyField', ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ splitSelectableColumns.length ? '选择分层变量' : '暂无可用字段' }}</option>
                <option v-for="column in splitSelectableColumns" :key="`split-stratify-${column}`" :value="column">{{ column }}</option>
              </select>
            </div>
            <div v-if="selectedNode.values.sampling === '时间切分'" class="space-y-1">
              <div class="flex items-center justify-between gap-2">
                <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">时间切分字段</label>
                <button
                  v-if="splitSuggestedTimeField(selectedNode) && splitSuggestedTimeField(selectedNode) !== selectedNode.values.timeSplitField"
                  class="text-[11px] font-semibold text-emerald-600"
                  type="button"
                  @click="updateNodeValue(selectedNode.id, 'timeSplitField', splitSuggestedTimeField(selectedNode))"
                >
                  用推荐项
                </button>
              </div>
              <select
                class="tool-input"
                :value="selectedNode.values.timeSplitField || ''"
                @change="updateNodeValue(selectedNode.id, 'timeSplitField', ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ splitSelectableColumns.length ? '选择时间字段' : '暂无可用字段' }}</option>
                <option v-for="column in splitSelectableColumns" :key="`split-time-${column}`" :value="column">{{ column }}</option>
              </select>
            </div>
            <div
              v-if="selectedNode.values.sampling !== '随机划分'"
              class="sm:col-span-2 rounded-[8px] border border-slate-200 bg-white px-2.5 py-2 text-[11px] leading-4.5 text-slate-500"
            >
              {{ splitSelectionHint(selectedNode) }}
            </div>
          </div>

          <div v-else class="grid gap-1.5 md:grid-cols-2">
            <div
              v-for="field in selectedNodeSettingFields"
              :key="field.key"
              :class="[
                'grid gap-1 sm:grid-cols-[84px_minmax(0,1fr)] sm:items-center',
                selectedNodeSettingFields.length === 1 && 'md:col-span-2',
              ]"
            >
              <label class="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">{{ field.label }}</label>
              <select
                v-if="field.type === 'select'"
                class="tool-input"
                :value="selectedNode.values[field.key]"
                @change="updateNodeValue(selectedNode.id, field.key, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="option in selectOptionsForField(field)" :key="option" :value="option">{{ option }}</option>
              </select>
              <select
                v-else-if="isDatasetColumnField(selectedNode.moduleId, field.key)"
                class="tool-input"
                :value="selectedNode.values[field.key] || ''"
                @change="updateNodeValue(selectedNode.id, field.key, ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ datasetColumnFieldEmptyLabel(selectedNode.moduleId, field.key) }}</option>
                <option v-for="column in datasetColumnNames" :key="`col-${selectedNode.moduleId}-${field.key}-${column}`" :value="column">{{ column }}</option>
              </select>
              <input
                v-else
                class="tool-input"
                :value="selectedNode.values[field.key]"
                :placeholder="selectedNode.moduleId === 'vif' && field.key === 'cutoff' ? '建议 5 或 10' : ''"
                @input="updateNodeValue(selectedNode.id, field.key, ($event.target as HTMLInputElement).value)"
              />
            </div>
          </div>

          <div
            v-if="showStandaloneModelPredictorPicker"
            class="settings-card rounded-[10px] border border-slate-200 bg-white p-2"
          >
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <h4 class="text-sm font-semibold text-slate-900">自变量选择</h4>
                <p class="mt-0.5 text-[11px] leading-4 text-slate-400">可选：为空则默认使用除结局/时间等以外的全部字段。</p>
              </div>
              <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-500">{{ selectedModelPredictors.length }} 个已选</span>
            </div>
            <div class="mt-1 flex flex-wrap gap-1">
              <button class="tool-btn px-2.5 py-1 text-[11px] font-semibold" type="button" :disabled="!modelPredictorCandidateColumns.length" @click="selectAllModelPredictors()">
                全选
              </button>
              <button class="tool-btn px-2.5 py-1 text-[11px] font-semibold" type="button" @click="clearModelPredictors()">
                清空
              </button>
            </div>
            <div v-if="modelPredictorCandidateColumns.length" class="mt-1.5 grid max-h-56 gap-1 overflow-y-auto pr-1 sm:grid-cols-2">
              <button
                v-for="column in modelPredictorCandidateColumns"
                :key="`model-predictor-${selectedNode.id}-${column}`"
                type="button"
                :class="[
                  'rounded-xl border px-2.5 py-1 text-left text-[11px] font-medium transition',
                  selectedModelPredictors.includes(column)
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                ]"
                @click="toggleModelPredictor(column)"
              >
                {{ column }}
              </button>
            </div>
            <div v-else class="mt-1 rounded-[8px] border border-slate-200 bg-white px-2 py-1.5 text-[11px] leading-4.5 text-slate-500">
              暂无可选字段：请先选择数据集，并设置结局/时间字段。
            </div>
          </div>

          <div v-if="selectedNode.moduleId === 'split'" class="settings-card rounded-[10px] border border-slate-200 bg-white p-2">
            <div class="flex items-center justify-between gap-2">
              <div>
                <h4 class="text-sm font-semibold text-slate-900">输入数据预览</h4>
                <p class="mt-0.5 text-[11px] leading-4 text-slate-400">运行前确认输入来源与行列规模。</p>
              </div>
              <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-slate-500">
                {{ selectedNodeIncomingNodes.length ? '来自上游' : '直接来自数据集' }}
              </span>
            </div>
            <div class="mt-1.5 grid gap-1 sm:grid-cols-2">
              <div class="rounded-[8px] border border-slate-200 bg-white px-2 py-1.5">
                <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">输入来源</p>
                <p class="mt-0.5 text-sm font-semibold text-slate-900">{{ splitInputSourceLabel(selectedNode) }}</p>
              </div>
              <div class="rounded-[8px] border border-slate-200 bg-white px-2 py-1.5">
                <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">预估输入规模</p>
                <p class="mt-0.5 text-sm font-semibold text-slate-900">{{ splitInputShapeText(selectedNode) }}</p>
              </div>
            </div>
            <div class="mt-1 rounded-[8px] border border-slate-200 bg-white px-2 py-1.5 text-[11px] leading-4.5 text-slate-500">{{ splitInputPreviewNote(selectedNode) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isResultDialogOpen && selectedNode" class="fixed inset-0 z-[75] flex items-center justify-center bg-slate-950/35 p-6 backdrop-blur-sm" @click.self="closeNodeDialogs">
      <div class="max-h-[88vh] w-full max-w-4xl overflow-y-auto rounded-[14px] border border-white/60 bg-white shadow-[0_36px_120px_-70px_rgba(15,23,42,0.45)]">
        <div class="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/90 px-5 py-3 backdrop-blur">
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-600">Results</p>
            <h3 class="mt-1 text-base font-semibold text-slate-900">{{ selectedNode.label }}</h3>
          </div>
          <button class="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700" type="button" @click="isResultDialogOpen = false">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div class="space-y-3 p-4">
          <div v-if="selectedNodeRunDetail" class="space-y-3">
            <div class="flex flex-wrap gap-2">
              <button
                :class="['result-tab-pill', activeResultTab === 'summary' && 'is-active']"
                type="button"
                @click="activeResultTab = 'summary'"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h1v4"/></svg>
                摘要
              </button>
              <button
                :class="['result-tab-pill', activeResultTab === 'tables' && 'is-active']"
                type="button"
                title="表格"
                @click="activeResultTab = 'tables'"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 9h16"/><path d="M4 15h16"/><path d="M10 4v16"/><path d="M14 4v16"/><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
                表格
              </button>
              <button
                :class="['result-tab-pill', activeResultTab === 'plots' && 'is-active']"
                type="button"
                title="图"
                @click="activeResultTab = 'plots'"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
                图
              </button>
              <button
                :class="['result-tab-pill', activeResultTab === 'downloads' && 'is-active']"
                type="button"
                title="下载"
                @click="activeResultTab = 'downloads'"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>
                下载
              </button>
            </div>

            <div class="relative" :style="resultPanelHeight ? { minHeight: `${resultPanelHeight}px` } : undefined">
            <div
              ref="resultSummaryPanelRef"
              :class="['result-tab-panel space-y-3', activeResultTab !== 'summary' && 'is-measure-hidden']"
            >
              <div class="rounded-[10px] border border-slate-200 bg-white px-3 py-2.5">
                <div class="flex items-center justify-between gap-3">
                  <div class="flex min-w-0 items-center gap-2">
                    <span class="truncate text-sm font-semibold text-slate-900">{{ selectedNodeRunDetail.message }}</span>
	                    <span v-if="selectedNodeRunSummary?.created_at" class="truncate text-xs text-slate-400">
	                      {{ formatBeijingCompact(selectedNodeRunSummary.created_at) }}
	                    </span>
                  </div>
                  <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="runStatusClass(selectedNodeRunDetail.status)">
                    {{ runStatusLabel(selectedNodeRunDetail.status) }}
                  </span>
                </div>
              </div>

              <div class="rounded-[10px] border border-slate-200 bg-white px-3 py-2.5 text-xs leading-5 text-slate-500">
                <p>运行批次：{{ shortRunId(selectedNodeRunDetail.run_id) }}</p>
                <p class="mt-1">执行顺序：第 {{ selectedNodeRunDetail.execution_order }} 步</p>
                <template v-for="item in compactTextSummaryEntries(selectedNodeRunDetail)" :key="`result-summary-${item.scope}-${item.key}`">
                  <p class="mt-1">{{ item.label }}：{{ item.value }}</p>
                </template>
              </div>

              <div v-if="selectedNodeMetricCards.length" class="grid gap-3 xl:grid-cols-2">
                <div
                  v-for="(card, cardIndex) in selectedNodeMetricCards"
                  :key="`result-metric-card-${cardIndex}`"
                  class="rounded-[10px] border border-slate-200 bg-white px-4 py-3"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <h5 class="text-sm font-semibold text-slate-900">{{ card.title }}</h5>
                      <p v-if="card.subtitle" class="mt-1 text-xs text-slate-400">{{ card.subtitle }}</p>
                    </div>
                    <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">{{ card.items.length }} 项</span>
                  </div>
                  <div class="mt-3 grid gap-2 sm:grid-cols-2">
                    <div
                      v-for="item in card.items"
                      :key="`result-metric-${cardIndex}-${item.label}`"
                      class="flex items-center justify-between gap-2 rounded-[8px] bg-slate-50/80 px-3 py-2"
                    >
                      <span class="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">{{ item.label }}</span>
                      <span class="rounded-full px-2 py-1 text-[11px] font-semibold" :class="previewToneClass(item.tone)">{{ item.value }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="selectedNodeRunDetail.module_id !== 'rcs' && normalizedNodeLogs(selectedNodeRunDetail).length" class="space-y-2">
                <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">日志</p>
                <div class="rounded-[10px] border border-slate-200 bg-white px-3 py-2.5">
                  <p
                    v-for="(item, index) in normalizedNodeLogs(selectedNodeRunDetail)"
                    :key="`summary-log-${index}`"
                    class="text-xs leading-5 text-slate-500"
                    :class="index > 0 && 'mt-1.5 border-t border-slate-100 pt-1.5'"
                  >
                    {{ item }}
                  </p>
                </div>
              </div>
            </div>

            <div
              v-if="selectedNodeTables.length"
              ref="resultTablesPanelRef"
              :class="['result-tab-panel space-y-3', activeResultTab !== 'tables' && 'is-measure-hidden']"
            >
              <div v-for="table in selectedNodeTables" :key="`result-${tableKey(table)}`" class="rounded-[10px] border border-slate-200 bg-white">
                <div class="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
                  <div>
                    <h5 class="text-sm font-semibold text-slate-900">{{ tableTitle(table) }}</h5>
                    <p class="mt-1 text-xs text-slate-400">结构化表格结果。</p>
                  </div>
                  <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">{{ displayTableRowCount(table) }} 行</span>
                </div>
                <div :class="tableBodyContainerClass(table)">
                  <table class="min-w-full divide-y divide-slate-100 text-left text-xs text-slate-600">
                    <thead :class="tableHeadClass(table)">
                      <tr>
                        <th v-for="column in displayTableColumns(table)" :key="`result-${tableKey(table)}-${column}`" :class="tableHeaderCellClass(table)">{{ column }}</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                      <tr v-for="(row, rowIndex) in displayTableRows(table)" :key="`result-${tableKey(table)}-${rowIndex}`">
                        <td v-for="(cell, cellIndex) in row" :key="`result-${tableKey(table)}-${rowIndex}-${cellIndex}`" :class="tableBodyCellClass(table)">
                          {{ formatResultValue(cell) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            <div
              v-else
              ref="resultTablesPanelRef"
              :class="['result-tab-panel rounded-[10px] border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm leading-6 text-slate-400', activeResultTab !== 'tables' && 'is-measure-hidden']"
            >
              当前节点没有表格结果。
            </div>

            <div
              v-if="selectedNodePlots.length"
              ref="resultPlotsPanelRef"
              :class="['result-tab-panel space-y-3', activeResultTab !== 'plots' && 'is-measure-hidden']"
            >
              <div :class="selectedNodePlotGridClass">
                <div v-for="plot in selectedNodePlots" :key="`result-${plotKey(plot)}`" class="rounded-[10px] border border-slate-200 bg-white">
                  <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3" :class="isPremiumPlotNodeResult && 'bg-emerald-50/70 border-emerald-100'">
                    <div class="min-w-0">
                      <h5 class="truncate text-[13px] font-semibold leading-5 text-slate-900">{{ plotTitle(plot) }}</h5>
                      <p class="mt-1 text-xs text-slate-400">{{ isPremiumPlotNodeResult ? '支持 PNG 下载与高清 PDF 导出。' : '图形结果预览。' }}</p>
                    </div>
                    <div v-if="isPremiumPlotNodeResult" class="flex items-center gap-2">
                      <button
                        type="button"
                        class="tool-btn px-2.5 py-2 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50"
                        @click="downloadNodePlotPng(plot)"
                      >
                        下载 PNG
                      </button>
                      <button
                        type="button"
                        class="tool-btn border-amber-200 bg-amber-50 px-2.5 py-2 text-[11px] font-semibold text-amber-700 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60"
                        :disabled="downloadingPlotKey === plotKey(plot)"
                        @click="downloadNodePlotPdf(plot)"
                      >
                        <span>{{ downloadingPlotKey === plotKey(plot) ? '导出中...' : '下载 PDF' }}</span>
                        <span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 drop-shadow-[0_0_10px_rgba(16,185,129,0.45)]">
                          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/></svg>
                          1
                        </span>
                      </button>
                    </div>
                    <span v-else class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">{{ plot.media_type || 'image/png' }}</span>
                  </div>
                  <div class="p-4" :class="isPremiumPlotNodeResult && 'bg-white sm:p-5'">
                    <img
                      v-if="plot.content_base64"
                      :src="plotImageSrc(plot)"
                      :alt="plotTitle(plot)"
                      class="w-full rounded-[8px] border border-slate-200 bg-white object-contain"
                      @load="updateResultPanelHeight"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div
              v-else
              ref="resultPlotsPanelRef"
              :class="['result-tab-panel rounded-[10px] border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm leading-6 text-slate-400', activeResultTab !== 'plots' && 'is-measure-hidden']"
            >
              当前节点没有图形结果。
            </div>

            <div
              ref="resultDownloadsPanelRef"
              :class="['result-tab-panel space-y-3', activeResultTab !== 'downloads' && 'is-measure-hidden']"
            >
              <div v-if="selectedNodeTables.length" class="space-y-2">
                <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">表格数据</p>
                <div v-for="table in selectedNodeTables" :key="`dl-table-${tableKey(table)}`" class="flex items-center justify-between gap-3 rounded-[10px] border border-slate-200 bg-white px-3 py-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-slate-900">{{ tableTitle(table) }}</p>
                    <p class="mt-1 truncate text-xs text-slate-500">{{ tableRowCount(table) }} 行 × {{ tableColumns(table).length }} 列 · CSV</p>
                  </div>
                  <button class="tool-btn px-3 py-2 text-xs font-semibold" type="button" @click="downloadTableAsCsv(table)">下载 CSV</button>
                </div>
              </div>

              <div v-if="!selectedNodeTables.length" class="rounded-[10px] border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm leading-6 text-slate-400">
                当前节点没有可下载产物。
              </div>
            </div>
            </div>
          </div>

          <div v-else class="rounded-[10px] border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm leading-6 text-slate-400">
            当前节点暂时没有可展示的运行结果。先运行该节点，或切换到已有运行记录。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  downloadLassoPlotPdf,
  getClinicalPipelineRun,
  getClinicalPipelineRunNode,
  getClinicalWorkflow,
  getDatasetSummary,
  getDatasets,
  getProjects,
  listClinicalPipelineRuns,
  runClinicalPipeline,
  saveClinicalWorkflow,
  updateClinicalWorkflow,
  type ClinicalPipelineNodeDetailResponse,
  type ClinicalPipelineRunDetailResponse,
  type ClinicalPipelineRunSummaryResponse,
  type DatasetItem,
  type DatasetSummaryResponse,
  type LassoPlotPayload,
} from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

type StageId =
  | 'data-preparation'
  | 'feature-processing'
  | 'model-development'
  | 'model-validation'

type FieldType = 'input' | 'select'

interface StageDefinition {
  id: StageId
  label: string
  shortLabel: string
  description: string
  badgeClass: string
  tagClass: string
}

interface ModuleField {
  key: string
  label: string
  type: FieldType
  options?: string[]
}

interface ModuleDefinition {
  id: string
  label: string
  description: string
  stageId: StageId
  fields: ModuleField[]
  defaults: Record<string, string>
}

interface ModuleGroup {
  id: string
  label: string
  shortLabel: string
  description: string
  icon: string
  iconClass: string
  modules: ModuleDefinition[]
}

interface TemplateNodeDefinition {
  moduleId: string
  values?: Record<string, string>
}

interface CanvasTemplate {
  id: string
  label: string
  description: string
  accentClass: string
  nodes: TemplateNodeDefinition[]
  connections: Array<[number, number]>
}

interface ProjectOption {
  id: string
  name: string
}

interface DatasetOption extends DatasetItem {}

interface CanvasNode {
  id: string
  moduleId: string
  label: string
  description: string
  stageId: StageId
  fields: ModuleField[]
  values: Record<string, string>
  x: number
  y: number
  order: number
}

type NodeStatus = 'ready' | 'incomplete' | 'blocked'

interface NodeStatusMeta {
  status: NodeStatus
  label: string
  message: string
}

type PreviewTone = 'neutral' | 'positive' | 'accent' | 'warning'

interface NodePreviewItem {
  label: string
  value: string
  tone?: PreviewTone
}

interface NodePreviewMeta {
  title: string
  subtitle: string
  items: NodePreviewItem[]
}

interface ResultMetricCard {
  title: string
  subtitle?: string
  items: NodePreviewItem[]
}

interface NodeConnection {
  id: string
  fromNodeId: string
  toNodeId: string
  outputPortId?: 'train' | 'test' | null
}

interface DragState {
  nodeIds: string[]
  startX: number
  startY: number
  origins: Array<{ id: string; x: number; y: number }>
}

interface LogEntry {
  id: number
  kind: string
  time: string
  message: string
}

interface SelectionRect {
  startX: number
  startY: number
  currentX: number
  currentY: number
  additive: boolean
}

interface PanState {
  startX: number
  startY: number
  scrollLeft: number
  scrollTop: number
}

interface WorkflowDraftPayload {
  projectId: string | null
  workflowName: string
  nodes: CanvasNode[]
  connections: NodeConnection[]
}

const NODE_WIDTH = 276
const NODE_HEIGHT = 172
const INPUT_PORT_X = -10
const OUTPUT_PORT_X = NODE_WIDTH - 10
const PORT_CENTER_Y = 86
const STAGE_ORDER = new Map<StageId, number>([
  ['data-preparation', 0],
  ['feature-processing', 1],
  ['model-development', 2],
  ['model-validation', 3],
])

const stages: StageDefinition[] = [
  {
    id: 'data-preparation',
    label: '数据准备',
    shortLabel: 'data',
    description: '导入、映射、清洗、编码与数据切分',
    badgeClass: 'bg-sky-100 text-sky-700',
    tagClass: 'bg-sky-50 text-sky-700',
  },
  {
    id: 'feature-processing',
    label: '特征处理',
    shortLabel: 'feature',
    description: '筛选、共线性、样条、交互项等',
    badgeClass: 'bg-violet-100 text-violet-700',
    tagClass: 'bg-violet-50 text-violet-700',
  },
  {
    id: 'model-development',
    label: '模型开发',
    shortLabel: 'model',
    description: '统计模型与机器学习模型节点',
    badgeClass: 'bg-emerald-100 text-emerald-700',
    tagClass: 'bg-emerald-50 text-emerald-700',
  },
  {
    id: 'model-validation',
    label: '模型验证',
    shortLabel: 'validate',
    description: 'ROC、校准、DCA、重采样与外部验证',
    badgeClass: 'bg-amber-100 text-amber-700',
    tagClass: 'bg-amber-50 text-amber-700',
  },

]

const moduleGroups: ModuleGroup[] = [
  {
    id: 'data-preparation',
    label: '数据准备模块',
    shortLabel: 'data',
    description: '画布入口通常从这里开始。',
    icon: '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8.5" ry="3.5"/><path d="M3.5 5v7c0 1.93 3.81 3.5 8.5 3.5s8.5-1.57 8.5-3.5V5"/><path d="M3.5 12v7c0 1.93 3.81 3.5 8.5 3.5s8.5-1.57 8.5-3.5v-7"/></svg>',
    iconClass: 'bg-sky-100 text-sky-700',
    modules: [
      {
        id: 'field-mapping',
        label: '字段映射',
        description: '指定 ID、结局、时间、分组和候选变量字段。',
        stageId: 'data-preparation',
        fields: [
          { key: 'idField', label: 'ID 字段', type: 'input' },
          { key: 'outcomeField', label: '结局字段', type: 'input' },
          { key: 'timeField', label: '时间字段', type: 'input' },
        ],
        defaults: { idField: 'patient_id', outcomeField: 'outcome', timeField: 'follow_up_days', predictorFields: '' },
      },
      {
        id: 'missing-value',
        label: '缺失值处理',
        description: '处理缺失观测，控制后续模型稳定性。',
        stageId: 'data-preparation',
        fields: [
          { key: 'method', label: '处理方式', type: 'select', options: ['删除缺失', '均值/众数插补', '多重插补'] },
          { key: 'threshold', label: '缺失比例阈值', type: 'input' },
        ],
        defaults: { method: '多重插补', threshold: '0.20' },
      },
      {
        id: 'split',
        label: '训练/测试集划分',
        description: '设置建模与验证数据切分逻辑。',
        stageId: 'data-preparation',
        fields: [
          { key: 'ratio', label: '划分比例', type: 'select', options: ['7:3', '8:2', '6:2:2'] },
          { key: 'sampling', label: '抽样方式', type: 'select', options: ['分层抽样', '随机划分', '时间切分'] },
          { key: 'seed', label: '随机种子', type: 'input' },
        ],
        defaults: { ratio: '7:3', sampling: '随机划分', seed: '2026', stratifyField: '', timeSplitField: '' },
      },
      {
        id: 'encoding',
        label: '分类变量编码',
        description: '为树模型或线性模型准备合适的编码形式。',
        stageId: 'data-preparation',
        fields: [
          { key: 'encoding', label: '编码方式', type: 'select', options: ['One-hot', '标签编码', '目标编码'] },
          { key: 'dropFirst', label: '首列丢弃', type: 'select', options: ['是', '否'] },
        ],
        defaults: { encoding: 'One-hot', dropFirst: '是' },
      },
    ],
  },
  {
    id: 'feature-processing',
    label: '特征处理模块',
    shortLabel: 'feature',
    description: '控制变量筛选、交互和非线性建模。',
    icon: '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v5"/><path d="M14 2v5"/><path d="M4 7h16"/><rect x="4" y="7" width="16" height="13" rx="2"/><path d="m9 14 2 2 4-4"/></svg>',
    iconClass: 'bg-violet-100 text-violet-700',
    modules: [
      {
        id: 'univariate-screen',
        label: '单因素筛选',
        description: '基于 P 值或效应量做候选变量初筛。',
        stageId: 'feature-processing',
        fields: [
          { key: 'rule', label: '筛选规则', type: 'select', options: ['P < 0.05', 'P < 0.10', '仅展示不筛除'] },
          { key: 'keepClinical', label: '保留临床变量', type: 'select', options: ['是', '否'] },
        ],
        defaults: { rule: 'P < 0.10', keepClinical: '是' },
      },
      {
        id: 'vif',
        label: 'VIF 共线性检查',
        description: '检查变量冗余并提示高共线性风险。',
        stageId: 'feature-processing',
        fields: [
          { key: 'cutoff', label: 'VIF 阈值', type: 'input' },
        ],
        defaults: { cutoff: '5' },
      },
      {
        id: 'lasso-selection',
        label: 'LASSO 特征选择',
        description: '适合高维变量筛选或与回归模型串联。',
        stageId: 'feature-processing',
        fields: [
          { key: 'criterion', label: 'Lambda 规则', type: 'select', options: ['lambda.min', 'lambda.1se'] },
          { key: 'folds', label: '交叉验证折数', type: 'input' },
        ],
        defaults: { criterion: 'lambda.1se', folds: '10' },
      },
      {
        id: 'rf-importance',
        label: '随机森林变量重要度',
        description: '基于随机森林重要度排序筛选候选变量。',
        stageId: 'feature-processing',
        fields: [
          { key: 'trees', label: '树数量', type: 'input' },
          { key: 'topN', label: '保留变量数', type: 'input' },
        ],
        defaults: { trees: '500', topN: '10' },
      },
      {
        id: 'boruta-selection',
        label: 'Boruta 变量筛选',
        description: '通过影子特征对照检验稳健确认变量。',
        stageId: 'feature-processing',
        fields: [
          { key: 'maxRuns', label: '最大迭代次数', type: 'input' },
        ],
        defaults: { maxRuns: '100' },
      },
      {
        id: 'feature-merge',
        label: '特征合并',
        description: '综合多条筛选分支，输出最终入模变量集。',
        stageId: 'feature-processing',
        fields: [
          { key: 'mergeRule', label: '合并规则', type: 'select', options: ['交集', '并集', '至少入选 N 次'] },
          { key: 'minVotes', label: '最少入选次数', type: 'input' },
        ],
        defaults: { mergeRule: '交集', minVotes: '2' },
      },
    ],
  },
  {
    id: 'model-development',
    label: '模型开发模块',
    shortLabel: 'model',
    description: '真正进入核心建模节点。',
    icon: '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M7 16V8"/><path d="M12 16V5"/><path d="M17 16v-4"/></svg>',
    iconClass: 'bg-emerald-100 text-emerald-700',
    modules: [
      {
        id: 'logistic-model',
        label: 'Logistic 回归',
        description: '二分类结局的经典基线模型。',
        stageId: 'model-development',
        fields: [
          { key: 'dataSource', label: '数据源', type: 'select', options: ['上游输出', '训练集', '测试集', '原始数据'] },
          { key: 'outcomeField', label: '结局变量(可选)', type: 'input' },
          { key: 'entry', label: '变量进入策略', type: 'select', options: ['强制进入', '逐步回归', '筛选后进入'] },
          { key: 'reference', label: '参考水平', type: 'input' },
          { key: 'ci', label: '置信区间', type: 'select', options: ['95%', '90%'] },
        ],
        defaults: { dataSource: '上游输出', outcomeField: '', entry: '筛选后进入', reference: '0', ci: '95%' },
      },
      {
        id: 'cox-model',
        label: 'Cox 回归',
        description: '生存结局常用预测模型节点。',
        stageId: 'model-development',
        fields: [
          { key: 'dataSource', label: '数据源', type: 'select', options: ['上游输出', '训练集', '测试集', '原始数据'] },
          { key: 'timeField', label: '时间变量(可选)', type: 'input' },
          { key: 'outcomeField', label: '事件变量(可选)', type: 'input' },
          { key: 'entry', label: '变量进入策略', type: 'select', options: ['强制进入', '筛选后进入'] },
          { key: 'ties', label: 'Ties 处理', type: 'select', options: ['efron', 'breslow', 'exact'] },
        ],
        defaults: { dataSource: '上游输出', timeField: '', outcomeField: '', entry: '筛选后进入', ties: 'efron' },
      },
      {
        id: 'xgboost',
        label: 'XGBoost',
        description: '非线性树模型节点。',
        stageId: 'model-development',
        fields: [
          { key: 'dataSource', label: '数据源', type: 'select', options: ['上游输出', '训练集', '测试集', '原始数据'] },
          { key: 'outcomeField', label: '结局变量(可选)', type: 'input' },
          { key: 'eta', label: '学习率 eta', type: 'input' },
          { key: 'depth', label: 'max_depth', type: 'input' },
          { key: 'rounds', label: 'nrounds', type: 'input' },
          { key: 'seed', label: '随机种子', type: 'input' },
        ],
        defaults: { dataSource: '上游输出', outcomeField: '', eta: '0.05', depth: '4', rounds: '300', seed: '2026' },
      },
      {
        id: 'random-forest',
        label: '随机森林',
        description: '稳健的树模型基线。',
        stageId: 'model-development',
        fields: [
          { key: 'dataSource', label: '数据源', type: 'select', options: ['上游输出', '训练集', '测试集', '原始数据'] },
          { key: 'outcomeField', label: '结局变量(可选)', type: 'input' },
          { key: 'trees', label: '树数量', type: 'input' },
          { key: 'mtry', label: 'mtry', type: 'input' },
          { key: 'seed', label: '随机种子', type: 'input' },
        ],
        defaults: { dataSource: '上游输出', outcomeField: '', trees: '500', mtry: 'sqrt(p)', seed: '2026' },
      },
      {
        id: 'model-comparison',
        label: '模型比较',
        description: '汇总多个模型的核心评价指标。',
        stageId: 'model-development',
        fields: [
          { key: 'primaryMetric', label: '主指标', type: 'select', options: ['AUC', 'C-index', '综合评分'] },
          { key: 'rankRule', label: '排序规则', type: 'select', options: ['主指标优先', '加权综合'] },
        ],
        defaults: { primaryMetric: '综合评分', rankRule: '加权综合' },
      },
    ],
  },
  {
    id: 'model-validation',
    label: '模型验证模块',
    shortLabel: 'validate',
    description: '把评价节点接在模型下游。',
    icon: '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    iconClass: 'bg-amber-100 text-amber-700',
    modules: [
      {
        id: 'roc',
        label: 'ROC / AUC',
        description: '二分类模型区分度评价。',
        stageId: 'model-validation',
        fields: [
          { key: 'ci', label: '区间估计', type: 'select', options: ['95% CI', 'Bootstrap CI'] },
          { key: 'cutoff', label: '最佳截点规则', type: 'select', options: ['Youden index', '固定阈值 0.5'] },
        ],
        defaults: { ci: '95% CI', cutoff: 'Youden index' },
      },
      {
        id: 'calibration',
        label: '校准曲线',
        description: '检查预测概率和实际事件率一致性。',
        stageId: 'model-validation',
        fields: [
          { key: 'bins', label: '分组策略', type: 'select', options: ['十分位', '五分位', 'Bootstrap 平滑'] },
          { key: 'resamples', label: '重采样次数', type: 'input' },
        ],
        defaults: { bins: 'Bootstrap 平滑', resamples: '1000' },
      },
      {
        id: 'dca',
        label: 'DCA 决策曲线',
        description: '展示阈值概率区间内的净获益。',
        stageId: 'model-validation',
        fields: [
          { key: 'range', label: '阈值范围', type: 'input' },
          { key: 'step', label: '步长', type: 'input' },
        ],
        defaults: { range: '0.05 - 0.80', step: '0.01' },
      },
      {
        id: 'nomogram',
        label: 'Nomogram 列线图',
        description: '生成临床风险预测列线图。',
        stageId: 'model-validation',
        fields: [
          { key: 'scale', label: '总分刻度', type: 'select', options: ['100 分', '200 分'] },
          { key: 'timepoint', label: '预测时间点', type: 'input' },
        ],
        defaults: { scale: '100 分', timepoint: '1 year' },
      },
      {
        id: 'rcs',
        label: '限制性立方样条',
        description: '为连续变量建立非线性效应。',
        stageId: 'model-validation',
        fields: [
          { key: 'target', label: '目标变量', type: 'input' },
          { key: 'knots', label: '节点数', type: 'select', options: ['3', '4', '5'] },
        ],
        defaults: { target: 'age', knots: '4' },
      },
    ],
  },
  
]

const canvasTemplates: CanvasTemplate[] = [
  {
    id: 'binary-classification',
    label: '二分类预测模板',
    description: '从字段映射、缺失处理到 Logistic、ROC、校准和 DCA 的常见链路。',
    accentClass: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    nodes: [
      { moduleId: 'field-mapping', values: { outcomeField: 'outcome_binary', timeField: 'follow_up_days' } },
      { moduleId: 'missing-value' },
      { moduleId: 'split', values: { ratio: '7:3', sampling: '分层抽样', stratifyField: 'outcome_binary' } },
      { moduleId: 'lasso-selection', values: { criterion: 'lambda.1se' } },
      { moduleId: 'logistic-model', values: { entry: '筛选后进入', reference: '0', ci: '95%' } },
      { moduleId: 'roc' },
      { moduleId: 'calibration' },
      { moduleId: 'dca' },
      { moduleId: 'nomogram', values: { timepoint: 'admission' } },
    ],
    connections: [
      [0, 1],
      [1, 2],
      [2, 3],
      [3, 4],
      [4, 5],
      [4, 6],
      [4, 7],
      [4, 8],
    ],
  },
  {
    id: 'survival-prognosis',
    label: '生存预测模板',
    description: '适合预后研究，从时间结局映射到 Cox、Bootstrap 与列线图。',
    accentClass: 'bg-sky-50 text-sky-700 ring-1 ring-sky-200',
    nodes: [
      { moduleId: 'field-mapping', values: { outcomeField: 'event', timeField: 'survival_days' } },
      { moduleId: 'missing-value', values: { method: '多重插补' } },
      { moduleId: 'univariate-screen', values: { rule: 'P < 0.10', keepClinical: '是' } },
      { moduleId: 'cox-model', values: { entry: '筛选后进入', ties: 'efron' } },
      { moduleId: 'bootstrap', values: { resamples: '1000' } },
      { moduleId: 'nomogram', values: { scale: '100 分', timepoint: '1 year' } },
    ],
    connections: [
      [0, 1],
      [1, 2],
      [2, 3],
      [3, 4],
      [3, 5],
    ],
  },
]

const canvasRef = ref<HTMLElement | null>(null)
const canvasNodes = ref<CanvasNode[]>([])
const connections = ref<NodeConnection[]>([])
const undoStack = ref<Array<{ nodes: CanvasNode[]; connections: NodeConnection[] }>>([])
const MAX_UNDO = 50
const route = useRoute()
const router = useRouter()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const PAID_SUBSCRIPTIONS = new Set(['basic', 'pro', 'enterprise'])
const canvasScale = ref(1)
const zoomPercent = ref(100)
const selectedNodeId = ref<string | null>(null)
const selectedNodeIds = ref<string[]>([])
const selectedConnectionId = ref<string | null>(null)
const isSettingsDialogOpen = ref(false)
const isResultDialogOpen = ref(false)
const activeResultTab = ref<'summary' | 'tables' | 'plots' | 'downloads'>('summary')
const resultSummaryPanelRef = ref<HTMLElement | null>(null)
const resultTablesPanelRef = ref<HTMLElement | null>(null)
const resultPlotsPanelRef = ref<HTMLElement | null>(null)
const resultDownloadsPanelRef = ref<HTMLElement | null>(null)
const resultPanelHeight = ref(0)
const draggingLibraryModuleId = ref<string | null>(null)
const dragState = ref<DragState | null>(null)
const selectionRect = ref<SelectionRect | null>(null)
const panState = ref<PanState | null>(null)
const pointerPosition = ref({ x: 0, y: 0 })
const pendingConnectionFrom = ref<string | null>(null)
const isTemplatePickerOpen = ref(false)
const projects = ref<ProjectOption[]>([])
const datasetOptions = ref<DatasetOption[]>([])
const datasetSummary = ref<DatasetSummaryResponse | null>(null)
const selectedProjectId = ref<string>((route.query.projectId as string) || '')
const selectedDatasetId = ref('')
const workflowName = ref('Untitled')
const isEditingWorkflowName = ref(false)
const workflowNameDraft = ref('')
const workflowNameInputRef = ref<HTMLInputElement | null>(null)
const loadingDatasets = ref(false)
const isRunningPipeline = ref(false)
const downloadingPlotKey = ref('')
const runningNodeIds = ref<string[]>([])
const isLoadingRunNode = ref(false)
const isRestoringDraft = ref(false)
const isSavingWorkflow = ref(false)
const savedWorkflowId = ref<string | null>(String(route.query.workflowId || '').trim() || null)
const pipelineRuns = ref<ClinicalPipelineRunSummaryResponse[]>([])
const activeRunId = ref<string | null>(null)
const activeRunDetail = ref<ClinicalPipelineRunDetailResponse | null>(null)
const selectedNodeRunDetail = ref<ClinicalPipelineNodeDetailResponse | null>(null)
const logCounter = ref(3)
const logs = ref<LogEntry[]>([
  { id: 1, kind: 'init', time: nowTime(), message: '节点画布已就绪。左侧拖入模块后，再通过输入输出端口手动连线。' },
  { id: 2, kind: 'tip', time: nowTime(), message: '建议第一个节点从“字段映射”或“缺失值处理”开始，这样整个分析链路更自然。' },
  { id: 3, kind: 'link', time: nowTime(), message: '先点击某个节点右侧输出端口，再点击另一个节点左侧输入端口，即可建立连接。' },
])

const totalModules = computed(() => moduleGroups.reduce((sum, group) => sum + group.modules.length, 0))
const canvasSurfaceWidth = computed(() => Math.max(1800, ...canvasNodes.value.map((node) => node.x + NODE_WIDTH + 120)))
const canvasSurfaceHeight = computed(() => Math.max(1200, ...canvasNodes.value.map((node) => node.y + NODE_HEIGHT + 120)))

const selectedNode = computed(() => canvasNodes.value.find((node) => node.id === selectedNodeId.value) ?? null)
const selectedNodeStatus = computed(() => (selectedNode.value ? nodeStatusMap.value.get(selectedNode.value.id) ?? null : null))
const selectedNodePreview = computed(() => (selectedNode.value ? nodePreviewMap.value.get(selectedNode.value.id) ?? null : null))
const selectedNodeIncomingNodes = computed(() => (selectedNode.value ? getIncomingNodes(selectedNode.value.id) : []))
const showInputDatasetPicker = computed(() => {
  if (!selectedNode.value) return false
  if (selectedNodeIncomingNodes.value.length) return false
  if (['field-mapping', 'missing-value', 'split', 'encoding'].includes(selectedNode.value.moduleId)) return true
  return isStandaloneModelNode.value
})
const selectedNodeSettingFields = computed(() => {
  if (!selectedNode.value) return []
  const fields = findModuleById(selectedNode.value.moduleId)?.fields ?? selectedNode.value.fields ?? []
  const hasUpstream = selectedNodeIncomingNodes.value.length > 0
  if (!hasUpstream) return fields
  if (['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) {
    return fields.filter((field) => field.key !== 'dataSource')
  }
  return fields
})
const isStandaloneModelNode = computed(() => {
  if (!selectedNode.value) return false
  if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return false
  return selectedNodeIncomingNodes.value.length === 0
})
const normalizedStandaloneModelDataSource = computed(() => {
  if (!selectedNode.value) return '上游输出'
  const raw = `${selectedNode.value.values.dataSource ?? ''}`.trim().replace('数据集', '').replace(/\s+/g, '')
  if (!raw) return '上游输出'
  if (raw.includes('原始')) return '原始数据'
  if (raw.includes('训练')) return '训练集'
  if (raw.includes('测试')) return '测试集'
  if (raw.includes('上游')) return '上游输出'
  return raw
})
const showStandaloneModelPredictorPicker = computed(() => isStandaloneModelNode.value && normalizedStandaloneModelDataSource.value !== '上游输出')
const selectedModelPredictors = computed(() => {
  if (!selectedNode.value) return []
  if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return []
  return parsePredictorFields(selectedNode.value.values.predictorFields || '')
})
const modelPredictorCandidateColumns = computed(() => {
  if (!selectedNode.value) return []
  if (!showStandaloneModelPredictorPicker.value) return []
  const fieldMappingNode = getFieldMappingNode()
  const excluded = new Set<string>()
  const mappedId = (fieldMappingNode?.values.idField || '').trim()
  if (mappedId) excluded.add(mappedId)
  const outcomeVar = (fieldMappingNode?.values.outcomeField || selectedNode.value.values.outcomeField || '').trim()
  const timeVar = (fieldMappingNode?.values.timeField || selectedNode.value.values.timeField || '').trim()
  if (outcomeVar) excluded.add(outcomeVar)
  if (timeVar) excluded.add(timeVar)
  return datasetColumnNames.value.filter((name) => !excluded.has(name))
})
const selectedDatasetOption = computed(() => datasetOptions.value.find((item) => item.id === selectedDatasetId.value) ?? null)
const datasetColumnNames = computed(() => (datasetSummary.value?.columns || []).map((column) => column.name))
const splitSelectableColumns = computed(() => {
  const fieldMappingNode = getFieldMappingNode()
  const mappedColumns = fieldMappingNode
    ? [
        fieldMappingNode.values.idField,
        fieldMappingNode.values.outcomeField,
        fieldMappingNode.values.timeField,
        ...parsePredictorFields(fieldMappingNode.values.predictorFields || ''),
      ]
    : []
  return Array.from(new Set([...datasetColumnNames.value, ...mappedColumns.map((item) => item?.trim() || '').filter(Boolean)]))
})
const selectedFieldMappingPredictors = computed(() => {
  if (!selectedNode.value || selectedNode.value.moduleId !== 'field-mapping') return []
  return parsePredictorFields(selectedNode.value.values.predictorFields || '')
})
const fieldMappingCandidateColumns = computed(() => {
  if (!selectedNode.value || selectedNode.value.moduleId !== 'field-mapping') return []
  const excluded = new Set([
    selectedNode.value.values.idField,
    selectedNode.value.values.outcomeField,
    selectedNode.value.values.timeField,
  ].filter(Boolean))
  return datasetColumnNames.value.filter((column) => !excluded.has(column))
})
const currentProject = computed(() => projects.value.find((item) => item.id === selectedProjectId.value) ?? null)
const hasMultiSelection = computed(() => selectedNodeIds.value.length > 1)
const selectedNodeTables = computed(() => selectedNodeRunDetail.value?.output_tables ?? [])
const selectedNodePlots = computed(() => selectedNodeRunDetail.value?.output_plots ?? [])
const selectedNodeModuleId = computed(() => {
  if (selectedNodeRunDetail.value?.module_id) return selectedNodeRunDetail.value.module_id
  return selectedNode.value?.moduleId || null
})
const selectedNodeRunSummary = computed(() =>
  pipelineRuns.value.find((item) => item.run_id === selectedNodeRunDetail.value?.run_id) ?? null,
)
const canDownloadPremiumPdf = computed(() => PAID_SUBSCRIPTIONS.has(authStore.user?.subscription || 'free'))
const premiumPlotNodeModules = new Set([
  'lasso-selection',
  'rf-importance',
  'boruta-selection',
  'rcs',
  'logistic-model',
  'cox-model',
  'xgboost',
  'random-forest',
  'model-comparison',
  'roc',
  'calibration',
  'dca',
  'bootstrap',
  'nomogram',
])
const isPremiumPlotNodeResult = computed(() => premiumPlotNodeModules.has(selectedNodeModuleId.value || ''))
const selectedNodePlotGridClass = computed(() =>
  isPremiumPlotNodeResult.value && selectedNodePlots.value.length > 1 ? 'grid gap-3 xl:grid-cols-2' : 'space-y-3',
)
const latestRunNodeMap = computed(() => new Map((activeRunDetail.value?.node_results || []).map((item) => [item.node_id, item])))
const selectedNodeMetricCards = computed<ResultMetricCard[]>(() => {
  const detail = selectedNodeRunDetail.value
  if (!detail) return []

  if (detail.module_id === 'calibration') {
    const summaryTable = detail.output_tables.find((table) => table?.name === 'calibration_summary')
    const rows = tableRowObjects(summaryTable)
    return rows.map((row: Record<string, unknown>) => ({
      title: `${previewMetricValue(row.dataset, '评估集')} 校准评价`,
      subtitle: '校准曲线节点输出的统计摘要。',
      items: [
        { label: 'C-index', value: previewMetricValue(row['C-index']), tone: previewMetricTone(row['C-index']) },
        { label: 'Dxy', value: previewMetricValue(row.Dxy), tone: previewMetricTone(row.Dxy) },
        { label: 'Intercept', value: previewMetricValue(row.Intercept), tone: 'accent' },
        { label: 'Slope', value: previewMetricValue(row.Slope), tone: previewMetricTone(row.Slope) },
        { label: 'Emax', value: previewMetricValue(row.Emax), tone: previewMetricTone(row.Emax) },
        { label: 'Eavg', value: previewMetricValue(row.Eavg), tone: previewMetricTone(row.Eavg) },
        { label: 'Brier', value: previewMetricValue(row.Brier), tone: previewMetricTone(row.Brier) },
        { label: 'R2', value: previewMetricValue(row.R2), tone: previewMetricTone(row.R2) },
      ],
    }))
  }
  return []
})
const selectionBounds = computed(() => {
  if (!selectionRect.value) return null
  const minX = Math.min(selectionRect.value.startX, selectionRect.value.currentX)
  const minY = Math.min(selectionRect.value.startY, selectionRect.value.currentY)
  return {
    x: minX,
    y: minY,
    width: Math.abs(selectionRect.value.currentX - selectionRect.value.startX),
    height: Math.abs(selectionRect.value.currentY - selectionRect.value.startY),
  }
})

const connectionPaths = computed(() =>
  connections.value
    .map((connection) => {
      const source = canvasNodes.value.find((node) => node.id === connection.fromNodeId)
      const target = canvasNodes.value.find((node) => node.id === connection.toNodeId)
      if (!source || !target) return null
      return {
        id: connection.id,
        d: buildConnectionPath(
          source.x + OUTPUT_PORT_X,
          source.y + PORT_CENTER_Y,
          target.x + INPUT_PORT_X + 20,
          target.y + PORT_CENTER_Y,
        ),
        isSelected:
          selectedConnectionId.value === connection.id ||
          selectedNodeId.value === source.id ||
          selectedNodeId.value === target.id,
      }
    })
    .filter((item): item is { id: string; d: string; isSelected: boolean } => Boolean(item)),
)

const nodeStatusMap = computed(() => {
  const statusMap = new Map<string, NodeStatusMeta>()

  for (let iteration = 0; iteration < canvasNodes.value.length + 2; iteration += 1) {
    for (const node of canvasNodes.value) {
      statusMap.set(node.id, evaluateNodeStatus(node, statusMap))
    }
  }

  return statusMap
})

const nodePreviewMap = computed(() => {
  const previewMap = new Map<string, NodePreviewMeta>()
  for (const node of canvasNodes.value) {
    const preview = buildNodePreview(node)
    if (preview) {
      previewMap.set(node.id, preview)
    }
  }
  return previewMap
})

const pendingConnectionPortId = ref<null>(null)

const temporaryConnectionPath = computed(() => {
  if (!pendingConnectionFrom.value) return ''
  const source = canvasNodes.value.find((node) => node.id === pendingConnectionFrom.value)
  if (!source) return ''
  return buildConnectionPath(
    source.x + OUTPUT_PORT_X,
    source.y + PORT_CENTER_Y,
    pointerPosition.value.x,
    pointerPosition.value.y,
  )
})

const rootNodeLabels = computed(() => {
  const targetIds = new Set(connections.value.map((item) => item.toNodeId))
  const labels = canvasNodes.value.filter((node) => !targetIds.has(node.id)).map((node) => node.label)
  return labels.length ? labels : ['暂无']
})

const leafNodeLabels = computed(() => {
  const sourceIds = new Set(connections.value.map((item) => item.fromNodeId))
  const labels = canvasNodes.value.filter((node) => !sourceIds.has(node.id)).map((node) => node.label)
  return labels.length ? labels : ['暂无']
})

const graphSummary = computed(() => {
  if (!canvasNodes.value.length) {
    return ['当前还没有任何节点。建议先从数据准备节点开始，再逐步向右串联。']
  }
  const counts = { ready: 0, incomplete: 0, blocked: 0 }
  for (const status of nodeStatusMap.value.values()) {
    counts[status.status] += 1
  }
  return [
    `当前共有 ${canvasNodes.value.length} 个节点，${connections.value.length} 条连线。`,
    `已就绪 ${counts.ready} 个，未完成 ${counts.incomplete} 个，被阻塞 ${counts.blocked} 个。`,
    `入口节点：${rootNodeLabels.value.join(' / ')}。`,
    `终点节点：${leafNodeLabels.value.join(' / ')}。`,
  ]
})

const connectionTips = computed(() => {
  const tips = [
    pendingConnectionFrom.value ? '你已选中一个输出端口，接下来点击另一个节点的输入端口即可完成连线。' : '当前没有进入连线模式。点击任意节点右侧端口即可开始连线。',
  ]
  if (selectedNode.value) {
    const status = nodeStatusMap.value.get(selectedNode.value.id)
    tips.push(`当前选中节点：${selectedNode.value.label}。${status ? status.message : '你可以继续拖动它，或在右侧修改参数。'}`)
  } else {
    tips.push('当前还没有选中节点。点击任意节点本体即可激活右侧参数面板。')
  }
  return tips
})

function nowTime() {
  return new Date().toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
}

const BEIJING_OFFSET_MS = 8 * 60 * 60 * 1000

function pad2(value: number) {
  return String(value).padStart(2, '0')
}

function formatBeijingCompact(timestamp: string) {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return ''
  const beijing = new Date(date.getTime() + BEIJING_OFFSET_MS)
  const month = pad2(beijing.getUTCMonth() + 1)
  const day = pad2(beijing.getUTCDate())
  const hour = pad2(beijing.getUTCHours())
  const minute = pad2(beijing.getUTCMinutes())
  return `${month}-${day} ${hour}:${minute}`
}

function stageLabel(stageId: StageId) {
  return stages.find((stage) => stage.id === stageId)?.label ?? ''
}

function shortStageLabel(stageId: StageId) {
  return stages.find((stage) => stage.id === stageId)?.shortLabel ?? ''
}

function stageTagClass(stageId: StageId) {
  return stages.find((stage) => stage.id === stageId)?.tagClass ?? 'bg-slate-100 text-slate-700'
}

function nodeStatusClass(nodeId: string) {
  const status = nodeStatusMap.value.get(nodeId)?.status
  if (status === 'ready') return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
  if (status === 'incomplete') return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
  return 'bg-rose-50 text-rose-700 ring-1 ring-rose-200'
}

function nodeStatusLabel(nodeId: string) {
  return nodeStatusMap.value.get(nodeId)?.label ?? '未评估'
}

function nodeStatusMessage(nodeId: string) {
  return nodeStatusMap.value.get(nodeId)?.message ?? '当前节点尚未评估。'
}

function previewToneClass(tone: PreviewTone = 'neutral') {
  if (tone === 'positive') return 'bg-emerald-50 text-emerald-700'
  if (tone === 'accent') return 'bg-sky-50 text-sky-700'
  if (tone === 'warning') return 'bg-amber-50 text-amber-700'
  return 'bg-slate-100 text-slate-700'
}

function nodePreview(nodeId: string) {
  return nodePreviewMap.value.get(nodeId) ?? null
}

function nodePreviewItems(nodeId: string, limit = 2) {
  return (nodePreview(nodeId)?.items ?? []).slice(0, limit)
}

function inputPortStateClass(nodeId: string) {
  if (!pendingConnectionFrom.value || pendingConnectionFrom.value === nodeId) return ''
  return validateConnection(pendingConnectionFrom.value, nodeId).ok ? 'is-connectable' : 'is-blocked'
}

function inputPortTitle(nodeId: string) {
  if (!pendingConnectionFrom.value || pendingConnectionFrom.value === nodeId) {
    return '输入端口'
  }
  const validation = validateConnection(pendingConnectionFrom.value, nodeId)
  return validation.ok ? '点击完成连接' : validation.message
}

function summarizeNode(node: CanvasNode) {
  const fields = findModuleById(node.moduleId)?.fields ?? node.fields
  return fields
    .slice(0, 3)
    .map((field) => {
      const value = node.values[field.key]
      return value ? `${field.label}: ${value}` : ''
    })
    .filter(Boolean)
}

function addLog(kind: string, message: string) {
  logCounter.value += 1
  logs.value.unshift({
    id: logCounter.value,
    kind,
    time: nowTime(),
    message,
  })
}

function findModuleById(moduleId: string) {
  return moduleGroups.flatMap((group) => group.modules).find((module) => module.id === moduleId) ?? null
}

function findTemplateById(templateId: string) {
  return canvasTemplates.find((template) => template.id === templateId) ?? null
}

function localDraftKey(projectId?: string | null) {
  return `medicode:clinical-model-builder:draft:${projectId || 'global'}`
}

function startEditingWorkflowName() {
  workflowNameDraft.value = workflowName.value.trim()
  isEditingWorkflowName.value = true
  void nextTick(() => {
    workflowNameInputRef.value?.focus()
    workflowNameInputRef.value?.select()
  })
}

function finishEditingWorkflowName() {
  const nextName = workflowNameDraft.value.trim()
  workflowName.value = nextName || 'Untitled'
  isEditingWorkflowName.value = false
}

function cancelEditingWorkflowName() {
  isEditingWorkflowName.value = false
  workflowNameDraft.value = ''
}

function serializeCanvasState(): WorkflowDraftPayload {
  return {
    projectId: selectedProjectId.value || null,
    workflowName: workflowName.value,
    nodes: canvasNodes.value.map((node) => ({ ...node, values: { ...node.values } })),
    connections: connections.value.map((connection) => ({ ...connection })),
  }
}

function applyWorkflowState(payload: {
  nodes: Array<{
    id: string
    moduleId?: string
    module_id?: string
    label: string
    description?: string | null
    stageId?: string
    stage_id?: string
    values: Record<string, string>
    x: number
    y: number
    order: number
  }>
  connections: Array<{
    id: string
    fromNodeId?: string
    from_node_id?: string
    toNodeId?: string
    to_node_id?: string
    outputPortId?: 'train' | 'test' | null
    output_port_id?: 'train' | 'test' | null
  }>
  workflowName?: string | null
}) {
  canvasNodes.value = payload.nodes.map((node) => ({
    id: node.id,
    moduleId: node.moduleId ?? node.module_id ?? '',
    label: node.label,
    description: node.description ?? findModuleById(node.moduleId ?? node.module_id ?? '')?.description ?? '',
    stageId: (findModuleById(node.moduleId ?? node.module_id ?? '')?.stageId ?? node.stageId ?? node.stage_id ?? 'data-preparation') as StageId,
    fields: findModuleById(node.moduleId ?? node.module_id ?? '')?.fields ?? [],
    values: { ...(node.values ?? {}) },
    x: Number(node.x ?? 72),
    y: Number(node.y ?? 70),
    order: Number(node.order ?? 1),
  }))
  connections.value = payload.connections.map((connection) => ({
    id: connection.id,
    fromNodeId: connection.fromNodeId ?? connection.from_node_id ?? '',
    toNodeId: connection.toNodeId ?? connection.to_node_id ?? '',
    outputPortId: connection.outputPortId ?? connection.output_port_id ?? null,
  }))
  selectedNodeIds.value = []
  selectedNodeId.value = canvasNodes.value[0]?.id ?? null
  selectedConnectionId.value = null
  pendingConnectionFrom.value = null
  pendingConnectionPortId.value = null
  selectionRect.value = null
  workflowName.value = payload.workflowName || workflowName.value
}

function saveDraftToLocal() {
  if (isRestoringDraft.value || typeof window === 'undefined') return
  const key = localDraftKey(selectedProjectId.value || null)
  window.localStorage.setItem(key, JSON.stringify(serializeCanvasState()))
}

async function saveWorkflowToBackend() {
  if (!selectedProjectId.value || isSavingWorkflow.value) return
  isSavingWorkflow.value = true
  try {
    const nodes = canvasNodes.value.map((n, i) => ({
      id: n.id,
      module_id: n.moduleId,
      label: n.label,
      description: n.description || null,
      stage_id: findModuleById(n.moduleId)?.stageId ?? n.stageId,
      values: { ...n.values },
      x: n.x,
      y: n.y,
      order: n.order ?? i,
    }))
    const conns = connections.value.map((c) => ({
      id: c.id,
      from_node_id: c.fromNodeId,
      to_node_id: c.toNodeId,
      output_port_id: c.outputPortId || null,
    }))

    if (savedWorkflowId.value) {
      await updateClinicalWorkflow(savedWorkflowId.value, {
        name: workflowName.value,
        nodes,
        connections: conns,
      })
    } else {
      const res = await saveClinicalWorkflow({
        project_id: selectedProjectId.value,
        name: workflowName.value,
        workflow_kind: 'clinical_prediction',
        nodes,
        connections: conns,
      })
      savedWorkflowId.value = res.id
    }
    if (savedWorkflowId.value) {
      await router.replace({
        name: 'ClinicalModelBuilder',
        query: {
          ...route.query,
          projectId: selectedProjectId.value,
          workflowId: savedWorkflowId.value,
        },
      })
    }
    notificationStore.success('流程已保存')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '保存失败'
    notificationStore.error('保存失败', msg)
  } finally {
    isSavingWorkflow.value = false
  }
}

async function loadWorkflowFromBackend(workflowId: string) {
  const normalizedId = String(workflowId || '').trim()
  if (!normalizedId) return
  try {
    const detail = await getClinicalWorkflow(normalizedId)
    savedWorkflowId.value = detail.id
    applyWorkflowState({
      nodes: detail.nodes as any,
      connections: detail.connections as any,
      workflowName: detail.name,
    })
    notificationStore.success('已加载保存流程', detail.name || 'workflow')
  } catch (error: any) {
    notificationStore.error('流程加载失败', error?.response?.data?.detail || '请稍后重试。')
  }
}

function restoreDraftFromLocal(projectId?: string | null) {
  if (typeof window === 'undefined') return false
  const key = localDraftKey(projectId || null)
  const raw = window.localStorage.getItem(key)
  if (!raw) return false

  try {
    isRestoringDraft.value = true
    const parsed = JSON.parse(raw) as WorkflowDraftPayload
    applyWorkflowState(parsed)
    return true
  } catch {
    window.localStorage.removeItem(key)
    return false
  } finally {
    isRestoringDraft.value = false
  }
}

async function loadDatasetsForProject(projectId: string) {
  if (!projectId) {
    datasetOptions.value = []
    selectedDatasetId.value = ''
    return
  }
  loadingDatasets.value = true
  try {
    datasetOptions.value = await getDatasets(projectId)
    if (!datasetOptions.value.some((item) => item.id === selectedDatasetId.value)) {
      selectedDatasetId.value = datasetOptions.value[0]?.id || ''
    }
  } catch (error: any) {
    datasetOptions.value = []
    selectedDatasetId.value = ''
    notificationStore.error('数据集列表加载失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    loadingDatasets.value = false
  }
}

async function refreshPipelineRuns() {
  if (!selectedProjectId.value) {
    pipelineRuns.value = []
    activeRunId.value = null
    activeRunDetail.value = null
    return
  }
  try {
    pipelineRuns.value = await listClinicalPipelineRuns(selectedProjectId.value)
    if (!pipelineRuns.value.some((item) => item.run_id === activeRunId.value)) {
      activeRunId.value = pipelineRuns.value[0]?.run_id || null
    }
  } catch (error: any) {
    pipelineRuns.value = []
    activeRunId.value = null
    activeRunDetail.value = null
    notificationStore.error('运行记录加载失败', error?.response?.data?.detail || '请稍后重试。')
  }
}

async function loadActiveRunDetail(runId: string) {
  try {
    activeRunDetail.value = await getClinicalPipelineRun(runId)
  } catch (error: any) {
    activeRunDetail.value = null
    notificationStore.error('运行详情加载失败', error?.response?.data?.detail || '请稍后重试。')
  }
}

async function loadSelectedNodeRunDetail(nodeId: string) {
  if (!nodeId) {
    selectedNodeRunDetail.value = null
    return
  }
  isLoadingRunNode.value = true
  try {
    const candidateRunIds = [
      activeRunId.value,
      ...pipelineRuns.value.map((item) => item.run_id),
    ].filter((runId, index, array): runId is string => Boolean(runId) && array.indexOf(runId) === index)

    selectedNodeRunDetail.value = null
    for (const runId of candidateRunIds) {
      try {
        const detail = await getClinicalPipelineRunNode(runId, nodeId)
        selectedNodeRunDetail.value = detail
        break
      } catch (error: any) {
        if (error?.response?.status && error.response.status !== 404) {
          throw error
        }
      }
    }
  } catch {
    selectedNodeRunDetail.value = null
  } finally {
    isLoadingRunNode.value = false
  }
}

async function loadProjects() {
  const result = (await getProjects()) as ProjectOption[]
  projects.value = result.map((item) => ({ id: item.id, name: item.name }))
  if (!selectedProjectId.value && projects.value[0]?.id) {
    selectedProjectId.value = projects.value[0].id
  }
}

function inferWorkflowTemplateKind(
  nodes: CanvasNode[] = canvasNodes.value,
) {
  const hasCox = nodes.some((node) => node.moduleId === 'cox-model')
  if (hasCox) return 'survival' as const
  return 'binary' as const
}

function getFieldMappingNode() {
  return canvasNodes.value.find((node) => node.moduleId === 'field-mapping') ?? null
}

async function ensureDatasetSummary() {
  if (!selectedDatasetId.value) return null
  if (datasetSummary.value) {
    return datasetSummary.value
  }
  datasetSummary.value = await getDatasetSummary(selectedDatasetId.value)
  return datasetSummary.value
}

function formatResultValue(value: unknown) {
  if (value == null || value === '') return '-'
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function plotKey(plot: Record<string, any>) {
  return plot.name || plot.filename || `${plot.media_type || 'plot'}-${plot.content_base64 ? plot.content_base64.slice(0, 16) : 'preview'}`
}

function plotTitle(plot: Record<string, any>) {
  return plot.name || plot.filename || '图形结果'
}

function plotImageSrc(plot: Record<string, any>) {
  const mediaType = plot.media_type || 'image/png'
  return `data:${mediaType};base64,${plot.content_base64 || ''}`
}

function asLassoPlotPayload(plot: Record<string, any>): LassoPlotPayload | null {
  if (!plot?.content_base64) return null
  return {
    name: String(plot.name || plot.filename || 'LASSO 图形'),
    filename: String(plot.filename || `${plotKey(plot)}.png`),
    media_type: String(plot.media_type || 'image/png'),
    content_base64: String(plot.content_base64 || ''),
    vector_pdf_filename: plot.vector_pdf_filename ? String(plot.vector_pdf_filename) : null,
    vector_pdf_base64: plot.vector_pdf_base64 ? String(plot.vector_pdf_base64) : null,
  }
}

function triggerBlobDownload(url: string, filename: string) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
}

function base64ToBlob(base64: string, mediaType: string) {
  const binary = window.atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Blob([bytes], { type: mediaType })
}

function downloadTableAsCsv(table: Record<string, any>) {
  const columns = tableColumns(table)
  const rows = tableRows(table)
  if (!columns.length) return
  const csvLines = [columns.join(',')]
  for (const row of rows) {
    csvLines.push(row.map((cell: unknown) => {
      const value = formatResultValue(cell)
      return /[,"\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value
    }).join(','))
  }
  const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  triggerBlobDownload(url, `${tableTitle(table)}.csv`)
  window.URL.revokeObjectURL(url)
}

function downloadNodePlotPng(plot: Record<string, any>) {
  const payload = asLassoPlotPayload(plot)
  if (!payload) {
    notificationStore.error('下载失败', '当前图形缺少可下载内容。')
    return
  }
  triggerBlobDownload(plotImageSrc(payload), payload.filename)
}

function summaryEntries(payload?: Record<string, unknown> | null) {
  return Object.entries(payload || {})
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => ({ key, value: formatResultValue(value) }))
}

function latestNodeResult(nodeId: string) {
  return latestRunNodeMap.value.get(nodeId) ?? null
}

function nodeResultTable(nodeId: string, tableName: string) {
  const tables = latestNodeResult(nodeId)?.output_tables
  if (!Array.isArray(tables)) return null
  return tables.find((table: any) => table?.name === tableName) ?? null
}

	function tableRowObjects(table: any): Record<string, unknown>[] {
	  const columns = Array.isArray(table?.columns) ? table.columns.map((item: unknown) => String(item)) : []
	  const rows = Array.isArray(table?.rows) ? table.rows : []
	  if (!columns.length || !rows.length) return []
	  return rows
    .map((row: unknown) => {
      if (Array.isArray(row)) {
        return Object.fromEntries(columns.map((column: string, index: number) => [column, row[index]]))
      }
      if (row && typeof row === 'object') {
        return Object.fromEntries(columns.map((column: string) => [column, (row as Record<string, unknown>)[column]]))
      }
      return null
    })
    .filter((row: Record<string, unknown> | null): row is Record<string, unknown> => Boolean(row))
}

function tableRowObject(table: any, preferredDataset?: string) {
  const mappedRows = tableRowObjects(table)
  if (!mappedRows.length) return null
  if (preferredDataset) {
    const matched = mappedRows.find((row: Record<string, unknown>) => String(row.dataset || row.evaluation_dataset || '') === preferredDataset)
    if (matched) return matched
  }
  return mappedRows[0]
}

function nodeMetricRow(nodeId: string, tableNames: string[]) {
  for (const tableName of tableNames) {
    const table = nodeResultTable(nodeId, tableName)
    const preferred = tableRowObject(table, '测试集')
    if (preferred) return preferred
  }
  return null
}

function formatPreviewMetric(value: unknown, digits = 3) {
  if (value === null || value === undefined || value === '') return 'NA'
  const num = Number(value)
  if (Number.isFinite(num)) {
    return num.toFixed(digits).replace(/\.?0+$/, '')
  }
  return String(value)
}

function latestNodeSummary(nodeId: string) {
  return latestNodeResult(nodeId)?.output_summary ?? null
}

function previewMetricValue(value: unknown, fallback = '待运行', digits = 3) {
  if (value === null || value === undefined || value === '') return fallback
  return formatPreviewMetric(value, digits)
}

function previewMetricTone(value: unknown): PreviewTone {
  if (value === null || value === undefined || value === '') return 'neutral'
  const num = Number(value)
  return Number.isFinite(num) ? 'positive' : 'neutral'
}

function previewPValueTone(value: unknown): PreviewTone {
  const num = Number(value)
  if (!Number.isFinite(num)) return 'neutral'
  return num >= 0.05 ? 'positive' : 'warning'
}

function shortRunId(runId?: string | null) {
  if (!runId) return '-'
  return runId.slice(0, 8)
}

function compactTextSummaryEntries(detail: ClinicalPipelineNodeDetailResponse) {
  const outputItems = summaryEntries(detail.output_summary).map((item) => ({
    ...item,
    scope: 'output',
    label: `输出 · ${item.key}`,
  }))
  if (detail.module_id === 'roc') {
    return outputItems.slice(0, 8)
  }
  const inputItems = summaryEntries(detail.input_snapshot).map((item) => ({
    ...item,
    scope: 'input',
    label: `输入 · ${item.key}`,
  }))
  return [...outputItems, ...inputItems].slice(0, 8)
}

function normalizedNodeLogs(detail?: ClinicalPipelineNodeDetailResponse | null) {
  const raw: unknown = detail?.logs
  if (!raw) return []
  if (Array.isArray(raw)) {
    const normalized = raw
      .map((item) => {
        const text = typeof item === 'string' ? item : formatResultValue(item)
        return String(text).trim()
      })
      .filter(Boolean)
    if (normalized.length > 1 && normalized.every((item) => item.length === 1)) {
      return [normalized.join('')]
    }
    return normalized
  }
  if (typeof raw === 'string') {
    const text = String(raw).trim()
    return text ? [text] : []
  }
  return [formatResultValue(raw)]
}

function datasetShapeText(summary?: DatasetSummaryResponse | null) {
  if (!summary) return '未加载'
  return `${summary.total_rows} 行 × ${summary.total_columns} 列`
}

function tableKey(table: Record<string, any>) {
  if (table.name || table.title) return table.name || table.title
  const columns = tableColumns(table)
  return `${columns.join('|')}-${tableRowCount(table)}`
}

function tableTitle(table: Record<string, any>) {
  return table.name || table.title || '结果表'
}

type DisplayTablePayload = {
  columns: string[]
  rows: unknown[][]
}

const displayTableCache = new WeakMap<Record<string, any>, DisplayTablePayload>()

function isDcaCurveTable(table: Record<string, any>) {
  const name = String(table?.name || table?.title || '')
  return name === 'dca_curve'
}

function buildDcaCurveWideTable(table: Record<string, any>): DisplayTablePayload | null {
  const rawRows = tableRowObjects(table)
  if (!rawRows.length) return null
  if (!rawRows.some((row) => 'evaluation_dataset' in row)) return null

  type CurveRow = {
    threshold: unknown
    model_net_benefit: unknown
    treat_all_net_benefit: unknown
    treat_none_net_benefit: unknown
    evaluation_dataset: unknown
  }

  const grouped = new Map<string, { thresholdNum: number; threshold: unknown; train?: CurveRow; test?: CurveRow }>()
  for (const row of rawRows as Record<string, unknown>[]) {
    const threshold = row.threshold
    const key = String(threshold)
    const thresholdNum = Number(threshold)
    const dataset = String(row.evaluation_dataset || row.dataset || '')
    const entry = grouped.get(key) || { thresholdNum: Number.isFinite(thresholdNum) ? thresholdNum : Number.POSITIVE_INFINITY, threshold }
    const curveRow: CurveRow = {
      threshold: row.threshold,
      model_net_benefit: row.model_net_benefit,
      treat_all_net_benefit: row.treat_all_net_benefit,
      treat_none_net_benefit: row.treat_none_net_benefit,
      evaluation_dataset: row.evaluation_dataset,
    }
    if (dataset.includes('测试')) {
      entry.test = curveRow
    } else {
      entry.train = curveRow
    }
    grouped.set(key, entry)
  }

  const hasTest = Array.from(grouped.values()).some((item) => Boolean(item.test))
  const columns = hasTest
    ? ['阈值', '训练-模型', '训练-全治', '训练-不治', '测试-模型', '测试-全治', '测试-不治']
    : ['阈值', '训练-模型', '训练-全治', '训练-不治']

  const rows = Array.from(grouped.values())
    .sort((a, b) => a.thresholdNum - b.thresholdNum)
    .map((entry) => {
      const train = entry.train
      const test = entry.test
      const base = [entry.threshold, train?.model_net_benefit, train?.treat_all_net_benefit, train?.treat_none_net_benefit]
      if (!hasTest) return base
      return [...base, test?.model_net_benefit, test?.treat_all_net_benefit, test?.treat_none_net_benefit]
    })

  return { columns, rows }
}

function displayTablePayload(table: Record<string, any>): DisplayTablePayload {
  const cached = displayTableCache.get(table)
  if (cached) return cached

  const payload =
    isDcaCurveTable(table)
      ? (buildDcaCurveWideTable(table) ?? { columns: tableColumns(table), rows: tableRows(table) })
      : { columns: tableColumns(table), rows: tableRows(table) }
  displayTableCache.set(table, payload)
  return payload
}

function displayTableColumns(table: Record<string, any>) {
  return displayTablePayload(table).columns
}

function displayTableRows(table: Record<string, any>) {
  return displayTablePayload(table).rows
}

function displayTableRowCount(table: Record<string, any>) {
  return displayTableRows(table).length
}

function tableColumns(table: Record<string, any>) {
  return Array.isArray(table.columns) ? table.columns.map((item: unknown) => String(item)) : []
}

function tableRows(table: Record<string, any>) {
  const columns = tableColumns(table)
  if (!Array.isArray(table.rows)) return []
  return table.rows.map((row: unknown) => {
    if (Array.isArray(row)) {
      return row
    }
    if (row && typeof row === 'object') {
      return columns.map((column) => (row as Record<string, unknown>)[column])
    }
    return [row]
  })
}

function tableRowCount(table: Record<string, any>) {
  return Array.isArray(table.rows) ? table.rows.length : 0
}

function tableBodyContainerClass(table: Record<string, any>) {
  if (selectedNodeModuleId.value === 'dca' && isDcaCurveTable(table)) {
    return 'max-h-[440px] overflow-auto overscroll-contain'
  }
  return 'overflow-x-auto'
}

function tableHeadClass(table: Record<string, any>) {
  const base = 'bg-slate-50/80 text-[11px] uppercase tracking-[0.14em] text-slate-500'
  if (selectedNodeModuleId.value === 'dca' && isDcaCurveTable(table)) {
    return `${base} sticky top-0 z-10 backdrop-blur`
  }
  return base
}

function tableHeaderCellClass(table: Record<string, any>) {
  if (selectedNodeModuleId.value === 'dca' && isDcaCurveTable(table)) {
    return 'whitespace-nowrap px-4 py-2.5 font-semibold'
  }
  return 'whitespace-nowrap px-4 py-3 font-semibold'
}

function tableBodyCellClass(table: Record<string, any>) {
  if (selectedNodeModuleId.value === 'dca' && isDcaCurveTable(table)) {
    return 'whitespace-nowrap px-4 py-2'
  }
  return 'whitespace-nowrap px-4 py-3'
}

async function updateResultPanelHeight() {
  await nextTick()
  const heights = [
    resultSummaryPanelRef.value?.offsetHeight || 0,
    resultTablesPanelRef.value?.offsetHeight || 0,
    resultPlotsPanelRef.value?.offsetHeight || 0,
    resultDownloadsPanelRef.value?.offsetHeight || 0,
  ].filter((value) => value > 0)
  resultPanelHeight.value = heights.length ? Math.max(...heights) : 0
}

function runStatusLabel(status?: string | null) {
  if (status === 'completed') return '已完成'
  if (status === 'configured') return '已配置'
  if (status === 'unsupported') return '未接入'
  if (status === 'skipped') return '已跳过'
  if (status === 'failed') return '失败'
  return status || '未知'
}

function runStatusClass(status?: string | null) {
  if (status === 'completed') return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
  if (status === 'configured') return 'bg-sky-50 text-sky-700 ring-1 ring-sky-200'
  if (status === 'skipped') return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
  if (status === 'failed') return 'bg-rose-50 text-rose-700 ring-1 ring-rose-200'
  return 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
}

function nodeExecutionCardClass(nodeId: string) {
  const result = latestRunNodeMap.value.get(nodeId)
  if (!result) return 'border-slate-200'
  if (result.status === 'completed' || result.status === 'configured') return 'border-emerald-300 shadow-[0_0_0_1px_rgba(52,211,153,0.08),0_22px_48px_-30px_rgba(16,185,129,0.28)]'
  if (result.status === 'failed') return 'border-rose-300 shadow-[0_0_0_1px_rgba(251,113,133,0.08),0_22px_48px_-30px_rgba(244,63,94,0.24)]'
  return 'border-slate-200'
}

function hasNodeRunResult(nodeId: string) {
  return latestRunNodeMap.value.has(nodeId)
}

function isNodeRunning(nodeId: string) {
  return runningNodeIds.value.includes(nodeId)
}

function nodeRunActionTooltip(nodeId: string) {
  if (isNodeRunning(nodeId)) return '正在运行'
  if (!selectedProjectId.value || !selectedDatasetId.value) return '先选择项目和数据集，再运行当前节点。'
  return '运行节点'
}

function nodeLastRunTime(nodeId: string) {
  const nodeResult = latestRunNodeMap.value.get(nodeId) ?? null
  if (!nodeResult || !(nodeResult as any).created_at) {
    if (!activeRunDetail.value?.completed_at && !activeRunDetail.value?.created_at) return ''
  }
  const timestamp = (nodeResult as any)?.created_at || activeRunDetail.value?.completed_at || activeRunDetail.value?.created_at
  if (!timestamp) return ''
  return formatBeijingCompact(String(timestamp))
}

function openNodeSettings(nodeId: string) {
  selectNode(nodeId)
  isSettingsDialogOpen.value = true
}

async function openNodeResults(nodeId: string) {
  selectNode(nodeId)
  activeResultTab.value = 'summary'
  isResultDialogOpen.value = true
  if (pipelineRuns.value.length) {
    await loadSelectedNodeRunDetail(nodeId)
  }
}

function closeNodeDialogs() {
  isSettingsDialogOpen.value = false
  isResultDialogOpen.value = false
}

async function runNodeOnly(node: CanvasNode) {
  const subgraph = collectUpstreamSubgraph(node.id)
  await executeWorkflowRun({
    nodes: subgraph.nodes,
    runConnections: subgraph.connections,
    runLabel: `节点”${node.label}”`,
    successMessage: `已完成节点”${node.label}”及其必要上游的运行。`,
    focusNodeId: node.id,
    skipCompleted: true,
  })
}

async function executeWorkflowRun(options: {
  nodes: CanvasNode[]
  runConnections?: NodeConnection[]
  runLabel: string
  successMessage: string
  focusNodeId?: string
  skipCompleted?: boolean
}) {
  if (isRunningPipeline.value) {
    notificationStore.warning('任务仍在运行', '请等待当前节点执行结束后再发起新的运行。')
    return
  }

  if (!selectedProjectId.value || !selectedDatasetId.value) {
    notificationStore.warning('缺少运行参数', '请先选择项目和数据集。')
    return
  }

  const runConnections = options.runConnections ?? connections.value
  const runNodes = _sortNodesForRun(options.nodes)
  const subgraphNodeIds = new Set(runNodes.map((node) => node.id))
  const filteredConnections = runConnections.filter(
    (connection) => subgraphNodeIds.has(connection.fromNodeId) && subgraphNodeIds.has(connection.toNodeId),
  )

  isRunningPipeline.value = true
  runningNodeIds.value = options.focusNodeId ? [options.focusNodeId] : runNodes.map((node) => node.id)
  try {
    const summary = await ensureDatasetSummary()
    const fieldMapping = runNodes.find((node) => node.moduleId === 'field-mapping') ?? null
    const templateKind = inferWorkflowTemplateKind(runNodes)
    const outcomeFallbackNode = [...runNodes].reverse().find((node) => `${node.values.outcomeField || ''}`.trim().length > 0) ?? null
    const timeFallbackNode = [...runNodes].reverse().find((node) => `${node.values.timeField || ''}`.trim().length > 0) ?? null
    const outcomeVariable = (outcomeFallbackNode?.values.outcomeField || fieldMapping?.values.outcomeField || '').trim() || null
    const timeVariable = templateKind === 'survival'
      ? ((timeFallbackNode?.values.timeField || fieldMapping?.values.timeField || '').trim() || null)
      : null
    const eventVariable = templateKind === 'survival' ? outcomeVariable : null

    const availableColumns = new Set((summary?.columns || []).map((column) => column.name))
    if (outcomeVariable && !availableColumns.has(outcomeVariable)) {
      notificationStore.warning('结局字段不存在', `当前选择的结局/事件字段“${outcomeVariable}”不在数据集中，请在字段映射或模型/验证节点中重新选择。`)
      return
    }
    if (templateKind === 'survival' && timeVariable && !availableColumns.has(timeVariable)) {
      notificationStore.warning('时间字段不存在', `当前选择的时间字段“${timeVariable}”不在数据集中，请在字段映射或 Cox/RCS 节点中重新选择。`)
      return
    }

    const fallbackPredictors = (summary?.columns || [])
      .map((column) => column.name)
      .filter((name) => !new Set([outcomeVariable, timeVariable].filter(Boolean) as string[]).has(name))
    const predictorVariables = buildRunPredictorVariables(fieldMapping, summary).length
      ? buildRunPredictorVariables(fieldMapping, summary)
      : fallbackPredictors

    if (templateKind === 'binary') {
      const needsOutcomeModules = new Set([
        'univariate-screen',
        'lasso-selection',
        'rf-importance',
        'boruta-selection',
        'logistic-model',
        'xgboost',
        'random-forest',
        'roc',
        'calibration',
        'dca',
        'nomogram',
      ])
      const requiresBinaryOutcomeModules = new Set([
        'univariate-screen',
        'lasso-selection',
        'rf-importance',
        'boruta-selection',
        'logistic-model',
        'roc',
        'calibration',
        'dca',
        'nomogram',
      ])

      const needsOutcome = runNodes.some((node) => needsOutcomeModules.has(node.moduleId))
      const requiresBinaryOutcome = runNodes.some((node) => requiresBinaryOutcomeModules.has(node.moduleId))

      if (needsOutcome && !outcomeVariable) {
        notificationStore.warning('缺少结局变量', '请先在“字段映射”节点填写结局字段，或在模型节点里选择结局变量。')
        return
      }
      const outcomeColumn = summary?.columns.find((column) => column.name === outcomeVariable) ?? null
      const isBinaryOutcome = outcomeColumn
        ? (
            outcomeColumn.kind === 'boolean' ||
            ((outcomeColumn.kind === 'categorical' || outcomeColumn.kind === 'numeric') && outcomeColumn.unique_count === 2)
          )
        : true
      if (requiresBinaryOutcome && outcomeVariable && !isBinaryOutcome) {
        notificationStore.error('结局类型不匹配', `当前流程包含特征筛选或 Logistic 相关节点，但结局变量“${outcomeVariable}”不是二分类。请更换为二分类结局，或移除这些节点后再运行。`)
        return
      }
    }

    if (templateKind === 'survival' && (!timeVariable || !eventVariable)) {
      notificationStore.warning('缺少生存结局映射', '请在“字段映射”节点填写时间字段与事件字段（结局字段），或在 Cox 节点里选择时间/事件变量。')
      return
    }

    const result = await runClinicalPipeline({
      project_id: selectedProjectId.value,
      dataset_id: selectedDatasetId.value,
      template_kind: templateKind,
      outcome_variable: templateKind === 'binary' ? outcomeVariable : null,
      time_variable: templateKind === 'survival' ? timeVariable : null,
      event_variable: templateKind === 'survival' ? eventVariable : null,
      predictor_variables: predictorVariables,
      alpha: 0.05,
      nfolds: 10,
      workflow_nodes: runNodes.map((node) => ({
        id: node.id,
        module_id: node.moduleId,
        label: node.label,
        stage_id: node.stageId,
        values: node.values,
      })),
      workflow_connections: filteredConnections.map((connection) => ({
        id: connection.id,
        from_node_id: connection.fromNodeId,
        to_node_id: connection.toNodeId,
        output_port_id: connection.outputPortId || null,
      })),
      skip_completed: options.skipCompleted ?? false,
    })

    await refreshPipelineRuns()
    if (result.run_id) {
      activeRunId.value = result.run_id
      await loadActiveRunDetail(result.run_id)
      if (options.focusNodeId) {
        selectedNodeId.value = options.focusNodeId
        await loadSelectedNodeRunDetail(options.focusNodeId)
      } else if (selectedNodeId.value) {
        await loadSelectedNodeRunDetail(selectedNodeId.value)
      }
    }
    const incrementalLog = (result.logs || []).find((item) => String(item).includes('增量运行'))
    if (incrementalLog) addLog('cache', String(incrementalLog))
    addLog('run', `${options.runLabel}已运行。`)
    notificationStore.success('运行完成', options.successMessage)
  } catch (error: any) {
    notificationStore.error('运行失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    isRunningPipeline.value = false
    runningNodeIds.value = []
  }
}

async function downloadNodePlotPdf(plot: Record<string, any>) {
  if (!selectedDatasetId.value) return
  const payload = asLassoPlotPayload(plot)
  if (!payload) {
    notificationStore.error('PDF 下载失败', '当前图形缺少可导出的内容。')
    return
  }
  if (!canDownloadPremiumPdf.value) {
    notificationStore.warning('请升级套餐', '图形 PDF 导出为付费会员功能，PNG 下载仍可免费使用。')
    return
  }

  downloadingPlotKey.value = plotKey(plot)
  try {
    if (selectedNodeModuleId.value === 'nomogram' && payload.vector_pdf_base64) {
      const blob = base64ToBlob(payload.vector_pdf_base64, 'application/pdf')
      const url = window.URL.createObjectURL(blob)
      triggerBlobDownload(url, payload.vector_pdf_filename || payload.filename.replace(/\.[^.]+$/, '') + '.pdf')
      window.URL.revokeObjectURL(url)
    } else {
      const pdf = await downloadLassoPlotPdf({
        dataset_id: selectedDatasetId.value,
        plot: payload,
      })
      const url = window.URL.createObjectURL(pdf.blob)
      triggerBlobDownload(url, payload.filename.replace(/\.[^.]+$/, '') + '.pdf')
      window.URL.revokeObjectURL(url)
      if (authStore.user && pdf.remainingResources !== null) {
        authStore.user.tokenBalance = pdf.remainingResources
      }
    }
  } catch (error: any) {
    console.error('Failed to download pipeline lasso plot pdf', error)
    notificationStore.error('PDF 下载失败', error?.response?.data?.detail || '请稍后重试。')
  } finally {
    downloadingPlotKey.value = ''
  }
}

function getIncomingConnections(nodeId: string) {
  return connections.value.filter((item) => item.toNodeId === nodeId)
}

function getIncomingNodes(nodeId: string) {
  return getIncomingConnections(nodeId)
    .map((connection) => canvasNodes.value.find((node) => node.id === connection.fromNodeId))
    .filter((node): node is CanvasNode => Boolean(node))
}

function estimateSampleSize(node: CanvasNode) {
  const upstream = getIncomingNodes(node.id)
  const upstreamModules = upstream.map((item) => item.moduleId)
  const baseRows = Math.max(datasetSummary.value?.total_rows || 1000, 0)

  if (node.moduleId === 'missing-value') {
    if (node.values.method === '删除缺失') return Math.max(1, Math.round(baseRows * 0.912))
    if (node.values.method === '均值/众数插补') return Math.max(1, Math.round(baseRows * 0.968))
    return Math.max(1, Math.round(baseRows * 0.992))
  }

  if (upstreamModules.includes('missing-value')) {
    const missingNode = upstream.find((item) => item.moduleId === 'missing-value')
    if (missingNode) return estimateSampleSize(missingNode)
  }

  return baseRows
}

function parseRatio(ratio: string) {
  const parts = ratio
    .split(':')
    .map((part) => Number(part.trim()))
    .filter((value) => Number.isFinite(value) && value > 0)

  return parts.length ? parts : [7, 3]
}

function parsePredictorFields(raw: string) {
  return raw
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function serializePredictorFields(values: string[]) {
  return Array.from(new Set(values.map((item) => item.trim()).filter(Boolean))).join(', ')
}

function toggleFieldMappingPredictor(column: string) {
  if (!selectedNode.value || selectedNode.value.moduleId !== 'field-mapping') return
  const current = parsePredictorFields(selectedNode.value.values.predictorFields || '')
  const next = current.includes(column)
    ? current.filter((item) => item !== column)
    : [...current, column]
  updateNodeValue(selectedNode.value.id, 'predictorFields', serializePredictorFields(next))
}

function selectAllFieldMappingPredictors() {
  if (!selectedNode.value || selectedNode.value.moduleId !== 'field-mapping') return
  updateNodeValue(selectedNode.value.id, 'predictorFields', serializePredictorFields(fieldMappingCandidateColumns.value))
}

function clearFieldMappingPredictors() {
  if (!selectedNode.value || selectedNode.value.moduleId !== 'field-mapping') return
  updateNodeValue(selectedNode.value.id, 'predictorFields', '')
}

function toggleModelPredictor(column: string) {
  if (!selectedNode.value) return
  if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return
  if (!showStandaloneModelPredictorPicker.value) return
  const current = parsePredictorFields(selectedNode.value.values.predictorFields || '')
  const next = current.includes(column)
    ? current.filter((item) => item !== column)
    : [...current, column]
  updateNodeValue(selectedNode.value.id, 'predictorFields', serializePredictorFields(next))
}

function selectAllModelPredictors() {
  if (!selectedNode.value) return
  if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return
  if (!showStandaloneModelPredictorPicker.value) return
  updateNodeValue(selectedNode.value.id, 'predictorFields', serializePredictorFields(modelPredictorCandidateColumns.value))
}

function clearModelPredictors() {
  if (!selectedNode.value) return
  if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return
  updateNodeValue(selectedNode.value.id, 'predictorFields', '')
}

function buildNodePreview(node: CanvasNode): NodePreviewMeta | null {
  const sampleSize = estimateSampleSize(node)
  const upstreamCount = getIncomingNodes(node.id).length

  switch (node.moduleId) {
    case 'field-mapping':
      {
        const selectedPredictors = parsePredictorFields(node.values.predictorFields || '')
      return {
        title: '数据概览',
        subtitle: '核心字段已被识别，后续节点会沿用这些映射。',
        items: [
          { label: 'ID', value: node.values.idField || 'patient_id', tone: 'accent' },
          { label: '结局', value: node.values.outcomeField || 'outcome', tone: 'positive' },
          { label: '时间', value: node.values.timeField || 'follow_up_days' },
          { label: '候选变量', value: selectedPredictors.length ? `${selectedPredictors.length} 项` : '未指定', tone: selectedPredictors.length ? 'positive' : 'warning' },
        ],
      }
      }
    case 'missing-value':
      return {
        title: '清洗后样本',
        subtitle: '预估缺失值处理后的有效样本量与保留规模。',
        items: [
          { label: '处理方式', value: node.values.method || '多重插补', tone: 'accent' },
          { label: '保留样本', value: `${sampleSize}`, tone: 'positive' },
          { label: '阈值', value: node.values.threshold || '0.20' },
        ],
      }
    case 'split': {
      const parts = parseRatio(node.values.ratio || '7:3')
      const total = parts.reduce((sum, value) => sum + value, 0)
      const counts = parts.map((part) => Math.round((sampleSize * part) / total))
      const modeField = node.values.sampling === '分层抽样'
        ? (node.values.stratifyField || '未设置')
        : node.values.sampling === '时间切分'
          ? (node.values.timeSplitField || '未设置')
          : '随机'
      return {
        title: '数据切分',
        subtitle: '按当前比例即时估算训练、测试和验证集样本量。',
        items: counts.length === 3
          ? [
              { label: '训练集', value: `${counts[0]}`, tone: 'positive' },
              { label: '测试集', value: `${counts[1]}`, tone: 'accent' },
              { label: '验证集', value: `${counts[2]}` },
              { label: '切分字段', value: modeField },
            ]
          : [
              { label: '训练集', value: `${counts[0]}`, tone: 'positive' },
              { label: '测试集', value: `${counts[1]}`, tone: 'accent' },
              { label: '抽样', value: node.values.sampling || '分层抽样' },
              { label: '切分字段', value: modeField },
            ],
      }
    }
    case 'encoding':
      return {
        title: '编码输出',
        subtitle: '分类变量编码会影响后续模型矩阵维度。',
        items: [
          { label: '方式', value: node.values.encoding || 'One-hot', tone: 'accent' },
          { label: '首列丢弃', value: node.values.dropFirst || '是' },
          { label: '预计展开', value: '18 列', tone: 'positive' },
        ],
      }
    case 'univariate-screen':
      return {
        title: '单因素筛选',
        subtitle: '候选变量将按阈值完成一轮快速预筛。',
        items: [
          { label: '阈值', value: node.values.rule || 'P < 0.10', tone: 'accent' },
          { label: '保留变量', value: node.values.rule === '仅展示不筛除' ? '18 项' : '7 项', tone: 'positive' },
          { label: '临床优先', value: node.values.keepClinical || '是' },
        ],
      }
    case 'vif':
      return {
        title: '共线性预警',
        subtitle: '预览高共线性变量数，提前暴露冗余风险。',
        items: [
          { label: 'VIF 阈值', value: node.values.cutoff || '5', tone: 'accent' },
          { label: '处理', value: '超阈值自动剔除', tone: 'warning' },
          { label: '输出', value: 'VIF 汇总 + 明细' },
        ],
      }
    case 'lasso-selection':
      return {
        title: 'LASSO 结果',
        subtitle: '即时预览交叉验证后预计保留的变量数量。',
        items: [
          { label: 'Lambda', value: node.values.criterion || 'lambda.1se', tone: 'accent' },
          { label: '折数', value: node.values.folds || '10' },
          { label: '入选变量', value: node.values.criterion === 'lambda.min' ? '8 项' : '5 项', tone: 'positive' },
        ],
      }
    case 'rf-importance':
      return {
        title: '随机森林筛选',
        subtitle: '按变量重要度排序，保留最有信息量的候选变量。',
        items: [
          { label: '树数量', value: node.values.trees || '500', tone: 'accent' },
          { label: '保留数', value: node.values.topN || '10' },
          { label: '输出', value: '重要度表 + 2 张图', tone: 'positive' },
        ],
      }
    case 'boruta-selection':
      return {
        title: 'Boruta 筛选',
        subtitle: '用影子特征做对照，确认真正稳定的变量。',
        items: [
          { label: '迭代次数', value: node.values.maxRuns || '100', tone: 'accent' },
          { label: '决策', value: 'Confirmed / Rejected' },
          { label: '输出', value: '统计表 + 2 张图', tone: 'positive' },
        ],
      }
    case 'feature-merge':
      return {
        title: '特征合并',
        subtitle: '汇总多条筛选分支，形成统一入模变量集。',
        items: [
          { label: '规则', value: node.values.mergeRule || '交集', tone: 'accent' },
          { label: '阈值', value: node.values.minVotes || '2' },
          { label: '输入', value: `${getIncomingNodes(node.id).length || 0} 条`, tone: 'positive' },
        ],
      }
    case 'rcs':
      return {
        title: '非线性项',
        subtitle: '限制性立方样条会自动扩展连续变量曲线效应。',
        items: [
          { label: '目标变量', value: node.values.target || 'age', tone: 'accent' },
          { label: '节点数', value: node.values.knots || '4' },
          { label: '新增特征', value: '3 项', tone: 'positive' },
        ],
      }
    case 'interaction':
      return {
        title: '交互项',
        subtitle: '交互项构建会增加模型解释维度。',
        items: [
          { label: '交互项', value: node.values.pair || 'age * treatment', tone: 'accent' },
          { label: '中心化', value: node.values.centering || '是' },
          { label: '新增项', value: '1 项', tone: 'positive' },
        ],
      }
    case 'logistic-model':
      {
        const metricRow = nodeMetricRow(node.id, ['logistic_performance'])
        const summary = latestNodeSummary(node.id)
        return {
          title: 'Logistic 模型',
          subtitle: metricRow ? `显示最近一次 ${String(metricRow.dataset || '模型')} 表现。` : '运行后显示 AUC、Accuracy、Recall、F1 与 H-L P。',
          items: [
            { label: 'AUC', value: previewMetricValue(metricRow?.auc), tone: previewMetricTone(metricRow?.auc) },
            { label: 'Accuracy', value: previewMetricValue(metricRow?.accuracy), tone: previewMetricTone(metricRow?.accuracy) },
            { label: 'Recall', value: previewMetricValue(metricRow?.sensitivity), tone: previewMetricTone(metricRow?.sensitivity) },
            { label: 'F1', value: previewMetricValue(metricRow?.f1), tone: previewMetricTone(metricRow?.f1) },
            { label: 'H-L P', value: previewMetricValue(metricRow?.hosmer_lemeshow_p_value ?? summary?.hosmer_lemeshow_p_value), tone: previewPValueTone(metricRow?.hosmer_lemeshow_p_value ?? summary?.hosmer_lemeshow_p_value) },
          ],
        }
      }
    case 'cox-model':
      {
        const summary = latestNodeSummary(node.id)
        return {
          title: 'Cox 模型',
          subtitle: summary ? '显示最近一次生存模型关键拟合指标。' : '运行后显示 C-index、PH 检验和事件规模。',
          items: [
            { label: 'C-index', value: previewMetricValue(summary?.concordance), tone: previewMetricTone(summary?.concordance) },
            { label: 'PH P', value: previewMetricValue(summary?.global_ph_p_value), tone: previewPValueTone(summary?.global_ph_p_value) },
            { label: '样本量', value: previewMetricValue(summary?.sample_size, `${sampleSize}`, 0), tone: 'accent' },
            { label: '事件数', value: previewMetricValue(summary?.event_count, '待运行', 0), tone: previewMetricTone(summary?.event_count) },
          ],
        }
      }
    case 'xgboost':
      {
        const metricRow = nodeMetricRow(node.id, ['xgboost_performance'])
        return {
          title: 'XGBoost 模型',
          subtitle: metricRow ? `显示最近一次 ${String(metricRow.dataset || '模型')} 表现。` : '运行后显示二分类模型核心性能指标。',
          items: [
            { label: 'AUC', value: previewMetricValue(metricRow?.auc), tone: previewMetricTone(metricRow?.auc) },
            { label: 'Accuracy', value: previewMetricValue(metricRow?.accuracy), tone: previewMetricTone(metricRow?.accuracy) },
            { label: 'Recall', value: previewMetricValue(metricRow?.sensitivity), tone: previewMetricTone(metricRow?.sensitivity) },
            { label: 'F1', value: previewMetricValue(metricRow?.f1), tone: previewMetricTone(metricRow?.f1) },
            { label: 'H-L P', value: previewMetricValue(metricRow?.hosmer_lemeshow_p_value), tone: previewPValueTone(metricRow?.hosmer_lemeshow_p_value) },
          ],
        }
      }
    case 'random-forest':
      {
        const metricRow = nodeMetricRow(node.id, ['random_forest_performance'])
        return {
          title: '随机森林模型',
          subtitle: metricRow ? `显示最近一次 ${String(metricRow.dataset || '模型')} 表现。` : '运行后显示二分类模型核心性能指标。',
          items: [
            { label: 'AUC', value: previewMetricValue(metricRow?.auc), tone: previewMetricTone(metricRow?.auc) },
            { label: 'Accuracy', value: previewMetricValue(metricRow?.accuracy), tone: previewMetricTone(metricRow?.accuracy) },
            { label: 'Recall', value: previewMetricValue(metricRow?.sensitivity), tone: previewMetricTone(metricRow?.sensitivity) },
            { label: 'F1', value: previewMetricValue(metricRow?.f1), tone: previewMetricTone(metricRow?.f1) },
            { label: 'H-L P', value: previewMetricValue(metricRow?.hosmer_lemeshow_p_value), tone: previewPValueTone(metricRow?.hosmer_lemeshow_p_value) },
          ],
        }
      }
    case 'model-comparison':
      return {
        title: '模型比较',
        subtitle: '多模型并联后，这里会预览当前领先方案。',
        items: [
          { label: '主指标', value: node.values.primaryMetric || '综合评分', tone: 'accent' },
          { label: '领先模型', value: 'XGBoost', tone: 'positive' },
          { label: '候选模型', value: `${Math.max(upstreamCount, 2)} 个` },
        ],
      }
    case 'roc':
      {
        const summary = latestNodeSummary(node.id)
        return {
          title: 'ROC / AUC',
          subtitle: summary ? '显示训练集与测试集的 ROC 对比结果。' : '运行后显示 AUC 与最佳阈值。',
          items: [
            { label: '训练集 AUC', value: previewMetricValue(summary?.train_auc), tone: previewMetricTone(summary?.train_auc) },
            { label: '测试集 AUC', value: previewMetricValue(summary?.test_auc), tone: previewMetricTone(summary?.test_auc) },
            { label: '训练集约登指数', value: previewMetricValue(summary?.train_youden_index), tone: previewMetricTone(summary?.train_youden_index) },
            { label: '测试集约登指数', value: previewMetricValue(summary?.test_youden_index), tone: previewMetricTone(summary?.test_youden_index) },
          ],
        }
      }
    case 'calibration':
      {
        const os = latestNodeSummary(node.id)
        return {
          title: '校准摘要',
          subtitle: os ? '显示训练集与测试集的校准结果。' : '运行后显示校准斜率、截距与 Brier。',
          items: [
            { label: '训练集 Slope', value: previewMetricValue(os?.train_slope), tone: previewMetricTone(os?.train_slope) },
            { label: '训练集 Brier', value: previewMetricValue(os?.train_brier), tone: previewMetricTone(os?.train_brier) },
            { label: '测试集 Slope', value: previewMetricValue(os?.test_slope), tone: previewMetricTone(os?.test_slope) },
            { label: '测试集 Brier', value: previewMetricValue(os?.test_brier), tone: previewMetricTone(os?.test_brier) },
          ],
        }
      }
    case 'dca':
      {
        const summary = nodeMetricRow(node.id, ['dca_summary'])
        const rangeText = summary
          ? `${previewMetricValue(summary.threshold_min, 'NA')} - ${previewMetricValue(summary.threshold_max, 'NA')}`
          : (node.values.range || '待运行')
        return {
          title: 'DCA 概览',
          subtitle: summary ? `显示最近一次 ${String(summary.evaluation_dataset || '评估集')} DCA 范围。` : '运行后显示 DCA 阈值区间与步长。',
          items: [
            { label: '阈值范围', value: rangeText, tone: 'accent' },
            { label: '步长', value: previewMetricValue(summary?.threshold_step, node.values.step || '待运行'), tone: previewMetricTone(summary?.threshold_step) },
            { label: '评估集', value: previewMetricValue(summary?.evaluation_dataset), tone: 'positive' },
          ],
        }
      }
    case 'bootstrap':
      {
        const summary = latestNodeSummary(node.id)
        return {
          title: 'Bootstrap 结果',
          subtitle: summary ? '显示最近一次 Bootstrap 校正结果。' : '运行后显示 optimism 与校正后指标。',
          items: [
            { label: '指标', value: previewMetricValue(summary?.metric_label, '待运行'), tone: 'accent' },
            { label: 'Apparent', value: previewMetricValue(summary?.apparent_metric), tone: previewMetricTone(summary?.apparent_metric) },
            { label: 'Optimism', value: previewMetricValue(summary?.mean_optimism), tone: previewMetricTone(summary?.mean_optimism) },
            { label: '校正后', value: previewMetricValue(summary?.optimism_corrected_metric), tone: previewMetricTone(summary?.optimism_corrected_metric) },
          ],
        }
      }
    case 'nomogram':
      return {
        title: 'Nomogram 预览',
        subtitle: '列线图会聚焦总分刻度和预测时点。',
        items: [
          { label: '刻度', value: node.values.scale || '100 分', tone: 'accent' },
          { label: '时间点', value: node.values.timepoint || '1 year' },
          { label: '风险层级', value: '低 / 中 / 高', tone: 'positive' },
        ],
      }
    default:
      return null
  }
}

function splitInputSourceLabel(node: CanvasNode) {
  const upstream = getIncomingNodes(node.id)
  if (upstream.length) {
    return upstream.map((item) => item.label).join(' / ')
  }
  return selectedDatasetOption.value?.name || '未选择数据集'
}

function splitSuggestedStratifyField(node: CanvasNode) {
  if (node.moduleId !== 'split') return ''
  const fieldMappingNode = getFieldMappingNode()
  return fieldMappingNode?.values.outcomeField?.trim() || ''
}

function splitSuggestedTimeField(node: CanvasNode) {
  if (node.moduleId !== 'split') return ''
  const fieldMappingNode = getFieldMappingNode()
  return fieldMappingNode?.values.timeField?.trim() || ''
}

function splitSelectionHint(node: CanvasNode) {
  if (node.moduleId !== 'split') return ''
  if (node.values.sampling === '分层抽样') {
    return node.values.stratifyField
      ? `当前将按“${node.values.stratifyField}”做分层划分，尽量保持各子集该变量分布一致。`
      : `请选择分层变量。通常建议使用结局变量${splitSuggestedStratifyField(node) ? `（推荐：${splitSuggestedStratifyField(node)}）` : ''}。`
  }
  if (node.values.sampling === '时间切分') {
    return node.values.timeSplitField
      ? `当前将按“${node.values.timeSplitField}”排序后切分，训练集会优先保留较早时间的数据。`
      : `请选择时间切分字段${splitSuggestedTimeField(node) ? `（推荐：${splitSuggestedTimeField(node)}）` : ''}。`
  }
  return '当前采用随机划分，所有样本会按随机种子打散后再切分。'
}

function splitInputShapeText(node: CanvasNode) {
  const rows = estimateSampleSize(node)
  const cols = datasetSummary.value?.total_columns
  if (!selectedDatasetId.value) return '未选择数据集'
  return `${rows} 行 × ${cols ?? '-'} 列`
}

function splitInputPreviewNote(node: CanvasNode) {
  const upstream = getIncomingNodes(node.id)
  const modeText = node.values.sampling === '分层抽样'
    ? `当前会按“${node.values.stratifyField || '未设置分层变量'}”分层后再切分。`
    : node.values.sampling === '时间切分'
      ? `当前会按“${node.values.timeSplitField || '未设置时间字段'}”排序后切分。`
      : '当前会按随机种子直接打散后切分。'
  if (upstream.length) {
    return `当前节点会接收上游节点“${upstream.map((item) => item.label).join('、')}”处理后的数据继续拆分。${modeText} 上面的行数是按当前流程配置估算的输入规模。`
  }
  return `当前节点从所选项目数据集启动拆分。${modeText} 你运行前在这里确认数据源、数据规模和划分比例即可。`
}

function collectUpstreamSubgraph(targetNodeId: string) {
  const visited = new Set<string>()
  const nodeIds = new Set<string>()
  const connectionIds = new Set<string>()
  const queue = [targetNodeId]

  while (queue.length) {
    const currentId = queue.shift()
    if (!currentId || visited.has(currentId)) continue
    visited.add(currentId)
    nodeIds.add(currentId)

    for (const connection of connections.value.filter((item) => item.toNodeId === currentId)) {
      connectionIds.add(connection.id)
      queue.push(connection.fromNodeId)
    }
  }

  const nodes = canvasNodes.value.filter((node) => nodeIds.has(node.id))
  const subConnections = connections.value.filter((connection) => connectionIds.has(connection.id))
  return {
    nodes: _sortNodesForRun(nodes),
    connections: subConnections,
  }
}

function _sortNodesForRun(nodes: CanvasNode[]) {
  return [...nodes].sort((a, b) => {
    const stageDiff = (STAGE_ORDER.get(a.stageId) ?? 99) - (STAGE_ORDER.get(b.stageId) ?? 99)
    if (stageDiff !== 0) return stageDiff
    return a.order - b.order
  })
}

function buildRunPredictorVariables(fieldMapping: CanvasNode | null, summary: DatasetSummaryResponse | null) {
  const datasetColumns = (summary?.columns || []).map((column) => column.name)
  if (!fieldMapping) {
    return []
  }
  const outcomeVariable = fieldMapping.values.outcomeField?.trim() || ''
  const timeVariable = fieldMapping.values.timeField?.trim() || ''
  const explicitlySelectedPredictors = parsePredictorFields(fieldMapping.values.predictorFields || '')
  const excluded = new Set([
    fieldMapping.values.idField?.trim(),
    outcomeVariable,
    timeVariable,
  ].filter(Boolean))

  return explicitlySelectedPredictors.length
    ? explicitlySelectedPredictors.filter((name) => datasetColumns.includes(name) && !excluded.has(name))
    : datasetColumns.filter((name) => !excluded.has(name))
}

function isDatasetColumnField(moduleId: string, fieldKey: string) {
  if (!datasetColumnNames.value.length) return false
  if (!['idField', 'outcomeField', 'timeField', 'target'].includes(fieldKey)) return false
  if (moduleId === 'split') return false
  if (moduleId === 'rcs' && fieldKey === 'target') return true
  if (fieldKey === 'target') return false
  return true
}

function datasetColumnFieldEmptyLabel(moduleId: string, fieldKey: string) {
  const isModelOverride = ['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(moduleId)
  if (isModelOverride) {
    return '沿用字段映射'
  }
  if (moduleId === 'rcs' && fieldKey === 'target') return datasetColumnNames.value.length ? '选择连续变量' : '暂无可用字段'
  if (fieldKey === 'idField') return datasetColumnNames.value.length ? '选择 ID 字段' : '暂无可用字段'
  if (fieldKey === 'timeField') return datasetColumnNames.value.length ? '选择时间字段' : '暂无可用字段'
  return datasetColumnNames.value.length ? '选择结局字段' : '暂无可用字段'
}

function selectOptionsForField(field: ModuleField) {
  if (field.type !== 'select') return field.options || []
  const options = field.options || []
  if (!selectedNode.value) return options
  if (
    field.key === 'dataSource' &&
    ['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId) &&
    selectedNodeIncomingNodes.value.length === 0
  ) {
    return options.filter((option) => option !== '上游输出')
  }
  return options
}

function validateConnection(sourceNodeId: string, targetNodeId: string) {
  const source = canvasNodes.value.find((node) => node.id === sourceNodeId)
  const target = canvasNodes.value.find((node) => node.id === targetNodeId)

  if (!source || !target) {
    return { ok: false, message: '未找到连线节点。' }
  }

  if (source.id === target.id) {
    return { ok: false, message: '同一个节点不能连接自己。' }
  }

  const sourceStageOrder = STAGE_ORDER.get(source.stageId) ?? 0
  const targetStageOrder = STAGE_ORDER.get(target.stageId) ?? 0
  if (sourceStageOrder > targetStageOrder) {
    return { ok: false, message: '流程不能反向连接到前面的阶段。' }
  }

  if (connections.value.some((item) => item.fromNodeId === source.id && item.toNodeId === target.id)) {
    return { ok: false, message: '这两个节点之间已经存在连线。' }
  }

  const singleInputModules = new Set([
    'missing-value',
    'split',
    'encoding',
    'univariate-screen',
    'vif',
    'lasso-selection',
    'rf-importance',
    'boruta-selection',
    'rcs',
    'interaction',
    'logistic-model',
    'cox-model',
    'xgboost',
    'random-forest',
    'roc',
    'calibration',
    'dca',
    'bootstrap',
    'nomogram',
  ])
  if (
    singleInputModules.has(target.moduleId) &&
    getIncomingConnections(target.id).some((item) => item.fromNodeId !== source.id)
  ) {
    return { ok: false, message: '该节点当前只允许保留一个上游输入。' }
  }

  if (target.stageId === 'model-validation' && source.stageId !== 'model-development') {
    return { ok: false, message: '验证类节点只能接在模型开发节点后面。' }
  }

  if (target.moduleId === 'nomogram' && !['logistic-model', 'cox-model'].includes(source.moduleId)) {
    return { ok: false, message: '列线图只能接在 Logistic 或 Cox 模型后面。' }
  }

  if (target.moduleId === 'rcs' && !['logistic-model', 'cox-model'].includes(source.moduleId)) {
    return { ok: false, message: '限制性立方样条只能接在 Logistic 或 Cox 模型后面。' }
  }

  if (target.moduleId === 'bootstrap' && source.stageId !== 'model-development') {
    return { ok: false, message: 'Bootstrap 需要直接接在模型开发节点后。' }
  }

  return { ok: true, message: '可以建立连接。' }
}

function evaluateNodeStatus(node: CanvasNode, currentStatuses: Map<string, NodeStatusMeta>): NodeStatusMeta {
  const runResult = latestNodeResult(node.id)
  const hasCompleted = runResult?.status === 'completed'
  const templateKind = inferWorkflowTemplateKind()
  const fieldMappingNode = getFieldMappingNode()
  const hasMappedOutcome = Boolean(fieldMappingNode?.values.outcomeField?.trim())
  const hasMappedTime = Boolean(fieldMappingNode?.values.timeField?.trim())
  const incomingNodes = getIncomingNodes(node.id)
  const moduleFields = findModuleById(node.moduleId)?.fields ?? node.fields

  const requiredFields = node.moduleId === 'field-mapping'
    ? moduleFields.filter((field) => {
        if (field.key === 'timeField') {
          return templateKind === 'survival'
        }
        return true
      })
    : moduleFields.filter((field) => {
        if (['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(node.moduleId) && field.key === 'dataSource') {
          return incomingNodes.length === 0
        }
        if (['logistic-model', 'xgboost', 'random-forest'].includes(node.moduleId) && field.key === 'outcomeField') {
          return !hasMappedOutcome
        }
        if (node.moduleId === 'cox-model' && field.key === 'outcomeField') {
          return !hasMappedOutcome
        }
        if (node.moduleId === 'cox-model' && field.key === 'timeField') {
          return templateKind === 'survival' && !hasMappedTime
        }
        return true
      })

  const missingFields = requiredFields
    .filter((field) => `${node.values[field.key] ?? ''}`.trim().length === 0)
    .map((field) => field.label)

  if (missingFields.length) {
    if (hasCompleted) {
      return {
        status: 'ready',
        label: '已就绪',
        message: `该节点已运行完成，但仍有参数未填写：${missingFields.join('、')}。`,
      }
    }
    return {
      status: 'incomplete',
      label: '未完成',
      message: `待填写：${missingFields.join('、')}。`,
    }
  }

  const dataPreparationModuleIds = new Set(['field-mapping', 'missing-value', 'split', 'encoding'])
  const modelStartableWithoutUpstream = (() => {
    if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(node.moduleId)) return false
    if (incomingNodes.length) return false
    const raw = `${node.values.dataSource ?? ''}`.trim().replace('数据集', '').replace(/\s+/g, '')
    return ['原始数据', '原始', '训练集', '训练', '测试集', '测试'].includes(raw)
  })()
  const needsUpstream = !dataPreparationModuleIds.has(node.moduleId) && !modelStartableWithoutUpstream

  if (!incomingNodes.length && (dataPreparationModuleIds.has(node.moduleId) || modelStartableWithoutUpstream) && !selectedDatasetId.value) {
    return {
      status: 'incomplete',
      label: '缺少数据源',
      message: '当前节点没有上游输入，请先选择项目数据集作为流程起点。',
    }
  }

  const predictorFields = parsePredictorFields(node.values.predictorFields || '')
  if (node.moduleId === 'field-mapping' && predictorFields.length === 0) {
    const warningText = '未显式选择候选变量字段，将默认使用除 ID/结局/时间 外的所有字段。'
    if (hasCompleted) {
      return {
        status: 'ready',
        label: '已就绪',
        message: `该节点已运行完成。${warningText}`,
      }
    }
    return {
      status: 'ready',
      label: '已就绪',
      message: warningText,
    }
  }

  if (node.moduleId === 'split' && node.values.sampling === '分层抽样' && !`${node.values.stratifyField ?? ''}`.trim()) {
    return {
      status: 'incomplete',
      label: '未完成',
      message: `分层抽样需要指定分层变量${splitSuggestedStratifyField(node) ? `，建议使用 ${splitSuggestedStratifyField(node)}` : ''}。`,
    }
  }

  if (node.moduleId === 'split' && node.values.sampling === '时间切分' && !`${node.values.timeSplitField ?? ''}`.trim()) {
    return {
      status: 'incomplete',
      label: '未完成',
      message: `时间切分需要指定排序字段${splitSuggestedTimeField(node) ? `，建议使用 ${splitSuggestedTimeField(node)}` : ''}。`,
    }
  }

  if (needsUpstream && incomingNodes.length === 0) {
    return {
      status: 'blocked',
      label: '待接入',
      message: '当前缺少上游节点，无法进入计算流程。',
    }
  }

  const notReadyUpstreams = incomingNodes.filter((upstream) => currentStatuses.get(upstream.id)?.status !== 'ready')
  if (notReadyUpstreams.length) {
    return {
      status: 'blocked',
      label: '被阻塞',
      message: `等待上游节点就绪：${notReadyUpstreams.map((nodeItem) => nodeItem.label).join('、')}。`,
    }
  }

  if (hasCompleted) {
    return {
      status: 'ready',
      label: '已就绪',
      message: '该节点已运行完成，可继续向下运行。',
    }
  }

  return {
    status: 'ready',
    label: '已就绪',
    message: incomingNodes.length ? `已接入 ${incomingNodes.length} 个上游节点，可继续向下运行。` : '当前节点可作为流程起点。',
  }
}

function buildNode(module: ModuleDefinition, x: number, y: number): CanvasNode {
  return {
    id: `${module.id}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    moduleId: module.id,
    label: module.label,
    description: module.description,
    stageId: module.stageId,
    fields: module.fields,
    values: { ...module.defaults },
    x,
    y,
    order: canvasNodes.value.length + 1,
  }
}

function buildNodeFromTemplate(templateNode: TemplateNodeDefinition, x: number, y: number) {
  const module = findModuleById(templateNode.moduleId)
  if (!module) return null

  const node = buildNode(module, x, y)
  return {
    ...node,
    values: {
      ...node.values,
      ...(templateNode.values ?? {}),
    },
  }
}

function addNodeFromLibrary(module: ModuleDefinition) {
  pushUndoState()
  const canvas = canvasRef.value
  const defaultX = 60 + (canvasNodes.value.length % 3) * 320
  const defaultY = 60 + Math.floor(canvasNodes.value.length / 3) * 220
  const viewportCenterX = canvas ? canvas.scrollLeft / canvasScale.value + canvas.clientWidth / (2 * canvasScale.value) : defaultX
  const viewportCenterY = canvas ? canvas.scrollTop / canvasScale.value + canvas.clientHeight / (2 * canvasScale.value) : defaultY
  const node = buildNode(module, Math.max(24, viewportCenterX - NODE_WIDTH / 2), Math.max(24, viewportCenterY - NODE_HEIGHT / 2))
  canvasNodes.value.push(node)
  selectedConnectionId.value = null
  selectedNodeIds.value = [node.id]
  selectedNodeId.value = node.id
  addLog('add', `已创建节点“${node.label}”。`)
}

function injectTemplate(templateId: string) {
  const template = findTemplateById(templateId)
  if (!template) return

  const createdNodes: CanvasNode[] = []
  const baseX = canvasNodes.value.length ? Math.max(...canvasNodes.value.map((node) => node.x + NODE_WIDTH)) + 120 : 72
  const baseY = canvasNodes.value.length ? 72 : 70

  template.nodes.forEach((templateNode, index) => {
    const node = buildNodeFromTemplate(templateNode, baseX + (index % 2) * 320, baseY + Math.floor(index / 2) * 220)
    if (node) {
      createdNodes.push(node)
    }
  })

  if (!createdNodes.length) {
    addLog('warn', `模板“${template.label}”未能成功注入。`)
    return
  }

  canvasNodes.value.push(...createdNodes)
  template.connections.forEach(([fromIndex, toIndex]) => {
    const source = createdNodes[fromIndex]
    const target = createdNodes[toIndex]
    if (!source || !target) return
    const validation = validateConnection(source.id, target.id)
    if (!validation.ok) return
    connections.value.push({
      id: `${source.id}-${target.id}`,
      fromNodeId: source.id,
      toNodeId: target.id,
      outputPortId: null,
    })
  })

  selectedConnectionId.value = null
  selectedNodeIds.value = createdNodes.map((node) => node.id)
  selectedNodeId.value = createdNodes[0]?.id ?? null
  isTemplatePickerOpen.value = false
  addLog('template', `已注入模板“${template.label}”，共创建 ${createdNodes.length} 个节点。`)

  window.requestAnimationFrame(() => {
    autoArrangeNodes()
  })
}

function onLibraryDragStart(module: ModuleDefinition) {
  draggingLibraryModuleId.value = module.id
}

function onCanvasDrop(event: DragEvent) {
  if (!draggingLibraryModuleId.value) return
  const module = findModuleById(draggingLibraryModuleId.value)
  const canvas = canvasRef.value
  if (!module || !canvas) return
  const rect = canvas.getBoundingClientRect()
  const fallbackX = rect.left + canvas.clientWidth / 2
  const fallbackY = rect.top + canvas.clientHeight / 2
  const point = getCanvasPointFromClient(event.clientX || fallbackX, event.clientY || fallbackY)
  if (!point) return
  const x = Math.max(24, point.x - NODE_WIDTH / 2)
  const y = Math.max(24, point.y - NODE_HEIGHT / 2)
  const node = buildNode(module, x, y)
  canvasNodes.value.push(node)
  selectedConnectionId.value = null
  selectedNodeIds.value = [node.id]
  selectedNodeId.value = node.id
  draggingLibraryModuleId.value = null
  addLog('drop', `已将“${node.label}”拖入画布。`)
}

function clearNodeSelection() {
  selectedNodeIds.value = []
  selectedNodeId.value = null
}

function setSelectedNodeIds(nodeIds: string[], anchorId?: string | null) {
  const uniqueIds = Array.from(new Set(nodeIds))
  selectedNodeIds.value = uniqueIds
  selectedNodeId.value = anchorId ?? uniqueIds[0] ?? null
}

function selectNode(nodeId: string, event?: MouseEvent) {
  selectedConnectionId.value = null
  if (event?.shiftKey) {
    if (selectedNodeIds.value.includes(nodeId)) {
      const nextIds = selectedNodeIds.value.filter((id) => id !== nodeId)
      setSelectedNodeIds(nextIds, nextIds[nextIds.length - 1] ?? null)
    } else {
      setSelectedNodeIds([...selectedNodeIds.value, nodeId], nodeId)
    }
    return
  }
  setSelectedNodeIds([nodeId], nodeId)
}

function selectConnection(connectionId: string) {
  clearNodeSelection()
  selectedConnectionId.value = connectionId
}

function removeNode(nodeId: string) {
  pushUndoState()
  const node = canvasNodes.value.find((item) => item.id === nodeId)
  canvasNodes.value = canvasNodes.value.filter((item) => item.id !== nodeId)
  const removedConnectionIds = new Set(
    connections.value
      .filter((item) => item.fromNodeId === nodeId || item.toNodeId === nodeId)
      .map((item) => item.id),
  )
  connections.value = connections.value.filter((item) => item.fromNodeId !== nodeId && item.toNodeId !== nodeId)
  if (selectedNodeId.value === nodeId) {
    selectedNodeId.value = canvasNodes.value[0]?.id ?? null
  }
  selectedNodeIds.value = selectedNodeIds.value.filter((id) => id !== nodeId)
  if (selectedConnectionId.value && removedConnectionIds.has(selectedConnectionId.value)) {
    selectedConnectionId.value = null
  }
  if (pendingConnectionFrom.value === nodeId) {
    pendingConnectionFrom.value = null
    pendingConnectionPortId.value = null
  }
  if (node) {
    addLog('remove', `已删除节点“${node.label}”及其相关连线。`)
  }
}

function updateNodeValue(nodeId: string, key: string, value: string) {
  canvasNodes.value = canvasNodes.value.map((node) =>
    node.id === nodeId
      ? {
          ...node,
          values: {
            ...node.values,
            [key]: value,
          },
        }
      : node,
  )
  const updatedNode = canvasNodes.value.find((node) => node.id === nodeId)
  if (updatedNode) {
    const status = nodeStatusMap.value.get(nodeId)
    addLog('config', `已更新“${updatedNode.label}”参数“${key}”。${status ? status.message : ''}`)
  }
}

function updateSplitSamplingValue(nodeId: string, sampling: string) {
  const node = canvasNodes.value.find((item) => item.id === nodeId)
  if (!node || node.moduleId !== 'split') {
    updateNodeValue(nodeId, 'sampling', sampling)
    return
  }

  const nextValues = {
    ...node.values,
    sampling,
    stratifyField: sampling === '分层抽样'
      ? (node.values.stratifyField || splitSuggestedStratifyField(node) || '')
      : '',
    timeSplitField: sampling === '时间切分'
      ? (node.values.timeSplitField || splitSuggestedTimeField(node) || '')
      : '',
  }

  canvasNodes.value = canvasNodes.value.map((item) =>
    item.id === nodeId
      ? {
          ...item,
          values: nextValues,
        }
      : item,
  )

  const updatedNode = canvasNodes.value.find((item) => item.id === nodeId)
  if (updatedNode) {
    const status = nodeStatusMap.value.get(nodeId)
    addLog('config', `已更新“${updatedNode.label}”抽样方式为“${sampling}”。${status ? status.message : ''}`)
  }
}

function startNodeDrag(event: MouseEvent, nodeId: string) {
  const node = canvasNodes.value.find((item) => item.id === nodeId)
  if (!node) return
  if (!selectedNodeIds.value.includes(nodeId)) {
    setSelectedNodeIds([nodeId], nodeId)
  }
  const nodeIds = selectedNodeIds.value.includes(nodeId) ? [...selectedNodeIds.value] : [nodeId]
  dragState.value = {
    nodeIds,
    startX: event.clientX,
    startY: event.clientY,
    origins: canvasNodes.value
      .filter((item) => nodeIds.includes(item.id))
      .map((item) => ({ id: item.id, x: item.x, y: item.y })),
  }
  window.addEventListener('mousemove', handleNodeDrag)
  window.addEventListener('mouseup', stopNodeDrag)
}

function handleNodeDrag(event: MouseEvent) {
  if (!dragState.value || !canvasRef.value) return
  const deltaX = (event.clientX - dragState.value.startX) / canvasScale.value
  const deltaY = (event.clientY - dragState.value.startY) / canvasScale.value
  const originMap = new Map(dragState.value.origins.map((item) => [item.id, item]))

  canvasNodes.value = canvasNodes.value.map((node) => {
    const origin = originMap.get(node.id)
    if (!origin) return node
    return {
      ...node,
      x: Math.min(Math.max(12, origin.x + deltaX), canvasSurfaceWidth.value - NODE_WIDTH - 12),
      y: Math.min(Math.max(12, origin.y + deltaY), canvasSurfaceHeight.value - NODE_HEIGHT - 12),
    }
  })
}

function stopNodeDrag() {
  if (dragState.value) {
    const movedNodes = canvasNodes.value.filter((node) => dragState.value?.nodeIds.includes(node.id))
    if (movedNodes.length === 1) {
      addLog('move', `已移动节点“${movedNodes[0].label}”。`)
    } else if (movedNodes.length > 1) {
      addLog('move', `已批量移动 ${movedNodes.length} 个节点。`)
    }
  }
  dragState.value = null
  window.removeEventListener('mousemove', handleNodeDrag)
  window.removeEventListener('mouseup', stopNodeDrag)
}

function beginConnection(nodeId: string) {
  selectedConnectionId.value = null
  setSelectedNodeIds([nodeId], nodeId)
  pendingConnectionFrom.value = nodeId
  pendingConnectionPortId.value = null
  selectedNodeId.value = nodeId
  addLog('link', `已选择”${canvasNodes.value.find((node) => node.id === nodeId)?.label || ''}”的输出端口，等待连接目标。`)
}

function completeConnection(targetNodeId: string) {
  if (!pendingConnectionFrom.value) {
    selectNode(targetNodeId)
    return
  }

  if (pendingConnectionFrom.value === targetNodeId) {
    addLog('warn', '同一个节点不能连接自己。')
    return
  }

  const source = canvasNodes.value.find((node) => node.id === pendingConnectionFrom.value)
  const target = canvasNodes.value.find((node) => node.id === targetNodeId)
  if (!source || !target) return

  const validation = validateConnection(source.id, target.id)
  if (!validation.ok) {
    addLog('warn', validation.message)
    return
  }

  pushUndoState()
  connections.value.push({
    id: `${source.id}-${target.id}`,
    fromNodeId: source.id,
    toNodeId: target.id,
    outputPortId: null,
  })
  selectedConnectionId.value = null
  pendingConnectionFrom.value = null
  pendingConnectionPortId.value = null
  addLog('link', `已连接"${source.label}" -> "${target.label}"。`)
}

function cancelPendingConnection() {
  if (selectedConnectionId.value) {
    pushUndoState()
    const connection = connections.value.find((item) => item.id === selectedConnectionId.value)
    connections.value = connections.value.filter((item) => item.id !== selectedConnectionId.value)
    selectedConnectionId.value = null
    if (connection) {
      const source = canvasNodes.value.find((node) => node.id === connection.fromNodeId)?.label ?? '起点节点'
      const target = canvasNodes.value.find((node) => node.id === connection.toNodeId)?.label ?? '终点节点'
      addLog('link', `已删除连线“${source} -> ${target}”。`)
      return
    }
  }
  if (pendingConnectionFrom.value) {
    pendingConnectionFrom.value = null
    pendingConnectionPortId.value = null
    addLog('link', '已取消当前连线。')
  }
}

function handleGlobalKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeNodeDialogs()
    return
  }

  if ((event.ctrlKey || event.metaKey) && event.key === 'z') {
    const target = event.target as HTMLElement | null
    const tagName = target?.tagName?.toLowerCase()
    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select' || target?.isContentEditable) {
      return
    }
    event.preventDefault()
    undo()
    return
  }

  if (event.key !== 'Delete' && event.key !== 'Backspace') return

  const target = event.target as HTMLElement | null
  const tagName = target?.tagName?.toLowerCase()
  if (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    target?.isContentEditable
  ) {
    return
  }

  event.preventDefault()
  if (selectedConnectionId.value) {
    cancelPendingConnection()
    return
  }
  if (selectedNodeIds.value.length) {
    deleteSelectedNodes()
  }
}

function handleCanvasContextMenu() {
  if (!pendingConnectionFrom.value && !selectedConnectionId.value) {
    return
  }
  cancelPendingConnection()
}

function getCanvasPointFromClient(clientX: number, clientY: number) {
  if (!canvasRef.value) return null
  const rect = canvasRef.value.getBoundingClientRect()
  return {
    x: (clientX - rect.left + canvasRef.value.scrollLeft) / canvasScale.value,
    y: (clientY - rect.top + canvasRef.value.scrollTop) / canvasScale.value,
  }
}

function getCanvasPoint(event: MouseEvent) {
  return getCanvasPointFromClient(event.clientX, event.clientY)
}

function handleCanvasMouseDown(event: MouseEvent) {
  if (!canvasRef.value) return

  const target = event.target as HTMLElement | null
  if (
    target?.closest('.node-card') ||
    target?.closest('.node-port') ||
    target?.closest('.connection-hit-path') ||
    target?.closest('.canvas-dock') ||
    target?.closest('.template-picker')
  ) {
    return
  }

  if (event.button === 2) {
    if (pendingConnectionFrom.value || selectedConnectionId.value) {
      return
    }
    event.preventDefault()
    panState.value = {
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: canvasRef.value.scrollLeft,
      scrollTop: canvasRef.value.scrollTop,
    }
    window.addEventListener('mousemove', handleCanvasPan)
    window.addEventListener('mouseup', stopCanvasPan)
    return
  }

  if (event.button !== 0) return

  const point = getCanvasPoint(event)
  if (!point) return

  selectedConnectionId.value = null
  if (!event.shiftKey) {
    clearNodeSelection()
  }

  selectionRect.value = {
    startX: point.x,
    startY: point.y,
    currentX: point.x,
    currentY: point.y,
    additive: event.shiftKey,
  }

  window.addEventListener('mousemove', handleSelectionDrag)
  window.addEventListener('mouseup', stopSelectionDrag)
}

function handleCanvasPan(event: MouseEvent) {
  if (!panState.value || !canvasRef.value) return
  const deltaX = event.clientX - panState.value.startX
  const deltaY = event.clientY - panState.value.startY

  canvasRef.value.scrollLeft = panState.value.scrollLeft - deltaX
  canvasRef.value.scrollTop = panState.value.scrollTop - deltaY
}

function stopCanvasPan() {
  panState.value = null
  window.removeEventListener('mousemove', handleCanvasPan)
  window.removeEventListener('mouseup', stopCanvasPan)
}

function handleSelectionDrag(event: MouseEvent) {
  if (!selectionRect.value) return
  const point = getCanvasPoint(event)
  if (!point) return
  selectionRect.value = {
    ...selectionRect.value,
    currentX: point.x,
    currentY: point.y,
  }
}

function stopSelectionDrag() {
  if (selectionRect.value) {
    const minX = Math.min(selectionRect.value.startX, selectionRect.value.currentX)
    const maxX = Math.max(selectionRect.value.startX, selectionRect.value.currentX)
    const minY = Math.min(selectionRect.value.startY, selectionRect.value.currentY)
    const maxY = Math.max(selectionRect.value.startY, selectionRect.value.currentY)

    const hitIds = canvasNodes.value
      .filter((node) => node.x < maxX && node.x + NODE_WIDTH > minX && node.y < maxY && node.y + NODE_HEIGHT > minY)
      .map((node) => node.id)

    if (selectionRect.value.additive) {
      setSelectedNodeIds([...selectedNodeIds.value, ...hitIds], hitIds[hitIds.length - 1] ?? selectedNodeId.value)
    } else if (hitIds.length) {
      setSelectedNodeIds(hitIds, hitIds[hitIds.length - 1])
    } else {
      clearNodeSelection()
    }

    if (hitIds.length > 1) {
      addLog('select', `已框选 ${hitIds.length} 个节点。`)
    }
  }

  selectionRect.value = null
  window.removeEventListener('mousemove', handleSelectionDrag)
  window.removeEventListener('mouseup', stopSelectionDrag)
}

function handleCanvasMouseMove(event: MouseEvent) {
  const point = getCanvasPoint(event)
  if (!point) return
  pointerPosition.value = point
}

function deleteSelectedNodes() {
  if (!selectedNodeIds.value.length) return
  const ids = [...selectedNodeIds.value]
  ids.forEach((id) => removeNode(id))
  clearNodeSelection()
  addLog('remove', `已批量删除 ${ids.length} 个节点。`)
}

function alignSelectedNodes(mode: 'left') {
  if (selectedNodeIds.value.length < 2) return
  const selectedNodes = canvasNodes.value.filter((node) => selectedNodeIds.value.includes(node.id))
  const minX = Math.min(...selectedNodes.map((node) => node.x))
  canvasNodes.value = canvasNodes.value.map((node) =>
    selectedNodeIds.value.includes(node.id)
      ? { ...node, x: minX }
      : node,
  )
  addLog('layout', `已将 ${selectedNodeIds.value.length} 个节点左对齐。`)
}

function distributeSelectedNodes(direction: 'horizontal' | 'vertical') {
  if (selectedNodeIds.value.length < 3) return
  const selectedNodes = canvasNodes.value
    .filter((node) => selectedNodeIds.value.includes(node.id))
    .sort((a, b) => (direction === 'horizontal' ? a.x - b.x : a.y - b.y))

  const first = selectedNodes[0]
  const last = selectedNodes[selectedNodes.length - 1]
  const span = direction === 'horizontal' ? last.x - first.x : last.y - first.y
  const gap = span / (selectedNodes.length - 1)
  const nextPositions = new Map<string, number>()

  selectedNodes.forEach((node, index) => {
    nextPositions.set(node.id, (direction === 'horizontal' ? first.x : first.y) + gap * index)
  })

  canvasNodes.value = canvasNodes.value.map((node) => {
    const nextValue = nextPositions.get(node.id)
    if (nextValue == null) return node
    return direction === 'horizontal'
      ? { ...node, x: nextValue }
      : { ...node, y: nextValue }
  })

  addLog('layout', `已将 ${selectedNodeIds.value.length} 个节点${direction === 'horizontal' ? '横向' : '纵向'}分布。`)
}

function setZoom(nextScale: number, anchor?: { x: number; y: number }) {
  const canvas = canvasRef.value
  const currentScale = canvasScale.value
  const normalized = Math.min(1.6, Math.max(0.5, Number(nextScale.toFixed(2))))

  if (!canvas || normalized === currentScale) {
    canvasScale.value = normalized
    zoomPercent.value = Math.round(normalized * 100)
    return
  }

  const anchorX = anchor?.x ?? canvas.clientWidth / 2
  const anchorY = anchor?.y ?? canvas.clientHeight / 2
  const worldX = (canvas.scrollLeft + anchorX) / currentScale
  const worldY = (canvas.scrollTop + anchorY) / currentScale

  canvasScale.value = normalized
  zoomPercent.value = Math.round(normalized * 100)

  canvas.scrollLeft = Math.max(0, worldX * normalized - anchorX)
  canvas.scrollTop = Math.max(0, worldY * normalized - anchorY)
}

function getGraphBounds(nodes = canvasNodes.value) {
  if (!nodes.length) {
    return null
  }

  const minX = Math.min(...nodes.map((node) => node.x))
  const minY = Math.min(...nodes.map((node) => node.y))
  const maxX = Math.max(...nodes.map((node) => node.x + NODE_WIDTH))
  const maxY = Math.max(...nodes.map((node) => node.y + NODE_HEIGHT))

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  }
}

function scrollCanvasToNodeBounds(bounds: { minX: number; minY: number; width: number; height: number }, padding = 40) {
  const canvas = canvasRef.value
  if (!canvas) return

  const viewportWidth = canvas.clientWidth
  const viewportHeight = canvas.clientHeight
  const zoom = canvasScale.value
  const targetLeft = Math.max(0, (bounds.minX - padding) * zoom - Math.max(0, viewportWidth - (bounds.width + padding * 2) * zoom) / 2)
  const targetTop = Math.max(0, (bounds.minY - padding) * zoom - Math.max(0, viewportHeight - (bounds.height + padding * 2) * zoom) / 2)

  canvas.scrollTo({
    left: targetLeft,
    top: targetTop,
    behavior: 'smooth',
  })
}

function arrangeNodesByConnections(options?: {
  columnGap?: number
  rowGap?: number
  paddingX?: number
  paddingY?: number
  maxRows?: number
}) {
  const canvas = canvasRef.value
  if (!canvasNodes.value.length) {
    addLog('layout', '当前画布为空，暂时没有节点可整理。')
    return false
  }

  const columnGap = options?.columnGap ?? 148
  const rowGap = options?.rowGap ?? 44
  const paddingX = options?.paddingX ?? 72
  const paddingY = options?.paddingY ?? 70
  const dx = NODE_WIDTH + columnGap

  const nodeMap = new Map(canvasNodes.value.map((node) => [node.id, node]))
  const outgoing = new Map<string, string[]>()
  const incoming = new Map<string, string[]>()
  const inDegree = new Map<string, number>()

  canvasNodes.value.forEach((node) => {
    outgoing.set(node.id, [])
    incoming.set(node.id, [])
    inDegree.set(node.id, 0)
  })

  connections.value.forEach((connection) => {
    if (!nodeMap.has(connection.fromNodeId) || !nodeMap.has(connection.toNodeId)) return
    outgoing.get(connection.fromNodeId)?.push(connection.toNodeId)
    incoming.get(connection.toNodeId)?.push(connection.fromNodeId)
    inDegree.set(connection.toNodeId, (inDegree.get(connection.toNodeId) ?? 0) + 1)
  })

  // Kahn topo sort (cycle-tolerant: remaining nodes appended by order).
  const queue = canvasNodes.value
    .filter((node) => (inDegree.get(node.id) ?? 0) === 0)
    .sort((a, b) => a.order - b.order)
    .map((node) => node.id)

  const topo: string[] = []
  while (queue.length) {
    const id = queue.shift() as string
    topo.push(id)
    for (const next of outgoing.get(id) ?? []) {
      const nextDegree = (inDegree.get(next) ?? 0) - 1
      inDegree.set(next, nextDegree)
      if (nextDegree === 0) queue.push(next)
    }
  }

  if (topo.length !== canvasNodes.value.length) {
    const remaining = canvasNodes.value
      .map((node) => node.id)
      .filter((id) => !topo.includes(id))
      .sort((a, b) => (nodeMap.get(a)?.order ?? 0) - (nodeMap.get(b)?.order ?? 0))
    topo.push(...remaining)
  }

  // Longest-path levels (gives left->right ordering for connected nodes).
  const level = new Map<string, number>()
  topo.forEach((id) => level.set(id, 0))
  for (const id of topo) {
    const parents = incoming.get(id) ?? []
    if (!parents.length) continue
    let maxParent = 0
    for (const parent of parents) {
      maxParent = Math.max(maxParent, (level.get(parent) ?? 0) + 1)
    }
    level.set(id, maxParent)
  }

  const maxLevel = Math.max(0, ...Array.from(level.values()))
  const levels: string[][] = Array.from({ length: maxLevel + 1 }, () => [])
  topo.forEach((id) => levels[level.get(id) ?? 0].push(id))

  // Sort each level by barycenter of parents' order to reduce crossings.
  const orderIndex = new Map<string, number>()
  levels[0].sort((a, b) => (nodeMap.get(a)?.order ?? 0) - (nodeMap.get(b)?.order ?? 0))
  levels[0].forEach((id, idx) => orderIndex.set(id, idx))
  for (let i = 1; i < levels.length; i += 1) {
    levels[i].sort((a, b) => {
      const aParents = incoming.get(a) ?? []
      const bParents = incoming.get(b) ?? []
      const aScore = aParents.length ? aParents.reduce((s, p) => s + (orderIndex.get(p) ?? 0), 0) / aParents.length : 1e9
      const bScore = bParents.length ? bParents.reduce((s, p) => s + (orderIndex.get(p) ?? 0), 0) / bParents.length : 1e9
      if (aScore !== bScore) return aScore - bScore
      return (nodeMap.get(a)?.order ?? 0) - (nodeMap.get(b)?.order ?? 0)
    })
    levels[i].forEach((id, idx) => orderIndex.set(id, idx))
  }

  const worldViewportHeight = canvas ? canvas.clientHeight / canvasScale.value : 720
  const computedMaxRows = Math.max(1, Math.floor((worldViewportHeight - paddingY * 2 + rowGap) / (NODE_HEIGHT + rowGap)))
  // "左右优先"：限制最大行数，更多节点向右换列。
  const maxRows = options?.maxRows ?? Math.max(1, Math.min(4, computedMaxRows))

  const wrapColsCount = levels.map((ids) => Math.max(1, Math.ceil(ids.length / maxRows)))
  const baseColumnOffset: number[] = []
  let columnCursor = 0
  for (let i = 0; i < wrapColsCount.length; i += 1) {
    baseColumnOffset[i] = columnCursor
    columnCursor += wrapColsCount[i]
  }

  canvasNodes.value = canvasNodes.value.map((node) => {
    const nodeLevel = level.get(node.id) ?? 0
    const ids = levels[nodeLevel] ?? []
    const index = ids.indexOf(node.id)
    const colInLevel = Math.max(0, Math.floor(index / maxRows))
    const rowInLevel = Math.max(0, index % maxRows)
    const colIndex = (baseColumnOffset[nodeLevel] ?? 0) + colInLevel
    return {
      ...node,
      x: paddingX + colIndex * dx,
      y: paddingY + rowInLevel * (NODE_HEIGHT + rowGap),
    }
  })

  return true
}

function arrangeNodes(options?: {
  columnGap?: number
  rowGap?: number
  paddingX?: number
  paddingY?: number
  maxRows?: number
}) {
  if (!canvasNodes.value.length) {
    addLog('layout', '当前画布为空，暂时没有节点可整理。')
    return false
  }

  const columnGap = options?.columnGap ?? 92
  const rowGap = options?.rowGap ?? 44
  const paddingX = options?.paddingX ?? 72
  const paddingY = options?.paddingY ?? 68

  const stageOrder = new Map(stages.map((stage, index) => [stage.id, index]))
  const grouped = new Map<StageId, CanvasNode[]>(
    stages.map((stage) => [stage.id, canvasNodes.value.filter((node) => node.stageId === stage.id).sort((a, b) => a.order - b.order)]),
  )

  const maxRows =
    options?.maxRows ??
    Math.max(
      1,
      ...Array.from(grouped.values()).map((nodes) => {
        const count = nodes.length
        if (count <= 1) return count || 1
        return Math.ceil(Math.sqrt(count))
      }),
    )

  canvasNodes.value = canvasNodes.value.map((node) => {
    const stageNodes = grouped.get(node.stageId) ?? []
    const stageIndex = stageOrder.get(node.stageId) ?? 0
    const nodeIndex = stageNodes.findIndex((item) => item.id === node.id)
    const row = Math.max(0, nodeIndex % maxRows)
    const column = Math.max(0, Math.floor(nodeIndex / maxRows))

    return {
      ...node,
      x: paddingX + stageIndex * (NODE_WIDTH + columnGap) + column * Math.max(42, NODE_WIDTH * 0.18),
      y: paddingY + row * (NODE_HEIGHT + rowGap),
    }
  })

  return true
}

function autoArrangeNodes() {
  if (
    !arrangeNodesByConnections({ columnGap: 20, rowGap: 44, paddingX: 72, paddingY: 70 }) &&
    !arrangeNodes({ columnGap: 20, rowGap: 56, paddingX: 72, paddingY: 70 })
  ) {
    return
  }
  addLog('layout', '已按节点连接顺序一键整理节点。')
  const bounds = getGraphBounds()
  if (bounds) {
    window.requestAnimationFrame(() => scrollCanvasToNodeBounds(bounds, 72))
  }
}

function pushUndoState() {
  undoStack.value.push({
    nodes: JSON.parse(JSON.stringify(canvasNodes.value)),
    connections: JSON.parse(JSON.stringify(connections.value)),
  })
  if (undoStack.value.length > MAX_UNDO) {
    undoStack.value.splice(0, undoStack.value.length - MAX_UNDO)
  }
}

function undo() {
  const state = undoStack.value.pop()
  if (!state) {
    addLog('layout', '没有可撤销的操作。')
    return
  }
  canvasNodes.value = state.nodes
  connections.value = state.connections
  selectedNodeId.value = canvasNodes.value[0]?.id ?? null
  selectedNodeIds.value = []
  selectedConnectionId.value = null
  addLog('layout', '已撤销上一步操作。')
}

function tidyCanvas() {
  pushUndoState()
  if (
    !arrangeNodesByConnections({ columnGap: 20, rowGap: 44, paddingX: 72, paddingY: 70 }) &&
    !arrangeNodes({ columnGap: 20, rowGap: 56, paddingX: 72, paddingY: 70 })
  ) {
    undoStack.value.pop()
    return
  }
  // 整理后居中到视口
  const canvas = canvasRef.value
  const bounds = getGraphBounds()
  if (canvas && bounds) {
    const viewportCenterX = canvas.scrollLeft / canvasScale.value + canvas.clientWidth / (2 * canvasScale.value)
    const viewportCenterY = canvas.scrollTop / canvasScale.value + canvas.clientHeight / (2 * canvasScale.value)
    const graphCenterX = bounds.minX + bounds.width / 2
    const graphCenterY = bounds.minY + bounds.height / 2
    const offsetX = viewportCenterX - graphCenterX
    const offsetY = viewportCenterY - graphCenterY
    canvasNodes.value = canvasNodes.value.map((node) => ({
      ...node,
      x: Math.max(24, node.x + offsetX),
      y: Math.max(24, node.y + offsetY),
    }))
  }
  addLog('layout', '已整理画布：节点有序排列并居中展示。')
  const finalBounds = getGraphBounds()
  if (finalBounds) {
    window.requestAnimationFrame(() => scrollCanvasToNodeBounds(finalBounds, 72))
  }
}

function stepZoom(delta: number) {
  setZoom(canvasScale.value + delta)
}

function resetZoom() {
  setZoom(1)
}

function handleCanvasWheel(event: WheelEvent) {
  if (!event.ctrlKey && !event.metaKey) return
  event.preventDefault()
  const direction = event.deltaY > 0 ? -0.05 : 0.05
  // 默认以画布窗口中心缩放（不会从左上角跳）。
  setZoom(canvasScale.value + direction)
}

function buildConnectionPath(startX: number, startY: number, endX: number, endY: number) {
  const controlOffset = Math.max(90, Math.abs(endX - startX) * 0.45)
  return `M ${startX} ${startY} C ${startX + controlOffset} ${startY}, ${endX - controlOffset} ${endY}, ${endX} ${endY}`
}

function clearLogs() {
  logs.value = [
    {
      id: ++logCounter.value,
      kind: 'reset',
      time: nowTime(),
      message: '日志已清空，后续节点操作会继续记录。',
    },
  ]
}

function resetCanvas() {
  pushUndoState()
  canvasNodes.value = []
  connections.value = []
  selectedNodeIds.value = []
  selectedNodeId.value = null
  selectedConnectionId.value = null
  pendingConnectionFrom.value = null
  pendingConnectionPortId.value = null
  selectionRect.value = null
  panState.value = null
  isTemplatePickerOpen.value = false
  addLog('reset', '节点画布已清空。')
}

watch(
  () => selectedProjectId.value,
  async (projectId, previousProjectId) => {
    if (projectId === previousProjectId) return
    isRestoringDraft.value = true
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('medicode:clinical-model-builder:last-project', projectId || '')
    }
    datasetSummary.value = null
    selectedNodeRunDetail.value = null
    await loadDatasetsForProject(projectId || '')
    restoreDraftFromLocal(projectId || null)
    await refreshPipelineRuns()
    isRestoringDraft.value = false
  },
)

watch(
  () => selectedDatasetId.value,
  async (datasetId) => {
    datasetSummary.value = null
    if (!datasetId) return
    try {
      await ensureDatasetSummary()
    } catch (error: any) {
      notificationStore.error('数据集摘要加载失败', error?.response?.data?.detail || '请稍后重试。')
    }
  },
)

watch(
  () => activeRunId.value,
  async (runId) => {
    selectedNodeRunDetail.value = null
    resultPanelHeight.value = 0
    if (!runId) {
      activeRunDetail.value = null
      return
    }
    await loadActiveRunDetail(runId)
    if (selectedNodeId.value) {
      await loadSelectedNodeRunDetail(selectedNodeId.value)
    }
  },
)

watch(
  () => selectedNodeId.value,
  async (nodeId) => {
    if (!nodeId || !pipelineRuns.value.length) {
      selectedNodeRunDetail.value = null
      resultPanelHeight.value = 0
      return
    }
    await loadSelectedNodeRunDetail(nodeId)
  },
)

watch(
  () => [isSettingsDialogOpen.value, selectedNodeId.value],
  () => {
    if (!isSettingsDialogOpen.value) return
    if (!selectedNode.value) return
    if (selectedNodeIncomingNodes.value.length) return
    if (!['logistic-model', 'cox-model', 'xgboost', 'random-forest'].includes(selectedNode.value.moduleId)) return
    const current = `${selectedNode.value.values.dataSource ?? ''}`.trim()
    if (!current || current === '上游输出') {
      updateNodeValue(selectedNode.value.id, 'dataSource', '原始数据')
    }
  },
)

watch(
  () => [
    selectedNodeRunDetail.value,
    selectedNodeTables.value.length,
    selectedNodePlots.value.length,
    selectedNodeRunSummary.value?.created_at,
  ],
  async () => {
    await updateResultPanelHeight()
  },
  { deep: true },
)

watch(
  () => [
    selectedProjectId.value,
    workflowName.value,
    canvasNodes.value,
    connections.value,
  ],
  () => {
    saveDraftToLocal()
  },
  { deep: true },
)

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  const lastProjectId = typeof window !== 'undefined'
    ? window.localStorage.getItem('medicode:clinical-model-builder:last-project')
    : null

  void (async () => {
    await loadProjects()
    if (!selectedProjectId.value && lastProjectId) {
      selectedProjectId.value = lastProjectId
    }
    if (selectedProjectId.value) {
      await loadDatasetsForProject(selectedProjectId.value)
    }
    const queryWorkflowId = String(route.query.workflowId || '').trim()
    if (queryWorkflowId) {
      await loadWorkflowFromBackend(queryWorkflowId)
    } else {
      const restored = restoreDraftFromLocal(selectedProjectId.value || null)
      if (restored) {
        notificationStore.success('已恢复本地草稿', '你上次编辑的临床模型流程已自动恢复。')
      }
    }
    await refreshPipelineRuns()
    if (selectedDatasetId.value) {
      try {
        await ensureDatasetSummary()
      } catch (error: any) {
        notificationStore.error('数据集摘要加载失败', error?.response?.data?.detail || '请稍后重试。')
      }
    }
  })()
})

watch(
  () => route.query.projectId,
  async (next) => {
    const normalized = String(next || '').trim()
    if (!normalized || normalized === selectedProjectId.value) return
    selectedProjectId.value = normalized
    await loadDatasetsForProject(selectedProjectId.value)
  },
)

watch(
  () => route.query.workflowId,
  async (next) => {
    const normalized = String(next || '').trim()
    if (!normalized || normalized === savedWorkflowId.value) return
    await loadWorkflowFromBackend(normalized)
  },
)

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('mousemove', handleNodeDrag)
  window.removeEventListener('mouseup', stopNodeDrag)
  window.removeEventListener('mousemove', handleSelectionDrag)
  window.removeEventListener('mouseup', stopSelectionDrag)
  window.removeEventListener('mousemove', handleCanvasPan)
  window.removeEventListener('mouseup', stopCanvasPan)
})
</script>

<style scoped>
.node-canvas {
  position: relative;
  height: clamp(640px, 78vh, 940px);
  overflow: auto;
  cursor: default;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background:
    linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.08), transparent 28%),
    #f8fafc;
  background-size: 28px 28px, 28px 28px, auto, auto;
}

.node-canvas.is-panning {
  cursor: grabbing;
}

.node-canvas-shell {
  position: relative;
}

.canvas-surface {
  position: relative;
  transform-origin: top left;
}

.node-card {
  width: 264px;
  user-select: none;
}

.node-card.is-selected {
  z-index: 20;
}

.node-card.is-selected > div {
  box-shadow:
    0 0 0 2px rgba(16, 185, 129, 0.35),
    0 22px 48px -30px rgba(15, 23, 42, 0.45);
}

.node-card.is-running > div {
  animation: nodePulse 1.4s ease-in-out infinite;
}

@keyframes nodePulse {
  0% {
    box-shadow:
      0 0 0 0 rgba(16, 185, 129, 0.22),
      0 22px 48px -30px rgba(15, 23, 42, 0.45);
  }
  50% {
    box-shadow:
      0 0 0 8px rgba(16, 185, 129, 0.06),
      0 28px 56px -34px rgba(16, 185, 129, 0.38);
  }
  100% {
    box-shadow:
      0 0 0 0 rgba(16, 185, 129, 0.18),
      0 22px 48px -30px rgba(15, 23, 42, 0.45);
  }
}

.node-port {
  position: absolute;
  top: 76px;
  z-index: 30;
  display: inline-flex;
  height: 20px;
  width: 20px;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  padding: 0;
}

.node-port span {
  display: block;
  height: 12px;
  width: 12px;
  border-radius: 9999px;
  background: #ffffff;
  border: 3px solid #94a3b8;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.92);
  transition: all 0.18s ease;
}

.node-port:hover span,
.node-port.is-armed span {
  border-color: #10b981;
  box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.14);
}

.node-port-input.is-connectable span {
  border-color: #10b981;
  box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.14);
}

.node-port-input.is-blocked span {
  border-color: #ef4444;
  box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.14);
}

.node-port-input {
  left: -10px;
}

.node-port-output {
  right: -10px;
}

.node-port-output-train {
  top: 58px;
  right: -10px;
}

.node-port-output-train span {
  border-color: #10b981;
  background: #ecfdf5;
}

.node-port-output-test {
  top: 94px;
  right: -10px;
}

.node-port-output-test span {
  border-color: #0ea5e9;
  background: #f0f9ff;
}

.node-port-output-test:hover span,
.node-port-output-test.is-armed span {
  border-color: #0284c7;
  box-shadow: 0 0 0 6px rgba(14, 165, 233, 0.14);
}

.node-port-label {
  position: absolute;
  right: 22px;
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  font-size: 10px;
  font-style: normal;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.04em;
  color: #64748b;
  pointer-events: none;
  opacity: 0.85;
  transition: opacity 0.16s ease;
}

.node-port:hover .node-port-label {
  opacity: 1;
}

.node-port-output-train .node-port-label {
  color: #059669;
}

.node-port-output-test .node-port-label {
  color: #0284c7;
}

.connection-hit-path {
  fill: none;
  stroke: transparent;
  stroke-width: 18;
  cursor: pointer;
}

.selection-marquee {
  fill: rgba(16, 185, 129, 0.1);
  stroke: rgba(16, 185, 129, 0.7);
  stroke-width: 2;
  stroke-dasharray: 8 6;
}

.canvas-zoom-btn {
  display: inline-flex;
  height: 30px;
  width: 30px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  font-size: 16px;
  font-weight: 700;
  transition: all 0.15s ease;
}

.canvas-zoom-btn:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
}

.canvas-icon-btn {
  display: inline-flex;
  height: 40px;
  width: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.92);
  color: #475569;
  transition: all 0.18s ease;
}

.canvas-icon-btn:hover {
  border-color: rgba(148, 163, 184, 0.8);
  background: #ffffff;
  color: #0f172a;
  transform: translateY(-1px);
}

.canvas-icon-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
  transform: none;
}

.canvas-icon-btn.is-primary {
  border-color: rgba(16, 185, 129, 0.28);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(16, 185, 129, 0.05));
  color: #047857;
  box-shadow: 0 14px 28px -22px rgba(16, 185, 129, 0.55);
}

.settings-modal-body .tool-input {
  min-height: 36px;
  padding-top: 7px;
  padding-bottom: 7px;
  font-size: 13px;
}

.settings-card {
  box-shadow: 0 8px 18px -18px rgba(15, 23, 42, 0.14);
}

.node-run-inline-btn {
  position: relative;
  display: inline-flex;
  height: 32px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.24);
  background: rgba(16, 185, 129, 0.08);
  padding: 0 12px;
  color: #059669;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  transition: all 0.18s ease;
}

.node-run-inline-btn::before {
  content: '';
  position: absolute;
  left: 50%;
  bottom: calc(100% + 2px);
  height: 8px;
  width: 8px;
  border-left: 1px solid rgba(226, 232, 240, 0.96);
  border-top: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.98);
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) rotate(45deg);
  transition: opacity 0.16s ease, bottom 0.16s ease;
}

.node-run-inline-btn::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 50%;
  bottom: calc(100% + 10px);
  width: max-content;
  min-width: 112px;
  max-width: 168px;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.98);
  color: #0f172a;
  padding: 7px 9px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  text-align: center;
  white-space: normal;
  opacity: 0;
  pointer-events: none;
  box-shadow: 0 14px 24px -20px rgba(15, 23, 42, 0.32);
  transform: translateX(-50%) translateY(4px);
  transition: opacity 0.16s ease, transform 0.16s ease;
  z-index: 35;
}

.node-run-inline-btn:hover,
.node-run-inline-btn:focus-visible {
  border-color: rgba(5, 150, 105, 0.32);
  background: rgba(16, 185, 129, 0.12);
}

.node-run-inline-btn:hover::before,
.node-run-inline-btn:hover::after,
.node-run-inline-btn:focus-visible::before,
.node-run-inline-btn:focus-visible::after {
  opacity: 1;
}

.node-run-inline-btn:hover::before,
.node-run-inline-btn:focus-visible::before {
  bottom: calc(100% + 6px);
}

.node-run-inline-btn:hover::after,
.node-run-inline-btn:focus-visible::after {
  transform: translateX(-50%) translateY(0);
}

.node-run-inline-btn.is-busy {
  border-color: rgba(14, 165, 233, 0.28);
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
  cursor: progress;
}

.node-tool-btn {
  position: relative;
  display: inline-flex;
  height: 30px;
  width: 30px;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: #ffffff;
  color: #64748b;
  transition: all 0.18s ease;
}

.node-tool-btn::before {
  content: '';
  position: absolute;
  left: 50%;
  bottom: calc(100% + 2px);
  height: 8px;
  width: 8px;
  border-left: 1px solid rgba(226, 232, 240, 0.96);
  border-top: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.98);
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) rotate(45deg);
  transition: opacity 0.16s ease, bottom 0.16s ease;
}

.node-tool-btn::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 50%;
  bottom: calc(100% + 10px);
  width: max-content;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.98);
  color: #0f172a;
  padding: 5px 8px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  box-shadow: 0 14px 24px -20px rgba(15, 23, 42, 0.32);
  transform: translateX(-50%) translateY(4px);
  transition: opacity 0.16s ease, transform 0.16s ease;
  z-index: 35;
}

.node-tool-btn:hover {
  border-color: rgba(16, 185, 129, 0.28);
  color: #047857;
  background: #f8fffc;
}

.node-tool-btn:hover::before,
.node-tool-btn:hover::after,
.node-tool-btn:focus-visible::before,
.node-tool-btn:focus-visible::after {
  opacity: 1;
}

.node-tool-btn:hover::before,
.node-tool-btn:focus-visible::before {
  bottom: calc(100% + 6px);
}

.node-tool-btn:hover::after,
.node-tool-btn:focus-visible::after {
  transform: translateX(-50%) translateY(0);
}

.node-tool-btn.is-primary {
  border-color: rgba(16, 185, 129, 0.26);
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.node-tool-btn.is-busy {
  border-color: rgba(14, 165, 233, 0.28);
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
  cursor: progress;
}

.node-tool-btn.is-result-ready {
  border-color: rgba(14, 165, 233, 0.22);
  color: #0369a1;
  background: rgba(14, 165, 233, 0.05);
}

.node-tool-btn.is-muted {
  color: #94a3b8;
}

.module-library-scroll {
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  padding-right: 2px;
}

.module-library-card {
  width: 100%;
  min-height: 0;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.94);
  padding: 8px 10px;
  text-align: left;
  box-shadow: 0 8px 16px -16px rgba(15, 23, 42, 0.24);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.module-library-card:hover {
  transform: translateY(-1px);
  border-color: rgba(16, 185, 129, 0.22);
  background: #ffffff;
  box-shadow: 0 12px 22px -20px rgba(16, 185, 129, 0.28);
}

.module-library-card.is-dragging {
  border-color: rgba(16, 185, 129, 0.28);
  background: rgba(236, 253, 245, 0.92);
  box-shadow: 0 14px 24px -20px rgba(16, 185, 129, 0.32);
}

.module-library-card__icon {
  display: inline-flex;
  height: 30px;
  width: 30px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.32);
}

.result-tab-pill {
  display: inline-flex;
  height: 36px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: #ffffff;
  color: #64748b;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.16s ease;
}

.result-tab-pill:hover {
  border-color: rgba(148, 163, 184, 0.78);
  color: #0f172a;
}

.result-tab-pill.is-active {
  border-color: rgba(16, 185, 129, 0.24);
  background: rgba(16, 185, 129, 0.08);
  color: #047857;
}

.result-tab-panel.is-measure-hidden {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  visibility: hidden;
  pointer-events: none;
  z-index: -1;
}

.canvas-overlay-top {
  position: absolute;
  top: 14px;
  left: 50%;
  z-index: 60;
  width: 100%;
  display: flex;
  justify-content: center;
  pointer-events: none;
  transform: translateX(-50%);
}

.canvas-overlay-bottom {
  position: absolute;
  bottom: 14px;
  left: 50%;
  z-index: 58;
  width: 100%;
  display: flex;
  justify-content: center;
  pointer-events: none;
  padding: 0 16px;
  transform: translateX(-50%);
}

.canvas-dock {
  pointer-events: auto;
  display: flex;
  width: fit-content;
  max-width: calc(100% - 32px);
  margin: 0;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  padding: 10px;
  box-shadow: 0 22px 44px -28px rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(16px);
}

.template-picker {
  pointer-events: auto;
  width: min(720px, calc(100% - 32px));
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  padding: 14px;
  box-shadow: 0 22px 44px -28px rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(16px);
}

.canvas-dock-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.95);
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
  height: 40px;
  width: 40px;
  padding: 0;
  transition: all 0.18s ease;
}

.canvas-dock-btn::after {
  content: attr(data-tooltip);
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%) translateY(-4px);
  white-space: nowrap;
  border-radius: 6px;
  border: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.98);
  color: #0f172a;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.01em;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.16s ease, transform 0.16s ease;
  box-shadow: 0 10px 20px -18px rgba(15, 23, 42, 0.28);
}

.canvas-dock-btn:hover {
  border-color: rgba(148, 163, 184, 0.75);
  background: #ffffff;
  color: #0f172a;
  transform: translateY(-1px);
}

.canvas-dock-btn:hover::after {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.canvas-dock-btn.is-primary {
  border-color: rgba(16, 185, 129, 0.26);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.14), rgba(16, 185, 129, 0.04));
  color: #047857;
  box-shadow: 0 14px 28px -20px rgba(16, 185, 129, 0.65);
}

@media (max-width: 1024px) {
  .module-library-scroll {
    max-height: none;
    overflow-y: visible;
    padding-right: 0;
  }

  .canvas-overlay-top {
    top: 10px;
  }

  .canvas-dock {
    border-radius: 16px;
  }
}
</style>
