# 从零开始编写 QFNU 空教室查询系统 - 完整代码教程

> 本文档面向零基础开发者，逐行解释项目中的每一行代码，帮助你理解为什么要这样写。

---

## 目录

1. [项目概述](#1-项目概述)
2. [项目架构与目录结构](#2-项目架构与目录结构)
3. [Go 语言基础概念速览](#3-go-语言基础概念速览)
4. [第一步：项目初始化](#4-第一步项目初始化)
5. [第二步：密码加密模块 (pkg/auth/crypto.go)](#5-第二步密码加密模块)
6. [第三步：HTTP 客户端封装 (pkg/cas/client.go)](#6-第三步http-客户端封装)
7. [第四步：CAS 登录流程 (pkg/cas/login.go)](#7-第四步cas-登录流程)
8. [第五步：日志系统 (pkg/logger/)](#8-第五步日志系统)
9. [第六步：数据模型定义 (internal/model/types.go)](#9-第六步数据模型定义)
10. [第七步：日历服务 (internal/service/calendar.go)](#10-第七步日历服务)
11. [第八步：空教室服务 (internal/service/classroom.go)](#11-第八步空教室服务)
12. [第九步：API 处理器 (internal/api/v1/handler.go)](#12-第九步api-处理器)
13. [第十步：静态资源嵌入 (web/assets.go)](#13-第十步静态资源嵌入)
14. [第十一步：程序入口 (main.go)](#14-第十一步程序入口)
15. [关键设计模式解析](#15-关键设计模式解析)
16. [总结](#16-总结)

---

## 1. 项目概述

### 这个项目是做什么的？

这是一个**曲阜师范大学空闲教室查询系统**，它的核心功能是：

1. **自动登录**：模拟浏览器登录学校的统一身份认证系统 (CAS)
2. **查询空教室**：登录后访问教务系统，查询指定时间段的空闲教室
3. **Web 界面**：提供一个简洁的网页让用户操作

### 涉及的技术栈

| 技术 | 用途 |
|------|------|
| Go 语言 | 后端开发 |
| Gin 框架 | Web 服务器 |
| goquery | HTML 解析（类似 jQuery） |
| AES 加密 | 密码加密 |
| embed | 将静态文件打包进二进制 |

---

## 2. 项目架构与目录结构

```
easy-qfnu-empty-classrooms/
├── main.go                          # 程序入口点
├── go.mod                           # Go 模块定义文件
├── go.sum                           # 依赖校验文件
│
├── pkg/                             # 可复用的公共包
│   ├── auth/
│   │   └── crypto.go               # AES 密码加密
│   ├── cas/
│   │   ├── client.go               # HTTP 客户端封装
│   │   └── login.go                # CAS 登录逻辑
│   └── logger/
│       ├── logger.go               # 日志初始化
│       ├── handler.go              # 自定义日志处理器
│       └── rotator.go              # 日志文件轮转
│
├── internal/                        # 项目内部包（不对外暴露）
│   ├── api/
│   │   └── v1/
│   │       └── handler.go          # HTTP API 处理器
│   ├── model/
│   │   └── types.go                # 数据结构定义
│   └── service/
│       ├── calendar.go             # 校历/周次服务
│       └── classroom.go            # 空教室查询服务
│
├── web/                             # 前端资源
│   ├── assets.go                   # Go embed 嵌入声明
│   ├── index.html                  # 前端页面
│   └── css/                        # 样式文件
│
└── docs/                            # 文档目录
```

### 为什么要这样组织目录？

这是 Go 社区推荐的**标准项目布局**：

- **`pkg/`**：存放**可被其他项目复用**的代码。比如 `auth` 包可以被任何需要 CAS 登录的项目使用。
- **`internal/`**：存放**本项目私有**的代码。Go 编译器会阻止其他项目导入 `internal` 包。
- **`web/`**：存放前端资源。
- **`main.go`**：程序入口，放在根目录便于直接 `go run .`。

---

## 3. Go 语言基础概念速览

在深入代码之前，先了解几个 Go 语言的核心概念：

### 3.1 包 (Package)

```go
package main  // 声明这个文件属于 main 包
```

- 每个 `.go` 文件的第一行必须声明它属于哪个包
- `main` 是特殊的包名，表示这是可执行程序的入口
- 其他包名通常与文件夹名相同

### 3.2 导入 (Import)

```go
import (
    "fmt"                                    // 标准库
    "github.com/gin-gonic/gin"               // 第三方库
    "github.com/W1ndys/xxx/internal/service" // 本项目的包
)
```

### 3.3 函数定义

```go
func 函数名(参数名 参数类型) 返回类型 {
    // 函数体
}

// 多个返回值
func 函数名() (返回值1类型, 返回值2类型) {
    return 值1, 值2
}
```

### 3.4 结构体 (Struct)

```go
// 定义结构体（类似其他语言的 class）
type Person struct {
    Name string  // 字段名大写 = 公开（其他包可访问）
    age  int     // 字段名小写 = 私有（仅本包可访问）
}

// 给结构体添加方法
func (p *Person) SayHello() {
    fmt.Println("Hello, I'm", p.Name)
}
```

### 3.5 错误处理

Go 语言没有 try-catch，而是通过返回值处理错误：

```go
result, err := someFunction()
if err != nil {
    // 处理错误
    return err
}
// 使用 result
```

---

## 4. 第一步：项目初始化

### 4.1 创建 go.mod 文件

```bash
go mod init github.com/W1ndys/easy-qfnu-empty-classrooms
```

这会创建 `go.mod` 文件：

```go
module github.com/W1ndys/easy-qfnu-empty-classrooms

go 1.25.6
```

**逐行解释：**

| 行 | 代码 | 解释 |
|---|------|------|
| 1 | `module github.com/...` | 声明模块路径，这是其他项目引用你的代码时使用的路径 |
| 3 | `go 1.25.6` | 指定最低 Go 版本要求 |

### 4.2 安装依赖

```bash
go get github.com/gin-gonic/gin       # Web 框架
go get github.com/PuerkitoBio/goquery # HTML 解析
go get github.com/joho/godotenv       # 读取 .env 文件
```

---

## 5. 第二步：密码加密模块

> 文件：`pkg/auth/crypto.go`

### 为什么需要加密？

学校的 CAS 系统不接受明文密码，而是要求：
1. 生成 64 位随机字符串作为前缀
2. 将"前缀 + 密码"用 AES/CBC 模式加密
3. 用 Base64 编码后发送

### 完整代码逐行解析

```go
package auth
```
**解释**：声明这个文件属于 `auth` 包。包名通常与文件夹名一致。

---

```go
import (
    "bytes"
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "encoding/base64"
    "fmt"
    "math/big"
)
```

**导入的包说明**：

| 包名 | 用途 |
|------|------|
| `bytes` | 字节操作，用于 PKCS7 填充 |
| `crypto/aes` | AES 加密算法 |
| `crypto/cipher` | 加密模式（CBC） |
| `crypto/rand` | 密码学安全的随机数生成器 |
| `encoding/base64` | Base64 编解码 |
| `fmt` | 格式化输出和错误信息 |
| `math/big` | 大整数运算（用于随机数范围） |

---

```go
const (
    aesChars    = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
    aesCharsLen = len(aesChars)
)
```

**解释**：
- `const` 声明常量，编译时确定，不可修改
- `aesChars`：随机字符串的字符集（注意：故意去掉了容易混淆的字符如 0/O, 1/l/I）
- `aesCharsLen`：字符集长度，用于后续取模运算

**为什么用 const 而不是 var？**
- 常量在编译时就确定了值，运行时不会变
- 编译器可以进行优化
- 避免意外修改

---

```go
// EncryptPassword 使用 QFNU CAS 特定的 AES/CBC/PKCS7 算法加密密码
// password: 明文密码
// salt: 从登录页面获取的动态盐
func EncryptPassword(password, salt string) (string, error) {
```

**函数签名解析**：

| 部分 | 说明 |
|------|------|
| `func` | 关键字，声明函数 |
| `EncryptPassword` | 函数名，大写开头表示**公开**（可被其他包调用） |
| `password, salt string` | 两个参数都是 string 类型，可以简写 |
| `(string, error)` | 返回两个值：加密后的字符串 和 可能的错误 |

**为什么返回 error？**

Go 语言的惯例是：可能失败的函数返回 `(结果, error)`。调用者必须检查 error 是否为 nil。

---

```go
    // 1. 生成64位随机前缀和16位随机IV
    prefix, err := randomString(64)
    if err != nil {
        return "", fmt.Errorf("生成随机前缀失败: %w", err)
    }
    iv, err := randomString(16)
    if err != nil {
        return "", fmt.Errorf("生成随机IV失败: %w", err)
    }
```

**解析**：
- `:=` 是**短变量声明**，自动推断类型并赋值
- `fmt.Errorf("...: %w", err)` 创建一个包装原始错误的新错误
  - `%w` 是 Go 1.13+ 的特殊格式，保留原始错误链
- `return "", ...` 返回空字符串表示失败

**为什么需要随机前缀和 IV？**
- **前缀**：即使两次输入相同密码，加密结果也不同，防止重放攻击
- **IV (Initialization Vector)**：CBC 模式要求，确保相同明文产生不同密文

---

```go
    // 2. 组合数据
    dataToEncrypt := []byte(prefix + password)
    key := []byte(salt)
    ivBytes := []byte(iv)
```

**解析**：
- `[]byte(...)` 将字符串转换为字节切片
- AES 加密操作的是字节，不是字符串

---

```go
    // 3. 创建 AES 加密器
    block, err := aes.NewCipher(key)
    if err != nil {
        return "", fmt.Errorf("创建 AES Cipher 失败: %w", err)
    }
```

**解析**：
- `aes.NewCipher(key)` 创建一个 AES 加密块
- `key` 必须是 16/24/32 字节（对应 AES-128/192/256）
- 学校的 salt 是 16 字节，所以用的是 AES-128

---

```go
    // 4. PKCS7 填充
    paddedData := pkcs7Pad(dataToEncrypt, aes.BlockSize)
```

**为什么需要填充？**
- AES 是**块加密**，一次只能加密固定长度（16 字节）的数据
- 如果数据长度不是 16 的倍数，就需要填充
- PKCS7 是一种标准的填充方式

---

```go
    // 5. CBC 模式加密
    mode := cipher.NewCBCEncrypter(block, ivBytes)
    encryptedData := make([]byte, len(paddedData))
    mode.CryptBlocks(encryptedData, paddedData)
```

**解析**：
- `cipher.NewCBCEncrypter` 创建 CBC 模式的加密器
- `make([]byte, len)` 创建指定长度的字节切片
- `CryptBlocks` 执行加密，结果写入 `encryptedData`

---

```go
    // 6. Base64 编码
    return base64.StdEncoding.EncodeToString(encryptedData), nil
}
```

**解析**：
- 加密后的数据是二进制，需要转成文本才能通过 HTTP 发送
- Base64 将二进制转为 ASCII 字符串
- `nil` 表示没有错误

---

### randomString 函数

```go
// randomString 生成指定长度的随机字符串
func randomString(length int) (string, error) {
    b := make([]byte, length)
    for i := range b {
        n, err := rand.Int(rand.Reader, big.NewInt(int64(aesCharsLen)))
        if err != nil {
            return "", err
        }
        b[i] = aesChars[n.Int64()]
    }
    return string(b), nil
}
```

**逐行解析**：

| 行 | 代码 | 解释 |
|---|------|------|
| 1 | `func randomString(length int)` | 小写开头 = 私有函数，仅本包可用 |
| 2 | `b := make([]byte, length)` | 创建长度为 `length` 的字节切片 |
| 3 | `for i := range b` | 遍历切片的索引 |
| 4 | `rand.Int(rand.Reader, ...)` | 生成 [0, aesCharsLen) 范围内的密码学安全随机数 |
| 6 | `b[i] = aesChars[n.Int64()]` | 用随机数作为索引，从字符集中取字符 |
| 8 | `return string(b), nil` | 将字节切片转为字符串返回 |

**为什么用 `crypto/rand` 而不是 `math/rand`？**
- `crypto/rand` 使用操作系统的随机源，适合密码学用途
- `math/rand` 是伪随机，可预测，不安全

---

### pkcs7Pad 函数

```go
// pkcs7Pad 对数据进行 PKCS7 填充
func pkcs7Pad(data []byte, blockSize int) []byte {
    padding := blockSize - len(data)%blockSize
    padText := bytes.Repeat([]byte{byte(padding)}, padding)
    return append(data, padText...)
}
```

**PKCS7 填充规则**：
- 计算需要填充多少字节：`blockSize - len(data) % blockSize`
- 填充的内容就是填充长度本身
- 例如：需要填充 5 字节，就填充 `[5, 5, 5, 5, 5]`

**代码解析**：

| 行 | 代码 | 解释 |
|---|------|------|
| 1 | `padding := blockSize - len(data)%blockSize` | 计算需要填充的字节数 |
| 2 | `bytes.Repeat([]byte{byte(padding)}, padding)` | 创建填充内容 |
| 3 | `append(data, padText...)` | 将填充追加到数据末尾 |

---

## 6. 第三步：HTTP 客户端封装

> 文件：`pkg/cas/client.go`

### 为什么要封装？

直接使用 `http.Client` 太底层，我们需要：
1. 自动管理 Cookie（登录后保持会话）
2. 统一配置超时时间
3. 提供简洁的 API

### 完整代码逐行解析

```go
package cas

import (
    "net/http"
    "net/http/cookiejar"
    "time"
)
```

**解释**：
- `net/http`：Go 标准库的 HTTP 包
- `net/http/cookiejar`：自动管理 Cookie 的容器
- `time`：时间相关操作

---

```go
const (
    DefaultTimeout = 30 * time.Second
)
```

**解释**：
- 定义默认超时时间为 30 秒
- `30 * time.Second` 是 Go 中表示时间的惯用方式

---

```go
// Client 封装了 CAS 登录和后续请求的 HTTP 客户端
// 采用 Facade 模式隐藏复杂的登录细节
type Client struct {
    httpClient *http.Client
    options    *clientOptions
}
```

**结构体解析**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `httpClient` | `*http.Client` | 底层 HTTP 客户端（带 Cookie 管理） |
| `options` | `*clientOptions` | 配置选项 |

**为什么用指针 `*` ？**
- 指针允许多个地方共享同一个对象
- 避免复制大对象的开销
- 允许修改原始对象

---

```go
type clientOptions struct {
    timeout time.Duration
}

// ClientOption 定义配置选项函数类型 (Functional Options Pattern)
type ClientOption func(*clientOptions)

// WithTimeout 设置请求超时时间
func WithTimeout(d time.Duration) ClientOption {
    return func(o *clientOptions) {
        o.timeout = d
    }
}
```

**这是 Functional Options 设计模式**：

使用方式：
```go
client := NewClient(WithTimeout(60 * time.Second))
```

**为什么用这种模式？**
1. **可选参数**：Go 不支持默认参数值，这种模式是优雅的替代方案
2. **可扩展**：添加新选项不破坏现有代码
3. **自文档化**：`WithTimeout` 比 `NewClient(60)` 更清晰

---

```go
// NewClient 创建一个新的 CAS 客户端
func NewClient(opts ...ClientOption) (*Client, error) {
```

**参数 `opts ...ClientOption` 解析**：
- `...` 表示**可变参数**，可以传入 0 到多个 `ClientOption`
- 内部作为切片处理

---

```go
    // 默认配置
    options := &clientOptions{
        timeout: DefaultTimeout,
    }

    for _, opt := range opts {
        opt(options)
    }
```

**解析**：
1. 先设置默认值
2. 遍历所有传入的选项函数，依次调用它们修改 options

---

```go
    // 初始化 CookieJar
    jar, err := cookiejar.New(nil)
    if err != nil {
        return nil, err
    }
```

**CookieJar 是什么？**
- 自动存储服务器返回的 Cookie
- 自动在后续请求中携带 Cookie
- 这是保持登录状态的关键

---

```go
    // 配置 HTTP Transport
    transport := &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 100,
        IdleConnTimeout:     90 * time.Second,
    }
```

**Transport 配置说明**：

| 字段 | 值 | 说明 |
|------|---|------|
| `MaxIdleConns` | 100 | 最大空闲连接数（连接池大小） |
| `MaxIdleConnsPerHost` | 100 | 每个主机的最大空闲连接数 |
| `IdleConnTimeout` | 90s | 空闲连接超时时间 |

**为什么要配置连接池？**
- HTTP 建立连接有开销（TCP 三次握手）
- 连接池复用已建立的连接，提高性能

---

```go
    httpClient := &http.Client{
        Jar:       jar,
        Timeout:   options.timeout,
        Transport: transport,
    }

    return &Client{
        httpClient: httpClient,
        options:    options,
    }, nil
}
```

**创建 http.Client 并返回封装的 Client**

---

```go
// GetClient 返回底层的 http.Client，用于已登录后的业务请求
func (c *Client) GetClient() *http.Client {
    return c.httpClient
}
```

**方法定义语法**：
```go
func (接收者变量 *类型) 方法名() 返回类型 {
    // 方法体
}
```

- `(c *Client)` 是**方法接收者**，表示这个方法属于 `Client` 类型
- 类似其他语言的 `this` 或 `self`

---

```go
// Do 发送 HTTP 请求 (代理方法)
func (c *Client) Do(req *http.Request) (*http.Response, error) {
    return c.httpClient.Do(req)
}
```

**代理模式**：简单地转发调用，保持接口统一。

---

## 7. 第四步：CAS 登录流程

> 文件：`pkg/cas/login.go`

### 登录流程概述

```
1. 检查是否需要验证码
2. 获取登录页面 → 提取 salt 和 execution 参数
3. 加密密码
4. 提交登录表单 → 获取 ticket URL
5. 完成 SSO 跳转 → 建立会话
```

### 完整代码逐行解析

```go
package cas

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "log"
    "net/http"
    "net/url"
    "strings"
    "time"

    "github.com/PuerkitoBio/goquery"
    "github.com/W1ndys/easy-qfnu-empty-classrooms/pkg/auth"
)
```

**关键导入**：
- `context`：用于超时控制和取消操作
- `github.com/PuerkitoBio/goquery`：jQuery 风格的 HTML 解析库

---

```go
const (
    // URL 常量
    URLService = "http://zhjw.qfnu.edu.cn/sso.jsp"
    URLLogin   = "http://ids.qfnu.edu.cn/authserver/login"
    URLMainPage    = "http://zhjw.qfnu.edu.cn/jsxsd/framework/jsMain.jsp"
    URLSuccessMark = "教学一体化服务平台"
)
```

**常量说明**：

| 常量 | 用途 |
|------|------|
| `URLService` | 教务系统地址，登录成功后跳转的目标 |
| `URLLogin` | CAS 统一认证登录页面 |
| `URLMainPage` | 教务系统主页，用于验证登录成功 |
| `URLSuccessMark` | 登录成功的标识文本 |

---

### Login 方法

```go
// Login 执行完整的 CAS 登录流程
func (c *Client) Login(ctx context.Context, username, password string) error {
```

**参数解析**：
- `ctx context.Context`：上下文，用于超时控制
- `username, password string`：凭据

**为什么需要 context？**
- 可以设置超时：`ctx, cancel := context.WithTimeout(...)`
- 可以取消操作：`cancel()`
- 是 Go 处理取消和超时的标准方式

---

```go
    // 0. 检查是否需要验证码
    if err := c.checkNeedCaptcha(ctx, username); err != nil {
        return err
    }
```

**为什么先检查验证码？**
- 如果账号因多次失败需要验证码，程序无法自动处理
- 提前检测可以给出明确的错误提示

---

```go
    loginPageURL := fmt.Sprintf("%s?service=%s", URLLogin, url.QueryEscape(URLService))
```

**解析**：
- 构造登录 URL，携带 `service` 参数
- `url.QueryEscape` 对 URL 进行编码（处理特殊字符）
- 最终 URL 类似：`http://ids.../login?service=http%3A%2F%2Fzhjw...`

---

```go
    // 1. 获取 salt 和 execution
    salt, execution, err := c.fetchLoginParams(ctx, loginPageURL)
    if err != nil {
        return err
    }
```

**这两个参数是什么？**
- `salt`：加密密码的密钥，每次访问登录页都不同
- `execution`：CSRF 令牌，防止跨站请求伪造

---

```go
    // 2. 加密密码
    encPassword, err := auth.EncryptPassword(password, salt)
    if err != nil {
        return fmt.Errorf("密码加密失败: %w", err)
    }
```

**调用我们之前写的加密模块**

---

```go
    // 3. 提交登录表单并获取 ticket 重定向链接
    ticketURL, err := c.submitForm(ctx, loginPageURL, username, encPassword, execution)
    if err != nil {
        return err
    }

    // 4. 完成 SSO 认证流程
    if err := c.completeSSO(ctx, ticketURL); err != nil {
        return err
    }

    return nil
}
```

**SSO 流程**：
1. 登录成功后，CAS 返回 302 重定向，URL 中携带 `ticket`
2. 访问这个 URL，教务系统验证 ticket 并设置会话 Cookie

---

### checkNeedCaptcha 方法

```go
func (c *Client) checkNeedCaptcha(ctx context.Context, username string) error {
    timestamp := time.Now().UnixMilli()
    checkURL := fmt.Sprintf("https://ids.qfnu.edu.cn/authserver/checkNeedCaptcha.htl?username=%s&_=%d", username, timestamp)
```

**为什么加时间戳？**
- 防止浏览器/代理缓存
- 确保每次请求都到达服务器

---

```go
    req, err := http.NewRequestWithContext(ctx, "GET", checkURL, nil)
```

**`http.NewRequestWithContext` vs `http.NewRequest`**：
- 带 Context 版本支持超时和取消
- 推荐始终使用带 Context 的版本

---

```go
    var result struct {
        IsNeed bool `json:"isNeed"`
    }

    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return fmt.Errorf("解析验证码检查响应失败: %w", err)
    }
```

**匿名结构体**：
- 当结构体只用一次时，可以直接定义
- `` `json:"isNeed"` `` 是**结构体标签**，告诉 JSON 解析器字段对应的 JSON key

---

### fetchLoginParams 方法

```go
func (c *Client) fetchLoginParams(ctx context.Context, url string) (salt, execution string, err error) {
```

**命名返回值**：
- `(salt, execution string, err error)` 预先声明了返回值变量
- 可以直接 `return` 而不带参数

---

```go
    doc, err := goquery.NewDocumentFromReader(resp.Body)
    if err != nil {
        return "", "", fmt.Errorf("解析 HTML 失败: %w", err)
    }

    salt, _ = doc.Find("#pwdEncryptSalt").Attr("value")
    execution, _ = doc.Find("#execution").Attr("value")
```

**goquery 用法**：
- `doc.Find("#pwdEncryptSalt")`：类似 jQuery 的选择器，找 id="pwdEncryptSalt" 的元素
- `.Attr("value")`：获取 value 属性

---

### submitForm 方法

```go
func (c *Client) submitForm(ctx context.Context, loginURL, username, encPassword, execution string) (*url.URL, error) {
    formData := url.Values{
        "username":  {username},
        "password":  {encPassword},
        "_eventId":  {"submit"},
        "cllt":      {"userNameLogin"},
        "dllt":      {"generalLogin"},
        "lt":        {""},
        "execution": {execution},
    }
```

**url.Values**：
- 用于构造 form 表单数据
- 键值对形式，值是字符串切片（支持同一个键多个值）

---

```go
    // 创建一个不自动重定向的 Client，用于捕获 302 跳转中的 Ticket
    noRedirectClient := &http.Client{
        Jar:     c.httpClient.Jar,
        Timeout: c.httpClient.Timeout,
        CheckRedirect: func(req *http.Request, via []*http.Request) error {
            return http.ErrUseLastResponse
        },
    }
```

**为什么禁用自动重定向？**
- 默认情况下，Go 的 http.Client 会自动跟随 302 重定向
- 我们需要**捕获**重定向的 URL（里面有 ticket）
- `http.ErrUseLastResponse` 告诉客户端"不要重定向，直接返回这个响应"

---

```go
    req, err := http.NewRequestWithContext(ctx, "POST", loginURL, strings.NewReader(formData.Encode()))
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
```

**HTTP 请求构造**：
- `strings.NewReader(formData.Encode())`：将 form 数据编码为请求体
- `Content-Type`：告诉服务器这是表单数据
- `User-Agent`：模拟浏览器，有些服务器会检查

---

```go
    // 检查是否重定向
    if resp.StatusCode == http.StatusFound || resp.StatusCode == http.StatusMovedPermanently {
        ticketURL, err := resp.Location()
        if err != nil {
            return nil, fmt.Errorf("获取重定向地址失败: %w", err)
        }
        return ticketURL, nil
    }
```

**HTTP 状态码**：
- `302 Found`（StatusFound）：临时重定向
- `301 Moved Permanently`：永久重定向
- `resp.Location()`：获取 `Location` 头，即重定向目标 URL

---

## 8. 第五步：日志系统

> 文件：`pkg/logger/`

### 为什么自己实现日志？

1. **控制台输出**：彩色、易读
2. **文件输出**：JSON 格式、便于分析
3. **自动轮转**：文件过大时自动创建新文件

### logger.go - 日志初始化

```go
package logger

import (
    "context"
    "fmt"
    "log/slog"
    "os"
)

var DefaultLogger *slog.Logger
```

**`slog` 是 Go 1.21+ 引入的结构化日志库**

---

```go
func init() {
```

**`init()` 函数**：
- 特殊函数，包被导入时自动执行
- 用于初始化工作
- 每个文件可以有多个 init()

---

```go
    // 1. 控制台处理器（极客风格，带颜色）
    consoleHandler := NewGeekHandler(os.Stdout)

    // 2. 文件处理器（JSON 结构化）带自动轮转
    rotator := NewLogRotator("logs", 10)
    fileHandler := slog.NewJSONHandler(rotator, &slog.HandlerOptions{
        Level: slog.LevelDebug,
    })

    // 3. 组合处理器
    finalHandler := NewFanoutHandler(consoleHandler, fileHandler)

    DefaultLogger = slog.New(finalHandler)
    slog.SetDefault(DefaultLogger)
}
```

**处理器架构**：
```
日志消息 → FanoutHandler → GeekHandler → 控制台（彩色）
                        ↘ JSONHandler → LogRotator → 文件（JSON）
```

---

```go
func Info(format string, v ...interface{}) {
    if len(v) == 0 {
        DefaultLogger.Info(format)
    } else {
        DefaultLogger.Info(fmt.Sprintf(format, v...))
    }
}
```

**封装便捷函数**：
- 支持 `logger.Info("hello")` 和 `logger.Info("hello %s", name)` 两种调用方式
- 类似 `fmt.Printf` 的格式化语法

---

### handler.go - 自定义处理器

```go
// ANSI 颜色代码
const (
    ColorReset  = "\033[0m"
    ColorRed    = "\033[31m"
    ColorGreen  = "\033[32m"
    ColorYellow = "\033[33m"
    // ...
)
```

**ANSI 转义序列**：
- 控制终端文字颜色
- `\033[31m` = 红色
- `\033[0m` = 重置为默认颜色

---

```go
type GeekHandler struct {
    w  io.Writer
    mu sync.Mutex
}
```

**为什么需要 Mutex？**
- 多个 goroutine 可能同时写日志
- Mutex 确保一次只有一个 goroutine 在写，避免输出混乱

---

```go
func (h *GeekHandler) Handle(ctx context.Context, r slog.Record) error {
    h.mu.Lock()
    defer h.mu.Unlock()
```

**`defer` 关键字**：
- 延迟执行，函数返回前执行
- 常用于资源清理（关闭文件、释放锁）
- 即使函数 panic，defer 也会执行

---

### FanoutHandler - 广播处理器

```go
// FanoutHandler 将日志广播给多个处理器
type FanoutHandler struct {
    handlers []slog.Handler
}

func (h *FanoutHandler) Handle(ctx context.Context, r slog.Record) error {
    var firstErr error
    for _, handler := range h.handlers {
        if handler.Enabled(ctx, r.Level) {
            if err := handler.Handle(ctx, r); err != nil && firstErr == nil {
                firstErr = err
            }
        }
    }
    return firstErr
}
```

**扇出模式**：一条日志同时发送给多个目标。

---

### rotator.go - 日志轮转

```go
type LogRotator struct {
    mu        sync.Mutex
    dir       string
    prefix    string
    ext       string
    file      *os.File
    size      int64
    maxSize   int64 // 字节
    startTime time.Time
    seq       int
}
```

**字段说明**：

| 字段 | 用途 |
|------|------|
| `mu` | 互斥锁，保护并发写入 |
| `dir` | 日志目录 |
| `file` | 当前正在写的文件 |
| `size` | 当前文件大小 |
| `maxSize` | 单文件最大大小 |
| `seq` | 序号（同一秒内创建多个文件时区分） |

---

```go
func (r *LogRotator) Write(p []byte) (n int, err error) {
    r.mu.Lock()
    defer r.mu.Unlock()

    // 首次写入时打开文件
    if r.file == nil {
        if err := r.openNewFile(); err != nil {
            return 0, err
        }
    }

    // 检查是否需要轮转
    if r.maxSize > 0 && r.size+int64(len(p)) > r.maxSize {
        r.seq++
        if err := r.openNewFile(); err != nil {
            return 0, err
        }
    }

    n, err = r.file.Write(p)
    r.size += int64(n)
    return n, err
}
```

**实现 `io.Writer` 接口**：
- 只要实现 `Write(p []byte) (n int, err error)` 方法
- 就可以被任何接受 `io.Writer` 的地方使用

---

## 9. 第六步：数据模型定义

> 文件：`internal/model/types.go`

```go
package model

// QueryRequest 前端查询请求参数
type QueryRequest struct {
    BuildingName string `json:"building"`     // 教学楼名称 (如 "老文史楼")
    StartNode    string `json:"start_node"`   // 起始节次 (如 "01")
    EndNode      string `json:"end_node"`     // 终止节次 (如 "02")
    DateOffset   int    `json:"date_offset"`  // 日期偏移 (0=今天, 1=明天...)
}
```

**结构体标签 (Struct Tags)**：
- `` `json:"building"` `` 告诉 JSON 库：
  - 序列化时：`BuildingName` → `"building"`
  - 反序列化时：`"building"` → `BuildingName`

**为什么字段名用大写？**
- 大写 = 公开 = JSON 库可以访问
- 小写 = 私有 = JSON 库无法访问

---

```go
// ClassroomResponse 返回给前端的响应
type ClassroomResponse struct {
    Date       string   `json:"date"`        // 查询日期 (YYYY-MM-DD)
    Week       int      `json:"week"`        // 教学周
    DayOfWeek  int      `json:"day_of_week"` // 星期几
    Classrooms []string `json:"classrooms"`  // 空教室列表
}
```

---

```go
// CalendarInfo 内部使用的日历信息
type CalendarInfo struct {
    Xnxqh string // 学年学期 (2025-2026-1)
    Zc    string // 周次 (字符串格式，用于请求)
    Xq    string // 星期 (1-7)
}
```

**没有 json 标签**：因为这是内部使用，不需要序列化。

---

## 10. 第七步：日历服务

> 文件：`internal/service/calendar.go`

### 单例模式

```go
var (
    calendarInstance *CalendarService
    calendarOnce     sync.Once
)

// GetCalendarService 单例获取
func GetCalendarService() *CalendarService {
    return calendarInstance
}

// InitCalendarService 初始化日历服务
func InitCalendarService(client *cas.Client) error {
    var err error
    calendarOnce.Do(func() {
        calendarInstance = &CalendarService{
            client: client,
        }
        err = calendarInstance.Refresh()
    })
    return err
}
```

**`sync.Once`**：
- 确保某段代码只执行一次
- 即使多个 goroutine 同时调用，也只执行一次
- 常用于单例模式、一次性初始化

**为什么用单例？**
- 日历服务只需要一个实例
- 避免重复初始化
- 全局共享状态

---

### 读写锁

```go
type CalendarService struct {
    client         *cas.Client
    currentYearStr string
    baseTime       time.Time
    baseWeek       int
    hasPermission  bool
    mu             sync.RWMutex  // 读写锁
}
```

**`sync.RWMutex` vs `sync.Mutex`**：
- `Mutex`：同时只能有一个 goroutine 持有
- `RWMutex`：可以多个读者同时读，但写者独占

```go
func (s *CalendarService) GetBaseWeek() int {
    s.mu.RLock()         // 读锁
    defer s.mu.RUnlock()
    return s.baseWeek
}

func (s *CalendarService) Refresh() error {
    s.mu.Lock()          // 写锁
    defer s.mu.Unlock()
    // 修改数据...
}
```

---

### 正则表达式

```go
reTerm := regexp.MustCompile(`\d{4}-\d{4}-\d`)
termMatch := reTerm.FindString(termText)
```

**正则解析**：
- `\d{4}`：匹配 4 个数字
- `-`：匹配横线
- 整体：匹配类似 `2025-2026-1` 的格式

---

### 周次计算逻辑

```go
func (s *CalendarService) GetDateInfo(offset int) (info model.CalendarInfo, dateStr string) {
    // ...

    // 计算星期几（Go: Sunday=0, Monday=1）
    targetWeekday := int(targetDate.Weekday())
    if targetWeekday == 0 {
        targetWeekday = 7  // 教务系统用 1-7，周日是 7
    }

    // 计算周次增量
    weekIncrement := (baseWeekday - 1 + offset) / 7
    currentWeek := s.baseWeek + weekIncrement
```

**为什么需要转换星期？**
- Go 的 `time.Weekday()`：Sunday=0, Monday=1, ..., Saturday=6
- 教务系统：Monday=1, Tuesday=2, ..., Sunday=7

---

## 11. 第八步：空教室服务

> 文件：`internal/service/classroom.go`

```go
func (s *ClassroomService) GetEmptyClassrooms(req model.QueryRequest) (*model.ClassroomResponse, error) {
    cal := GetCalendarService()
    if cal == nil {
        return nil, fmt.Errorf("日历服务未初始化")
    }

    // 1. 获取日期和周次信息
    calInfo, dateStr := cal.GetDateInfo(req.DateOffset)
```

**服务间依赖**：ClassroomService 依赖 CalendarService 获取周次信息。

---

```go
    // 2. 构建请求参数
    params := url.Values{}
    params.Set("typewhere", "jszq")
    params.Set("xnxqh", calInfo.Xnxqh)
    params.Set("jsmc_mh", req.BuildingName)  // 会自动 URL 编码
    params.Set("bjfh", "=")
    params.Set("jszt", "8")  // 完全空闲
    params.Set("zc", calInfo.Zc)
    params.Set("zc2", calInfo.Zc)
    params.Set("xq", calInfo.Xq)
    params.Set("xq2", calInfo.Xq)
    params.Set("jc", req.StartNode)
    params.Set("jc2", req.EndNode)
```

**参数说明**：

| 参数 | 含义 |
|------|------|
| `jszt=8` | 教室状态=完全空闲 |
| `zc/zc2` | 周次范围 |
| `xq/xq2` | 星期范围 |
| `jc/jc2` | 节次范围 |

---

```go
    // 解析 table#dataList
    doc.Find("table#dataList tr").Each(func(i int, s *goquery.Selection) {
        // 忽略表头
        if s.Find("th").Length() > 0 {
            return
        }

        td := s.Find("td").First()
        text := strings.TrimSpace(td.Text())

        // 文本类似于 " 老文史楼101(75/30)"
        if text != "" {
            idx := strings.Index(text, "(")
            if idx > 0 {
                name := strings.TrimSpace(text[:idx])
                if name != "" {
                    classrooms = append(classrooms, name)
                }
            }
        }
    })
```

**HTML 解析流程**：
1. 找到 id="dataList" 的表格
2. 遍历每一行 `tr`
3. 跳过表头（有 `th` 的行）
4. 提取教室名称（括号前的部分）

---

## 12. 第九步：API 处理器

> 文件：`internal/api/v1/handler.go`

```go
type Handler struct {
    classroomService *service.ClassroomService
}

func NewHandler(cs *service.ClassroomService) *Handler {
    return &Handler{classroomService: cs}
}
```

**依赖注入**：
- Handler 不自己创建 ClassroomService
- 而是从外部传入
- 好处：便于测试、解耦

---

```go
func (h *Handler) QueryClassrooms(c *gin.Context) {
    var req model.QueryRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "参数格式错误"})
        return
    }
```

**Gin 框架用法**：
- `c *gin.Context`：封装了请求和响应
- `c.ShouldBindJSON(&req)`：将请求体 JSON 解析到结构体
- `c.JSON(status, data)`：返回 JSON 响应
- `gin.H`：`map[string]interface{}` 的别名，方便构造 JSON

---

```go
    // 简单的校验
    if req.BuildingName == "" {
        c.JSON(http.StatusBadRequest, gin.H{"error": "请输入教学楼名称"})
        return
    }
```

**为什么要手动校验？**
- `ShouldBindJSON` 只检查 JSON 格式是否正确
- 业务逻辑校验（如必填字段）需要手动处理

---

## 13. 第十步：静态资源嵌入

> 文件：`web/assets.go`

```go
package web

import "embed"

//go:embed index.html css
var StaticFS embed.FS
```

**Go embed 指令**：
- `//go:embed` 是编译器指令（不是注释！）
- 将指定文件/目录嵌入到二进制文件中
- `embed.FS` 实现了 `fs.FS` 接口，可以像文件系统一样使用

**好处**：
- 部署时只需要一个二进制文件
- 不需要额外管理静态资源目录

---

## 14. 第十一步：程序入口

> 文件：`main.go`

```go
package main

import (
    "context"
    "net/http"
    "os"
    "time"

    v1 "github.com/W1ndys/easy-qfnu-empty-classrooms/internal/api/v1"
    "github.com/W1ndys/easy-qfnu-empty-classrooms/internal/service"
    "github.com/W1ndys/easy-qfnu-empty-classrooms/pkg/cas"
    "github.com/W1ndys/easy-qfnu-empty-classrooms/pkg/logger"
    "github.com/W1ndys/easy-qfnu-empty-classrooms/web"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
)
```

**导入别名**：
- `v1 "...internal/api/v1"` 给包起别名
- 避免包名与变量名冲突

---

```go
func main() {
    // 加载 .env
    _ = godotenv.Load()
```

**`_ =`**：
- Go 要求使用所有声明的变量
- `_` 是空白标识符，表示"丢弃这个值"
- 这里忽略 `.env` 不存在时的错误（不是必须的）

---

```go
    // 设置 Gin 模式
    if mode := os.Getenv("GIN_MODE"); mode != "" {
        gin.SetMode(mode)
    }
```

**短变量声明 + if**：
- `if mode := ...; mode != ""` 声明变量并立即使用
- `mode` 的作用域只在这个 if 块内

---

```go
    client, err := cas.NewClient(cas.WithTimeout(30 * time.Second))
    if err != nil {
        logger.Fatal("无法创建 CAS 客户端：%v", err)
    }

    // 尝试登录以获取 Session
    if username != "" {
        logger.Info("正在尝试登录 QFNU CAS...")
        ctx, cancel := context.WithTimeout(context.Background(), 1*time.Minute)
        err := client.Login(ctx, username, password)
        cancel()  // 重要：及时释放资源
        // ...
    }
```

**Context 超时控制**：
- `context.WithTimeout` 创建有超时限制的 Context
- 1 分钟内必须完成登录，否则取消
- `cancel()` 释放 Context 关联的资源

---

```go
    // 3. 设置 Gin
    r := gin.Default()
    // 禁用 Gin 的自动重定向行为
    r.RedirectTrailingSlash = false
    r.RedirectFixedPath = false
```

**`gin.Default()`**：
- 创建带默认中间件的路由
- 包括 Logger（日志）和 Recovery（panic 恢复）

---

```go
    // 静态文件服务 (Embed)
    r.StaticFS("/static", http.FS(web.StaticFS))

    // 根路径返回 index.html
    r.GET("/", func(c *gin.Context) {
        content, err := web.StaticFS.ReadFile("index.html")
        if err != nil {
            c.String(http.StatusInternalServerError, "无法加载 index.html")
            return
        }
        c.Data(http.StatusOK, "text/html; charset=utf-8", content)
    })
```

**为什么手动读取 index.html？**
- 避免 Gin 的自动重定向问题
- 直接返回文件内容，更可控

---

```go
    // API 路由
    api := r.Group("/api/v1")
    {
        api.GET("/status", apiHandler.GetStatus)
        api.POST("/query", apiHandler.QueryClassrooms)
    }
```

**路由组**：
- `r.Group("/api/v1")` 创建前缀为 `/api/v1` 的路由组
- 组内的路由会自动添加前缀
- `{}` 是纯装饰，让代码更清晰

---

```go
    // 启动
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    logger.Info("服务器正在启动，监听地址：http://localhost:%s", port)
    if err := r.Run(":" + port); err != nil {
        logger.Fatal("%v", err)
    }
}
```

**`r.Run()`**：
- 启动 HTTP 服务器
- 这是阻塞调用，直到服务器停止才返回

---

## 15. 关键设计模式解析

### 15.1 Functional Options 模式

```go
// 定义选项函数类型
type ClientOption func(*clientOptions)

// 创建选项函数
func WithTimeout(d time.Duration) ClientOption {
    return func(o *clientOptions) {
        o.timeout = d
    }
}

// 使用
client := NewClient(WithTimeout(60 * time.Second))
```

**优点**：
- 零值可用：`NewClient()` 也能工作
- 自文档化：选项名说明用途
- 可扩展：添加新选项不破坏 API

### 15.2 单例模式

```go
var (
    instance *Service
    once     sync.Once
)

func GetInstance() *Service {
    once.Do(func() {
        instance = &Service{}
    })
    return instance
}
```

### 15.3 依赖注入

```go
// 不好的做法：硬编码依赖
func (h *Handler) Query() {
    service := NewClassroomService()  // 内部创建
    // ...
}

// 好的做法：依赖注入
func NewHandler(service *ClassroomService) *Handler {
    return &Handler{service: service}  // 外部传入
}
```

### 15.4 接口隔离

```go
// io.Writer 接口只有一个方法
type Writer interface {
    Write(p []byte) (n int, err error)
}

// LogRotator 实现了 Writer 接口
// 因此可以传给任何接受 Writer 的函数
```

---

## 16. 总结

### 开发流程回顾

1. **项目初始化**：`go mod init`
2. **底层工具**：密码加密、HTTP 客户端
3. **业务逻辑**：登录、日历、查询
4. **API 层**：HTTP 处理器
5. **入口**：main.go 组装所有组件

### 关键技能点

| 技能 | 应用场景 |
|------|----------|
| 错误处理 | 每个可能失败的操作都检查 error |
| 并发安全 | sync.Mutex/RWMutex 保护共享数据 |
| Context | 超时控制、取消操作 |
| 接口 | 实现 io.Writer 等标准接口 |
| 设计模式 | Functional Options、单例、依赖注入 |

### 推荐学习路径

1. [Go 官方教程](https://go.dev/tour/)
2. [Effective Go](https://go.dev/doc/effective_go)
3. [Go by Example](https://gobyexample.com/)
4. 阅读标准库源码（从简单的如 `strings` 开始）

---

> 文档作者：Claude Code
> 生成时间：2024
