<template>
  <Teleport to="body">
    <div v-if="visible" class="payment-overlay" @click.self="handleClose">
      <div class="payment-dialog animate-scale-in">
        <!-- Close button -->
        <button class="close-btn" @click="handleClose">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>

        <!-- ===== STEP 1: Confirm Order ===== -->
        <div v-if="step === 'confirm'" class="dialog-body">
          <div class="step-icon bg-primary-50">
            <svg class="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
          </div>
          <h2 class="dialog-title">确认订单</h2>

          <div class="order-card">
            <div class="order-row">
              <span class="order-label">套餐</span>
              <span class="order-value font-semibold">{{ pkg?.name }}</span>
            </div>
            <div class="order-row">
              <span class="order-label">Token 数量</span>
              <span class="order-value text-primary font-semibold">{{ pkg?.tokens }}</span>
            </div>
            <div class="order-row">
              <span class="order-label">单价</span>
              <span class="order-value">¥{{ pkg?.unitPrice }}/Token</span>
            </div>
            <div class="order-divider"></div>
            <div class="order-row">
              <span class="order-label text-base font-semibold">应付金额</span>
              <span class="order-total">¥{{ pkg?.price }}</span>
            </div>
          </div>

          <div class="payment-method">
            <div class="method-selected">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none">
                <rect width="24" height="24" rx="4" fill="#1677FF"/>
                <path d="M6 12L18 12M6 8L18 8M6 16L14 16" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <span class="text-sm font-medium text-gray-700">支付宝扫码支付</span>
              <svg class="w-4 h-4 text-primary ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
          </div>

          <button class="pay-btn" @click="handleCreateOrder">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            确认支付 ¥{{ pkg?.price }}
          </button>
        </div>

        <!-- ===== STEP 2: QR Code ===== -->
        <div v-else-if="step === 'qrcode'" class="dialog-body">
          <div class="step-icon bg-blue-50">
            <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          </div>
          <h2 class="dialog-title">扫码支付</h2>
          <p class="dialog-subtitle">请使用支付宝 App 扫描下方二维码完成支付</p>

          <div class="qr-container">
            <div class="qr-frame">
              <!-- Loading state -->
              <div v-if="qrLoading" class="qr-loading">
                <div class="spinner"></div>
                <p class="text-sm text-gray-500 mt-3">正在生成支付码...</p>
              </div>
              <!-- QR code canvas -->
              <canvas v-show="!qrLoading && !qrError" ref="qrCanvas" class="qr-canvas"></canvas>
              <!-- Error state -->
              <div v-if="qrError" class="qr-error">
                <svg class="w-10 h-10 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                <p class="text-sm text-red-500 mt-2">二维码生成失败</p>
                <button class="retry-btn" @click="handleCreateOrder">重试</button>
              </div>
            </div>
            <!-- Alipay logo decoration -->
            <div class="alipay-badge">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none"><rect width="24" height="24" rx="4" fill="#1677FF"/><path d="M6 12L18 12M6 8L18 8M6 16L14 16" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span>支付宝安全支付</span>
            </div>
          </div>

          <div class="qr-info">
            <div class="info-row">
              <span>订单金额</span>
              <span class="text-lg font-bold text-gray-900">¥{{ pkg?.price }}</span>
            </div>
            <div class="info-row">
              <span>订单号</span>
              <span class="text-xs text-gray-400 font-mono">{{ orderId }}</span>
            </div>
            <div class="info-row">
              <span>支付状态</span>
              <span class="status-polling">
                <span class="polling-dot"></span>
                等待扫码支付...
              </span>
            </div>
          </div>

          <p class="qr-expire">二维码有效期 5 分钟，过期请重新生成</p>
        </div>

        <!-- ===== STEP 3: Success ===== -->
        <div v-else-if="step === 'success'" class="dialog-body">
          <div class="success-icon-wrapper">
            <div class="success-ring"></div>
            <div class="step-icon bg-green-50 success-bounce">
              <svg class="w-10 h-10 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
          </div>
          <h2 class="dialog-title text-green-600">支付成功！</h2>
          <p class="dialog-subtitle">Token 已充值到您的账户</p>

          <div class="success-card">
            <div class="success-row">
              <span>充值 Token</span>
              <span class="text-2xl font-bold text-primary">+{{ pkg?.tokens }}</span>
            </div>
            <div class="success-row">
              <span>支付金额</span>
              <span class="font-semibold text-gray-900">¥{{ pkg?.price }}</span>
            </div>
            <div class="success-row">
              <span>订单号</span>
              <span class="text-xs text-gray-400 font-mono">{{ orderId }}</span>
            </div>
          </div>

          <button class="done-btn" @click="handleDone">
            完成
          </button>
        </div>

        <!-- ===== STEP: Failed ===== -->
        <div v-else-if="step === 'failed'" class="dialog-body">
          <div class="step-icon bg-red-50">
            <svg class="w-10 h-10 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          </div>
          <h2 class="dialog-title text-red-600">支付失败</h2>
          <p class="dialog-subtitle">{{ errorMessage || '支付过程中出现问题，请重试' }}</p>

          <div class="flex gap-3 mt-6">
            <button class="retry-order-btn" @click="handleCreateOrder">重新支付</button>
            <button class="cancel-order-btn" @click="handleClose">取消</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import QRCode from 'qrcode'
import { createPayment, queryPaymentStatus } from '@/services/api'

interface PackageInfo {
  id: string
  name: string
  price: number
  tokens: number
  unitPrice: string
}

const props = defineProps<{
  visible: boolean
  pkg: PackageInfo | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'success', data: { orderId: string; tokens: number }): void
}>()

type Step = 'confirm' | 'qrcode' | 'success' | 'failed'

const step = ref<Step>('confirm')
const orderId = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)
const qrLoading = ref(false)
const qrError = ref(false)
const errorMessage = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null
let pollTimeout: ReturnType<typeof setTimeout> | null = null

// Reset state when dialog opens
watch(() => props.visible, (val) => {
  if (val) {
    step.value = 'confirm'
    orderId.value = ''
    qrError.value = false
    errorMessage.value = ''
  } else {
    stopPolling()
  }
})

function handleClose() {
  stopPolling()
  emit('update:visible', false)
}

async function handleCreateOrder() {
  if (!props.pkg) return

  qrLoading.value = true
  qrError.value = false
  step.value = 'qrcode'

  try {
    const res = await createPayment({
      packageId: props.pkg.id,
    })

    orderId.value = res.orderId

    // Render QR code
    await nextTick()
    if (qrCanvas.value) {
      await QRCode.toCanvas(qrCanvas.value, res.qrCodeUrl, {
        width: 220,
        margin: 2,
        color: { dark: '#1a1a2e', light: '#ffffff' },
      })
    }
    qrLoading.value = false

    // Start polling for payment status
    startPolling()
  } catch (err: any) {
    console.error('Payment creation failed:', err)
    qrLoading.value = false

    qrError.value = true
    errorMessage.value = err.response?.data?.detail || err.response?.data?.message || '创建订单失败，请稍后重试'
  }
}

function startPolling() {
  stopPolling()
  let elapsed = 0
  const maxDuration = 5 * 60 * 1000 // 5 minutes

  pollTimer = setInterval(async () => {
    elapsed += 3000
    if (elapsed >= maxDuration) {
      stopPolling()
      step.value = 'failed'
      errorMessage.value = '支付超时，请重新下单'
      return
    }

    try {
      const res = await queryPaymentStatus(orderId.value)
      if (res.status === 'paid') {
        stopPolling()
        step.value = 'success'
      } else if (res.status === 'failed' || res.status === 'expired') {
        stopPolling()
        step.value = 'failed'
        errorMessage.value = res.status === 'expired' ? '订单已过期' : '支付失败'
      }
    } catch {
      // Silently continue polling on network errors
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (pollTimeout) { clearTimeout(pollTimeout); pollTimeout = null }
}

function handleDone() {
  emit('success', { orderId: orderId.value, tokens: props.pkg?.tokens || 0 })
  handleClose()
}

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.payment-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.payment-dialog {
  position: relative;
  background: white;
  border-radius: 1.25rem;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 420px;
  max-height: 90vh;
  overflow-y: auto;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  color: #9ca3af;
  transition: all 0.15s;
  cursor: pointer;
  background: transparent;
  border: none;
}
.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.dialog-body {
  padding: 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-icon {
  width: 4rem;
  height: 4rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.dialog-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  font-family: var(--font-heading);
}

.dialog-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.375rem;
  text-align: center;
}

/* Order Card */
.order-card {
  width: 100%;
  margin-top: 1.25rem;
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
}

.order-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.order-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.order-value {
  font-size: 0.875rem;
  color: #111827;
}

.order-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 0.5rem 0;
}

.order-total {
  font-size: 1.5rem;
  font-weight: 700;
  color: #059669;
  font-family: var(--font-heading);
}

/* Payment Method */
.payment-method {
  width: 100%;
  margin-top: 1rem;
}

.method-selected {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 2px solid #059669;
  border-radius: 0.75rem;
  background: #f0fdf4;
}

/* Pay Button */
.pay-btn {
  width: 100%;
  margin-top: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  font-weight: 600;
  font-size: 1rem;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
}
.pay-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(5, 150, 105, 0.4);
}
.pay-btn:active {
  transform: translateY(0);
}

/* QR Code */
.qr-container {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-frame {
  position: relative;
  width: 240px;
  height: 240px;
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  overflow: hidden;
}

.qr-canvas {
  border-radius: 0.5rem;
}

.qr-loading,
.qr-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: #059669;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 0.75rem;
  padding: 0.375rem 1rem;
  font-size: 0.8125rem;
  color: #059669;
  background: #f0fdf4;
  border: 1px solid #059669;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.retry-btn:hover {
  background: #059669;
  color: white;
}

.alipay-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

/* QR Info */
.qr-info {
  width: 100%;
  margin-top: 1.25rem;
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.375rem 0;
  font-size: 0.8125rem;
  color: #6b7280;
}

.status-polling {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: #059669;
  font-weight: 500;
}

.polling-dot {
  width: 0.5rem;
  height: 0.5rem;
  background: #059669;
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.qr-expire {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: center;
}

/* Success */
.success-icon-wrapper {
  position: relative;
  margin-bottom: 0.5rem;
}

.success-ring {
  position: absolute;
  inset: -0.75rem;
  border: 2px solid #bbf7d0;
  border-radius: 1.25rem;
  animation: ring-expand 0.6s ease-out;
}

@keyframes ring-expand {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.success-bounce {
  animation: bounce-in 0.5s ease-out;
}

@keyframes bounce-in {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.1); }
  70% { transform: scale(0.95); }
  100% { transform: scale(1); opacity: 1; }
}

.success-card {
  width: 100%;
  margin-top: 1.5rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
}

.success-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.done-btn {
  width: 100%;
  margin-top: 1.5rem;
  padding: 0.875rem;
  background: #059669;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.done-btn:hover {
  background: #047857;
}

/* Failed state buttons */
.retry-order-btn {
  flex: 1;
  padding: 0.75rem;
  background: #059669;
  color: white;
  font-weight: 600;
  border-radius: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.retry-order-btn:hover {
  background: #047857;
}

.cancel-order-btn {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  color: #6b7280;
  font-weight: 500;
  border-radius: 0.75rem;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.15s;
}
.cancel-order-btn:hover {
  background: #f3f4f6;
}

/* Animation */
.animate-scale-in {
  animation: scaleIn 0.25s ease-out;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
