# UI 设计规范 v1.0

## 设计理念

**简洁 · 优雅 · 温暖**

采用温暖的曲奇棕色作为主题色，结合 iOS 设计语言，打造简洁、优雅、富有亲和力的移动端体验。

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

---

## 2. 排版系统

### 2.1 字体

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue",
  "PingFang SC", sans-serif;
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

```css
.fade-enter {
  opacity: 0;
}
.fade-enter-active {
  transition: opacity 250ms ease-out;
}
.fade-leave-active {
  transition: opacity 200ms ease-in;
}
.fade-leave-to {
  opacity: 0;
}
```

#### 滑入滑出（从下往上）

```css
.slide-up-enter {
  transform: translateY(16px);
  opacity: 0;
}
.slide-up-enter-active {
  transition: all 300ms ease-out;
}
.slide-up-leave-active {
  transition: all 200ms ease-in;
}
.slide-up-leave-to {
  transform: translateY(8px);
  opacity: 0;
}
```

#### 展开收起

```css
.expand-enter {
  max-height: 0;
  opacity: 0;
}
.expand-enter-active {
  transition: all 350ms ease-out;
  overflow: hidden;
}
.expand-leave-active {
  transition: all 250ms ease-in;
  overflow: hidden;
}
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
```

#### 按下反馈

```css
.pressable:active {
  transform: scale(0.98);
  transition: transform 100ms ease-out;
}
```

---

## 7. 组件规范

### 7.1 卡片

```css
.card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  /* 无阴影或极淡阴影 */
}
```

### 7.2 列表项

```css
.list-item {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-bottom: 0.5px solid var(--bg-tertiary);
}

.list-item:active {
  background: var(--bg-tertiary);
}
```

### 7.3 按钮

**主按钮**

```css
.btn-primary {
  background: var(--primary-color);
  color: white;
  border-radius: var(--radius-md);
  padding: 12px 24px;
  font-weight: 600;
}

.btn-primary:active {
  background: var(--primary-color-dark);
  transform: scale(0.98);
}
```

**次按钮**

```css
.btn-secondary {
  background: var(--primary-color-opacity-10);
  color: var(--primary-color);
  border-radius: var(--radius-md);
}
```

### 7.4 标签

```css
.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.tag-primary {
  background: var(--primary-color-opacity-10);
  color: var(--primary-color);
}

.tag-success {
  background: rgba(52, 199, 89, 0.12);
  color: #34c759;
}

.tag-warning {
  background: rgba(255, 149, 0, 0.12);
  color: #ff9500;
}
```

### 7.5 导航栏

```css
.nav-bar {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 0.5px solid var(--bg-tertiary);
}
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

---

## 9. 图标规范

- 使用 Vant 内置图标
- 尺寸: 16px (小)、20px (中)、24px (大)
- 颜色: 主色或次要文字色

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

## 附录: CSS 变量速查

```css
/* 主色 */
--primary-color: #885021;
--primary-color-light: #8b5a2b;
--primary-color-dark: #5d3615;
--primary-color-opacity-10: rgba(118, 69, 28, 0.1);

/* 语义色 */
--success-color: #34c759;
--warning-color: #ff9500;
--danger-color: #ff3b30;

/* 中性色 */
--text-primary: #1c1c1e;
--text-secondary: #8e8e93;
--text-tertiary: #c7c7cc;
--bg-primary: #f2f2f7;
--bg-secondary: #ffffff;
--bg-tertiary: #e5e5ea;

/* 间距 */
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 20px;

/* 圆角 */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;

/* 动画 */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 350ms;
```
