package main

import (
	"context"
	"flag"
	"log"
	"os"
	"time"

	"github.com/W1ndys/qfnu-cas-go/pkg/cas"
	"github.com/joho/godotenv"
)

func main() {
	// 尝试加载 .env 文件（如果存在）
	_ = godotenv.Load()

	// 优先从环境变量读取
	username := os.Getenv("QFNU_USERNAME")
	password := os.Getenv("QFNU_PASSWORD")

	// CLI 参数作为备选
	flag.StringVar(&username, "u", username, "学号/工号（默认读取 QFNU_USERNAME 环境变量）")
	flag.StringVar(&password, "p", password, "密码（默认读取 QFNU_PASSWORD 环境变量）")
	timeout := flag.Duration("t", 30*time.Second, "请求超时时间")
	flag.Parse()

	if username == "" || password == "" {
		log.Println("错误: 未配置账号或密码")
		log.Println("\n配置方式（优先级从高到低）:")
		log.Println("1. 环境变量: export QFNU_USERNAME=学号 QFNU_PASSWORD=密码")
		log.Println("2. .env 文件: 创建 .env 文件并填写 QFNU_USERNAME 和 QFNU_PASSWORD")
		log.Println("3. CLI 参数: go run . -u 学号 -p 密码")
		os.Exit(1)
	}

	ctx := context.Background()

	// 初始化客户端
	client, err := cas.NewClient(cas.WithTimeout(*timeout))
	if err != nil {
		log.Fatalf("初始化客户端失败: %v", err)
	}

	log.Printf("正在尝试登录用户: %s ...\n", username)

	// 执行登录
	startTime := time.Now()
	if err := client.Login(ctx, username, password); err != nil {
		log.Fatalf("登录失败: %v", err)
	}
	duration := time.Since(startTime)

	log.Printf("登录成功! 耗时: %v\n", duration)
	log.Println("Session Cookie 已建立，可进行后续操作。")
	log.Println("提示: 可使用 client.GetClient() 进行后续教务系统 API 调用")
}