# 曲阜师范大学教务系统登录接口文档

本文档提取自 QFNUCourseGrabber 项目，用于在其他项目中复用登录接口。

## 登录流程概述

曲阜师范大学教务系统采用 CAS 统一身份认证，登录流程如下：

1. 访问登录页面，获取 `salt`（密码加密盐）和 `execution`（CSRF token）
2. 使用 AES/CBC/PKCS7 加密密码
3. 提交登录表单，获取带 ticket 的重定向 URL
4. 访问 ticket URL 完成 SSO 认证
5. 访问 sso.jsp 完成认证
6. 访问教务系统主页确认登录成功

## 关键 URL

```
统一认证登录页: http://ids.qfnu.edu.cn/authserver/login?service=http://zhjw.qfnu.edu.cn/sso.jsp
教务系统 SSO:   http://zhjw.qfnu.edu.cn/sso.jsp
教务系统主页:   http://zhjw.qfnu.edu.cn/jsxsd/framework/xsMain.jsp
```

## 密码加密算法

教务系统使用 AES/CBC/PKCS7 加密密码，加密步骤：

1. 生成 64 位随机前缀
2. 生成 16 位随机 IV
3. 将前缀和密码拼接作为待加密数据
4. 使用 PKCS7 填充
5. 使用 AES-CBC 模式加密
6. Base64 编码输出

### Go 语言实现

```go
package auth

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"math/big"
)

const (
	aesChars    = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
	aesCharsLen = len(aesChars)
)

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

// pkcs7Pad 对数据进行 PKCS7 填充
func pkcs7Pad(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	padText := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(data, padText...)
}

// encryptPassword 使用 AES/CBC/PKCS7 加密密码
// password: 明文密码
// salt: 从登录页面获取的加密盐（#pwdEncryptSalt 元素的 value）
func encryptPassword(password, salt string) (string, error) {
	// 1. 生成64位随机前缀和16位随机IV
	prefix, err := randomString(64)
	if err != nil {
		return "", err
	}
	iv, err := randomString(16)
	if err != nil {
		return "", err
	}

	// 2. 组合数据
	dataToEncrypt := []byte(prefix + password)
	key := []byte(salt)
	ivBytes := []byte(iv)

	// 3. 创建 AES 加密器
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}

	// 4. PKCS7 填充
	paddedData := pkcs7Pad(dataToEncrypt, aes.BlockSize)

	// 5. CBC 模式加密
	mode := cipher.NewCBCEncrypter(block, ivBytes)
	encryptedData := make([]byte, len(paddedData))
	mode.CryptBlocks(encryptedData, paddedData)

	// 6. Base64 编码
	return base64.StdEncoding.EncodeToString(encryptedData), nil
}
```

## 登录流程实现

### 1. 获取 salt 和 execution

从登录页面 HTML 中解析以下元素：
- `#pwdEncryptSalt` 的 `value` 属性 → salt
- `#execution` 的 `value` 属性 → execution

```go
import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"

	"github.com/PuerkitoBio/goquery"
)

func getSaltAndExecution(ctx context.Context, client *http.Client, loginPageURL string) (salt, execution string, err error) {
	req, err := http.NewRequestWithContext(ctx, "GET", loginPageURL, nil)
	if err != nil {
		return "", "", fmt.Errorf("创建请求失败: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", "", fmt.Errorf("访问登录页失败: %w", err)
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return "", "", fmt.Errorf("解析登录页HTML失败: %w", err)
	}

	salt, okSalt := doc.Find("#pwdEncryptSalt").Attr("value")
	execution, okExec := doc.Find("#execution").Attr("value")

	if !okSalt || !okExec {
		return "", "", errors.New("未能在页面上找到 salt 或 execution")
	}

	return salt, execution, nil
}
```

### 2. 提交登录表单

登录表单字段：

| 字段名 | 值 |
|--------|----|
| username | 学号 |
| password | 加密后的密码 |
| _eventId | submit |
| cllt | userNameLogin |
| dllt | generalLogin |
| lt | (空) |
| execution | 从页面获取的 execution |

```go
import (
	"io"
	"net/http"
	"net/url"
	"strings"
)

func submitLoginForm(ctx context.Context, client *http.Client, username, password string) (*url.URL, error) {
	const serviceURL = "http://zhjw.qfnu.edu.cn/sso.jsp"
	loginPageURL := fmt.Sprintf("http://ids.qfnu.edu.cn/authserver/login?service=%s", url.QueryEscape(serviceURL))

	// 1. 获取 salt 和 execution
	salt, execution, err := getSaltAndExecution(ctx, client, loginPageURL)
	if err != nil {
		return nil, err
	}

	// 2. 加密密码
	encPassword, err := encryptPassword(password, salt)
	if err != nil {
		return nil, fmt.Errorf("密码加密失败: %w", err)
	}

	// 3. 构造登录表单
	formData := url.Values{
		"username":  {username},
		"password":  {encPassword},
		"_eventId":  {"submit"},
		"cllt":      {"userNameLogin"},
		"dllt":      {"generalLogin"},
		"lt":        {""},
		"execution": {execution},
	}

	// 4. 创建不自动重定向的客户端
	noRedirectClient := &http.Client{
		Jar:     client.Jar,
		Timeout: 30 * time.Second,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	// 5. 提交表单
	req, err := http.NewRequestWithContext(ctx, "POST", loginPageURL, strings.NewReader(formData.Encode()))
	if err != nil {
		return nil, fmt.Errorf("创建登录请求失败: %w", err)
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := noRedirectClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("提交登录表单失败: %w", err)
	}
	defer resp.Body.Close()

	// 6. 获取重定向链接（带 ticket）
	ticketURL, err := resp.Location()
	if err != nil {
		bodyBytes, _ := io.ReadAll(resp.Body)
		responseBody := string(bodyBytes)

		// 检测错误类型
		if strings.Contains(responseBody, "您提供的用户名或者密码有误") {
			return nil, errors.New("账号密码错误")
		}
		if strings.Contains(responseBody, "验证码") || strings.Contains(responseBody, "captcha") {
			return nil, errors.New("需要验证码，请先手动登录一次")
		}

		return nil, errors.New("登录失败，未获取到重定向链接")
	}

	return ticketURL, nil
}
```

### 3. 完整登录流程

```go
import (
	"context"
	"errors"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"
)

// Login 执行完整的登录流程
// 返回已登录的 http.Client，可用于后续请求
func Login(ctx context.Context, username, password string) (*http.Client, error) {
	// 创建带 cookie jar 的客户端
	jar, _ := cookiejar.New(nil)
	client := &http.Client{
		Jar:     jar,
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	const serviceURL = "http://zhjw.qfnu.edu.cn/sso.jsp"

	// 1. 提交登录表单并获取 ticket
	ticketURL, err := submitLoginForm(ctx, client, username, password)
	if err != nil {
		return nil, err
	}

	// 2. 访问 ticket 链接完成 SSO
	req, err := http.NewRequestWithContext(ctx, "GET", ticketURL.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("创建 ticket 请求失败: %w", err)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("访问 ticket 链接失败: %w", err)
	}
	resp.Body.Close()

	// 3. 访问 sso.jsp
	req, err = http.NewRequestWithContext(ctx, "GET", serviceURL, nil)
	if err != nil {
		return nil, fmt.Errorf("创建 sso 请求失败: %w", err)
	}
	resp, err = client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("访问 sso.jsp 失败: %w", err)
	}
	resp.Body.Close()

	// 4. 访问教务系统主页确认登录
	const mainPageURL = "http://zhjw.qfnu.edu.cn/jsxsd/framework/xsMain.jsp"
	req, err = http.NewRequestWithContext(ctx, "GET", mainPageURL, nil)
	if err != nil {
		return nil, fmt.Errorf("创建主页请求失败: %w", err)
	}
	resp, err = client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("访问教务系统主页失败: %w", err)
	}
	defer resp.Body.Close()

	bodyBytes, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(bodyBytes), "教学一体化服务平台") {
		return nil, errors.New("登录教务系统失败，未在主页找到成功标识")
	}

	return client, nil
}
```

## 使用示例

```go
package main

import (
	"context"
	"fmt"
	"log"
)

func main() {
	ctx := context.Background()

	// 登录
	client, err := Login(ctx, "你的学号", "你的密码")
	if err != nil {
		log.Fatalf("登录失败: %v", err)
	}

	fmt.Println("登录成功!")

	// 使用 client 进行后续请求...
	// 例如获取成绩、课表等
}
```

## 依赖库

```go
require github.com/PuerkitoBio/goquery v1.8.1
```

## 注意事项

1. **验证码处理**: 如果多次登录失败或触发风控，可能需要输入验证码。此时需要先在浏览器中手动登录一次。

2. **Cookie 管理**: 登录成功后的 cookie 保存在 `http.Client` 的 `Jar` 中，后续请求会自动携带。

3. **会话保持**: 教务系统会话有时效性，长时间不活动可能需要重新登录。

4. **并发连接**: 如果需要高并发请求，建议配置 `Transport` 的 `MaxIdleConnsPerHost`。

5. **错误处理**: 登录失败可能返回以下错误：
   - 账号密码错误
   - 需要验证码
   - 网络超时
   - 教务系统维护

## 原始代码位置

- 加密函数: `internal/auth/encrypt.go`
- 登录客户端: `internal/auth/client.go`
