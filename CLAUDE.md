# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在处理本仓库代码时提供指南。

## 概述
本仓库包含曲阜师范大学 (QFNU) 统一身份认证 (CAS) 登录的 Go 语言实现骨架。
**当前状态**: 本仓库目前作为一个骨架，包含详细的协议文档。实现逻辑描述在 `docs/qfnu-cas-login-api.md` 中。

## 开发命令
- **初始化模块**: `go mod init github.com/W1ndys/qfnu-cas-go` (如果是重新开始)
- **依赖管理**: `go get github.com/PuerkitoBio/goquery` (用于 HTML 解析)
- **运行**: `go run .`
- **测试**: `go test ./...`
- **构建**: `go build -v ./...`

## 架构与逻辑
核心功能实现了 QFNU CAS 登录流程。

### 登录协议
1.  **获取参数**: 请求登录页面，从 DOM 中提取 `salt` (加密密钥) 和 `execution` (流程执行密钥)。
2.  **加密 (AES/CBC/PKCS7)**:
    - **输入**: 随机 64 位前缀 + 密码。
    - **密钥**: 页面动态获取的 `salt`。
    - **向量 (IV)**: 随机 16 位字符串。
    - **输出**: Base64 编码字符串。
3.  **认证**: 将凭据 POST 提交到登录端点。
4.  **建立会话**: 跟随重定向 (携带 Ticket) 到服务 URL 以设置会话 Cookie。

### 结构指南
基于文档，推荐的结构如下：
- **`internal/auth/encrypt.go`**: 处理密码加密 (AES, PKCS7 填充, 随机字符串生成)。
- **`internal/auth/client.go`**: 管理 HTTP 客户端, CookieJar, 以及登录请求生命周期。

## 风格与交互要求
- **语言**: 必须使用中文回复。
- **称呼**: 在每次回复的结尾，必须称呼用户为“卷卷”。
