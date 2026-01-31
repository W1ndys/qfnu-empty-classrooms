package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/W1ndys/qfnu-cas-go/pkg/cas"
)

func main() {
	// 命令行参数处理
	username := flag.String("u", "", "学号/工号")
	password := flag.String("p", "", "密码")
	timeout := flag.Duration("t", 30*time.Second, "请求超时时间")
	flag.Parse()

	if *username == "" || *password == "" {
		fmt.Println("使用方法:")
		fmt.Println("  demo.exe -u <username> -p <password>")
		flag.PrintDefaults()
		os.Exit(1)
	}

	ctx := context.Background()

	// 1. 初始化客户端
	client, err := cas.NewClient(cas.WithTimeout(*timeout))
	if err != nil {
		log.Fatalf("初始化客户端失败: %v", err)
	}

	log.Printf("正在尝试登录用户: %s ...\n", *username)

	// 2. 执行登录
	startTime := time.Now()
	if err := client.Login(ctx, *username, *password); err != nil {
		log.Fatalf("登录失败: %v", err)
	}
	duration := time.Since(startTime)

	log.Printf("登录成功! 耗时: %v\n", duration)
	log.Println("Session Cookie 已建立，可进行后续操作。")

	// 3. 示例：这里可以继续使用 client.GetClient() 进行其他教务系统 API 的调用
	// httpClient := client.GetClient()
	// ...
}
