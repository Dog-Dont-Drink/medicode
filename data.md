# 在你的项目文件夹创建这个脚本
cat > create-docs.sh << 'EOF'
#!/bin/bash

# 创建完整文档
mkdir -p docs

# 创建前端设计文档
cat > docs/01-前端系统设计.md << 'FRONTEND_DOC'
[前面已完整列出的前端设计内容]
FRONTEND_DOC

# 创建后端设计文档
cat > docs/02-后端系统设计.md << 'BACKEND_DOC'
[前面已完整列出的后端设计内容]
BACKEND_DOC

# 创建数据库设计文档
cat > docs/03-数据库设计文档.md << 'DATABASE_DOC'
# 医学统计分析平台 - 数据库完整设计文档

## 📊 数据库模型全景

[详细的数据库设计内容]

DATABASE_DOC

# 创建项目初始化指南
cat > docs/04-项目初始化指南.md << 'INIT_DOC'
# 医学统计分析平台 - 项目初始化指南

## 前端项目初始化

### 1. 创建Vue3项目
\`\`\`bash
npm create vite@latest medical-stats -- --template vue-ts
cd medical-stats
npm install
\`\`\`

### 2. 安装依赖
\`\`\`bash
npm install -D tailwindcss postcss autoprefixer
npm install axios pinia vue-router vee-validate zod
npm install echarts plotly.js day.js
npm install -D @types/node
\`\`\`

### 3. 初始化Tailwind CSS
\`\`\`bash
npx tailwindcss init -p
\`\`\`

### 4. 项目结构初始化
\`\`\`bash
mkdir -p src/{api,stores,router,components,views,composables,utils,types,assets,config}
mkdir -p src/components/{common,form,table,chart,analysis,stats}
mkdir -p src/views/{auth,dashboard,project,data,analysis,report,cart,account,admin,error}
\`\`\`

## 后端项目初始化

### 1. 创建虚拟环境
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
\`\`\`

### 2. 安装FastAPI依赖
\`\`\`bash
pip install fastapi uvicorn
pip install sqlalchemy psycopg2-binary
pip install pydantic python-dotenv
pip install python-jose passlib bcrypt
pip install aioredis celery
pip install httpx
\`\`\`

### 3. 项目结构初始化
\`\`\`bash
mkdir -p app/{db,api/v1/endpoints,schemas,services,workers,compute,middleware,utils}
mkdir -p resources/{r_scripts,templates}
mkdir -p tests/{unit,integration}
\`\`\`

INIT_DOC

echo "✅ 文档生成完成！"
echo "📁 所有文档已保存到 docs/ 文件夹"
echo "📄 文件清单："
echo "  - 01-前端系统设计.md"
echo "  - 02-后端系统设计.md"
echo "  - 03-数据库设计文档.md"
echo "  - 04-项目初始化指南.md"
EOF

chmod +x create-docs.sh
./create-docs.sh