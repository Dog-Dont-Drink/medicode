import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import api from '@/services/api'

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
            { path: 'admin-login', name: 'AdminLoginAlias', component: () => import('@/views/auth/AdminLoginView.vue') },
            { path: 'register', name: 'Register', component: () => import('@/views/auth/RegisterView.vue') },
            { path: 'forgot-password', name: 'ForgotPassword', component: () => import('@/views/auth/ForgotPasswordView.vue') },
            { path: 'verify-email', name: 'VerifyEmail', component: () => import('@/views/auth/EmailVerifyView.vue') },
        ],
    },
    {
        path: '/admin/login',
        name: 'AdminLogin',
        component: () => import('@/views/auth/AdminLoginView.vue'),
    },
    {
        path: '/admin',
        component: () => import('@/layouts/AdminLayout.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
            { path: '', name: 'AdminDashboard', component: () => import('@/views/admin/AdminDashboardView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
            { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/AdminUsersView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
            { path: 'tables/:tableName?', name: 'AdminTables', component: () => import('@/views/admin/AdminTablesView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
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

            // Data management
            { path: 'data', name: 'DataUpload', component: () => import('@/views/data/DataView.vue'), meta: { requiresAuth: true } },
            { path: 'data/cleaning', name: 'DataCleaning', component: () => import('@/views/data/DataCleaningView.vue'), meta: { requiresAuth: true } },
            { path: 'data/dictionary', name: 'DataDictionary', component: () => import('@/views/data/DataDictionaryView.vue'), meta: { requiresAuth: true } },

            // Analysis
            { path: 'analysis', name: 'AnalysisList', component: () => import('@/views/analysis/AnalysisListView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/descriptive', name: 'DescriptiveTable', component: () => import('@/views/analysis/DescriptiveTableView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/t-test', name: 'TTest', component: () => import('@/views/analysis/TTestView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/anova', name: 'Anova', component: () => import('@/views/analysis/AnovaView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/linear-regression', name: 'LinearRegression', component: () => import('@/views/analysis/LinearRegressionView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/lasso-regression', name: 'LassoRegression', component: () => import('@/views/analysis/LassoRegressionView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/logistic-regression', name: 'LogisticRegression', component: () => import('@/views/analysis/LogisticRegressionView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/cox-regression', name: 'CoxRegression', component: () => import('@/views/analysis/CoxRegressionView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/clinical-model-builder', name: 'ClinicalModelBuilder', component: () => import('@/views/analysis/ClinicalModelWorkbenchView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/repeated-measures-anova', name: 'RepeatedMeasuresAnova', component: () => import('@/views/analysis/RepeatedMeasuresAnovaView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/chi-square', name: 'ChiSquare', component: () => import('@/views/analysis/ChiSquareView.vue'), meta: { requiresAuth: true } },
            { path: 'analysis/new', name: 'AnalysisCreate', component: () => import('@/views/analysis/AnalysisCreateView.vue'), meta: { requiresAuth: true } },

            // Reports
            { path: 'reports', name: 'Reports', component: () => import('@/views/report/ReportsView.vue'), meta: { requiresAuth: true } },

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
router.beforeEach(async (to, from, next) => {
    const token = localStorage.getItem('auth_token')
    if (to.meta.requiresAuth && !token) {
        next(
            to.meta.requiresAdmin
                ? { name: 'AdminLogin' }
                : { name: 'Login', query: { redirect: to.fullPath } }
        )
        return
    }

    if (to.meta.requiresAdmin) {
        let role = localStorage.getItem('auth_user_role')

        if (!role && token) {
            try {
                const res = await api.get('/api/v1/users/profile')
                role = res.data?.role || 'user'
                localStorage.setItem('auth_user_role', role || 'user')
            } catch {
                localStorage.removeItem('auth_token')
                localStorage.removeItem('auth_user_role')
                next({ name: 'AdminLogin' })
                return
            }
        }

        if (role !== 'admin') {
            next({ name: token ? 'Dashboard' : 'AdminLogin' })
            return
        }
    }

    next()
})

export default router
