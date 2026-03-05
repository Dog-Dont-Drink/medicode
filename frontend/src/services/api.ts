import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Attach auth token to requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// ========================
// Payment API
// ========================

export interface PaymentCreateRequest {
    packageId: string
}

export interface PaymentCreateResponse {
    orderId: string
    qrCodeUrl: string
    totalAmount: string
    expireTime: string
}

export interface PaymentStatusResponse {
    orderId: string
    status: 'pending' | 'paid' | 'failed' | 'expired'
    paidAt?: string
    tokensAdded?: number
}

export interface OrderRecord {
    orderId: string
    packageName: string
    amount: number
    tokens: number
    status: 'pending' | 'paid' | 'failed' | 'expired'
    createdAt: string
    paidAt?: string
}

export interface PaymentPackage {
    id: string
    name: string
    price: number
    tokens: number
    unitPrice: string
    badge: string
    features: string[]
}

export interface TokenBalanceResponse {
    balance: number
    plan: string
    used_this_month: number
}

/**
 * Create a payment order (calls alipay.trade.precreate on backend)
 */
export async function createPayment(data: PaymentCreateRequest): Promise<PaymentCreateResponse> {
    const res = await apiClient.post('/api/v1/payment/precreate', data)
    return res.data
}

export async function getPaymentPackages(): Promise<PaymentPackage[]> {
    const res = await apiClient.get('/api/v1/payment/packages')
    return res.data
}

/**
 * Query order payment status
 */
export async function queryPaymentStatus(orderId: string): Promise<PaymentStatusResponse> {
    const res = await apiClient.get(`/api/v1/payment/query/${orderId}`)
    return res.data
}

/**
 * Get user's order history
 */
export async function getOrderHistory(): Promise<OrderRecord[]> {
    const res = await apiClient.get('/api/v1/payment/orders')
    return res.data
}

/**
 * Get current token balance
 */
export async function getTokenBalance(): Promise<TokenBalanceResponse> {
    const res = await apiClient.get('/api/v1/users/balance')
    return res.data
}

// ========================
// Dashboard API
// ========================
export async function getDashboardData() {
    const res = await apiClient.get('/api/v1/dashboard')
    return res.data
}

// ========================
// Users API
// ========================
export async function getUserProfile() {
    const res = await apiClient.get('/api/v1/users/profile')
    return res.data
}

export async function updateUserProfile(data: any) {
    const res = await apiClient.put('/api/v1/users/profile', data)
    return res.data
}

export async function uploadAvatar(data: FormData) {
    const res = await apiClient.post('/api/v1/users/avatar', data, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
    return res.data
}

export async function changePassword(data: any) {
    const res = await apiClient.post('/api/v1/users/change-password', data)
    return res.data
}

// ========================
// Projects API
// ========================
export async function getProjects() {
    const res = await apiClient.get('/api/v1/projects')
    return res.data
}

export async function getProject(projectId: string) {
    const res = await apiClient.get(`/api/v1/projects/${projectId}`)
    return res.data
}

export async function createProject(data: any) {
    const res = await apiClient.post('/api/v1/projects', data)
    return res.data
}

// ========================
// Datasets API
// ========================
export async function getDatasets(projectId: string) {
    const res = await apiClient.get('/api/v1/datasets', { params: { project_id: projectId } })
    return res.data
}

export async function uploadDataset(data: FormData) {
    const res = await apiClient.post('/api/v1/datasets/upload', data, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
    return res.data
}

export default apiClient
