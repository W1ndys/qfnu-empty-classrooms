# UI 设计规范 v2.0

## 设计理念

**简洁 · 优雅 · 温暖 · 直觉**

采用温暖的曲奇棕色作为主题色，深度融合 iOS Human Interface Guidelines，打造简洁、优雅、富有亲和力的移动端体验。

### 核心设计原则

#### 1. 清晰性 (Clarity)

- 内容始终是第一位的，界面元素不应喧宾夺主
- 文字清晰易读，图标精准表意
- 功能明确，用户无需思考即可理解

#### 2. 遵从性 (Deference)

- 界面帮助用户理解内容并与之交互，但不与内容竞争
- 使用半透明和模糊效果暗示更多内容
- 最小化装饰元素，让内容充满整个屏幕

#### 3. 深度感 (Depth)

- 通过层次和动效传达视觉深度
- 使用阴影和模糊创建层级关系
- 动画和过渡增强用户对层级的感知

#### 4. 一致性 (Consistency)

- 系统级的交互模式
- 熟悉的图标和术语
- 统一的设计语言贯穿整个应用

---

## 1. 色彩系统

### 1.1 主色 - 曲奇棕

| 名称     | 色值                      | 用途                 |
| -------- | ------------------------- | -------------------- |
| **主色** | `#885021`                 | 按钮、链接、强调元素 |
| 主色-浅  | `#8B5A2B`                 | 悬停状态             |
| 主色-淡  | `#A67C52`                 | 次要按钮、图标       |
| 主色-深  | `#5D3615`                 | 按下状态             |
| 主色-10% | `rgba(118, 69, 28, 0.1)`  | 标签背景、淡色填充   |
| 主色-5%  | `rgba(118, 69, 28, 0.05)` | 卡片悬停背景         |

### 1.2 辅助色

| 名称   | 色值      | 用途               |
| ------ | --------- | ------------------ |
| 奶油色 | `#F5E6D3` | 温暖背景、高亮区域 |
| 焦糖色 | `#C4956A` | 装饰元素           |

### 1.3 语义色（iOS 标准）

| 语义 | 色值      | 用途             |
| ---- | --------- | ---------------- |
| 成功 | `#34C759` | 完成、通过、已修 |
| 警告 | `#FF9500` | 待处理、未完成   |
| 危险 | `#FF3B30` | 错误、删除       |
| 信息 | `#007AFF` | 链接、提示       |

### 1.4 中性色

| 名称      | 色值      | 用途               |
| --------- | --------- | ------------------ |
| 文字-主要 | `#1C1C1E` | 标题、正文         |
| 文字-次要 | `#8E8E93` | 描述、辅助文字     |
| 文字-占位 | `#C7C7CC` | 占位符、禁用状态   |
| 背景-页面 | `#F2F2F7` | 页面背景           |
| 背景-卡片 | `#FFFFFF` | 卡片、弹窗         |
| 背景-分组 | `#E5E5EA` | 分隔线、输入框背景 |

### 1.5 深色模式 (Dark Mode)

遵循 iOS 深色模式设计规范，提供舒适的夜间浏览体验：

| 名称      | 浅色模式  | 深色模式  | 用途               |
| --------- | --------- | --------- | ------------------ |
| 主色      | `#885021` | `#A67C52` | 按钮、链接         |
| 文字-主要 | `#1C1C1E` | `#FFFFFF` | 标题、正文         |
| 文字-次要 | `#8E8E93` | `#98989D` | 描述文字           |
| 文字-占位 | `#C7C7CC` | `#48484A` | 占位符             |
| 背景-页面 | `#F2F2F7` | `#000000` | 页面背景           |
| 背景-卡片 | `#FFFFFF` | `#1C1C1E` | 卡片、弹窗         |
| 背景-分组 | `#E5E5EA` | `#2C2C2E` | 分隔线、输入框背景 |
| 分隔线    | `#C6C6C8` | `#38383A` | 边框、分隔线       |

**深色模式设计原则：**

- 使用真黑色 (#000000) 作为背景，提升 OLED 屏幕显示效果
- 降低白色文字亮度，避免眼睛疲劳
- 主色调整为更亮的色调，保持可读性
- 阴影改用高亮边框或半透明白色叠加

---

## 2. 排版系统

### 2.1 字体

使用 Tailwind CSS CDN 配置自定义字体：

```html
<!-- 在 head 中引入 Tailwind CDN 并配置 -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: {
          sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Helvetica Neue', 'PingFang SC', 'sans-serif'],
        },
      },
    },
  }
</script>

<!-- 使用方式 -->
<div class="font-sans">文本内容</div>
```

### 2.2 字号

| 级别    | 大小 | 行高 | 用途             |
| ------- | ---- | ---- | ---------------- |
| H1      | 28px | 1.2  | 页面大标题       |
| H2      | 22px | 1.3  | 区块标题         |
| H3      | 17px | 1.4  | 卡片标题、导航栏 |
| Body    | 15px | 1.5  | 正文内容         |
| Caption | 13px | 1.4  | 辅助说明         |
| Small   | 11px | 1.3  | 标签、时间戳     |

### 2.3 字重

- **Regular (400)**: 正文
- **Medium (500)**: 强调文字
- **Semibold (600)**: 标题、按钮

---

## 3. 间距系统

采用 4px 基准的间距系统：

| 变量            | 值   | 用途           |
| --------------- | ---- | -------------- |
| `--spacing-xs`  | 4px  | 紧凑元素间距   |
| `--spacing-sm`  | 8px  | 图标与文字间距 |
| `--spacing-md`  | 12px | 列表项内边距   |
| `--spacing-lg`  | 16px | 卡片内边距     |
| `--spacing-xl`  | 20px | 区块间距       |
| `--spacing-xxl` | 24px | 大区块间距     |

---

## 4. 圆角系统

| 变量            | 值     | 用途             |
| --------------- | ------ | ---------------- |
| `--radius-sm`   | 8px    | 小按钮、标签     |
| `--radius-md`   | 12px   | 输入框、普通按钮 |
| `--radius-lg`   | 16px   | 卡片             |
| `--radius-xl`   | 20px   | 弹窗、大卡片     |
| `--radius-full` | 9999px | 胶囊按钮、头像   |

---

## 5. 阴影系统

简洁的阴影，仅用于提升层级感：

| 变量          | 值                            | 用途           |
| ------------- | ----------------------------- | -------------- |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.06)`  | 卡片静态       |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.08)` | 卡片悬停、浮层 |
| `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.12)` | 弹窗、模态框   |

---

## 6. 动画规范

### 6.1 时长

| 变量                | 值    | 用途               |
| ------------------- | ----- | ------------------ |
| `--duration-fast`   | 150ms | 按钮反馈、开关     |
| `--duration-normal` | 250ms | 普通过渡           |
| `--duration-slow`   | 350ms | 页面切换、展开收起 |

### 6.2 缓动函数

| 名称            | 值                                  | 用途     |
| --------------- | ----------------------------------- | -------- |
| **ease-out**    | `cubic-bezier(0, 0, 0.2, 1)`        | 元素进入 |
| **ease-in**     | `cubic-bezier(0.4, 0, 1, 1)`        | 元素离开 |
| **ease-in-out** | `cubic-bezier(0.4, 0, 0.2, 1)`      | 状态切换 |
| **spring**      | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性效果 |

### 6.3 标准动画

#### 淡入淡出

```html
<!-- 基础淡入效果 -->
<div class="transition-opacity duration-[250ms] ease-out opacity-100">
  淡入内容
</div>

<!-- 配合 JavaScript 控制显示/隐藏 -->
<div id="fadeElement" class="transition-opacity duration-[250ms] ease-out opacity-0">
  内容
</div>
<script>
  // 淡入
  document.getElementById('fadeElement').classList.replace('opacity-0', 'opacity-100');
  // 淡出
  document.getElementById('fadeElement').classList.replace('opacity-100', 'opacity-0');
</script>
```

#### 滑入滑出（从下往上）

```html
<!-- 滑入效果 -->
<div class="transition-all duration-300 ease-out transform translate-y-0 opacity-100">
  内容
</div>

<!-- 初始隐藏状态 -->
<div class="transition-all duration-300 ease-out transform translate-y-4 opacity-0">
  内容
</div>

<!-- 配合 JavaScript 控制 -->
<script>
  // 滑入：移除 translate-y-4 opacity-0，添加 translate-y-0 opacity-100
  // 滑出：移除 translate-y-0 opacity-100，添加 translate-y-2 opacity-0
</script>
```

#### 展开收起

```html
<!-- 展开状态 -->
<div class="transition-all duration-[350ms] ease-out overflow-hidden max-h-96 opacity-100">
  展开内容
</div>

<!-- 收起状态 -->
<div class="transition-all duration-[250ms] ease-in overflow-hidden max-h-0 opacity-0">
  收起内容
</div>

<!-- 配合 JavaScript 控制 -->
<script>
  function toggleExpand(el) {
    el.classList.toggle('max-h-0');
    el.classList.toggle('max-h-96');
    el.classList.toggle('opacity-0');
    el.classList.toggle('opacity-100');
  }
</script>
```

#### 按下反馈

```html
<!-- 可按压元素 -->
<button class="transition-transform duration-100 ease-out active:scale-[0.98]">
  可按压按钮
</button>
```

#### 弹性弹出 (Spring Pop)

```html
<!-- 在 Tailwind CDN 配置中添加弹性缓动 -->
<script>
  tailwind.config = {
    theme: {
      extend: {
        transitionTimingFunction: {
          'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        },
      },
    },
  }
</script>

<!-- 弹性弹出效果 -->
<div class="transition-all duration-[400ms] ease-spring transform scale-100 opacity-100">
  弹出内容
</div>

<!-- 初始隐藏状态 -->
<div class="transition-all duration-[400ms] ease-spring transform scale-75 opacity-0">
  隐藏内容
</div>
```

#### 旋转加载

```html
<!-- Tailwind 内置 animate-spin -->
<div class="animate-spin w-5 h-5 border-2 border-gray-300 border-t-[#885021] rounded-full"></div>

<!-- 或使用 SVG 图标 -->
<svg class="animate-spin h-5 w-5 text-[#885021]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
</svg>
```

#### 呼吸动画

```html
<!-- 在 Tailwind CDN 配置中添加呼吸动画 -->
<script>
  tailwind.config = {
    theme: {
      extend: {
        animation: {
          'breathe': 'breathe 2s ease-in-out infinite',
        },
        keyframes: {
          breathe: {
            '0%, 100%': { opacity: '1' },
            '50%': { opacity: '0.6' },
          },
        },
      },
    },
  }
</script>

<!-- 使用呼吸动画 -->
<div class="animate-breathe">呼吸效果内容</div>

<!-- 或使用内置的 animate-pulse（效果类似） -->
<div class="animate-pulse">脉冲效果</div>
```

---

## 7. 组件规范

### 7.1 卡片

```html
<div class="bg-white rounded-2xl p-4">
  卡片内容
</div>

<!-- 深色模式支持 -->
<div class="bg-white dark:bg-[#1C1C1E] rounded-2xl p-4">
  卡片内容
</div>
```

### 7.2 列表项

```html
<div class="px-4 py-3 bg-white border-b border-[#E5E5EA] active:bg-[#E5E5EA] transition-colors">
  列表项内容
</div>

<!-- 深色模式支持 -->
<div class="px-4 py-3 bg-white dark:bg-[#1C1C1E] border-b border-[#E5E5EA] dark:border-[#38383A] active:bg-[#E5E5EA] dark:active:bg-[#2C2C2E] transition-colors">
  列表项内容
</div>
```

### 7.3 按钮

**主按钮**

```html
<button class="bg-[#885021] text-white rounded-xl px-6 py-3 font-semibold transition-all active:bg-[#5D3615] active:scale-[0.98]">
  主按钮
</button>
```

**次按钮**

```html
<button class="bg-[#885021]/10 text-[#885021] rounded-xl px-6 py-3 font-semibold transition-all active:bg-[#885021]/20">
  次按钮
</button>
```

### 7.4 标签

```html
<!-- 主色标签 -->
<span class="text-[11px] px-2 py-0.5 rounded-[10px] font-medium bg-[#885021]/10 text-[#885021]">
  主色标签
</span>

<!-- 成功标签 -->
<span class="text-[11px] px-2 py-0.5 rounded-[10px] font-medium bg-[#34C759]/10 text-[#34C759]">
  成功标签
</span>

<!-- 警告标签 -->
<span class="text-[11px] px-2 py-0.5 rounded-[10px] font-medium bg-[#FF9500]/10 text-[#FF9500]">
  警告标签
</span>
```

### 7.5 导航栏

```html
<nav class="bg-white/85 dark:bg-[#1C1C1E]/85 backdrop-blur-xl border-b border-[#E5E5EA] dark:border-[#38383A]">
  导航内容
</nav>
```

### 7.6 输入框

**标准输入框**

```html
<input
  type="text"
  class="w-full bg-[#E5E5EA] dark:bg-[#2C2C2E] border-none rounded-xl px-4 py-3 text-[15px] text-[#1C1C1E] dark:text-white placeholder-[#C7C7CC] dark:placeholder-[#48484A] transition-all duration-200 focus:bg-white dark:focus:bg-[#1C1C1E] focus:ring-2 focus:ring-[#885021]/10 focus:outline-none"
  placeholder="请输入..."
/>
```

**搜索框**

```html
<div class="relative">
  <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8E8E93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
  </svg>
  <input
    type="text"
    class="w-full bg-[#E5E5EA] dark:bg-[#2C2C2E] rounded-xl py-2 pl-9 pr-3 text-[15px] placeholder-[#8E8E93] focus:outline-none"
    placeholder="搜索..."
  />
</div>
```

### 7.7 开关 (Switch)

```html
<!-- 关闭状态 -->
<div class="w-[51px] h-[31px] bg-[#E5E5EA] dark:bg-[#2C2C2E] rounded-2xl relative transition-colors duration-[250ms] cursor-pointer" onclick="this.classList.toggle('bg-[#885021]')">
  <div class="w-[27px] h-[27px] bg-white rounded-full absolute top-[2px] left-[2px] shadow transition-transform duration-[250ms]"></div>
</div>

<!-- 开启状态 -->
<div class="w-[51px] h-[31px] bg-[#885021] rounded-2xl relative transition-colors duration-[250ms] cursor-pointer">
  <div class="w-[27px] h-[27px] bg-white rounded-full absolute top-[2px] left-[2px] shadow transition-transform duration-[250ms] translate-x-5"></div>
</div>
```

### 7.8 分段控制器 (Segmented Control)

```html
<div class="bg-[#E5E5EA] dark:bg-[#2C2C2E] rounded-xl p-0.5 flex relative">
  <!-- 背景指示器 -->
  <div class="absolute bg-white dark:bg-[#1C1C1E] rounded-lg shadow-sm transition-transform duration-[250ms] h-[calc(100%-4px)] w-1/3 top-0.5 left-0.5"></div>

  <!-- 分段选项 -->
  <button class="flex-1 py-1.5 px-3 text-center text-[13px] font-medium text-[#1C1C1E] dark:text-white relative z-10 transition-colors duration-200">
    选项一
  </button>
  <button class="flex-1 py-1.5 px-3 text-center text-[13px] font-medium text-[#8E8E93] relative z-10 transition-colors duration-200">
    选项二
  </button>
  <button class="flex-1 py-1.5 px-3 text-center text-[13px] font-medium text-[#8E8E93] relative z-10 transition-colors duration-200">
    选项三
  </button>
</div>
```

### 7.9 底部操作栏 (Action Sheet)

```html
<div class="bg-white dark:bg-[#1C1C1E] rounded-t-[20px] p-2 shadow-[0_-4px_24px_rgba(0,0,0,0.12)]">
  <button class="w-full p-4 text-center text-[17px] text-[#885021] rounded-xl transition-colors duration-150 active:bg-[#E5E5EA] dark:active:bg-[#2C2C2E]">
    操作选项
  </button>
  <button class="w-full p-4 text-center text-[17px] text-[#FF3B30] rounded-xl transition-colors duration-150 active:bg-[#E5E5EA] dark:active:bg-[#2C2C2E]">
    删除
  </button>
  <button class="w-full p-4 mt-2 text-center text-[17px] text-[#885021] font-semibold bg-white dark:bg-[#1C1C1E] rounded-xl">
    取消
  </button>
</div>
```

### 7.10 Toast 提示

```html
<div class="bg-[#1C1C1E]/90 backdrop-blur-xl text-white px-5 py-3 rounded-2xl text-[15px] shadow-lg max-w-[80%] text-center">
  提示消息
</div>

<!-- 成功 Toast -->
<div class="bg-[#1C1C1E]/90 backdrop-blur-xl text-white px-5 py-3 rounded-2xl text-[15px] shadow-lg max-w-[80%] text-center flex items-center justify-center gap-2">
  <span class="text-[#34C759]">✓</span>
  <span>操作成功</span>
</div>
```

### 7.11 骨架屏 (Skeleton)

```html
<!-- 在 Tailwind CDN 配置中添加骨架屏动画 -->
<script>
  tailwind.config = {
    theme: {
      extend: {
        animation: {
          'skeleton': 'skeleton 1.5s ease-in-out infinite',
        },
        keyframes: {
          skeleton: {
            '0%': { backgroundPosition: '200% 0' },
            '100%': { backgroundPosition: '-200% 0' },
          },
        },
      },
    },
  }
</script>

<!-- 骨架屏元素 -->
<div class="h-4 rounded-xl bg-gradient-to-r from-[#E5E5EA] via-white to-[#E5E5EA] bg-[length:200%_100%] animate-skeleton"></div>

<!-- 或使用 Tailwind 内置的 animate-pulse -->
<div class="h-4 rounded-xl bg-[#E5E5EA] animate-pulse"></div>
```

### 7.12 下拉刷新指示器

```html
<div class="flex items-center justify-center h-[60px] text-[#8E8E93]">
  <div class="w-5 h-5 border-2 border-[#E5E5EA] border-t-[#885021] rounded-full animate-spin"></div>
</div>
```

---

## 8. 页面布局

### 8.1 基本结构

```
┌─────────────────────────┐
│      导航栏 (sticky)     │
├─────────────────────────┤
│                         │
│      页面内容区域         │
│   padding: 16px         │
│                         │
├─────────────────────────┤
│      页脚 (可选)         │
└─────────────────────────┘
```

### 8.2 内容区域

- 页面左右内边距: 16px
- 卡片间距: 12px
- 分组间距: 20px

### 8.3 安全区域 (Safe Area)

遵循 iOS 安全区域规范，适配刘海屏和底部指示器：

```html
<div class="pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]">
  页面内容
</div>

<!-- 或使用 style 属性 -->
<div style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom); padding-left: env(safe-area-inset-left); padding-right: env(safe-area-inset-right);">
  页面内容
</div>
```

### 8.4 大标题布局 (Large Title)

```html
<header class="px-4 pt-5 pb-3 bg-[#F2F2F7] dark:bg-black">
  <h1 class="text-[34px] font-bold leading-tight tracking-tight text-[#1C1C1E] dark:text-white transition-all duration-300">
    大标题
  </h1>
</header>

<!-- 滚动时收缩的标题 -->
<header class="px-4 py-3 bg-[#F2F2F7] dark:bg-black">
  <h1 class="text-[17px] font-semibold text-[#1C1C1E] dark:text-white transition-all duration-300">
    收缩标题
  </h1>
</header>
```

---

## 9. 图标规范

- 使用 Vant 内置图标或 SF Symbols 风格图标
- 尺寸: 16px (小)、20px (中)、24px (大)
- 颜色: 主色或次要文字色
- 线条粗细: 1.5px - 2px
- 圆角: 与整体设计保持一致

### 9.1 图标使用原则

- **语义明确**: 图标应直观表达功能，避免歧义
- **视觉平衡**: 图标大小和粗细保持一致
- **适当留白**: 图标周围保持足够的点击区域 (最小 44x44px)
- **状态区分**: 使用颜色或填充区分激活/未激活状态

---

## 10. 设计原则

### 10.1 简洁

- 避免过多装饰元素
- 不使用渐变背景（除非特殊场景）
- 阴影轻柔或不使用

### 10.2 优雅

- 统一的圆角系统
- 协调的色彩搭配
- 恰当的留白

### 10.3 动画丰富但不抢眼

- 所有交互都有反馈
- 动画时长适中，不超过 350ms
- 使用缓动函数，避免线性动画

### 10.4 一致性

- 同类元素使用相同样式
- 相同操作产生相同反馈
- 遵循 iOS 设计语言

---

## 11. 交互设计规范

### 11.1 触摸目标

遵循 Apple 的可触摸性指南：

- **最小触摸区域**: 44x44 pt (约 44x44 px)
- **推荐触摸区域**: 48x48 pt
- **按钮间距**: 至少 8px

### 11.2 手势交互

| 手势     | 用途             | 反馈                |
| -------- | ---------------- | ------------------- |
| 点击     | 选择、激活       | 高亮、缩放 (0.98)   |
| 长按     | 显示上下文菜单   | 轻微震动 + 菜单弹出 |
| 滑动     | 导航、删除       | 跟随手指移动        |
| 下拉     | 刷新             | 显示刷新指示器      |
| 上拉     | 加载更多         | 显示加载指示器      |
| 双击     | 放大/缩小 (图片) | 平滑缩放动画        |
| 捏合     | 缩放             | 实时缩放            |
| 边缘滑动 | 返回上一页       | 页面跟随手指滑出    |

### 11.3 反馈机制

**视觉反馈**

- 按钮按下: 缩放至 0.98 + 颜色加深
- 列表项选中: 背景色变化
- 加载中: 旋转动画或骨架屏
- 成功: 绿色勾号 + Toast
- 错误: 红色提示 + 震动

**触觉反馈 (Haptic Feedback)**

```javascript
// 轻触反馈
navigator.vibrate(10);

// 成功反馈
navigator.vibrate([10, 50, 10]);

// 错误反馈
navigator.vibrate([50, 100, 50]);
```

### 11.4 加载状态

**骨架屏** (推荐)

- 用于首次加载
- 保持内容结构
- 使用动画暗示加载中

**加载指示器**

- 用于刷新、提交等操作
- 居中显示或在操作位置显示
- 配合文字说明

**进度条**

- 用于文件上传、下载
- 显示具体进度百分比
- 可取消操作

### 11.5 空状态设计

```html
<div class="flex flex-col items-center justify-center px-10 py-16 text-center">
  <div class="w-[120px] h-[120px] mb-5 opacity-30">
    <!-- 空状态图标 -->
    <svg class="w-full h-full text-[#8E8E93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
    </svg>
  </div>
  <h3 class="text-[17px] font-semibold text-[#1C1C1E] dark:text-white mb-2">暂无内容</h3>
  <p class="text-[15px] text-[#8E8E93] leading-relaxed">这里还没有任何内容，快去添加吧</p>
</div>
```

**空状态原则**

- 使用友好的插图或图标
- 提供清晰的说明文字
- 提供明确的操作指引
- 避免使用技术术语

### 11.6 错误处理

**内联错误**

```html
<input
  type="text"
  class="w-full border border-[#FF3B30] bg-[#FF3B30]/5 rounded-xl px-4 py-3 text-[15px] focus:outline-none"
  placeholder="请输入..."
/>
<p class="text-[#FF3B30] text-[13px] mt-1">请输入有效的内容</p>
```

**错误页面**

- 使用友好的插图
- 说明错误原因
- 提供解决方案或重试按钮
- 避免显示技术错误信息

---

## 12. 毛玻璃效果 (Frosted Glass)

iOS 标志性的毛玻璃效果，用于创建层次感：

```html
<!-- 浅色模式毛玻璃 -->
<div class="bg-white/70 backdrop-blur-xl backdrop-saturate-[180%]">
  毛玻璃内容
</div>

<!-- 深色模式毛玻璃 -->
<div class="bg-white/70 dark:bg-[#1C1C1E]/70 backdrop-blur-xl backdrop-saturate-[180%]">
  毛玻璃内容
</div>
```

**使用场景**

- 导航栏
- 底部标签栏
- 弹出菜单
- 模态框背景

---

## 13. 层级系统 (Z-Index)

统一的层级管理，避免层级冲突：

| 层级名称 | Z-Index | 用途           |
| -------- | ------- | -------------- |
| base     | 0       | 基础内容       |
| dropdown | 100     | 下拉菜单       |
| sticky   | 200     | 吸顶元素       |
| fixed    | 300     | 固定定位元素   |
| modal-bg | 400     | 模态框背景遮罩 |
| modal    | 500     | 模态框、弹窗   |
| popover  | 600     | 气泡提示       |
| toast    | 700     | Toast 提示     |
| loading  | 800     | 全局加载遮罩   |

---

## 14. 微交互设计

### 14.1 按钮点击

```html
<button class="transition-all duration-150 ease-out active:scale-[0.98] active:opacity-80">
  可点击按钮
</button>
```

### 14.2 卡片悬停

```html
<div class="bg-white rounded-2xl p-4 transition-all duration-[250ms] ease-out hover:-translate-y-0.5 hover:shadow-md">
  卡片内容
</div>
```

### 14.3 输入框聚焦

```html
<input
  type="text"
  class="transition-all duration-200 ease-out focus:scale-[1.02] focus:ring-4 focus:ring-[#885021]/10 focus:outline-none"
  placeholder="请输入..."
/>
```

### 14.4 列表项滑动删除

```html
<div class="relative">
  <!-- 列表项 -->
  <div class="relative bg-white transition-transform duration-[250ms] ease-out" id="listItem">
    列表项内容
  </div>
  <!-- 删除按钮 -->
  <div class="absolute right-0 top-0 bottom-0 w-20 bg-[#FF3B30] flex items-center justify-center text-white">
    删除
  </div>
</div>

<script>
  // 滑动时添加 -translate-x-20 类
  document.getElementById('listItem').classList.add('-translate-x-20');
</script>
```

---

## 15. 响应式设计

### 15.1 断点系统

| 断点 | 宽度范围   | 设备类型 |
| ---- | ---------- | -------- |
| xs   | < 375px    | 小屏手机 |
| sm   | 375-414px  | 标准手机 |
| md   | 414-768px  | 大屏手机 |
| lg   | 768-1024px | 平板     |
| xl   | > 1024px   | 桌面     |

### 15.2 响应式原则

- **移动优先**: 从小屏幕开始设计
- **流式布局**: 使用百分比和 flex 布局
- **弹性图片**: 图片自适应容器大小
- **触摸友好**: 保持足够的触摸区域

```html
<!-- 移动优先的响应式容器 -->
<div class="p-4 md:p-6 md:max-w-5xl md:mx-auto">
  内容区域
</div>

<!-- 响应式网格布局 -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  <div>卡片 1</div>
  <div>卡片 2</div>
  <div>卡片 3</div>
</div>
```

---

## 16. 可访问性 (Accessibility)

### 16.1 颜色对比度

- 正文文字: 至少 4.5:1
- 大号文字 (18px+): 至少 3:1
- 图标和图形: 至少 3:1

### 16.2 语义化 HTML

```html
<!-- 使用语义化标签 -->
<nav>导航栏</nav>
<main>主要内容</main>
<article>文章</article>
<aside>侧边栏</aside>
<footer>页脚</footer>

<!-- 使用 ARIA 标签 -->
<button aria-label="关闭">×</button>
<div role="alert">错误提示</div>
```

### 16.3 键盘导航

- 所有交互元素可通过 Tab 键访问
- 使用 Enter/Space 激活按钮
- 使用 Esc 关闭弹窗
- 显示清晰的焦点状态

```html
<button class="focus-visible:outline-2 focus-visible:outline focus-visible:outline-[#885021] focus-visible:outline-offset-2">
  可聚焦按钮
</button>
```

### 16.4 屏幕阅读器支持

- 为图片添加 alt 文本
- 为图标按钮添加 aria-label
- 使用 aria-live 通知动态内容变化
- 隐藏装饰性元素 (aria-hidden="true")

---

## 17. 性能优化

### 17.1 动画性能

- 优先使用 `transform` 和 `opacity`
- 避免动画 `width`、`height`、`margin` 等触发重排的属性
- 使用 `will-change` 提示浏览器优化

```html
<!-- 优化动画性能 -->
<div class="will-change-transform transform-gpu transition-transform duration-300">
  高性能动画元素
</div>
```

### 17.2 图片优化

- 使用 WebP 格式
- 提供多种尺寸 (srcset)
- 懒加载非首屏图片
- 使用适当的压缩率

```html
<img
  src="image.webp"
  srcset="image-small.webp 375w, image-large.webp 768w"
  loading="lazy"
  alt="描述" />
```

---

## 附录: CSS 变量速查

```css
/* ==================== 主色系统 ==================== */
--primary-color: #885021;
--primary-color-light: #8b5a2b;
--primary-color-lighter: #a67c52;
--primary-color-dark: #5d3615;
--primary-color-opacity-10: rgba(118, 69, 28, 0.1);
--primary-color-opacity-5: rgba(118, 69, 28, 0.05);

/* ==================== 辅助色 ==================== */
--cream-color: #f5e6d3;
--caramel-color: #c4956a;

/* ==================== 语义色 ==================== */
--success-color: #34c759;
--warning-color: #ff9500;
--danger-color: #ff3b30;
--info-color: #007aff;

/* ==================== 中性色 (浅色模式) ==================== */
--text-primary: #1c1c1e;
--text-secondary: #8e8e93;
--text-tertiary: #c7c7cc;
--bg-primary: #f2f2f7;
--bg-secondary: #ffffff;
--bg-tertiary: #e5e5ea;
--border-color: #c6c6c8;

/* ==================== 中性色 (深色模式) ==================== */
@media (prefers-color-scheme: dark) {
  --primary-color: #a67c52;
  --text-primary: #ffffff;
  --text-secondary: #98989d;
  --text-tertiary: #48484a;
  --bg-primary: #000000;
  --bg-secondary: #1c1c1e;
  --bg-tertiary: #2c2c2e;
  --border-color: #38383a;
}

/* ==================== 间距系统 ==================== */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 20px;
--spacing-xxl: 24px;
--spacing-xxxl: 32px;

/* ==================== 圆角系统 ==================== */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-full: 9999px;

/* ==================== 阴影系统 ==================== */
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);

/* ==================== 动画时长 ==================== */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 350ms;
--duration-slower: 500ms;

/* ==================== 缓动函数 ==================== */
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

/* ==================== 层级系统 ==================== */
--z-base: 0;
--z-dropdown: 100;
--z-sticky: 200;
--z-fixed: 300;
--z-modal-bg: 400;
--z-modal: 500;
--z-popover: 600;
--z-toast: 700;
--z-loading: 800;

/* ==================== 字体系统 ==================== */
--font-family:
  -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue",
  "PingFang SC", sans-serif;
--font-size-h1: 28px;
--font-size-h2: 22px;
--font-size-h3: 17px;
--font-size-body: 15px;
--font-size-caption: 13px;
--font-size-small: 11px;
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* ==================== 触摸目标 ==================== */
--touch-target-min: 44px;
--touch-target-recommended: 48px;

/* ==================== 安全区域 ==================== */
--safe-area-top: env(safe-area-inset-top);
--safe-area-bottom: env(safe-area-inset-bottom);
--safe-area-left: env(safe-area-inset-left);
--safe-area-right: env(safe-area-inset-right);
```

---

## 附录: 设计检查清单

### 视觉设计

- [ ] 使用了正确的主题色 (#885021)
- [ ] 文字颜色对比度符合 WCAG 标准
- [ ] 圆角统一使用设计系统中的值
- [ ] 间距使用 4px 基准的倍数
- [ ] 阴影轻柔且一致

### 交互设计

- [ ] 所有可点击元素至少 44x44px
- [ ] 按钮有明确的按下反馈
- [ ] 加载状态有清晰的指示
- [ ] 错误提示友好且可操作
- [ ] 空状态提供明确的指引

### 动画效果

- [ ] 动画时长不超过 350ms
- [ ] 使用了合适的缓动函数
- [ ] 避免动画触发重排的属性
- [ ] 动画流畅不卡顿

### 响应式

- [ ] 在不同屏幕尺寸下正常显示
- [ ] 适配了安全区域
- [ ] 图片自适应容器大小
- [ ] 文字在小屏幕上可读

### 可访问性

- [ ] 图片有 alt 文本
- [ ] 按钮有 aria-label
- [ ] 可通过键盘导航
- [ ] 焦点状态清晰可见
- [ ] 支持屏幕阅读器

### 性能

- [ ] 图片使用了懒加载
- [ ] 动画使用了 transform 和 opacity
- [ ] 避免了不必要的重绘和重排
- [ ] 首屏加载时间 < 2s

### 深色模式

- [ ] 深色模式下颜色正确
- [ ] 文字在深色背景上可读
- [ ] 阴影改用边框或高亮
- [ ] 图片在深色模式下适配

---

## 附录: 常见设计模式

### 列表页

- 使用卡片或列表项展示内容
- 提供下拉刷新和上拉加载
- 空状态友好提示
- 支持滑动删除

### 详情页

- 大标题 + 内容区域
- 使用分组卡片组织信息
- 底部固定操作按钮
- 支持返回手势

### 表单页

- 分组展示表单项
- 实时验证输入
- 错误提示清晰
- 提交按钮固定在底部

### 搜索页

- 顶部搜索框
- 搜索历史和热门搜索
- 实时搜索建议
- 空结果友好提示

### 设置页

- 使用列表项展示选项
- 分组组织相关设置
- 使用开关、选择器等组件
- 重要操作需要二次确认

---

## 版本历史

### v2.0 (2026-01-24)

- 新增深色模式支持
- 新增交互设计规范
- 新增微交互设计
- 新增可访问性规范
- 新增响应式设计指南
- 新增性能优化建议
- 扩展组件规范
- 新增设计检查清单
- 新增常见设计模式

### v1.0

- 初始版本
- 基础色彩系统
- 基础组件规范
- 基础动画规范

```

```
