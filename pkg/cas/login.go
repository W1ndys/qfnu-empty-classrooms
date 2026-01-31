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
	"github.com/W1ndys/qfnu-cas-go/pkg/auth"
)

const (
	// URL 常量
	URLService  = "http://zhjw.qfnu.edu.cn/sso.jsp"
	URLLogin    = "http://ids.qfnu.edu.cn/authserver/login"
	URLMainPage = "http://zhjw.qfnu.edu.cn/jsxsd/framework/xsMain.jsp"
	// URLMainPage = "http://zhjw.qfnu.edu.cn/jsxsd/framework/jsMain.jsp" // 教师端请使用这个
	URLSuccessMark = "教学一体化服务平台" // 登录成功的页面标识
)

// Login 执行完整的 CAS 登录流程
func (c *Client) Login(ctx context.Context, username, password string) error {
	// 0. 检查是否需要验证码
	if err := c.checkNeedCaptcha(ctx, username); err != nil {
		return err
	}

	loginPageURL := fmt.Sprintf("%s?service=%s", URLLogin, url.QueryEscape(URLService))

	// 1. 获取 salt 和 execution
	salt, execution, err := c.fetchLoginParams(ctx, loginPageURL)
	if err != nil {
		return err
	}

	// 2. 加密密码
	encPassword, err := auth.EncryptPassword(password, salt)
	if err != nil {
		return fmt.Errorf("密码加密失败: %w", err)
	}

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

// checkNeedCaptcha 检查账号是否需要验证码
func (c *Client) checkNeedCaptcha(ctx context.Context, username string) error {
	timestamp := time.Now().UnixMilli()
	checkURL := fmt.Sprintf("https://ids.qfnu.edu.cn/authserver/checkNeedCaptcha.htl?username=%s&_=%d", username, timestamp)

	req, err := http.NewRequestWithContext(ctx, "GET", checkURL, nil)
	if err != nil {
		return fmt.Errorf("创建验证码检查请求失败: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("检查验证码状态失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("验证码检查接口异常: %d", resp.StatusCode)
	}

	var result struct {
		IsNeed bool `json:"isNeed"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return fmt.Errorf("解析验证码检查响应失败: %w", err)
	}

	if result.IsNeed {
		return errors.New("当前账号需输入验证码，请先在浏览器手动登录一次以消除验证状态")
	}

	return nil
}

// fetchLoginParams 获取登录页面所需的动态参数
func (c *Client) fetchLoginParams(ctx context.Context, url string) (salt, execution string, err error) {
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return "", "", err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", "", fmt.Errorf("访问登录页失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", "", fmt.Errorf("访问登录页异常: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return "", "", fmt.Errorf("解析 HTML 失败: %w", err)
	}

	salt, _ = doc.Find("#pwdEncryptSalt").Attr("value")
	execution, _ = doc.Find("#execution").Attr("value")

	if salt == "" || execution == "" {
		return "", "", errors.New("无法获取 salt 或 execution，页面结构可能已变更")
	}

	return salt, execution, nil
}

// submitForm 提交表单，返回携带 ticket 的 URL
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

	// 创建一个不自动重定向的 Client，用于捕获 302 跳转中的 Ticket
	// 注意：这里复用 c.httpClient 的 CookieJar，以保持会话
	noRedirectClient := &http.Client{
		Jar:     c.httpClient.Jar,
		Timeout: c.httpClient.Timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	req, err := http.NewRequestWithContext(ctx, "POST", loginURL, strings.NewReader(formData.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := noRedirectClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("提交登录表单失败: %w", err)
	}
	defer resp.Body.Close()

	// 检查是否重定向
	if resp.StatusCode == http.StatusFound || resp.StatusCode == http.StatusMovedPermanently {
		ticketURL, err := resp.Location()
		if err != nil {
			return nil, fmt.Errorf("获取重定向地址失败: %w", err)
		}
		return ticketURL, nil
	}

	// 如果没有重定向，说明登录失败（可能在当前页面显示错误信息）
	bodyBytes, _ := io.ReadAll(resp.Body)
	bodyStr := string(bodyBytes)

	if strings.Contains(bodyStr, "您提供的用户名或者密码有误") {
		return nil, errors.New("账号或密码错误")
	}
	if strings.Contains(bodyStr, "验证码") || strings.Contains(bodyStr, "captcha") {
		return nil, errors.New("系统检测到异常，需要验证码 (需人工介入)")
	}

	return nil, fmt.Errorf("登录未成功，状态码: %d", resp.StatusCode)
}

// completeSSO 完成后续的 SSO 跳转和验证
func (c *Client) completeSSO(ctx context.Context, ticketURL *url.URL) error {
	// 1. 访问 Ticket URL
	if err := c.simpleGet(ctx, ticketURL.String()); err != nil {
		return fmt.Errorf("Ticket 验证失败: %w", err)
	}

	// 2. 访问 sso.jsp (确保 Cookie 写入)
	if err := c.simpleGet(ctx, URLService); err != nil {
		return fmt.Errorf("SSO 初始化失败: %w", err)
	}

	// 3. 访问主页验证最终结果
	req, err := http.NewRequestWithContext(ctx, "GET", URLMainPage, nil)
	if err != nil {
		return err
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("访问主页失败: %w", err)
	}
	defer resp.Body.Close()

	bodyBytes, _ := io.ReadAll(resp.Body)
	if !strings.Contains(string(bodyBytes), URLSuccessMark) {
		return errors.New("登录流程结束，但未检测到登录成功标识")
	} else {
		log.Println("检测到登录成功标识，登录流程完成。")
	}

	return nil
}

func (c *Client) simpleGet(ctx context.Context, urlStr string) error {
	req, err := http.NewRequestWithContext(ctx, "GET", urlStr, nil)
	if err != nil {
		return err
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}
