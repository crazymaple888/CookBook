# 菜谱应用 (Cookbook)

一个中文菜谱应用：首页随机预览菜谱、按食材匹配菜谱、完整社区功能。一套 React Native 代码同时支持 iOS、Android、Web 三端。

## 功能一览

- **首页随机菜谱**：每次刷新/下拉出现新菜谱，无固定顺序，支持无限下拉加载（首屏 10 条 + 每页追加 5 条）
- **食材匹配**：选择或输入你有的食材，按"覆盖优先"匹配菜谱——覆盖率越高越靠前，缺失食材标注"需购买"
- **社区**：注册登录、收藏菜谱、点赞、评论、搜索菜谱
- **发布菜谱**：登录用户可申请上传权限，管理员审核通过后才能发布
- **管理后台**：管理员可审核用户上传权限申请（`/admin`）
- **暗色主题**：全站墨绿→黑色渐变背景，深色卡片与文字
- **三端**：iOS、Android、Web 共用一套代码

## 技术栈

| 端 | 技术 |
|---|---|
| **前端** | React Native (Expo SDK 57) + Expo Router + TanStack Query + Zustand |
| **后端** | FastAPI + SQLAlchemy 2.0 + Alembic + APScheduler |
| **数据库** | PostgreSQL 16 |
| **缓存** | Redis |
| **数据源** | 下厨房菜谱语料库（公开数据集，HuggingFace） |
| **部署** | Docker Compose（PostgreSQL + Redis + API） |

## 项目结构

```
cookbook/
├── docker-compose.yml          # 后端编排：db / redis / api 三服务
├── .env.example                # 后端环境变量示例
├── README.md
│
├── backend/                    # ======== 后端（FastAPI）========
│   ├── Dockerfile              # 应用镜像（多级构建引用数据镜像）
│   ├── pyproject.toml          # Python 依赖
│   ├── alembic.ini / alembic/  # 数据库迁移
│   ├── scripts/                # 工具脚本（数据导入、食材清洗等）
│   ├── data-image/             # 语料库数据镜像（scratch + gzip）
│   ├── tests/                  # pytest 测试
│   └── app/
│       ├── main.py             # FastAPI 入口 + 路由注册
│       ├── core/               # 配置、安全、依赖注入、Redis、异常
│       ├── models/             # SQLAlchemy 模型
│       ├── schemas/            # Pydantic 模型
│       ├── routers/            # API 路由（auth/recipes/ingredients/matching/community/admin）
│       ├── services/           # 业务逻辑（含食材匹配算法、数据导入管线）
│       ├── scheduler/          # APScheduler 定时任务
│       └── utils/              # 工具函数
│
└── app/                        # ======== 前端（Expo / React Native）========
    ├── app.json                # Expo 配置
    ├── package.json
    ├── .env / .env.production  # API 地址配置
    └── src/
        ├── app/                # Expo Router 文件路由
        │   ├── _layout.tsx     # 根布局
        │   ├── (tabs)/         # 底部 4 个 tab（首页/食材匹配/社区/我的）
        │   ├── recipe/[id].tsx # 菜谱详情
        │   ├── auth.tsx        # 登录/注册
        │   ├── favorites.tsx   # 我的收藏
        │   └── recipe/me.tsx   # 我发布的菜谱
        ├── components/         # 通用组件（菜谱卡片等）
        ├── features/           # 各功能模块（hooks、queries）
        ├── lib/                # API 客户端、类型、存储
        └── store/              # Zustand 状态（登录态等）
```

---

## 一、后端（FastAPI + PostgreSQL）

### 1. 环境要求

- Python 3.12+（建议 3.12，3.14 亦可）
- Docker（用于 PostgreSQL / Redis / 部署）
- 或本地安装 PostgreSQL 16 + Redis

### 2. 安装依赖

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Windows
# 或 .venv/bin/pip install -e ".[dev]"  # macOS/Linux
```

### 3. 启动数据库

**方式 A：Docker Compose（推荐）**

```bash
cd ..   # 回到项目根目录
docker compose up -d db redis
```

**方式 B：本地已有 PostgreSQL + Redis**

直接使用本地服务，把连接地址填进 `.env`。

### 4. 配置环境变量

复制 `.env.example` 为 `.env`（或直接用环境变量），按需修改：

```bash
# backend/.env
DATABASE_URL=postgresql+psycopg://cookbook:cookbook@localhost:5432/cookbook
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-me
```

### 5. 初始化数据库

```bash
.venv/Scripts/python -m alembic upgrade head   # 建表
.venv/Scripts/python -m scripts.init_ingredients  # 灌入种子食材库（番茄=西红柿等）
```

### 6. 启动后端

```bash
.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- API 文档：http://localhost:8000/docs （Swagger）
- 健康检查：http://localhost:8000/api/health

### 7. 导入菜谱数据

#### 方式一：语料库数据镜像（推荐）

语料库（下厨房语料库，约 1.8GB）**不放进 git**，通过独立的 **Docker 数据镜像**分发。整个流程中，**只有本机构建镜像前需要 gzip 一次**，服务端拉取镜像后全自动解压，**不需要手动处理任何 JSON 文件**：

```bash
# —— 本机（仅需做一次）——
# 1. 下载语料库 JSON 并压缩成 .gz（backend/data-image/ 目录下）
#    语料库 JSON（约 1.8GB）不放进 git，需从数据源下载：
#    下载地址：https://huggingface.co/datasets/xzm1999/XiaChuFang_Recipe_Corpus
#    文件：recipe_corpus_full.json
#    下载后放到 backend/data-image/ 目录，然后 gzip：
gzip -9 -k recipe_corpus_full.json      # 生成 recipe_corpus_full.json.gz，约 400MB

# 2. 构建数据镜像（通过根目录 docker-compose.yml 的 corpus 服务）
docker compose build corpus      # 等价于 cd backend/data-image && docker build

# 3. 推送到镜像仓库（阿里云 ACR / 本地镜像仓库均可）
docker tag cookbook/corpus:latest <registry>/cookbook/corpus:latest
docker push <registry>/cookbook/corpus:latest

# —— 服务端（全自动，无需手动处理数据）——
# 4. 拉取数据镜像
docker pull <registry>/cookbook/corpus:latest

# 5. 构建应用镜像并启动
#    应用镜像构建时自动从数据镜像复制 .gz 到容器内 /data/
#    后端 fetcher 启动时自动解压并读取，无需手动解压 JSON
docker compose up --build
```

**说明**：
- 语料库数据镜像由根目录 `docker-compose.yml` 中的 `corpus` 服务管理（`profiles: ["data"]`，默认不随 `up` 启动）
- 本机构建：`docker compose build corpus`
- 服务端拉取后构建应用镜像，会自动带上语料库

**自动化机制**：
- `backend/Dockerfile` 通过多级构建从 `cookbook/corpus:latest` 复制语料库到 `/data/`
- 后端 `fetcher.py` 检测到 `/data/recipe_corpus_full.json.gz` 自动解压读取（`IMPORT_DATA_DIR=/data`）
- 更新语料库 = 重新构建数据镜像 + 推送 + 服务端重新 `docker compose up --build`

#### 方式二：手动触发导入

创建管理员账号后（注册后手动改数据库 `is_admin` 字段为 true），调用：

```bash
# 手动触发数据导入（需要 admin token）
curl -X POST http://localhost:8000/api/admin/import/trigger \
  -H "Authorization: Bearer <admin_token>"

# 查看导入状态
curl http://localhost:8000/api/admin/import/status \
  -H "Authorization: Bearer <admin_token>"
```

每日凌晨 3:17 会自动增量更新（APScheduler + PostgreSQL advisory lock 防并发）。

### 8. 运行后端测试

```bash
cd backend
.venv/Scripts/python -m pytest
```

---

## 二、前端（Expo / React Native）

### 1. 环境要求

- Node.js 18+
- npm（或 yarn / pnpm）
- 手机调试需安装 Expo Go App（iOS/Android）

### 2. 安装依赖

```bash
cd app
npm install
```

### 3. 配置 API 地址

编辑 `app/.env`：

```
# Web 端（浏览器访问 localhost 后端）
EXPO_PUBLIC_API_URL=http://localhost:8000/api
```

真机调试时改为局域网 IP：

```
# app/.env.local（覆盖 .env，git 忽略）
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000/api
```

生产环境用 `app/.env.production` 配置线上 API 地址。

### 4. 启动开发服务器

```bash
npm run web        # Web 端（浏览器访问 http://localhost:8081）
# 或 npm run android  # Android 真机（需 Expo Go）
# 或 npm run ios      # iOS 真机（需 Expo Go）
```

### 5. 构建发布

```bash
npx expo export --platform web    # Web 静态导出
# 或 npx expo build:android        # Android 构建
# 或 npx expo build:ios            # iOS 构建
```

### 6. 前端类型检查

```bash
cd app
npx tsc --noEmit
```

---

## 三、完整部署（Docker Compose）

在根目录一键启动全部后端服务：

```bash
docker compose up -d --build
```

- `db`：PostgreSQL 16（数据持久化到 volume）
- `redis`：Redis 7
- `api`：FastAPI 应用（自动跑 Alembic 迁移 + 启动）

前端为独立应用，通过 `EXPO_PUBLIC_API_URL` 指向 api 服务，可单独构建部署（Web 静态托管 / 应用商店）。

---

## 核心算法：食材匹配

```
coverage(recipe) = |用户拥有的食材 ∩ 菜谱所需食材| / |菜谱所需食材|
```

- **覆盖率越高排越前**
- 覆盖率相同时，所需食材越少（缺口越小）越靠前
- 缺失的食材标注 **"需购买"**
- 支持同义词归一化（番茄 = 西红柿），文本输入自动剥离量词（"猪肉500克" → "猪肉"）

匹配流程：用户输入/点选食材 → 后端同义词归一化 → 计算每道菜的覆盖率 → 按覆盖率 + 缺口排序返回 → 前端展示"食材齐全 / xx%"与需购买清单。
