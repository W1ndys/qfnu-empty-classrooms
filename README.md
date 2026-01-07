# 曲阜师范大学空教室查询系统

一个基于 Flask 的空教室查询 Web 服务，自动检测设备类型并展示对应的页面。

## 功能特性

- 实时查询指定条件的空教室
- 支持自定义教学楼、节次、日期
- 根据当前时间智能设置默认查询参数
- 根据设备自动路由：PC 端使用 Element Plus，移动端使用 Vant

## 快速开始

### 1. 安装 uv（如未安装）

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆项目并安装依赖

```bash
git clone https://github.com/W1ndys/qfnu-empty-classrooms.git
cd qfnu-empty-classrooms

# 使用 uv 同步依赖
uv sync
```

### 3. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的教务系统账号密码
```

### 4. 启动服务

```bash
# 使用 uv 运行
uv run python app.py
```

访问 http://localhost:5000 即可使用。

## 环境变量说明

| 变量名        | 必填 | 默认值  | 说明             |
| ------------- | ---- | ------- | ---------------- |
| QFNU_USERNAME | 是   | -       | 教务系统账号     |
| QFNU_PASSWORD | 是   | -       | 教务系统密码     |
| FLASK_HOST    | 否   | 0.0.0.0 | 服务监听地址     |
| FLASK_PORT    | 否   | 5000    | 服务端口         |
| FLASK_DEBUG   | 否   | false   | 是否开启调试模式 |

## API 接口

| 路径           | 方法 | 说明                       |
| -------------- | ---- | -------------------------- |
| `/`            | GET  | 根据设备自动跳转到对应页面 |
| `/desktop`     | GET  | PC 端页面 (Element Plus)   |
| `/mobile`      | GET  | 移动端页面 (Vant)          |
| `/api/query`   | GET  | 实时查询空教室             |
| `/api/info`    | GET  | 获取服务状态信息           |
| `/api/refresh` | GET  | 重新初始化服务             |
| `/api/health`  | GET  | 健康检查                   |

### `/api/query` 参数说明

| 参数          | 类型   | 必填 | 默认值 | 说明                          |
| ------------- | ------ | ---- | ------ | ----------------------------- |
| building      | string | 否   | ""     | 教学楼关键词，如 "格物楼 B10" |
| start_section | string | 否   | "01"   | 开始节次（01/03/05/07/09）    |
| end_section   | string | 否   | "02"   | 结束节次（02/04/06/08/11）    |
| day_offset    | int    | 否   | 0      | 日期偏移（0=今天，1=明天...） |

## 项目结构

```
qfnu-empty-classrooms/
├── app.py              # Flask 应用主文件
├── services.py         # 服务层（登录、查询等核心功能）
├── templates/
│   ├── desktop.html    # PC 端页面 (Element Plus)
│   └── mobile.html     # 移动端页面 (Vant)
├── pyproject.toml      # uv 依赖配置
├── .env.example        # 环境变量示例
└── README.md
```

## 技术栈

- **后端**: Flask + Python 3.11+
- **PC 端**: Vue 3 + Element Plus
- **移动端**: Vue 3 + Vant 4
- **依赖管理**: uv
- **验证码识别**: ddddocr
