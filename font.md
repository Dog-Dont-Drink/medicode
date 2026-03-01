# 医学统计分析平台 - 前端完整系统设计

## 📌 前端整体架构设计

### 技术栈
- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **样式**：Tailwind CSS + 自定义组件库
- **状态管理**：Pinia
- **路由**：Vue Router
- **HTTP客户端**：Axios + 请求拦截
- **图表库**：ECharts + Plotly.js
- **表格**：TanStack Vue Table 或 Element Plus
- **表单**：Vee-validate + Zod验证
- **富文本/代码编辑**：Monaco Editor（R脚本展示）
- **文件上传**：Dropzone.js
- **日期选择**：Day.js + Headless UI
- **通知/加载**：Nuxt UI / Headless UI
- **UI组件库**：Headless UI + 自定义Tailwind组件

### 开发端口
- **本地开发**：http://localhost:5173
- **后端API**：http://localhost:8000
- **Supabase**：https://your-project.supabase.co

---

## 🗂️ 项目目录结构

\`\`\`
frontend/
├── src/
│   ├── main.ts                          # 入口文件
│   ├── App.vue                          # 根组件
│   ├── env.d.ts                         # 环境变量类型定义
│   │
│   ├── api/                             # API服务层
│   │   ├── auth.ts                      # 身份验证API
│   │   ├── projects.ts                  # 项目管理API
│   │   ├── datasets.ts                  # 数据集管理API
│   │   ├── analysis.ts                  # 分析API
│   │   ├── payment.ts                   # 支付相关API
│   │   ├── user.ts                      # 用户信息API
│   │   └── index.ts                     # API统一导出
│   │
│   ├── stores/                          # Pinia全局状态
│   │   ├── auth.ts                      # 认证状态
│   │   ├── project.ts                   # 项目状态
│   │   ├── dataset.ts                   # 数据集状态
│   │   ├── analysis.ts                  # 分析任务状态
│   │   ├── cart.ts                      # 购物车状态
│   │   └── notification.ts              # 通知状态
│   │
│   ├── router/                          # 路由配置
│   │   └── index.ts                     # 路由定义与中间件
│   │
│   ├── components/                      # 可复用组件
│   │   ├── common/
│   │   │   ├── Header.vue               # 页头组件
│   │   │   ├── Sidebar.vue              # 侧边栏
│   │   │   ├── Footer.vue               # 页脚
│   │   │   ├── Breadcrumb.vue           # 面包屑导航
│   │   │   └── Modal.vue                # 模态框基类
│   │   │
│   │   ├── form/
│   │   │   ├── FormInput.vue            # 输入框
│   │   │   ├── FormSelect.vue           # 下拉选择
│   │   │   ├── FormCheckbox.vue         # 复选框
│   │   │   ├── FormRadio.vue            # 单选框
│   │   │   └── FormFileUpload.vue       # 文件上传
│   │   │
│   │   ├── table/
│   │   │   ├── DataTable.vue            # 通用数据表格
│   │   │   ├── StickyHeader.vue         # 固定表头
│   │   │   └── TableExport.vue          # 表格导出
│   │   │
│   │   ├── chart/
│   │   │   ├── BaseChart.vue            # 图表基类
│   │   │   ├── LineChart.vue            # 折线图
│   │   │   ├── BarChart.vue             # 条形图
│   │   │   ├── BoxPlotChart.vue         # 箱线图
│   │   │   ├── ViolinChart.vue          # 小提琴图
│   │   │   ├── ScatterChart.vue         # 散点图
│   │   │   ├── ROCChart.vue             # ROC曲线
│   │   │   ├── KMChart.vue              # KM生存曲线
│   │   │   ├── ForestPlotChart.vue      # 森林图
│   │   │   ├── HeatmapChart.vue         # 热图
│   │   │   └── CalibrationChart.vue     # 校准曲线
│   │   │
│   │   ├── analysis/
│   │   │   ├── DataPreview.vue          # 数据预览
│   │   │   ├── VariableSelector.vue     # 变量选择器
│   │   │   ├── AnalysisBuilder.vue      # 分析构建器
│   │   │   ├── ResultViewer.vue         # 结果查看器
│   │   │   └── ProgressTask.vue         # 后台任务进度
│   │   │
│   │   └── stats/
│   │       ├── StatisticCard.vue        # 统计卡片
│   │       └── KpiDashboard.vue         # KPI仪表板
│   │
│   ├── views/                           # 页面组件
│   │   ├── auth/
│   │   │   ├── LoginView.vue            # 登录页
│   │   │   ├── RegisterView.vue         # 注册页
│   │   │   ├── ForgotPasswordView.vue   # 忘记密码
│   │   │   └── EmailVerifyView.vue      # 邮箱验证
│   │   │
│   │   ├── dashboard/
│   │   │   ├── DashboardView.vue        # 仪表板主页
│   │   │   ├── TokenOverviewCard.vue    # Token概览卡片
│   │   │   ├── RecentProjectCard.vue    # 最近项目卡片
│   │   │   └── UsageStatsCard.vue       # 使用统计卡片
│   │   │
│   │   ├── project/
│   │   │   ├── ProjectListView.vue      # 项目列表页
│   │   │   ├── ProjectCreateView.vue    # 创建项目
│   │   │   ├── ProjectDetailView.vue    # 项目详情
│   │   │   └── ProjectSettingsView.vue  # 项目设置
│   │   │
│   │   ├── data/
│   │   │   ├── DataUploadView.vue       # 数据导入页
│   │   │   ├── DataPreviewView.vue      # 数据预览页
│   │   │   ├── DataDictionaryView.vue   # 数据字典编辑
│   │   │   ├── DataCleaningView.vue     # 数据清洗工作流
│   │   │   ├── DataTransformView.vue    # 数据转换与派生
│   │   │   ├── DataVersionView.vue      # 版本管理
│   │   │   └── AuditLogView.vue         # 审计日志
│   │   │
│   │   ├── analysis/
│   │   │   ├── AnalysisListView.vue     # 分析标签页
│   │   │   ├── AnalysisCreateView.vue   # 创建分析
│   │   │   ├── AnalysisEditView.vue     # 编辑分析
│   │   │   ├── ResultsView.vue          # 结果详情页
│   │   │   │   ├── DescriptiveView.vue         # 描述统计结果
│   │   │   │   ├── InferenceView.vue           # 假设检验结果
│   │   │   │   ├── RegressionView.vue         # 回归结果
│   │   │   │   ├── SurvivalView.vue           # 生存分析结果
│   │   │   │   ├── PredictionView.vue         # 预测模型结果
│   │   │   │   ├── DiagnosticView.vue         # 诊断试验结果
│   │   │   │   ├── CausalView.vue             # 因果推断结果
│   │   │   │   └── SubgroupView.vue           # 亚组分析结果
│   │   │   │
│   │   │   └── TaskMonitorView.vue      # 任务监控
│   │   │
│   │   ├── report/
│   │   │   ├── ReportListView.vue       # 报告列表
│   │   │   ├── ReportGeneratorView.vue  # 报告生成器
│   │   │   ├── ReportPreviewView.vue    # 报告预览
│   │   │   └── ReportShareView.vue      # 报告分享
│   │   │
│   │   ├── cart/
│   │   │   ├── CartView.vue             # 购物车页面
│   │   │   ├── CheckoutView.vue         # 结算页面
│   │   │   └── PaymentView.vue          # 支付页面
│   │   │
│   │   ├── account/
│   │   │   ├── ProfileView.vue          # 个人资料
│   │   │   ├── AccountSettingsView.vue  # 账户设置
│   │   │   ├── SecurityView.vue         # 安全设置
│   │   │   ├── BillingView.vue          # 账单管理
│   │   │   ├── OrderHistoryView.vue     # 订单历史
│   │   │   ├── TokenHistoryView.vue     # Token使用历史
│   │   │   └── PermissionManageView.vue # 权限管理
│   │   │
│   │   ├── admin/
│   │   │   ├── AdminDashboardView.vue   # 管理员仪表板
│   │   │   ├── UserManageView.vue       # 用户管理
│   │   │   ├── SystemLogView.vue        # 系统日志
│   │   │   └── ConfigView.vue           # 系统配置
│   │   │
│   │   └── error/
│   │       ├── NotFoundView.vue         # 404页面
│   │       ├── ForbiddenView.vue        # 403页面
│   │       └── ErrorView.vue            # 通用错误页
│   │
│   ├── composables/                     # 复合逻辑（Hooks）
│   │   ├── useAuth.ts                   # 认证逻辑
│   │   ├── useProject.ts                # 项目管理逻辑
│   │   ├── useDataset.ts                # 数据集逻辑
│   │   ├── useAnalysis.ts               # 分析逻辑
│   │   ├── useApi.ts                    # API调用封装
│   │   ├── useNotification.ts           # 通知逻辑
│   │   ├── usePagination.ts             # 分页逻辑
│   │   ├── useChart.ts                  # 图表逻辑
│   │   ├── useTimeout.ts                # 定时器逻辑
│   │   └── useLocalStorage.ts           # 本地存储逻辑
│   │
│   ├── utils/                           # 工具函数
│   │   ├── api-client.ts                # API客户端配置
│   │   ├── auth.ts                      # 认证相关工具
│   │   ├── validators.ts                # 表单验证规则
│   │   ├── formatters.ts                # 数据格式化
│   │   ├── statistics.ts                # 统计计算工具
│   │   ├── export.ts                    # 导出工具
│   │   ├── http.ts                      # HTTP拦截器
│   │   ├── token.ts                     # Token管理
│   │   ├── constants.ts                 # 常量定义
│   │   └── helpers.ts                   # 通用辅助函数
│   │
│   ├── types/                           # TypeScript类型定义
│   │   ├── api.ts                       # API响应类型
│   │   ├── auth.ts                      # 认证相关类型
│   │   ├── project.ts                   # 项目类型
│   │   ├── dataset.ts                   # 数据集类型
│   │   ├── analysis.ts                  # 分析类型
│   │   ├── payment.ts                   # 支付类型
│   │   └── common.ts                    # 通用类型
│   │
│   ├── assets/                          # 静态资源
│   │   ├── images/
│   │   │   ├── logo.svg
│   │   │   └── icons/
│   │   ├── styles/
│   │   │   ├── globals.css              # 全局样式
│   │   │   ├── variables.css            # CSS变量
│   │   │   └── transitions.css          # 转换动画
│   │   └── fonts/
│   │
│   └── config/                          # 配置文件
│       ├── api-endpoints.ts             # API端点配置
│       ├── menu-config.ts               # 菜单配置
│       └── theme-config.ts              # 主题配置
│
├── public/                              # 公共资源
│   └── index.html
│
├── tests/                               # 测试文件
│   ├── unit/                            # 单元测试
│   ├── integration/                     # 集成测试
│   └── e2e/                             # 端到端测试
│
├── vite.config.ts                       # Vite配置
├── tsconfig.json                        # TypeScript配置
├── tailwind.config.js                   # Tailwind CSS配置
├── postcss.config.js                    # PostCSS配置
├── .env.example                         # 环境变量示例
└── package.json
\`\`\`

---

## 🌐 前端路由设计（完整路由表）

\`\`\`
/                                 # 根路由/重定向
├── /auth                         # 认证模块
│   ├── /login                    # 登录页
│   ├── /register                 # 注册页
│   ├── /forgot-password          # 忘记密码
│   ├── /verify-email             # 邮箱验证
│   └── /reset-password/:token    # 重置密码
│
├── /dashboard                    # 首页/仪表板
│   └── (受保护，需要登录)
│
├── /projects                     # 项目管理
│   ├── /                         # 项目列表
│   ├── /new                      # 创建新项目
│   └── /:projectId               # 项目详情
│       ├── /                     # 项目概览
│       ├── /data                 # 数据管理
│       │   ├── /upload           # 上传数据
│       │   ├── /preview          # 数据预览
│       │   ├── /dictionary       # 数据字典
│       │   ├── /cleaning         # 数据清洗
│       │   ├── /transform        # 数据转换
│       │   ├── /versions         # 版本管理
│       │   └── /audit            # 审计日志
│       │
│       ├── /analysis             # 分析模块
│       │   ├── /                 # 分析列表
│       │   ├── /new              # 创建分析
│       │   ├── /:analysisId      # 分析详情
│       │   │   ├── /edit         # 编辑分析
│       │   │   ├── /results      # 查看结果
│       │   │   │   ├── /descriptive
│       │   │   │   ├── /inference
│       │   │   │   ├── /regression
│       │   │   │   ├── /survival
│       │   │   │   ├── /prediction
│       │   │   │   ├── /diagnostic
│       │   │   │   ├── /causal
│       │   │   │   ├── /subgroup
│       │   │   │   └── /download
│       │   │   └── /script       # 可复现脚本
│       │   └── /monitor          # 任务监控
│       │
│       ├── /report               # 报告管理
│       │   ├── /                 # 报告列表
│       │   ├── /generate         # 生成报告
│       │   ├── /:reportId        # 报告预览
│       │   └── /:reportId/share  # 报告分享
│       │
│       ├── /settings             # 项目设置
│       └── /members              # 成员管理
│
├── /cart                         # 购物车
│   └── /                         # 购物车页面
│
├── /checkout                     # 结算
│   └── /                         # 结算页面
│       └── /payment              # 支付页面
│
├── /account                      # 用户账户
│   ├── /profile                  # 个人资料
│   ├── /settings                 # 账户设置
│   ├── /security                 # 安全设置
│   ├── /billing                  # 账单管理
│   ├── /orders                   # 订单历史
│   ├── /tokens                   # Token历史
│   └── /permissions              # 权限管理
│
├── /admin                        # 管理员模块
│   ├── /                         # 管理员仪表板
│   ├── /users                    # 用户管理
│   ├── /logs                     # 系统日志
│   └── /config                   # 系统配置
│
└── /errors
    ├── /404                      # 404页面
    ├── /403                      # 403页面
    └── /500                      # 500页面
\`\`\`

---

## 🔌 API端点映射表

### 认证模块
\`\`\`
POST   /api/auth/register           # 用户注册
POST   /api/auth/login              # 用户登录
POST   /api/auth/logout             # 登出
POST   /api/auth/verify-email       # 邮箱验证
POST   /api/auth/forgot-password    # 忘记密码
POST   /api/auth/reset-password     # 重置密码
POST   /api/auth/refresh-token      # 刷新Token
\`\`\`

### 项目管理
\`\`\`
GET    /api/projects                # 获取项目列表
POST   /api/projects                # 创建项目
GET    /api/projects/:id            # 获取项目详情
PUT    /api/projects/:id            # 更新项目
DELETE /api/projects/:id            # 删除项目
GET    /api/projects/:id/datasets   # 获取项目数据集列表
GET    /api/projects/:id/analyses   # 获取项目分析列表
GET    /api/projects/:id/reports    # 获取项目报告列表
GET    /api/projects/:id/members    # 获取项目成员
POST   /api/projects/:id/members    # 添加项目成员
DELETE /api/projects/:id/members/:uid # 移除成员
GET    /api/projects/:id/tasks      # 获取后台任务列表
\`\`\`

### 数据集管理
\`\`\`
GET    /api/datasets                # 获取数据集列表
POST   /api/datasets/upload         # 上传数据集
GET    /api/datasets/:id            # 获取数据集基本信息
GET    /api/datasets/:id/preview    # 获取数据预览
GET    /api/datasets/:id/columns    # 获取列信息
GET    /api/datasets/:id/dictionary # 获取数据字典
PUT    /api/datasets/:id/dictionary # 更新数据字典
DELETE /api/datasets/:id            # 删除数据集
GET    /api/datasets/:id/versions   # 获取版本列表
POST   /api/datasets/:id/versions/:vid/restore # 恢复版本
GET    /api/datasets/:id/audit-log  # 获取审计日志
\`\`\`

### 数据分析
\`\`\`
POST   /api/analysis/data-cleaning
POST   /api/analysis/data-transform
GET    /api/analyses                # 获取分析列表
POST   /api/analyses                # 创建分析
GET    /api/analyses/:id            # 获取分析详情
PUT    /api/analyses/:id            # 更新分析
DELETE /api/analyses/:id            # 删除分析
POST   /api/analyses/:id/run        # 执行分析
GET    /api/analyses/:id/status     # 获取分析状态
GET    /api/analyses/:id/results/*  # 获取各类结果
GET    /api/analyses/:id/script     # 获取可复现脚本
\`\`\`

### 报告管理
\`\`\`
GET    /api/reports                 # 获取报告列表
POST   /api/reports/generate        # 生成报告
GET    /api/reports/:id             # 获取报告详情
GET    /api/reports/:id/download    # 下载报告
DELETE /api/reports/:id             # 删除报告
POST   /api/reports/:id/share       # 分享报告
\`\`\`

### 购物车与支付
\`\`\`
GET    /api/cart                    # 获取购物车
POST   /api/cart/items              # 添加到购物车
DELETE /api/cart/items/:id          # 移除购物车项
PUT    /api/cart/items/:id          # 更新购物车项
POST   /api/payment/alipay/create   # 创建支付宝订单
GET    /api/payment/alipay/notify   # 支付宝回调
GET    /api/packages                # 获取Token套餐列表
POST   /api/purchase/package        # 直接购买套餐
\`\`\`

### 用户账户
\`\`\`
GET    /api/user/profile            # 获取用户资料
PUT    /api/user/profile            # 更新用户资料
GET    /api/user/balance            # 获取Token余额
GET    /api/user/orders             # 获取订单历史
GET    /api/user/token-usage        # 获取Token使用记录
POST   /api/user/change-password    # 修改密码
GET    /api/user/permissions        # 获取用户权限
\`\`\`

### 管理员模块
\`\`\`
GET    /api/admin/users             # 获取所有用户
DELETE /api/admin/users/:id         # 删除用户
GET    /api/admin/logs              # 获取系统日志
GET    /api/admin/config            # 获取系统配置
PUT    /api/admin/config            # 更新系统配置
GET    /api/admin/stats             # 获取系统统计
\`\`\`

---

## 🎨 UI/UX设计规范 - Tailwind CSS清新简约风格

### 色彩系统

#### 基础色
\`\`\`
主色：#0066CC (蓝色) - bg-blue-600, text-blue-600
次色：#00CC88 (绿色) - bg-green-500, text-green-500
警告：#FF9900 (橙色) - bg-amber-500, text-amber-500
危险：#FF3333 (红色) - bg-red-500, text-red-500
\`\`\`

#### 中性色（清新简约）
\`\`\`
背景：#FAFBFC (超浅灰) - bg-slate-50
次背景：#F3F4F6 (浅灰) - bg-gray-100
边界：#E5E7EB (灰色边框) - border-gray-300
文本主：#1F2937 (深灰) - text-gray-800
文本副：#6B7280 (中灰) - text-gray-600
文本辅：#9CA3AF (浅灰) - text-gray-400
\`\`\`

#### Tailwind CSS色值映射
\`\`\`tailwind
// tailwind.config.js
module.exports = {
  theme: {
    colors: {
      primary: '#0066CC',    // blue-600
      secondary: '#00CC88',  // green-500
      warning: '#FF9900',    // amber-500
      danger: '#FF3333',     // red-500
      success: '#10B981',    // green-500
    },
    extend: {
      spacing: {
        'xs': '0.5rem',
        'sm': '1rem',
        'md': '1.5rem',
        'lg': '2rem',
        'xl': '3rem',
      },
    },
  },
}
\`\`\`

### 组件设计规范

#### 按钮 (Button)
\`\`\`
Primary: bg-blue-600 text-white hover:bg-blue-700 rounded-lg px-4 py-2
Secondary: bg-gray-200 text-gray-800 hover:bg-gray-300 rounded-lg px-4 py-2
Danger: bg-red-500 text-white hover:bg-red-600 rounded-lg px-4 py-2
Ghost: bg-transparent border border-gray-300 text-gray-800 hover:bg-gray-100
Disabled: bg-gray-300 text-gray-500 cursor-not-allowed
Loading: opacity-75 cursor-not-allowed (带loading icon)
\`\`\`

#### 输入框 (Input)
\`\`\`
基础样式: px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
占位符: placeholder:text-gray-500
错误状态: border-red-500 focus:ring-red-500
成功状态: border-green-500 focus:ring-green-500
禁用状态: bg-gray-100 text-gray-500 cursor-not-allowed
\`\`\`

#### 卡片 (Card)
\`\`\`
基础: bg-white border border-gray-200 rounded-lg p-4 shadow-sm
悬停: hover:shadow-md transition-shadow
无边框: bg-white rounded-lg p-4 shadow-sm
\`\`\`

#### 表格 (Table)
\`\`\`
表头: bg-gray-50 border-b border-gray-200 font-semibold text-gray-800
行: border-b border-gray-100 hover:bg-gray-50
斑马纹: nth-child(even):bg-gray-50
选中行: bg-blue-50
\`\`\`

#### 模态框 (Modal)
\`\`\`
遮罩: bg-black/50 backdrop-blur-sm
内容: bg-white rounded-lg shadow-xl
标题: text-xl font-semibold text-gray-800 pb-4
内容: text-gray-600 py-4
按钮: flex gap-2 justify-end pt-4 border-t border-gray-200
\`\`\`

#### 通知/Alert
\`\`\`
成功: bg-green-50 border-l-4 border-green-500 text-green-800 p-4
警告: bg-amber-50 border-l-4 border-amber-500 text-amber-800 p-4
错误: bg-red-50 border-l-4 border-red-500 text-red-800 p-4
信息: bg-blue-50 border-l-4 border-blue-600 text-blue-800 p-4
\`\`\`

#### 标签 (Badge)
\`\`\`
默认: bg-gray-200 text-gray-800 px-2 py-1 rounded-full text-sm
主色: bg-blue-100 text-blue-800
成功: bg-green-100 text-green-800
警告: bg-amber-100 text-amber-800
危险: bg-red-100 text-red-800
\`\`\`

### 排版规范

#### 字体
\`\`\`
字体族: Noto Sans SC  Source Han Sans
\`\`\`

#### 字体大小
\`\`\`
标题一级 (H1): text-3xl font-bold text-gray-900
标题二级 (H2): text-2xl font-bold text-gray-800
标题三级 (H3): text-xl font-semibold text-gray-800
标题四级 (H4): text-lg font-semibold text-gray-800
正文 (Body): text-base font-normal text-gray-700
小文本: text-sm font-normal text-gray-600
超小文本: text-xs font-normal text-gray-500
\`\`\`

#### 行高
\`\`\`
紧凑: leading-tight
标准: leading-normal
宽松: leading-relaxed
\`\`\`

#### 文字颜色
\`\`\`
主要: text-gray-900
次要: text-gray-700
辅助: text-gray-600
弱化: text-gray-500
禁用: text-gray-400
\`\`\`

### 间距规范

\`\`\`
特小: 0.25rem (1px)
超小: 0.5rem (2px)
小: 1rem (4px)
中: 1.5rem (6px)
大: 2rem (8px)
超大: 3rem (12px)
特大: 4rem (16px)
\`\`\`

### 圆角规范

\`\`\`
无: rounded-none
小: rounded-sm (0.125rem)
中: rounded (0.25rem)
大: rounded-lg (0.5rem)
超大: rounded-xl (0.75rem)
完全: rounded-full
\`\`\`

### 阴影规范

\`\`\`
轻: shadow-sm (0 1px 2px)
中: shadow (0 1px 3px)
重: shadow-md (0 4px 6px)
更重: shadow-lg (0 10px 15px)
\`\`\`

### 边框规范

\`\`\`
宽度: border-0 | border (1px) | border-2 (2px)
颜色: border-gray-300 (默认) | border-blue-600 (焦点) | border-red-500 (错误)
样式: solid (默认) | dashed
\`\`\`

### 响应式设计断点

\`\`\`
中 (md): ≥ 768px - 平板竖屏
大 (lg): ≥ 1024px - 平板横屏
超大 (xl): ≥ 1280px - 桌面
特大 (2xl): ≥ 1536px - 宽屏

使用示例:
w-full md:w-1/2 lg:w-1/3
grid-cols-1 md:grid-cols-2 lg:grid-cols-3
\`\`\`

### 过渡与动画

\`\`\`
淡入淡出: transition-opacity duration-200
平滑移动: transition-all duration-300
颜色变化: transition-colors duration-150
\`\`\`

### 清新简约风格建议

1. **极简主义**
   - 最少化视觉元素
   - 大量留白 (space-y-4, space-y-6)
   - 清晰的信息层级

2. **配色**
   - 背景：白色 (bg-white) 或 超浅灰 (bg-slate-50)
   - 文字：黑深灰 (text-gray-800) 或 黑中灰 (text-gray-600)
   - 强调：蓝色 (bg-blue-600)
   - 避免鲜艳对比

3. **字体**
   - 使用系统字体
   - 字号简洁 (16px基础)
   - 行高宽松 (1.5 - 1.6)

4. **组件**
   - 边框最小化，多用阴影
   - 圆角适度 (rounded-lg)
   - 按钮扁平化设计

5. **间距**
   - 多用gap和p而非margin
   - 保持垂直节奏
   - 组件间距一致

6. **交互**
   - 轻微悬停效果 (hover:shadow-md)
   - 平滑过渡 (duration-200)
   - 无过度动画

---

## 📱 响应式设计

\`\`\`
Desktop (lg) ≥1024px：三列布局，完整导航
Tablet (md) 768-1023px：两列布局，可折叠菜单
Mobile (sm) <768px：单列布局，汉堡菜单
\`\`\`

---

## ⚡ 性能优化建议

- 路由懒加载：使用Vue Router lazy loading
- 图片优化：使用webp格式，CDN加速
- 代码分割：按模块分割，按需加载
- 虚拟滚动：大列表使用虚拟滚动
- 缓存策略：HTTP缓存 + 本地存储
- 预加载：关键资源预加载

---

## 🔐 安全建议

- XSS防护：DOMPurify清理用户输入
- CSRF防护：自动CSRF Token管理
- 敏感数据：不存储在本地存储，使用内存
- HTTPS强制：生产环境必须HTTPS
- CSP头：严格内容安全策略

---

## 📱 本地开发启动

\`\`\`bash
# 安装依赖
npm install

# 启动开发服务器（localhost:5173）
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 运行测试
npm run test

# 代码格式化
npm run format
\`\`\`

---

**文档完成时间**：2026年3月1日

\`\`\`