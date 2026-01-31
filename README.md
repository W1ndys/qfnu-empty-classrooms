# qfnu-cas-go

曲阜师范大学 (QFNU) 统一身份认证 (CAS) 登录的 Go 语言实现。

## 如何使用

本项目提供了灵活的配置方式，支持命令行参数、环境变量和 `.env` 配置文件。

### 1. 准备工作

首先，确保你已经安装了 Go 语言环境。

克隆仓库并下载依赖：

```bash
git clone https://github.com/W1ndys/qfnu-cas-go.git
cd qfnu-cas-go
go mod download
```

### 2. 运行方式

你可以直接运行源码来测试登录功能。

#### 方式一：命令行参数（推荐）

直接通过 `-u` 指定账号，`-p` 指定密码：

```bash
go run . -u <你的学号> -p <你的密码>
```

#### 方式二：.env 配置文件

在项目根目录下创建一个名为 `.env` 的文件，填入以下内容：

```env
QFNU_USERNAME=你的学号
QFNU_PASSWORD=你的密码
```

然后直接运行，程序会自动读取配置：

```bash
go run .
```

#### 方式三：环境变量

你也可以设置系统环境变量 `QFNU_USERNAME` 和 `QFNU_PASSWORD`，然后直接运行 `go run .`。

## 如何编译

如果你希望生成可执行文件以便分发或部署，可以使用以下命令进行编译。

### 编译主程序

在项目根目录下执行：

```bash
# 默认编译，生成的文件名取决于目录名（如 qfnu-cas-go）
go build -v .

# 或者指定输出文件名
# Windows
go build -o qfnu-login.exe .
# Linux/macOS
go build -o qfnu-login .
```

编译完成后，即可直接运行生成的可执行文件：

```bash
./qfnu-login -u <学号> -p <密码>
```

### 编译 Demo

如果你想编译 `cmd/demo` 下的示例程序：

```bash
go build -v ./cmd/demo
```
