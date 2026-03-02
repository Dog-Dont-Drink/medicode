import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

interface User {
    id: string
    email: string
    name: string
    avatar?: string
    role: 'user' | 'admin'
    tokenBalance: number
}

export const useAuthStore = defineStore('auth', () => {
    const user = ref<User | null>(null)
    const token = ref<string | null>(localStorage.getItem('auth_token'))
    const loading = ref(false)

    // 注册后待验证的邮箱
    const pendingEmail = ref<string | null>(null)
    const pendingPurpose = ref<string | null>(null)

    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    function setUser(userData: User) {
        user.value = userData
    }

    function setToken(newToken: string) {
        token.value = newToken
        localStorage.setItem('auth_token', newToken)
    }

    function logout() {
        user.value = null
        token.value = null
        pendingEmail.value = null
        pendingPurpose.value = null
        localStorage.removeItem('auth_token')
    }

    // 设置待验证邮箱（注册/忘记密码后跳转验证页）
    function setPendingVerification(email: string, purpose: string) {
        pendingEmail.value = email
        pendingPurpose.value = purpose
    }

    function clearPending() {
        pendingEmail.value = null
        pendingPurpose.value = null
    }

    // 注册 —— 先发送注册请求
    async function register(name: string, email: string, password: string, code: string) {
        loading.value = true
        try {
            const res = await api.post('/api/v1/auth/register', { name, email, password, code })

            // 如果后端直接返回 token，这里可以选择直接登录
            if (res.data?.access_token) {
                const { access_token, user: userData } = res.data
                setUser(userData)
                setToken(access_token)
            }

            return { success: true }
        } catch (error: any) {
            return { success: false, error: error.response?.data?.detail || '注册失败' }
        } finally {
            loading.value = false
        }
    }

    // 登录
    async function login(email: string, password: string) {
        loading.value = true
        try {
            const res = await api.post('/api/v1/auth/login', { email, password })

            const { access_token, user: userData } = res.data

            setUser(userData)
            setToken(access_token)
            return { success: true }
        } catch (error: any) {
            // 如果后端返回 403 + needVerify
            if (error?.response?.data?.need_verify) {
                setPendingVerification(email, 'register')
                return { success: false, needVerify: true, error: '邮箱未验证，请先完成验证' }
            }
            return { success: false, error: error.response?.data?.detail || '登录失败' }
        } finally {
            loading.value = false
        }
    }

    // 验证邮箱验证码
    async function verifyCode(email: string, code: string, purpose: string) {
        loading.value = true
        try {
            await api.post('/api/v1/auth/verify-code', { email, code, purpose })
            clearPending()
            return { success: true }
        } catch (error: any) {
            return { success: false, error: error.response?.data?.detail || '验证码错误或已过期' }
        } finally {
            loading.value = false
        }
    }

    // 发送/重发验证码
    async function sendCode(email: string, purpose: string) {
        try {
            const res = await api.post('/api/v1/auth/send-code', { email, purpose })
            return { success: true, message: '验证码已发送', expireSeconds: res.data.expire_seconds || 600 }
        } catch (error: any) {
            return { success: false, error: error.response?.data?.detail || '发送失败，请稍后重试' }
        }
    }

    // 重置密码
    async function resetPassword(email: string, code: string, newPassword: string) {
        loading.value = true
        try {
            await api.post('/api/v1/auth/reset-password', { email, code, new_password: newPassword })
            clearPending()
            return { success: true }
        } catch (error: any) {
            return { success: false, error: error.response?.data?.detail || '重置密码失败' }
        } finally {
            loading.value = false
        }
    }

    return {
        user, token, loading, pendingEmail, pendingPurpose,
        isAuthenticated, isAdmin,
        login, register, logout,
        setUser, setToken,
        setPendingVerification, clearPending,
        verifyCode, sendCode, resetPassword,
    }
})
