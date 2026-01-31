package cas

import (
	"net/http"
	"net/http/cookiejar"
	"time"
)

const (
	DefaultTimeout = 30 * time.Second
)

// Client 封装了 CAS 登录和后续请求的 HTTP 客户端
// 采用 Facade 模式隐藏复杂的登录细节
type Client struct {
	httpClient *http.Client
	options    *clientOptions
}

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

// NewClient 创建一个新的 CAS 客户端
func NewClient(opts ...ClientOption) (*Client, error) {
	// 默认配置
	options := &clientOptions{
		timeout: DefaultTimeout,
	}

	for _, opt := range opts {
		opt(options)
	}

	// 初始化 CookieJar
	jar, err := cookiejar.New(nil)
	if err != nil {
		return nil, err
	}

	// 配置 HTTP Transport
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 100,
		IdleConnTimeout:     90 * time.Second,
	}

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

// GetClient 返回底层的 http.Client，用于已登录后的业务请求
func (c *Client) GetClient() *http.Client {
	return c.httpClient
}

// Do 发送 HTTP 请求 (代理方法)
func (c *Client) Do(req *http.Request) (*http.Response, error) {
	return c.httpClient.Do(req)
}
