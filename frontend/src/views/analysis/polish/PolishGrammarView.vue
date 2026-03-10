<template>
  <div class="scipolish-root flex min-h-screen flex-col p-3 md:p-5">
    <header class="mx-auto mb-2 w-full max-w-7xl" data-purpose="top-navigation-controls">
      <div class="custom-shadow flex flex-wrap items-center justify-center gap-x-5 gap-y-2 rounded-[24px] bg-white/80 px-4 py-3 backdrop-blur-xl">
        <div
          class="control-card control-card-intensity"
          data-purpose="intensity-selector"
          @mouseenter="intensityDrawerOpen = true"
          @mouseleave="intensityDrawerOpen = false"
        >
          <div class="flex min-w-0 items-center gap-2">
            <div class="control-icon control-icon-teal">
              <CircleGauge :size="15" />
            </div>
            <span class="control-title">润色强度</span>
          </div>
          <div class="shrink-0">
            <button class="control-trigger" type="button" aria-label="Open intensity options">
              <ChevronDown :size="14" />
            </button>
          </div>

          <Transition name="drawer-down">
            <div
              v-if="intensityDrawerOpen"
              class="drawer-panel absolute left-0 top-[calc(100%+8px)] z-20 w-full"
            >
              <button
                v-for="option in intensityOptions"
                :key="option.id"
                class="drawer-option compact"
                :class="selectedIntensity === option.id ? 'drawer-option-active' : ''"
                type="button"
                @click="selectIntensity(option.id)"
              >
                <div class="flex items-center gap-2">
                  <component :is="option.icon" :size="14" class="shrink-0" />
                  <span class="drawer-label">{{ option.label }}</span>
                </div>
                <Check v-if="selectedIntensity === option.id" :size="13" class="text-teal-600" />
              </button>
            </div>
          </Transition>
        </div>

        <div class="control-card" data-purpose="term-protection-toggle">
          <label class="flex min-w-0 cursor-pointer items-center gap-2">
            <div class="control-icon control-icon-blue">
              <ShieldCheck :size="15" />
            </div>
                    <span class="control-title">术语保护</span>
            <input v-model="protectTerms" type="checkbox" class="peer sr-only" />
            <span class="check-square">
              <Check :size="12" class="check-square-icon" />
            </span>
    
          </label>
        </div>

        <div class="control-card" data-purpose="structure-protection-toggle">
          <label class="flex min-w-0 cursor-pointer items-center gap-2">
            <div class="control-icon control-icon-violet">
              <GitBranchPlus :size="15" />
            </div>
            <span class="control-title">结构保留</span>
            <input v-model="preserveStructure" type="checkbox" class="peer sr-only" />
            <span class="check-square">
              <Check :size="12" class="check-square-icon" />
            </span>
            
          </label>
        </div>
      </div>
    </header>

    <main
      class="mx-auto grid w-full max-w-7xl flex-grow grid-cols-1 gap-4 overflow-hidden pb-24 lg:grid-cols-12"
      data-purpose="editor-grid"
    >
      <section class="flex h-full flex-col lg:col-span-4" data-purpose="original-text-column">
        <div class="custom-shadow flex h-full flex-col rounded-3xl border border-gray-50 bg-white">
          <div class="flex items-center justify-between border-b border-gray-50 p-5">
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">Original Text</h2>
            <div class="flex gap-2">
              <button
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
                type="button"
                title="Use sample"
                @click="useSampleContent"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                </svg>
              </button>
              <button
                class="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
                type="button"
                title="Apply prompt"
                @click="applyCommandInput"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                  />
                </svg>
              </button>
            </div>
          </div>
          <div class="no-scrollbar flex-grow overflow-y-auto p-6">
            <div class="space-y-6 text-sm leading-relaxed text-gray-700">
              <p v-for="section in originalSections" :key="section.id">
                <strong>{{ section.label }}:</strong>
                {{ section.text }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section class="flex h-full flex-col lg:col-span-5" data-purpose="polished-results-column">
        <div class="custom-shadow flex h-full flex-col rounded-3xl border border-gray-50 bg-white">
          <div class="border-b border-gray-50 p-5">
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">Polished Results</h2>
          </div>
          <div class="no-scrollbar flex-grow overflow-y-auto p-6">
            <div class="space-y-6 text-sm leading-relaxed text-gray-800">
              <p v-for="section in polishedSections" :key="section.id">
                <strong>{{ section.label }}:</strong>
                <template v-for="segment in section.segments" :key="segment.id">
                  <template v-if="segment.kind === 'text'">
                    {{ segment.text }}
                  </template>
                  <span v-else class="relative group" :class="segment.block ? 'mt-2 block' : ''">
                    <span :class="isAccepted(segment.id) ? 'highlight-teal px-1' : ''">
                      {{ isAccepted(segment.id) ? segment.revisedText : segment.originalText }}
                    </span>
                    <span class="absolute -right-2 top-0 flex translate-x-full gap-1">
                      <button
                        class="btn-icon rounded-full bg-teal-500 p-1 text-white shadow-md disabled:opacity-60"
                        type="button"
                        :disabled="isAccepted(segment.id)"
                        @click="setSuggestionState(segment.id, true)"
                      >
                        <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fill-rule="evenodd"
                            clip-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          />
                        </svg>
                      </button>
                      <button
                        class="btn-icon rounded-full bg-rose-100 p-1 text-rose-500 shadow-md disabled:opacity-60"
                        type="button"
                        :disabled="!isAccepted(segment.id)"
                        @click="setSuggestionState(segment.id, false)"
                      >
                        <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fill-rule="evenodd"
                            clip-rule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          />
                        </svg>
                      </button>
                    </span>
                  </span>
                </template>
              </p>
            </div>
          </div>
        </div>
      </section>

      <section class="no-scrollbar flex flex-col gap-4 overflow-y-auto lg:col-span-3" data-purpose="insights-column">
        <h2 class="px-2 text-xs font-bold uppercase tracking-widest text-gray-500">Suggestions &amp; Insights</h2>
        <div
          v-for="card in insightCards"
          :key="card.title"
          class="custom-shadow space-y-4 rounded-3xl border border-gray-50 bg-white p-5"
          data-purpose="insight-card"
        >
          <div class="flex items-center gap-3">
            <div class="rounded-xl p-2" :class="card.tintClass">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  :d="card.iconPath"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                />
              </svg>
            </div>
            <h3 class="font-bold text-gray-700">{{ card.title }}</h3>
          </div>
          <ul class="space-y-3 text-sm text-gray-600">
            <li
              v-for="item in card.items"
              :key="item"
              class="group flex cursor-pointer items-center justify-between hover:text-teal-600"
            >
              <span>• {{ item }}</span>
              <svg class="h-4 w-4 opacity-0 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
            </li>
          </ul>
        </div>
      </section>
    </main>

    <footer class="fixed bottom-8 left-1/2 w-full max-w-2xl -translate-x-1/2 px-4" data-purpose="bottom-bar">
      <div class="custom-shadow flex flex-wrap items-center gap-3 rounded-2xl border border-white bg-white/90 p-2 backdrop-blur-md md:flex-nowrap">
        <button class="btn-icon rounded-xl bg-gray-50 p-3 text-gray-500 hover:bg-gray-100" type="button" @click="useSampleContent">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
          </svg>
        </button>

        <button
          class="flex items-center gap-2 rounded-xl bg-gray-50 px-4 py-2 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-100"
          type="button"
          @click="useSampleContent"
        >
          <svg class="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              d="M13 10V3L4 14h7v7l9-11h-7z"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
            />
          </svg>
          <span>Inspiration <span class="ml-1 text-xs">▼</span></span>
        </button>

        <div class="flex flex-grow items-center rounded-xl bg-gray-50 px-4 py-2 ring-teal-500/20 focus-within:ring-2">
          <input
            v-model="commandInput"
            class="w-full border-none bg-transparent text-sm placeholder-gray-400 focus:ring-0"
            placeholder="Enter your text here for polishing..."
            type="text"
            @keydown.enter.prevent="applyCommandInput"
          />
          <button class="p-1 text-gray-400 hover:text-gray-600" type="button">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
              />
            </svg>
          </button>
        </div>

        <button
          class="btn-icon rounded-xl bg-teal-400 p-3 text-white shadow-lg shadow-teal-500/30 hover:bg-teal-500"
          type="button"
          @click="applyCommandInput"
        >
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M5 10l7-7m0 0l7 7m-7-7v18" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" />
          </svg>
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Check, ChevronDown, CircleGauge, GitBranchPlus, ShieldCheck, WandSparkles } from 'lucide-vue-next'

type OriginalSection = {
  id: string
  label: string
  text: string
}

type TextSegment = {
  id: string
  kind: 'text'
  text: string
}

type SuggestionSegment = {
  id: string
  kind: 'suggestion'
  originalText: string
  revisedText: string
  block?: boolean
}

type PolishedSection = {
  id: string
  label: string
  segments: Array<TextSegment | SuggestionSegment>
}

type InsightCard = {
  title: string
  tintClass: string
  iconPath: string
  items: string[]
}

type IntensityOption = {
  id: 'conservative' | 'standard' | 'advanced'
  label: string
  icon: unknown
}

const intensityOptions: IntensityOption[] = [
  {
    id: 'conservative',
    label: '保守纠错',
    icon: ShieldCheck,
  },
  {
    id: 'standard',
    label: '标准润色',
    icon: CircleGauge,
  },
  {
    id: 'advanced',
    label: '深度润色',
    icon: WandSparkles,
  },
]

const selectedIntensity = ref<IntensityOption['id']>('standard')
const intensityDrawerOpen = ref(false)
const protectTerms = ref(true)
const preserveStructure = ref(false)
const commandInput = ref('')
const customText = ref('')

const suggestionState = reactive<Record<string, boolean>>({
  'background-edit': true,
  'methods-edit': true,
})

const sampleOriginalSections: OriginalSection[] = [
  {
    id: 'background',
    label: 'Background',
    text: 'Chronic pain is a prevalent condition affecting a significant portion of the population, leading to reduced quality of life and increased healthcare utilization. Current treatments often have limited efficacy and can be associated with side effects.',
  },
  {
    id: 'methods',
    label: 'Methods',
    text: 'We conducted a double-blind, randomized, placebo-controlled trial to evaluate the efficacy and safety of a novel non-opioid analgesic in patients with chronic low back pain. A total of 200 participants were enrolled and randomized to receive either the investigational drug or a matching placebo for 12 weeks.',
  },
  {
    id: 'results',
    label: 'Results',
    text: 'The primary endpoint was the change in pain intensity from baseline to week 12, measured using a numerical rating scale (NRS). The results showed a statistically significant reduction in pain scores in the active treatment group compared to the placebo group (p < 0.001). Secondary endpoints, including functional improvement and patient-reported outcomes, also demonstrated favorable results.',
  },
  {
    id: 'conclusions',
    label: 'Conclusions',
    text: 'Our findings suggest that the novel non-opioid analgesic is effective and safe for the management of chronic low back pain. Further studies are warranted to confirm these results and assess long-term efficacy.',
  },
]

const samplePolishedSections: PolishedSection[] = [
  {
    id: 'background',
    label: 'Background',
    segments: [
      {
        id: 'background-text',
        kind: 'text',
        text: 'Chronic pain is a prevalent condition affecting a significant portion of the population, leading to reduced quality of life and increased healthcare utilization. Current treatments often have limited ',
      },
      {
        id: 'background-edit',
        kind: 'suggestion',
        originalText: 'efficacy and can be associated with side effects.',
        revisedText: 'Existing therapies frequently demonstrate constrained efficacy and may entail adverse effects.',
      },
    ],
  },
  {
    id: 'methods',
    label: 'Methods',
    segments: [
      {
        id: 'methods-text',
        kind: 'text',
        text: 'We conducted a double-blind, randomized, placebo-controlled trial to evaluate the efficacy and safety of a novel non-opioid analgesic in patients with chronic low back pain. A total of 200 participants were ',
      },
      {
        id: 'methods-edit',
        kind: 'suggestion',
        originalText: 'enrolled and randomized to receive either the investigational drug or a matching placebo for 12 weeks.',
        revisedText:
          'Two hundred subjects were recruited and randomly assigned to receive either the investigational pharmacological agent or a corresponding placebo for a 12-week duration.',
        block: true,
      },
    ],
  },
  {
    id: 'results',
    label: 'Results',
    segments: [
      {
        id: 'results-text',
        kind: 'text',
        text: 'The primary endpoint was the change in pain intensity from baseline to week 12, measured using a numerical rating scale (NRS). The results showed a statistically significant reduction in pain scores in the active treatment group compared to the placebo group (p < 0.001). Secondary endpoints, including functional improvement and patient-reported outcomes, also demonstrated favorable results.',
      },
    ],
  },
  {
    id: 'conclusions',
    label: 'Conclusions',
    segments: [
      {
        id: 'conclusions-text',
        kind: 'text',
        text: 'Our findings suggest that the novel non-opioid analgesic is effective and safe for the management of chronic low back pain. Further studies are warranted to confirm these results and assess long-term efficacy.',
      },
    ],
  },
]

const insightCards: InsightCard[] = [
  {
    title: 'Grammar & Syntax',
    tintClass: 'bg-blue-50 text-blue-500',
    iconPath:
      'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
    items: ['Enhance sentence structure', 'Correct verb tense usage', 'Improve punctuation marks'],
  },
  {
    title: 'Tone & Clarity',
    tintClass: 'bg-amber-50 text-amber-500',
    iconPath: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    items: ['Adopt formal academic tone', 'Ensure precise terminology'],
  },
  {
    title: 'Structure & Flow',
    tintClass: 'bg-purple-50 text-purple-500',
    iconPath: 'M9.663 17h4.674a1 1 0 00.922-.617l2.108-4.742A1 1 0 0016.446 10h-2.108l.392-3.137a1 1 0 00-1.543-1.026l-7.477 9.471a1 1 0 00.747 1.692z',
    items: ['Strengthen logical transitions', 'Optimize info hierarchy'],
  },
]

const isUsingSample = computed(() => customText.value.trim().length === 0)

const originalSections = computed(() => {
  if (isUsingSample.value) return sampleOriginalSections
  return parseCustomSections(customText.value)
})

const polishedSections = computed<PolishedSection[]>(() => {
  if (isUsingSample.value) return samplePolishedSections
  return originalSections.value.map(section => ({
    id: section.id,
    label: section.label,
    segments: [
      {
        id: `${section.id}-text`,
        kind: 'text',
        text: section.text,
      },
    ],
  }))
})

function parseCustomSections(text: string): OriginalSection[] {
  return text
    .split(/\n\s*\n/)
    .map(paragraph => paragraph.trim())
    .filter(Boolean)
    .map((paragraph, index) => {
      const match = paragraph.match(/^([A-Za-z][A-Za-z /-]{1,40}):\s*(.*)$/s)
      if (match) {
        return {
          id: `custom-${index + 1}`,
          label: match[1].trim(),
          text: match[2].trim(),
        }
      }

      return {
        id: `custom-${index + 1}`,
        label: `Paragraph ${index + 1}`,
        text: paragraph,
      }
    })
}

function isAccepted(id: string) {
  return suggestionState[id] !== false
}

function selectIntensity(id: IntensityOption['id']) {
  selectedIntensity.value = id
  intensityDrawerOpen.value = false
}

function setSuggestionState(id: string, accepted: boolean) {
  suggestionState[id] = accepted
}

function useSampleContent() {
  customText.value = ''
  commandInput.value = ''
  suggestionState['background-edit'] = true
  suggestionState['methods-edit'] = true
}

function applyCommandInput() {
  const trimmed = commandInput.value.trim()
  if (!trimmed) return
  customText.value = trimmed
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.scipolish-root {
  --intensity-card-width: min(220px, 76vw);
  font-family: 'Inter', sans-serif;
  background-color: #f8fafc;
}

.custom-shadow {
  box-shadow:
    0 20px 40px -32px rgba(15, 23, 42, 0.18),
    0 10px 20px -18px rgba(15, 23, 42, 0.08);
}

.control-card {
  position: relative;
  display: flex;
  flex: 0 0 auto;
  width: var(--intensity-card-width);
  min-width: var(--intensity-card-width);
  max-width: var(--intensity-card-width);
  min-height: 44px;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  overflow: visible;
  border-radius: 18px;
  padding: 0.2rem 0.85rem;
}

.control-card-intensity {
  z-index: 10;
}

.control-icon {
  display: flex;
  height: 1.75rem;
  width: 1.75rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: transparent;
  color: #64748b;
  transition:
    background-color 0.25s ease,
    color 0.25s ease,
    box-shadow 0.25s ease;
}

.control-icon-teal:hover,
.control-card:hover .control-icon-teal {
  background: rgba(236, 253, 245, 0.92);
  color: #0f766e;
  box-shadow: 0 8px 18px -14px rgba(13, 148, 136, 0.35);
}

.control-icon-blue:hover,
.control-card:hover .control-icon-blue {
  background: rgba(239, 246, 255, 0.94);
  color: #2563eb;
  box-shadow: 0 8px 18px -14px rgba(37, 99, 235, 0.3);
}

.control-icon-violet:hover,
.control-card:hover .control-icon-violet {
  background: rgba(245, 243, 255, 0.94);
  color: #7c3aed;
  box-shadow: 0 8px 18px -14px rgba(124, 58, 237, 0.28);
}

.control-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: #334155;
}

.control-trigger {
  display: flex;
  height: 1.7rem;
  width: 1.7rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  color: #94a3b8;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.control-trigger:hover {
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
}

.check-square {
  display: inline-flex;
  height: 1rem;
  width: 1rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.22rem;
  border: 1px solid rgba(203, 213, 225, 0.95);
  background: #fff;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.check-square-icon {
  opacity: 0;
  color: #ffffff;
  transition: opacity 0.2s ease;
}

.peer:checked + .check-square {
  border-color: rgba(13, 148, 136, 0.9);
  background: linear-gradient(135deg, rgba(45, 212, 191, 0.95), rgba(13, 148, 136, 0.95));
  box-shadow: 0 8px 16px -12px rgba(13, 148, 136, 0.75);
}

.peer:checked + .check-square .check-square-icon {
  opacity: 1;
}

.drawer-panel {
  width: var(--intensity-card-width);
  min-width: var(--intensity-card-width);
  max-width: var(--intensity-card-width);
  border-radius: 0 0 10px 10px;
  background: rgba(255, 255, 255, 0.96);
  padding: 0;
  box-shadow:
    0 20px 44px -30px rgba(15, 23, 42, 0.24),
    0 10px 18px -16px rgba(15, 23, 42, 0.12);
  overflow: hidden;
  box-sizing: border-box;
}

.drawer-option {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-radius: 0;
  padding: 0.65rem 0.75rem;
  text-align: left;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.drawer-option.compact {
  padding-top: 0.55rem;
  padding-bottom: 0.55rem;
}

.drawer-option:hover {
  background: rgba(248, 250, 252, 0.98);
}

.drawer-option-active {
  background: linear-gradient(135deg, rgba(204, 251, 241, 0.95), rgba(240, 253, 250, 0.98));
  box-shadow: inset 0 0 0 1px rgba(45, 212, 191, 0.35);
}

.drawer-label {
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
}

.drawer-down-enter-active,
.drawer-down-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
  transform-origin: top right;
}

.drawer-down-enter-from,
.drawer-down-leave-to {
  opacity: 0;
  transform: translateY(-6px) scaleY(0.94);
}

.drawer-down-enter-to,
.drawer-down-leave-from {
  opacity: 1;
  transform: translateY(0) scaleY(1);
}

.highlight-teal {
  background-color: #e6fffa;
  border-radius: 4px;
  padding: 2px 0;
}

.btn-icon {
  transition: all 0.2s;
}

.btn-icon:hover {
  transform: scale(1.1);
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
