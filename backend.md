# 医学统计分析平台 - 后端完整系统设计

## 📌 后端整体架构设计

### 技术栈
- **框架**：FastAPI
- **Web服务器**：Uvicorn
- **数据库**：Supabase (PostgreSQL)
- **缓存**：Redis
- **任务队列**：Celery + Redis
- **ORM**：SQLAlchemy
- **认证**：JWT
- **API文档**：SwaggerUI / OpenAPI
- **统计计算**：R、Python (scipy, sklearn, statsmodels)
- **数据处理**：Pandas、NumPy
- **异步**：asyncio、aioredis
- **日志**：Structlog、loguru
- **监控**：Sentry

### 开发端口
- **本地开发**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **Redis**：localhost:6379
- **Supabase**：https://your-project.supabase.co

---

## 🗂️ 项目目录结构

\`\`\`
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # 应用入口，FastAPI初始化
│   ├── core/                            # 核心配置
│   │   ├── config.py                    # 环境配置、常量
│   │   ├── security.py                  # JWT、密码加密
│   │   ├── logger.py                    # 日志配置
│   │   └── exceptions.py                # 自定义异常
│   │
│   ├── db/                              # 数据库相关
│   │   ├── database.py                  # 数据库连接配置
│   │   ├── session.py                   # Session管理
│   │   └── models.py                    # SQLAlchemy模型
│   │       ├── user.py                  # 用户模型
│   │       ├── project.py               # 项目模型
│   │       ├── dataset.py               # 数据集模型
│   │       ├── analysis.py              # 分析模型
│   │       ├── order.py                 # 订单模型
│   │       ├── audit_log.py             # 审计日志模型
│   │       └── __init__.py
│   │
│   ├── schemas/                         # Pydantic数据验证模式
│   │   ├── auth.py                      # 认证schema
│   │   ├── user.py                      # 用户schema
│   │   ├── project.py                   # 项目schema
│   │   ├── dataset.py                   # 数据集schema
│   │   ├── analysis.py                  # 分析schema
│   │   ├── payment.py                   # 支付schema
│   │   └── common.py                    # 通用schema
│   │
│   ├── api/                             # API路由
│   │   ├── v1/                          # API v1版本
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py              # 认证API
│   │   │   │   ├── users.py             # 用户管理API
│   │   │   │   ├── projects.py          # 项目管理API
│   │   │   │   ├── datasets.py          # 数据集API
│   │   │   │   ├── analysis.py          # 分析API
│   │   │   │   ├── payment.py           # 支付API
│   │   │   │   ├── reports.py           # 报告API
│   │   │   │   ├── cart.py              # 购物车API
│   │   │   │   ├── admin.py             # 管理员API
│   │   │   │   └── health.py            # 健康检查
│   │   │   └── api.py                   # 路由集成
│   │   └── dependencies.py              # 依赖注入
│   │
│   ├── services/                        # 业务逻辑层
│   │   ├── auth_service.py              # 认证服务
│   │   ├── user_service.py              # 用户服务
│   │   ├── project_service.py           # 项目服务
│   │   ├── dataset_service.py           # 数据集服务
│   │   ├── analysis_service.py          # 分析服务
│   │   ├── payment_service.py           # 支付服务
│   │   ├── report_service.py            # 报告服务
│   │   ├── file_service.py              # 文件处理服务
│   │   └── cache_service.py             # 缓存服务
│   │
│   ├── workers/                         # Celery任务
│   │   ├── tasks.py                     # 异步任务定义
│   │   ├── data_processing.py           # 数据处理任务
│   │   ├── analysis_tasks.py            # 分析计算任务
│   │   ├── report_tasks.py              # 报告生成任务
│   │   └── cleanup_tasks.py             # 清理任务
│   │
│   ├── compute/                         # 统计计算引擎
│   │   ├── r_executor.py                # R脚本执行器
│   │   ├── python_executor.py           # Python计算执行器
│   │   ├── descriptive.py               # 描述统计模块
│   │   ├── inference.py                 # 假设检验模块
│   │   ├── regression.py                # 回归分析模块
│   │   ├── survival.py                  # 生存分析模块
│   │   ├── prediction.py                # 预测模型模块
│   │   ├── diagnostic.py                # 诊断试验模块
│   │   ├── causal.py                    # 因果推断模块
│   │   └── utils.py                     # 计算工具函数
│   │
│   ├── middleware/                      # 中间件
│   │   ├── auth_middleware.py           # JWT认证中间件
│   │   ├── logging_middleware.py        # 日志中间件
│   │   ├── error_handler.py             # 错误处理
│   │   └── cors_middleware.py           # CORS中间件
│   │
│   ├── utils/                           # 工具函数
│   │   ├── validators.py                # 数据验证
│   │   ├── formatters.py                # 数据格式化
│   │   ├── file_handlers.py             # 文件处理
│   │   ├── encryption.py                # 加密解密
│   │   ├── s3_client.py                 # S3客户端
│   │   └── constants.py                 # 常量定义
│   │
│   └── migrations/                      # 数据库迁移
│       └── alembic/                     # Alembic配置
│
├── resources/                           # 资源文件
│   ├── r_scripts/                       # R脚本模板
│   │   ├── descriptive.R
│   │   ├── regression.R
│   │   ├── survival.R
│   │   └── ...
│   └── templates/                       # 报告模板
│       └── ...
│
├── tests/                               # 测试文件
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_projects.py
│   │   └── ...
│   ├── integration/
│   ├── conftest.py                      # pytest配置
│   └── fixtures/
│
├── docker/                              # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .env.example                         # 环境变量示例
├── requirements.txt                     # Python依赖
├── pyproject.toml                       # 项目配置
└── README.md
\`\`\`

---

## 🔌 API路由设计

### 认证模块 (/api/v1/auth)
\`\`\`
POST   /register               # 用户注册
POST   /login                  # 用户登录
POST   /logout                 # 登出
POST   /verify-email/:token    # 邮箱验证
POST   /forgot-password        # 忘记密码
POST   /reset-password         # 重置密码
POST   /refresh-token          # 刷新token
\`\`\`

### 用户管理 (/api/v1/users)
\`\`\`
GET    /profile                # 获取个人资料
PUT    /profile                # 更新个人资料
POST   /change-password        # 修改密码
GET    /balance                # 获取token余额
GET    /orders                 # 获取订单历史
GET    /token-usage            # 获取token使用记录
GET    /permissions            # 获取权限列表
\`\`\`

### 项目管理 (/api/v1/projects)
\`\`\`
GET    /                       # 获取项目列表
POST   /                       # 创建项目
GET    /:id                    # 获取项目详情
PUT    /:id                    # 更新项目
DELETE /:id                    # 删除项目
GET    /:id/datasets           # 获取数据集列表
GET    /:id/analyses           # 获取分析列表
GET    /:id/reports            # 获取报告列表
GET    /:id/members            # 获取成员列表
POST   /:id/members            # 添加成员
DELETE /:id/members/:uid       # 移除成员
GET    /:id/tasks              # 获取后台任务列表
\`\`\`

### 数据集管理 (/api/v1/datasets)
\`\`\`
GET    /                       # 获取数据集列表
POST   /upload                 # 上传数据集
GET    /:id                    # 获取数据集信息
GET    /:id/preview            # 获取数据预览
GET    /:id/columns            # 获取列信息
GET    /:id/dictionary         # 获取数据字典
PUT    /:id/dictionary         # 更新数据字典
DELETE /:id                    # 删除数据集
GET    /:id/versions           # 获取版本列表
POST   /:id/versions/:vid/restore  # 恢复版本
GET    /:id/audit-log          # 获取审计日志
\`\`\`

### 分析模块 (/api/v1/analysis)
\`\`\`
POST   /data-cleaning          # 执行数据清洗
POST   /data-transform         # 执行数据转换
GET    /                       # 获取分析列表
POST   /                       # 创建分析配置
GET    /:id                    # 获取分析详情
PUT    /:id                    # 更新分析配置
DELETE /:id                    # 删除分析
POST   /:id/run                # 执行分析
GET    /:id/status             # 获取执行状态
GET    /:id/results/descriptive    # 描述统计结果
GET    /:id/results/inference      # 假设检验结果
GET    /:id/results/regression     # 回归结果
GET    /:id/results/survival       # 生存分析结果
GET    /:id/results/prediction     # 预测模型结果
GET    /:id/results/diagnostic     # 诊断试验结果
GET    /:id/results/causal         # 因果推断结果
GET    /:id/results/subgroup       # 亚组分析结果
GET    /:id/script             # 获取可复现脚本
\`\`\`

### 报告管理 (/api/v1/reports)
\`\`\`
GET    /                       # 获取报告列表
POST   /generate               # 生成报告
GET    /:id                    # 获取报告详情
GET    /:id/download           # 下载报告
DELETE /:id                    # 删除报告
POST   /:id/share              # 分享报告
GET    /:id/public/:token      # 公开链接访问
\`\`\`

### 购物车与支付 (/api/v1/)
\`\`\`
GET    /cart                   # 获取购物车
POST   /cart/items             # 添加购物车项
DELETE /cart/items/:id         # 删除购物车项
PUT    /cart/items/:id         # 更新购物车项

POST   /payment/alipay/create  # 创建支付宝订单
GET    /payment/alipay/notify  # 支付宝回调
GET    /packages               # 获取套餐列表
POST   /purchase/package       # 直接购买套餐
\`\`\`

### 管理员模块 (/api/v1/admin)
\`\`\`
GET    /users                  # 获取所有用户
DELETE /users/:id              # 删除用户
GET    /logs                   # 获取系统日志
GET    /logs/filter            # 过滤日志
GET    /config                 # 获取系统配置
PUT    /config                 # 更新系统配置
GET    /stats                  # 获取系统统计
\`\`\`

---

## 🗄️ 数据库核心表设计

### 用户表 (users)
\`\`\`sql
- id (PK)
- email (unique, indexed)
- password_hash
- first_name
- last_name
- organization
- bio
- avatar_url
- token_balance
- subscription_level (free, pro, enterprise)
- is_email_verified
- is_active
- created_at
- updated_at
- last_login_at
\`\`\`

### 项目表 (projects)
\`\`\`sql
- id (PK)
- name
- description
- owner_id (FK users)
- is_public
- created_at
- updated_at
\`\`\`

### 项目成员表 (project_members)
\`\`\`sql
- id (PK)
- project_id (FK projects)
- user_id (FK users)
- role (owner, editor, viewer)
- created_at
\`\`\`

### 数据集表 (datasets)
\`\`\`sql
- id (PK)
- project_id (FK projects)
- name
- description
- file_path
- file_size
- file_format (csv, excel, sas, spss, stata, rds)
- row_count
- column_count
- created_at
- updated_at
\`\`\`

### 数据集版本表 (dataset_versions)
\`\`\`sql
- id (PK)
- dataset_id (FK datasets)
- version_number
- file_path
- change_description
- created_by (FK users)
- created_at
\`\`\`

### 数据集字典表 (dataset_dictionary)
\`\`\`sql
- id (PK)
- dataset_id (FK datasets)
- column_name
- column_label (中文标签)
- data_type (numeric, categorical, date, time)
- description
- codebook (取值编码)
- created_at
- updated_at
\`\`\`

### 分析表 (analyses)
\`\`\`sql
- id (PK)
- project_id (FK projects)
- dataset_id (FK datasets)
- name
- analysis_type (descriptive, inference, regression, survival, prediction, diagnostic, causal, subgroup)
- configuration (JSON)
- status (pending, running, completed, failed, cancelled)
- created_by (FK users)
- created_at
- updated_at
- executed_at
- execution_time (ms)
\`\`\`

### 分析结果表 (analysis_results)
\`\`\`sql
- id (PK)
- analysis_id (FK analyses)
- result_type (descriptive, inference, regression, ...)
- result_data (JSON)
- tables (JSON - 结果表格)
- charts (JSON - 图表配置)
- script_r (R脚本)
- script_python (Python脚本)
- cached_at
\`\`\`

### 订单表 (orders)
\`\`\`sql
- id (PK)
- user_id (FK users)
- amount
- currency (CNY)
- status (pending, paid, failed, refunded)
- alipay_trade_no
- created_at
- paid_at
- notes
\`\`\`

### Token消费表 (token_usage)
\`\`\`sql
- id (PK)
- user_id (FK users)
- analysis_id (FK analyses, nullable)
- analysis_type
- tokens_consumed
- operation_type (analysis, export, ...)
- created_at
\`\`\`

### 审计日志表 (audit_logs)
\`\`\`sql
- id (PK)
- user_id (FK users, nullable)
- resource_type (user, project, dataset, analysis, ...)
- resource_id
- action (create, read, update, delete)
- changes (JSON)
- ip_address
- user_agent
- status (success, failure)
- error_message
- created_at
\`\`\`

### 权限表 (permissions)
\`\`\`sql
- id (PK)
- user_id (FK users)
- resource_type (project, dataset, analysis, report)
- resource_id
- permission_type (view, edit, delete, share)
- granted_by (FK users)
- created_at
- expires_at (nullable)
\`\`\`

---

## 🔐 认证与授权

### JWT Token结构
\`\`\`json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "user/admin",
  "exp": 1234567890,
  "iat": 1234567890,
  "scope": ["read:projects", "write:analyses"]
}
\`\`\`

### 权限模型
\`\`\`
基于角色 (RBAC):
- Admin: 所有权限
- User: 读写自己的资源，可与他人共享

细粒度控制:
- 项目级: owner, editor, viewer
- 数据集级: 继承项目权限
- 分析级: 继承项目权限
- 报告级: 继承项目权限
\`\`\`

---

## 💰 Token计费系统

### 计费规则
\`\`\`
基础包: 100 tokens = ¥10
标准包: 500 tokens = ¥45
专业包: 1000 tokens = ¥80
企业包: 自定义

分析消费 (每个分析):
- 描述统计: 1-5 tokens
- 假设检验: 2-5 tokens
- 线性回归: 3-8 tokens
- Logistic回归: 5-10 tokens
- 生存分析: 5-15 tokens
- 预测建模: 10-20 tokens
- 因果推断: 10-15 tokens

导出费用:
- PDF报告: 5 tokens
- Word报告: 3 tokens
- 可复现脚本: 2 tokens
\`\`\`

---

## 🔄 异步任务队列 (Celery)

### 任务类型
\`\`\`
1. 数据处理任务
   - 上传文件解析
   - 数据清洗
   - 数据转换

2. 分析任务
   - 统计计算
   - 生成结果表格与图表
   - 生成可复现脚本

3. 报告生成
   - Word/PDF生成
   - HTML报告生成

4. 清理任务
   - 临时文件清除
   - 过期token回收
   - 日志轮转

5. 定时任务
   - 每天晚上备份数据
   - 每周统计报告
   - 月度账单生成
\`\`\`

---

## 📊 性能与缓存策略

### Redis缓存
\`\`\`
用户session: 用户登录状态，过期时间24小时
分析结果缓存: 同样参数快速返回，过期时间7天
用户权限缓存: 加速权限检查，过期时间1小时
经常访问的数据: 项目列表、数据集列表缓存
\`\`\`

### 数据库索引
\`\`\`
- users: email, created_at
- projects: owner_id, created_at
- datasets: project_id, created_at
- analyses: project_id, status, created_at
- audit_logs: user_id, created_at, resource_type
\`\`\`

---

## 🚀 部署与运维

### Docker容器化
\`\`\`dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
\`\`\`

### 环境变量
\`\`\`
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# 支付宝
ALIPAY_APPID=your_appid
ALIPAY_API_KEY=your_api_key

# SMTP邮件
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password

# 日志
LOG_LEVEL=INFO
SENTRY_DSN=https://...
\`\`\`

---

## 🧪 测试策略

### 测试框架
\`\`\`
- pytest: 单元测试
- pytest-asyncio: 异步测试
- httpx: API测试客户端
- pytest-cov: 覆盖率
\`\`\`

### 测试覆盖范围
\`\`\`
- 单元测试: 业务逻辑、验证、格式化
- 集成测试: API端点、数据库交互
- 端到端测试: 完整业务流程
\`\`\`

---

## 📖 API文档生成

通过FastAPI自动生成的SwaggerUI文档：
http://localhost:8000/docs

---

## 🔒 安全事项

- 密码: bcrypt加密存储
- API: 速率限制、CORS配置
- 数据: SQL注入防护、XSS防护
- 传输: HTTPS强制、CSP头
- 日志: 敏感信息脱敏
- 备份: 定期数据备份

---

**文档完成时间**：2026年3月1日

\`\`\`