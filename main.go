package main

import (
	"context"
	"net/http"
	"os"
	"time"

	v1 "github.com/W1ndys/qfnu-cas-go/internal/api/v1"
	"github.com/W1ndys/qfnu-cas-go/internal/service"
	"github.com/W1ndys/qfnu-cas-go/pkg/cas"
	"github.com/W1ndys/qfnu-cas-go/pkg/logger"
	"github.com/W1ndys/qfnu-cas-go/web"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// 加载 .env
	_ = godotenv.Load()

	// 设置 Gin 模式
	if mode := os.Getenv("GIN_MODE"); mode != "" {
		gin.SetMode(mode)
	}

	// 1. 初始化 CAS 客户端
	// 注意：实际生产环境需要配置账号密码，用于获取 Session
	username := os.Getenv("QFNU_USER")
	password := os.Getenv("QFNU_PASS")

	// 兼容 main.go 原有逻辑，也尝试读取 QFNU_USERNAME/PASSWORD
	if username == "" {
		username = os.Getenv("QFNU_USERNAME")
	}
	if password == "" {
		password = os.Getenv("QFNU_PASSWORD")
	}

	if username == "" || password == "" {
		logger.Warn("未设置 QFNU_USER/QFNU_PASS。由于缺少会话，后端查询可能会失败。")
	}

	client, err := cas.NewClient(cas.WithTimeout(30 * time.Second))
	if err != nil {
		logger.Fatal("无法创建 CAS 客户端：%v", err)
	}

	// 尝试登录以获取 Session
	if username != "" {
		logger.Info("正在尝试登录 QFNU CAS...")
		ctx, cancel := context.WithTimeout(context.Background(), 1*time.Minute)
		err := client.Login(ctx, username, password)
		cancel()
		if err != nil {
			logger.Warn("登录失败：%v。程序将继续运行，但查询可能会失败。", err)
		} else {
			logger.Info("登录成功。")
		}
	}

	// 2. 初始化服务
	if err := service.InitCalendarService(client); err != nil {
		logger.Warn("初始化日历服务失败：%v。日历功能可能不准确。", err)
	}
	classroomService := service.NewClassroomService(client)
	apiHandler := v1.NewHandler(classroomService)

	// 3. 设置 Gin
	r := gin.Default()
	// 禁用 Gin 的自动重定向行为，防止 index.html 路径与 / 路径发生死循环
	r.RedirectTrailingSlash = false
	r.RedirectFixedPath = false

	// 静态文件服务 (Embed)
	// web.StaticFS 根目录下就是 index.html 和 css/
	r.StaticFS("/static", http.FS(web.StaticFS))

	// 根路径返回 index.html (显式读取模式)
	// 使用 ReadFile 显式加载并返回，避免 FileFromFS 可能触发的路径重定向问题
	r.GET("/", func(c *gin.Context) {
		content, err := web.StaticFS.ReadFile("index.html")
		if err != nil {
			c.String(http.StatusInternalServerError, "无法加载 index.html")
			return
		}
		c.Data(http.StatusOK, "text/html; charset=utf-8", content)
	})

	// API 路由
	api := r.Group("/api/v1")
	{
		api.GET("/status", apiHandler.GetStatus)
		api.POST("/query", apiHandler.QueryClassrooms)
	}

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
