# 前端 Vue 3 重构方案

## 一、重构背景与目标

### 1.1 现状分析

当前前端采用**纯静态 HTML + Alpine.js + Axios + Tailwind CSS v3** 的技术栈：

- **3 个独立 HTML 页面**：`index.html`（首页）、`empty-classroom.html`（空教室查询）、`full-day-status.html`（全天状态）
- **无 JavaScript 构建流程**：所有 JS 逻辑以内联 `<script>` 块的形式嵌在各 HTML 文件中
- **Alpine.js** 通过 CDN 引入，用于页面内的响应式数据绑定
- **Axios** 通过 CDN 引入，用于 API 请求
- **Tailwind CSS v3** 是唯一有构建步骤的部分（`input.css` → `style.css`）
- **Go embed** 将所有前端文件嵌入 Go 二进制，通过 Gin 框架提供服务

### 1.2 重构目标

- 将前端迁移到 **Vue 3** 单页应用（SPA），使用 **Vite** 作为构建工具
- 保持 **Tailwind CSS v3** 作为样式技术栈
- 保持与后端 Go API 的完全兼容，API 接口不做任何变更
- 保持 Go embed 嵌入前端产物的部署方式
- 提升代码可维护性、组件复用性和开发体验

### 1.3 不变的部分

- **后端 Go 代码**：`internal/`、`pkg/` 目录下的所有 Go 代码不做修改
- **API 接口**：三个接口 `GET /api/v1/status`、`POST /api/v1/query`、`POST /api/v1/query-full-day` 保持不变
- **部署方式**：交叉编译 + SSH 上传 + supervisord 管理的模式不变
- **品牌风格**：曲奇棕主题色 `#885021` 及整体 UI 风格保持一致

---

## 二、技术选型

| 类别 | 选型 | 说明 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | 使用 `<script setup>` 语法 |
| 构建工具 | Vite | 开发快速热更新，生产高效打包 |
| 路由 | Vue Router 4 | SPA 路由管理，使用 HTML5 History 模式 |
| HTTP 客户端 | Axios | 保持现有选择，统一封装 |
| 样式 | Tailwind CSS v3 | 保持现有版本，集成到 Vite 构建流程 |
| 状态管理 | 不引入（组件内管理） | 项目规模小，无需 Pinia/Vuex |
| 图标 | 内联 SVG 组件化 | 将现有 SVG 抽取为 Vue 组件 |

---

## 三、目录结构设计

重构后前端代码将放置在项目根目录下的 `frontend/` 目录中，构建产物输出到 `web/dist/` 目录供 Go embed 嵌入。

```
frontend/                          # Vue 3 前端源码目录（新增）
├── index.html                     # Vite 入口 HTML
├── vite.config.js                 # Vite 配置
├── tailwind.config.js             # Tailwind CSS v3 配置（从项目根目录迁入）
├── postcss.config.js              # PostCSS 配置
├── package.json                   # 前端依赖管理
├── src/
│   ├── main.js                    # Vue 应用入口
│   ├── App.vue                    # 根组件
│   ├── router/
│   │   └── index.js               # Vue Router 配置
│   ├── api/
│   │   └── index.js               # Axios 实例与 API 封装
│   ├── composables/               # 组合式函数（可复用逻辑）
│   │   ├── useSystemStatus.js     # 系统状态检查逻辑
│   │   └── useDateSelection.js    # 日期选择逻辑
│   ├── components/                # 公共组件
│   │   ├── AppHeader.vue          # 页面顶部导航栏
│   │   ├── AppFooter.vue          # 页面底部
│   │   ├── StatusWarning.vue      # 权限/状态警告提示
│   │   ├── DateSelector.vue       # 日期选择器（今天/明天/后天/自定义）
│   │   ├── LoadingSpinner.vue     # 加载动画
│   │   ├── QRCodeCard.vue         # 微信二维码推广卡片
│   │   └── EmptyState.vue         # 空状态提示
│   ├── views/                     # 页面级组件
│   │   ├── HomeView.vue           # 首页
│   │   ├── EmptyClassroomView.vue # 空教室查询页
│   │   └── FullDayStatusView.vue  # 全天状态查询页
│   ├── assets/
│   │   ├── css/
│   │   │   └── main.css           # Tailwind 入口 CSS（含自定义变量）
│   │   └── images/
│   │       └── qrcode.png         # 微信二维码（从 web/images 迁移）
│   └── utils/
│       └── date.js                # 日期工具函数
│
web/                               # Go embed 目录（修改）
├── assets.go                      # 修改 embed 指令，嵌入 dist/ 目录
└── dist/                          # Vite 构建产物输出目录（构建时生成）
    ├── index.html
    ├── assets/
    │   ├── index-[hash].js
    │   └── index-[hash].css
    └── images/
        └── qrcode.png
```

---

## 四、详细修改方案

### 4.1 前端工程初始化

#### 4.1.1 创建 `frontend/` 目录

在项目根目录下创建 `frontend/` 目录，作为 Vue 3 项目的根目录。

#### 4.1.2 `frontend/package.json`

新建 `package.json`，包含以下依赖：

- **生产依赖**：`vue`、`vue-router`、`axios`
- **开发依赖**：`vite`、`@vitejs/plugin-vue`、`tailwindcss`（v3）、`postcss`、`autoprefixer`

脚本命令：
- `dev`：启动 Vite 开发服务器（带 API 代理）
- `build`：构建生产版本，输出到 `../web/dist/`
- `preview`：本地预览构建产物

#### 4.1.3 `frontend/vite.config.js`

关键配置项：
- **输出目录**：`outDir: '../web/dist'`，确保构建产物放到 Go embed 能读取的位置
- **base**：设置为 `'./'` 或 `'/'`，确保资源路径正确
- **开发代理**：将 `/api` 请求代理到 Go 后端（默认 `http://localhost:8080`），实现前后端分离开发
- **构建清理**：每次构建前清空 `dist/` 目录

#### 4.1.4 `frontend/tailwind.config.js`

从项目根目录的 `tailwind.config.js` 迁移，修改 `content` 扫描路径：
- 扫描 `./src/**/*.{vue,js,ts,jsx,tsx}` 和 `./index.html`
- 在 `theme.extend.colors` 中注册主题色变量，替代之前 HTML 中大量使用的任意值写法（如 `text-[#885021]`）

#### 4.1.5 `frontend/postcss.config.js`

标准 PostCSS 配置，引入 `tailwindcss` 和 `autoprefixer` 插件。

---

### 4.2 Vue 应用架构

#### 4.2.1 入口文件 `frontend/src/main.js`

- 创建 Vue 应用实例
- 注册 Vue Router
- 引入 Tailwind CSS 入口文件（`./assets/css/main.css`）
- 挂载到 `#app`

#### 4.2.2 根组件 `frontend/src/App.vue`

- 包含 `<router-view />` 作为页面容器
- 可选：包含全局的 `<AppFooter />` 组件

#### 4.2.3 路由配置 `frontend/src/router/index.js`

路由映射与当前 HTML 页面一一对应：

| 路径 | 组件 | 对应原页面 |
|------|------|-----------|
| `/` | `HomeView` | `index.html` |
| `/empty-classroom` | `EmptyClassroomView` | `empty-classroom.html` |
| `/full-day-status` | `FullDayStatusView` | `full-day-status.html` |

使用 **HTML5 History 模式**（`createWebHistory()`），保持 URL 与当前完全一致。

---

### 4.3 API 封装

#### 4.3.1 `frontend/src/api/index.js`

创建 Axios 实例，统一配置：
- `baseURL`：留空（同源请求）
- `timeout`：30 秒
- 请求拦截器：可选（当前无鉴权需求）
- 响应拦截器：统一错误处理

封装三个 API 函数：
- `getStatus()` → `GET /api/v1/status`
- `queryClassrooms(params)` → `POST /api/v1/query`
- `queryFullDayStatus(params)` → `POST /api/v1/query-full-day`

请求参数和响应格式与当前完全一致，无需修改后端。

---

### 4.4 组合式函数（Composables）

#### 4.4.1 `useSystemStatus.js`

提取两个页面共享的系统状态检查逻辑：

- **状态变量**：`statusLoading`、`inTeachingCalendar`、`hasPermission`、`currentWeek`、`currentTerm`
- **方法**：`checkStatus()` — 调用 `getStatus()` API 并更新状态
- 在组件 `onMounted` 时自动调用

这段逻辑在 `empty-classroom.html` 和 `full-day-status.html` 中完全重复，提取后可复用。

#### 4.4.2 `useDateSelection.js`

提取两个页面共享的日期选择逻辑：

- **状态变量**：`quickDateLabels`、`useCustomDate`、`customOffset`、`dateOffset`
- **计算属性**：`customDatePreview` — 显示目标日期的预览文本
- **方法**：`setQuickDate(offset)`、`toggleCustomDate()`、`updateCustomOffset()`

这段逻辑在两个查询页面中也是完全重复的。

---

### 4.5 公共组件设计

#### 4.5.1 `AppHeader.vue`

对应当前每个页面顶部的 sticky 导航栏。

**Props**：
- `title: string` — 页面标题（如"空教室查询"、"教室全天状态"）
- `showBack: boolean` — 是否显示返回按钮（首页不需要）

**行为**：
- 返回按钮使用 `router.back()` 或 `router.push('/')`
- 保持毛玻璃效果（`bg-white/80 backdrop-blur-md`）

#### 4.5.2 `StatusWarning.vue`

封装权限不足和非教学周的两种警告提示。

**Props**：
- `type: 'error' | 'warning'` — 控制颜色方案（红色/琥珀色）
- `title: string` — 警告标题
- `message: string` — 警告描述

#### 4.5.3 `DateSelector.vue`

封装日期选择功能，包括快捷日期按钮和自定义偏移输入。

**Props**：无（内部使用 `useDateSelection` 组合式函数）

**Emits**：
- `update:offset` — 当日期偏移发生变化时向外发出事件

或者使用 `v-model:offset` 实现双向绑定。

#### 4.5.4 `LoadingSpinner.vue`

简单的加载动画组件，封装当前的 SVG 旋转动画。

**Props**：
- `text: string` — 加载提示文字（默认 "加载中..."）

#### 4.5.5 `QRCodeCard.vue`

封装微信公众号二维码推广卡片，三个页面中都有出现（首页和两个查询页）。

**Props**：无（内容固定）

#### 4.5.6 `EmptyState.vue`

空结果状态提示。

**Props**：
- `text: string` — 提示文字（如 "该时间段暂无空闲教室"）

---

### 4.6 页面组件设计

#### 4.6.1 `HomeView.vue`

对应 `index.html`，纯展示页面。

**结构**：
- 标题区域（QFNU 教室查询系统）
- 两个功能卡片（使用 `<router-link>` 代替 `<a>` 标签）
- `<QRCodeCard />` 公众号推广
- `<AppFooter />`

**特点**：无 JS 逻辑，纯模板渲染。

#### 4.6.2 `EmptyClassroomView.vue`

对应 `empty-classroom.html`，空教室查询页。

**组合式函数引用**：
- `useSystemStatus()` — 系统状态检查
- `useDateSelection()` — 日期选择

**页面私有状态**：
- `form.building` — 教学楼名称
- `form.start` / `form.end` — 起始/终止节次
- `loading` — 查询加载状态
- `hasSearched` — 是否已查询
- `results` — 查询结果（教室列表）
- `resultInfo` — 结果元数据（日期、周次、星期）
- `displayLimit` — 分页加载限制

**子组件引用**：
- `<AppHeader title="空教室查询" showBack />`
- `<StatusWarning />` × 2（权限、教学周）
- `<DateSelector v-model:offset="form.offset" />`
- `<LoadingSpinner />` (状态检查时)
- `<QRCodeCard />`
- `<EmptyState />`

**方法**：
- `search()` — 调用 `queryClassrooms()` API

#### 4.6.3 `FullDayStatusView.vue`

对应 `full-day-status.html`，全天状态查询页。

**组合式函数引用**：
- `useSystemStatus()` — 系统状态检查
- `useDateSelection()` — 日期选择

**页面私有状态**：
- `form.building` — 教学楼名称
- `loading` — 查询加载状态
- `hasSearched` — 是否已查询
- `resultData` — 完整的查询响应数据
- `legendItems` — 状态图例数组（emoji + 名称）

**子组件引用**：
- `<AppHeader title="教室全天状态" showBack />`
- `<StatusWarning />` × 2
- `<DateSelector v-model:offset="form.offset" />`
- `<QRCodeCard />`

**方法**：
- `search()` — 调用 `queryFullDayStatus()` API
- `getEmoji(statusId)` — 根据状态 ID 返回对应 emoji

**注意**：全天状态表格的样式（横向滚动、固定首列）需要在该组件中保留，可使用 scoped style 或 Tailwind 类实现。

---

### 4.7 样式迁移

#### 4.7.1 Tailwind CSS 入口文件

将 `web/css/input.css` 的内容迁移到 `frontend/src/assets/css/main.css`：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --color-primary: #885021;
    --color-primary-light: #8B5A2B;
    --color-primary-lighter: #A67C52;
    --color-primary-dark: #5D3615;
    --color-primary-10: rgba(118, 69, 28, 0.1);
    --color-cream: #F5E6D3;
    --color-caramel: #C4956A;
    --color-bg-page: #F2F2F7;
    --color-bg-card: #FFFFFF;
    --color-text-main: #1C1C1E;
    --color-text-sub: #8E8E93;
  }
}
```

#### 4.7.2 Tailwind 主题色注册

在 `tailwind.config.js` 的 `theme.extend.colors` 中注册常用主题色，减少模板中的任意值写法：

```js
colors: {
  primary: {
    DEFAULT: '#885021',
    light: '#8B5A2B',
    lighter: '#A67C52',
    dark: '#5D3615',
  }
}
```

这样模板中可以写 `text-primary` 代替 `text-[#885021]`，`bg-primary/10` 代替 `bg-[#885021]/10`。

#### 4.7.3 全天状态页特有样式

`full-day-status.html` 中的内联 `<style>`（状态颜色类、表格横向滚动、固定首列）将迁移到 `FullDayStatusView.vue` 的 `<style scoped>` 中。

---

### 4.8 静态资源处理

#### 4.8.1 图片

将 `web/images/qrcode.png` 复制到 `frontend/src/assets/images/qrcode.png`。

在 Vue 组件中通过模块化导入使用：
```html
<img :src="qrcodeUrl" alt="微信公众号二维码" />
```
```js
import qrcodeUrl from '@/assets/images/qrcode.png'
```

Vite 会自动处理图片的 hash 命名和路径。

#### 4.8.2 SVG 图标

当前 HTML 中内联了大量 SVG 代码（返回箭头、搜索图标、建筑图标、警告图标等），建议以下处理方式：

- **方案 A**（推荐）：继续在模板中直接内联 SVG，与现有方式一致，无额外依赖
- **方案 B**：将高频使用的 SVG 抽取为独立的 Vue 组件（如 `IconArrowLeft.vue`、`IconSearch.vue`），按需引用

考虑到项目规模较小，推荐方案 A，保持简单。

---

## 五、后端修改方案

### 5.1 `web/assets.go` 修改

将 embed 指令修改为嵌入 Vite 的构建产物：

```go
//go:embed dist
var StaticFS embed.FS
```

注意：由于 `embed.FS` 的路径会包含 `dist/` 前缀，在使用时需要通过 `fs.Sub` 去除前缀。

### 5.2 `main.go` 路由修改

**核心变化**：由于重构为 SPA，所有页面路由都由 Vue Router 在客户端处理，后端只需要：

1. **API 路由不变**：`/api/v1/*` 保持原样
2. **静态资源路由**：`/assets/*` 对应 Vite 构建产物中的 `assets/` 目录（JS、CSS、图片等）
3. **SPA Fallback**：所有非 API、非静态资源的 GET 请求，都返回 `index.html`，由 Vue Router 处理前端路由

具体修改：
- 移除对 `empty-classroom.html` 和 `full-day-status.html` 的显式 `ReadFile` 路由
- 移除旧的 `/static` 路由
- 添加 `dist/assets/` 的静态文件服务
- 添加 `dist/images/` 的静态文件服务（如有）
- 添加 SPA fallback：未匹配的路由返回 `dist/index.html`

### 5.3 路由伪代码逻辑

```
GET /api/v1/*        → API Handler（不变）
GET /assets/*        → 静态文件（dist/assets/）
GET /images/*        → 静态文件（dist/images/，如有）
GET /*               → dist/index.html（SPA fallback）
```

---

## 六、开发工作流

### 6.1 开发环境

前后端分离开发：

1. 启动 Go 后端：`go run .`（监听 `:8080`）
2. 启动 Vite 开发服务器：`cd frontend && npm run dev`（监听 `:5173`）
3. Vite 开发代理将 `/api` 请求转发到 `http://localhost:8080`

开发时直接访问 Vite 的 `:5173` 端口，享受热更新。

### 6.2 构建与部署

```bash
# 1. 构建前端
cd frontend && npm run build
# 产物输出到 ../web/dist/

# 2. 构建 Go 二进制（embed 包含前端产物）
go build -o app .

# 3. 部署（现有 deploy.ps1 流程不变）
.\deploy.ps1
```

### 6.3 根目录 `package.json` 处理

原有的根目录 `package.json` 将被替换。可以保留一个简化版，通过 npm scripts 统一管理前后端命令：

```json
{
  "scripts": {
    "dev:frontend": "cd frontend && npm run dev",
    "build:frontend": "cd frontend && npm run build",
    "dev:backend": "air"
  }
}
```

或者直接删除根目录的 `package.json`（及 `node_modules/`、`tailwind.config.js`），将所有前端依赖移到 `frontend/` 目录中管理。

---

## 七、`.gitignore` 更新

需要添加/修改的忽略规则：

```gitignore
# Vue 3 前端
frontend/node_modules/
frontend/dist/

# Vite 构建产物（嵌入 Go 二进制前需要先构建）
web/dist/

# 移除旧的 CSS 忽略规则（如果有）
# web/css/style.css  ← 不再需要
```

---

## 八、旧文件清理

重构完成后，以下文件/目录可以删除：

| 文件/目录 | 说明 |
|-----------|------|
| `web/index.html` | 已迁移到 `frontend/src/views/HomeView.vue` |
| `web/empty-classroom.html` | 已迁移到 `frontend/src/views/EmptyClassroomView.vue` |
| `web/full-day-status.html` | 已迁移到 `frontend/src/views/FullDayStatusView.vue` |
| `web/css/` | CSS 构建已集成到 Vite，由 `frontend/src/assets/css/main.css` 替代 |
| `web/images/` | 图片已迁移到 `frontend/src/assets/images/` |
| 根目录 `tailwind.config.js` | 已迁移到 `frontend/tailwind.config.js` |
| 根目录 `package.json` | 已替换为 `frontend/package.json`（或保留简化版） |
| 根目录 `package-lock.json` | 随 `package.json` 一起清理 |
| 根目录 `node_modules/` | 随 `package.json` 一起清理 |

---

## 九、迁移映射对照表

### 9.1 页面映射

| 原文件 | 新文件 | 路由 |
|--------|--------|------|
| `web/index.html` | `frontend/src/views/HomeView.vue` | `/` |
| `web/empty-classroom.html` | `frontend/src/views/EmptyClassroomView.vue` | `/empty-classroom` |
| `web/full-day-status.html` | `frontend/src/views/FullDayStatusView.vue` | `/full-day-status` |

### 9.2 逻辑映射

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `empty-classroom.html` 内联 `app()` 函数 | `EmptyClassroomView.vue` + `useSystemStatus` + `useDateSelection` | 拆分为组件逻辑和可复用组合函数 |
| `full-day-status.html` 内联 `fullDayApp()` 函数 | `FullDayStatusView.vue` + `useSystemStatus` + `useDateSelection` | 同上 |
| 两个页面重复的 `checkStatus()` | `composables/useSystemStatus.js` | 消除重复 |
| 两个页面重复的日期选择逻辑 | `composables/useDateSelection.js` | 消除重复 |
| CDN 引入的 Alpine.js | 移除 | 由 Vue 3 替代 |
| CDN 引入的 Axios | npm 安装 + 模块化导入 | 统一管理版本 |

### 9.3 样式映射

| 原位置 | 新位置 |
|--------|--------|
| `web/css/input.css` | `frontend/src/assets/css/main.css` |
| 根目录 `tailwind.config.js` | `frontend/tailwind.config.js` |
| `full-day-status.html` 内联 `<style>` | `FullDayStatusView.vue` 的 `<style scoped>` |
| HTML 中的 `text-[#885021]` | `text-primary`（通过 Tailwind 主题配置） |
| HTML 中的 `bg-[#885021]/10` | `bg-primary/10` |

---

## 十、实施步骤

建议按以下顺序实施，每一步完成后可独立验证：

### 第一步：搭建 Vue 3 工程骨架
1. 创建 `frontend/` 目录及配置文件（`package.json`、`vite.config.js`、`tailwind.config.js`、`postcss.config.js`）
2. 安装依赖
3. 创建 `main.js`、`App.vue`、路由配置
4. 创建 Tailwind CSS 入口文件
5. 验证：Vite 开发服务器能正常启动，看到空白页面

### 第二步：实现公共组件与组合式函数
1. 实现 `useSystemStatus.js` 和 `useDateSelection.js`
2. 实现 `AppHeader.vue`、`AppFooter.vue`、`StatusWarning.vue`、`DateSelector.vue`、`LoadingSpinner.vue`、`QRCodeCard.vue`、`EmptyState.vue`
3. 封装 API 模块 `api/index.js`
4. 验证：各组件能独立渲染

### 第三步：实现页面组件
1. 实现 `HomeView.vue`（最简单，纯展示）
2. 实现 `EmptyClassroomView.vue`（查询功能）
3. 实现 `FullDayStatusView.vue`（表格功能）
4. 验证：通过 Vite 代理访问 Go 后端 API，功能正常

### 第四步：修改后端集成
1. 修改 `web/assets.go` 的 embed 指令
2. 修改 `main.go` 的路由配置（SPA fallback）
3. 执行前端构建 `npm run build`
4. 验证：直接运行 Go 二进制，前端页面和 API 都正常工作

### 第五步：清理与收尾
1. 删除旧的 HTML 文件和 CSS 文件
2. 清理根目录的 Node.js 相关文件
3. 更新 `.gitignore`
4. 更新 `deploy.ps1`（在部署前先构建前端）
5. 更新项目 README

---

## 十一、风险与注意事项

### 11.1 SPA History 模式的服务端配合

Vue Router 使用 HTML5 History 模式时，用户直接访问 `/empty-classroom` 或刷新页面时，请求会到达 Go 后端。后端必须对所有未匹配的路由返回 `index.html`，否则会 404。这是最关键的后端修改点。

### 11.2 Go embed 的路径前缀

使用 `//go:embed dist` 时，`embed.FS` 中的文件路径会带有 `dist/` 前缀。例如读取 `index.html` 需要使用 `dist/index.html`。建议使用 `io/fs` 包的 `fs.Sub()` 函数去除前缀：

```go
subFS, _ := fs.Sub(StaticFS, "dist")
```

### 11.3 构建顺序

部署时必须**先构建前端**（`npm run build`），再构建 Go 二进制。否则 `web/dist/` 目录不存在会导致 Go 编译失败（embed 找不到文件）。`deploy.ps1` 需要相应更新。

### 11.4 开发环境双服务器

开发时需要同时运行 Vite 和 Go 两个服务器。可以考虑使用 `concurrently` 或类似工具来同时管理，或者在 Air 的 `.air.toml` 中配置前端构建命令。

### 11.5 首次构建问题

由于 `web/dist/` 是 gitignore 的目录，新克隆的项目需要先执行 `cd frontend && npm install && npm run build` 才能编译 Go 项目。建议在 README 中明确说明这一点。
