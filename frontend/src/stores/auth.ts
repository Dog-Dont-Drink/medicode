import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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

    // 注册 —— 不再自动登录，而是发送验证码
    async function register(name: string, email: string, password: string) {
        loading.value = true
        try {
            // TODO: 替换为真实 API 调用
            // const res = await apiClient.post('/api/v1/auth/register', { name, email, password })
            await new Promise(resolve => setTimeout(resolve, 1000))

            // 注册成功后设置待验证邮箱，不返回 token
            setPendingVerification(email, 'register')
            return { success: true, message: '验证码已发送到您的邮箱' }
        } catch (error) {
            return { success: false, error: '注册失败' }
        } finally {
            loading.value = false
        }
    }

    // 登录
    async function login(email: string, password: string) {
        loading.value = true
        try {
            // TODO: 替换为真实 API 调用
            await new Promise(resolve => setTimeout(resolve, 1000))

            // 模拟：如果邮箱未验证，返回需要验证的提示
            // 真实场景下后端会返回 403 + needVerify
            const mockUser: User = {
                id: '1',
                email,
                name: email.split('@')[0],
                role: 'user',
                tokenBalance: 1500,
            }
            setUser(mockUser)
            setToken('mock-jwt-token-' + Date.now())
            return { success: true }
        } catch (error: any) {
            // 如果后端返回 403 + needVerify
            if (error?.response?.status === 403 && error?.response?.data?.needVerify) {
                setPendingVerification(email, 'register')
                return { success: false, needVerify: true, error: '邮箱未验证，请先完成验证' }
            }
            return { success: false, error: '登录失败' }
        } finally {
            loading.value = false
        }
    }

    // 验证邮箱验证码
    async function verifyCode(email: string, code: string, purpose: string) {
        loading.value = true
        try {
            // TODO: 替换为真实 API 调用
            // const res = await apiClient.post('/api/v1/auth/verify-code', { email, code, purpose })
            await new Promise(resolve => setTimeout(resolve, 1000))

            if (purpose === 'register') {
                // 注册验证成功后自动登录
                const mockUser: User = {
                    id: '2',
                    email,
                    name: email.split('@')[0],
                    role: 'user',
                    tokenBalance: 100,
                }
                setUser(mockUser)
                setToken('mock-jwt-token-' + Date.now())
            }

            clearPending()
            return { success: true }
        } catch (error) {
            return { success: false, error: '验证码错误或已过期' }
        } finally {
            loading.value = false
        }
    }

    // 发送/重发验证码
    async function sendCode(email: string, purpose: string) {
        try {
            // TODO: 替换为真实 API 调用
            // await apiClient.post('/api/v1/auth/send-code', { email, purpose })
            await new Promise(resolve => setTimeout(resolve, 500))
            return { success: true, message: '验证码已发送', expireSeconds: 600 }
        } catch (error) {
            return { success: false, error: '发送失败，请稍后重试' }
        }
    }

    // 重置密码
    async function resetPassword(email: string, code: string, newPassword: string) {
        loading.value = true
        try {
            // TODO: 替换为真实 API 调用
            await new Promise(resolve => setTimeout(resolve, 1000))
            clearPending()
            return { success: true }
        } catch (error) {
            return { success: false, error: '重置失败' }
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
