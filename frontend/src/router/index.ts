import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
    // Home / Landing page (standalone, no layout)
    {
        path: '/',
        name: 'Home',
        component: () => import('@/views/HomeView.vue'),
    },

    // Auth routes (no sidebar)
    {
        path: '/auth',
        component: () => import('@/layouts/AuthLayout.vue'),
        children: [
            { path: 'login', name: 'Login', component: () => import('@/views/auth/LoginView.vue') },
            { path: 'register', name: 'Register', component: () => import('@/views/auth/RegisterView.vue') },
            { path: 'forgot-password', name: 'ForgotPassword', component: () => import('@/views/auth/ForgotPasswordView.vue') },
            { path: 'verify-email', name: 'VerifyEmail', component: () => import('@/views/auth/EmailVerifyView.vue') },
        ],
    },

    // Dashboard routes (with sidebar)
    {
        path: '/',
        component: () => import('@/layouts/DashboardLayout.vue'),
        children: [
            { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/DashboardView.vue'), meta: { requiresAuth: true } },

            // Projects (merged list + create)
            { path: 'projects', name: 'Projects', component: () => import('@/views/project/ProjectListView.vue'), meta: { requiresAuth: true } },
            { path: 'projects/:projectId', name: 'ProjectDetail', component: () => import('@/views/project/ProjectDetailView.vue'), meta: { requiresAuth: true } },

            // Data management (merged upload + preview)
            { path: 'data', name: 'DataManagement', component: () => import('@/views/data/DataView.vue'), meta: { requiresAuth: true } },
            { path: 'data/dictionary', name: 'DataDictionary', component: () => import('@/views/data/DataDictionaryView.vue'), meta: { requiresAuth: true } },

            // Analysis
            { path: 'analysis', name: 'AnalysisList', component: () => import('@/views/analysis/AnalysisListView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/new', name: 'AnalysisCreate', component: () => import('@/views/analysis/AnalysisCreateView.vue'), meta: { requiresAuth: true } },

            // Reports
            { path: 'reports', name: 'Reports', component: () => import('@/views/analysis/AnalysisListView.vue'), meta: { requiresAuth: true } },

            // Account
            { path: 'account/profile', name: 'Profile', component: () => import('@/views/account/ProfileView.vue'), meta: { requiresAuth: true } },
            { path: 'account/settings', name: 'AccountSettings', component: () => import('@/views/account/AccountSettingsView.vue'), meta: { requiresAuth: true } },
            { path: 'account/billing', name: 'Billing', component: () => import('@/views/account/BillingView.vue'), meta: { requiresAuth: true } },
        ],
    },

    // Error routes
    { path: '/403', name: 'Forbidden', component: () => import('@/views/error/ForbiddenView.vue') },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/error/NotFoundView.vue') },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) return savedPosition
        return { top: 0 }
    },
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('auth_token')
    if (to.meta.requiresAuth && !token) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
        next()
    }
})

export default router
