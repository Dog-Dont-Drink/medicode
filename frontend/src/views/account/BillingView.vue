<template>
  <div class="max-w-4xl mx-auto space-y-8 animate-fade-in pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-heading font-bold text-gray-900">账单管理</h1>
      <p class="text-sm text-gray-500 mt-1">购买 Token 套餐，管理您的订单记录</p>
    </div>

    <!-- Current Balance Card -->
    <div class="balance-card">
      <div class="flex items-center gap-4">
        <div class="balance-icon">
          <svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 100 4h4a2 2 0 010 4H8"/><path d="M12 18V6"/></svg>
        </div>
        <div>
          <p class="text-sm text-white/70">当前 Token 余额</p>
          <p class="text-3xl font-heading font-bold text-white mt-0.5">{{ tokenBalance.toLocaleString() }}</p>
        </div>
      </div>
      <div class="flex items-center gap-4 mt-4 sm:mt-0">
        <div class="text-right hidden sm:block">
          <p class="text-xs text-white/50">套餐等级</p>
          <p class="text-sm font-semibold text-white">{{ currentPlan }}</p>
        </div>
        <div class="w-px h-8 bg-white/20 hidden sm:block"></div>
        <div class="text-right hidden sm:block">
          <p class="text-xs text-white/50">本月已用</p>
          <p class="text-sm font-semibold text-white">{{ usedThisMonth }} Token</p>
        </div>
      </div>
    </div>

    <!-- Token Packages -->
    <div>
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-heading font-semibold text-gray-900">Token 套餐</h2>
        <span class="text-xs text-gray-400">支持支付宝扫码支付</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div v-for="pkg in packages" :key="pkg.id"
          @mouseenter="activePackage = pkg.id"
          @click="activePackage = pkg.id"
          :class="['package-card', activePackage === pkg.id ? 'package-active' : '']"
        >
          <!-- Popular badge -->
          <div v-if="pkg.badge" :class="['popular-badge', activePackage === pkg.id ? 'popular-badge-active' : 'popular-badge-inactive']">
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            {{ pkg.badge }}
          </div>

          <!-- Package content -->
          <div class="package-body">
            <h3 :class="['text-base font-semibold', activePackage === pkg.id ? 'text-white' : 'text-gray-900']">{{ pkg.name }}</h3>
            <div class="mt-3">
              <span class="text-3xl font-heading font-bold" :class="activePackage === pkg.id ? 'text-white' : 'text-gray-900'">¥{{ pkg.price }}</span>
            </div>
            <div class="mt-2 space-y-1">
              <p :class="['text-sm', activePackage === pkg.id ? 'text-white/80' : 'text-gray-600']">
                <span :class="['font-semibold', activePackage === pkg.id ? 'text-white' : 'text-gray-800']">{{ pkg.tokens }}</span> Token
              </p>
              <p :class="['text-xs', activePackage === pkg.id ? 'text-white/60' : 'text-gray-400']">¥{{ pkg.unitPrice }}/Token</p>
            </div>

            <!-- Features list -->
            <ul class="mt-4 space-y-1.5">
              <li v-for="feat in pkg.features" :key="feat" :class="['flex items-center gap-1.5 text-xs', activePackage === pkg.id ? 'text-white/80' : 'text-gray-500']">
                <svg :class="['w-3.5 h-3.5 flex-shrink-0', activePackage === pkg.id ? 'text-white' : 'text-primary']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                {{ feat }}
              </li>
            </ul>
          </div>

          <!-- Purchase button -->
          <button
            :class="['purchase-btn', activePackage === pkg.id ? 'purchase-btn-active' : 'purchase-btn-outline']"
            @click.stop="openPayment(pkg)"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
            立即购买
          </button>
        </div>
      </div>
    </div>

    <!-- Order History -->
    <div>
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-heading font-semibold text-gray-900">订单记录</h2>
        <button class="text-xs text-primary hover:text-primary-600 font-medium transition-colors cursor-pointer">查看全部</button>
      </div>

      <div v-if="orders.length === 0" class="empty-orders">
        <svg class="w-12 h-12 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <p class="text-sm text-gray-400 mt-3">暂无订单记录</p>
      </div>

      <div v-else class="orders-table">
        <table>
          <thead>
            <tr>
              <th>订单号</th>
              <th>套餐</th>
              <th>金额</th>
              <th>Token</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.orderId">
              <td class="font-mono text-xs text-gray-400">{{ order.orderId.slice(0, 16) }}...</td>
              <td class="font-medium text-gray-800">{{ order.packageName }}</td>
              <td class="font-semibold">¥{{ order.amount }}</td>
              <td class="text-primary font-semibold">+{{ order.tokens.toLocaleString() }}</td>
              <td>
                <span :class="['order-status', `status-${order.status}`]">
                  {{ statusLabels[order.status] }}
                </span>
              </td>
              <td class="text-xs text-gray-400">{{ formatTime(order.createdAt) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payment Dialog -->
    <PaymentDialog
      v-model:visible="paymentVisible"
      :pkg="selectedPkg"
      @success="onPaymentSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PaymentDialog from '@/components/PaymentDialog.vue'
import type { OrderRecord } from '@/services/api'

interface Package {
  id: string
  name: string
  price: number
  tokens: string
  unitPrice: string
  badge: string
  features: string[]
}

const tokenBalance = ref(1250)
const currentPlan = ref('专业版')
const usedThisMonth = ref(380)
const activePackage = ref('pro')

const packages = ref<Package[]>([
  {
    id: 'basic',
    name: '基础包',
    price: 49,
    tokens: '500',
    unitPrice: '0.098',
    badge: '',
    features: ['描述统计分析', '基础图表生成', 'CSV/Excel 格式', '邮件支持'],
  },
  {
    id: 'pro',
    name: '专业包',
    price: 199,
    tokens: '2,500',
    unitPrice: '0.080',
    badge: '最受欢迎',
    features: ['全部分析方法', '可复现 R 脚本', '专业报告导出', '优先技术支持'],
  },
  {
    id: 'enterprise',
    name: '企业包',
    price: 499,
    tokens: '8,000',
    unitPrice: '0.062',
    badge: '',
    features: ['无限分析方法', '定制分析模块', 'API 集成接口', '专属技术顾问'],
  },
])

const orders = ref<OrderRecord[]>([
  {
    orderId: 'ORD20260301143200A1B2C3',
    packageName: '专业包',
    amount: 199,
    tokens: 2500,
    status: 'paid',
    createdAt: '2026-02-28T14:32:00Z',
    paidAt: '2026-02-28T14:33:12Z',
  },
  {
    orderId: 'ORD20260215101500D4E5F6',
    packageName: '基础包',
    amount: 49,
    tokens: 500,
    status: 'paid',
    createdAt: '2026-02-15T10:15:00Z',
    paidAt: '2026-02-15T10:16:45Z',
  },
])

const statusLabels: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
  failed: '失败',
  expired: '已过期',
}

// Payment dialog
const paymentVisible = ref(false)
const selectedPkg = ref<Package | null>(null)

function openPayment(pkg: Package) {
  selectedPkg.value = pkg
  paymentVisible.value = true
}

function onPaymentSuccess(data: { orderId: string; tokens: string }) {
  // Add to order history
  const tokensNum = parseInt(data.tokens.replace(/,/g, ''))
  orders.value.unshift({
    orderId: data.orderId,
    packageName: selectedPkg.value?.name || '',
    amount: selectedPkg.value?.price || 0,
    tokens: tokensNum,
    status: 'paid',
    createdAt: new Date().toISOString(),
    paidAt: new Date().toISOString(),
  })
  // Update balance
  tokenBalance.value += tokensNum
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
/* Balance Card */
.balance-card {
  background: linear-gradient(135deg, #059669 0%, #047857 60%, #065F46 100%);
  border-radius: 1rem;
  padding: 1.5rem 1.75rem;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(5, 150, 105, 0.25);
}
@media (min-width: 640px) {
  .balance-card {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.balance-icon {
  width: 3.5rem;
  height: 3.5rem;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
}

/* Package Cards */
.package-card {
  position: relative;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  cursor: pointer;
}
.package-card:hover {
  transform: translateY(-2px);
}

.package-active {
  background: linear-gradient(135deg, #059669 0%, #047857 60%, #065F46 100%);
  border-color: #059669;
  box-shadow: 0 12px 32px rgba(5, 150, 105, 0.25);
  transform: translateY(-4px) scale(1.02);
}
.package-active:hover {
  transform: translateY(-4px) scale(1.02);
}

.popular-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.3s;
}
.popular-badge-active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}
.popular-badge-inactive {
  background: #f0fdf4;
  color: #059669;
}

.package-body {
  padding: 1.25rem 1.5rem;
  flex: 1;
}

/* Purchase Buttons */
.purchase-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.75rem;
  margin: 0 1.25rem 1.25rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.purchase-btn-active {
  background: white;
  color: #059669;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.purchase-btn-active:hover {
  background: #f0fdf4;
  transform: translateY(-1px);
}

.purchase-btn-outline {
  background: transparent;
  color: #059669;
  border: 1.5px solid #059669;
}
.purchase-btn-outline:hover {
  background: #f0fdf4;
}

/* Orders */
.empty-orders {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 1rem;
  background: #f9fafb;
  border-radius: 0.75rem;
  border: 1px dashed #e5e7eb;
}

.orders-table {
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 0.75rem;
  overflow: hidden;
}

.orders-table table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  border-bottom: 1px solid #f3f4f6;
}

.orders-table td {
  padding: 0.75rem 1rem;
  font-size: 0.8125rem;
  border-bottom: 1px solid #f9fafb;
}

.orders-table tbody tr:hover {
  background: #fafafa;
}

.order-status {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  font-weight: 600;
}

.status-paid {
  background: #f0fdf4;
  color: #059669;
}

.status-pending {
  background: #fffbeb;
  color: #d97706;
}

.status-failed {
  background: #fef2f2;
  color: #dc2626;
}

.status-expired {
  background: #f3f4f6;
  color: #6b7280;
}
</style>
