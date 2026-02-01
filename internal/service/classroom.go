package service

import (
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/W1ndys/qfnu-cas-go/internal/model"
	"github.com/W1ndys/qfnu-cas-go/pkg/cas"
)

type ClassroomService struct {
	client *cas.Client
}

func NewClassroomService(client *cas.Client) *ClassroomService {
	return &ClassroomService{client: client}
}

func (s *ClassroomService) GetEmptyClassrooms(req model.QueryRequest) (*model.ClassroomResponse, error) {
	cal := GetCalendarService()
	if cal == nil {
		return nil, fmt.Errorf("日历服务未初始化")
	}

	// 1. 获取日期和周次信息
	calInfo, dateStr := cal.GetDateInfo(req.DateOffset)

	// 2. 构建请求参数
	// URL: http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query2
	apiURL := "http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query2"

	// 参数构造
	params := url.Values{}
	params.Set("typewhere", "jszq")
	params.Set("xnxqh", calInfo.Xnxqh)
	params.Set("jsmc_mh", req.BuildingName) // 会自动 URL 编码
	params.Set("bjfh", "=")
	params.Set("jszt", "8") // 完全空闲
	params.Set("zc", calInfo.Zc)
	params.Set("zc2", calInfo.Zc) // 似乎是一样的
	params.Set("xq", calInfo.Xq)
	params.Set("xq2", calInfo.Xq)
	params.Set("jc", req.StartNode)
	params.Set("jc2", req.EndNode)

	// 发送 POST 请求
	httpReq, err := http.NewRequest("POST", apiURL, strings.NewReader(params.Encode()))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := s.client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("查询空教室失败：%w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("查询空教室状态错误：%d", resp.StatusCode)
	}

	// 3. 解析 HTML
	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("解析 HTML 失败：%w", err)
	}

	var classrooms []string

	// 解析 table#dataList
	// 每一行 tr, 里面有 checkbox 的 td
	// 结构: <tr ... jsbh="1306" ...> <td ...> <input type="checkbox" ...> 教室名称(...) </td> ... </tr>
	doc.Find("table#dataList tr").Each(func(i int, s *goquery.Selection) {
		// 忽略表头
		if s.Find("th").Length() > 0 {
			return
		}

		// 提取包含 checkbox 的 td
		td := s.Find("td").First()
		text := strings.TrimSpace(td.Text())

		// 文本类似于 " 老文史楼101(75/30)"
		// 我们需要提取 "老文史楼101"
		if text != "" {
			// 去掉 (及其后面的内容
			idx := strings.Index(text, "(")
			if idx > 0 {
				name := strings.TrimSpace(text[:idx])
				if name != "" {
					classrooms = append(classrooms, name)
				}
			}
		}
	})

	weekInt, _ := strconv.Atoi(calInfo.Zc)
	dayInt, _ := strconv.Atoi(calInfo.Xq)

	return &model.ClassroomResponse{
		Date:       dateStr,
		Week:       weekInt,
		DayOfWeek:  dayInt,
		Classrooms: classrooms,
	}, nil
}
