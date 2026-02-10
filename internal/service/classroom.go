package service

import (
	"fmt"
	"net/http"
	"net/url"
	"sort"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/W1ndys/easy-qfnu-empty-classrooms/internal/model"
	"github.com/W1ndys/easy-qfnu-empty-classrooms/pkg/cas"
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

// GetFullDayStatus 获取指定教学楼一整天的教室状态
func (s *ClassroomService) GetFullDayStatus(req model.FullDayQueryRequest) (*model.FullDayStatusResponse, error) {
	cal := GetCalendarService()
	if cal == nil {
		return nil, fmt.Errorf("日历服务未初始化")
	}

	// 1. 获取日期和周次信息
	calInfo, dateStr := cal.GetDateInfo(req.DateOffset)

	// 2. 一次查询全天所有节次（jc 和 jc2 置空）
	nodeList, classrooms, err := s.queryFullDay(req.BuildingName, calInfo)
	if err != nil {
		return nil, fmt.Errorf("查询全天状态失败：%w", err)
	}

	weekInt, _ := strconv.Atoi(calInfo.Zc)
	dayInt, _ := strconv.Atoi(calInfo.Xq)

	return &model.FullDayStatusResponse{
		Date:        dateStr,
		Week:        weekInt,
		DayOfWeek:   dayInt,
		CurrentTerm: calInfo.Xnxqh,
		Building:    req.BuildingName,
		NodeList:    nodeList,
		Classrooms:  classrooms,
	}, nil
}

// queryFullDay 查询全天教室状态
// 关键：jc 和 jc2 置空，同时不设置 jszt 参数，获取全天所有状态
func (s *ClassroomService) queryFullDay(building string, calInfo model.CalendarInfo) ([]model.NodeInfo, []model.ClassroomFullStatus, error) {
	apiURL := "http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query2"

	params := url.Values{}
	params.Set("typewhere", "jszq")
	params.Set("xnxqh", calInfo.Xnxqh)
	params.Set("jsmc_mh", building)
	params.Set("bjfh", "=")
	// 关键：不设置 jszt 参数，查询所有状态（不只是空闲）
	params.Set("zc", calInfo.Zc)
	params.Set("zc2", calInfo.Zc)
	params.Set("xq", calInfo.Xq)
	params.Set("xq2", calInfo.Xq)
	// 关键：jc 和 jc2 置空，查询全天所有节次
	// 不设置 jc 和 jc2 参数

	httpReq, err := http.NewRequest("POST", apiURL, strings.NewReader(params.Encode()))
	if err != nil {
		return nil, nil, err
	}
	httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	httpReq.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := s.client.Do(httpReq)
	if err != nil {
		return nil, nil, err
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, nil, err
	}

	return parseFullDayStatusFromHTML(doc)
}

// parseFullDayStatusFromHTML 从HTML中解析全天教室状态
// 返回数据结构：按教室分组的节次状态列表（教室-节次-状态）
func parseFullDayStatusFromHTML(doc *goquery.Document) ([]model.NodeInfo, []model.ClassroomFullStatus, error) {
	// 解析表格结构：
	// thead 中包含节次信息（第1节、第2节...）
	// tbody 中每行代表一个教室，每列代表该教室在对应节次的状态

	var nodeList []model.NodeInfo
	classroomMap := make(map[string]*model.ClassroomFullStatus) // 临时map，key为教室名

	// 先解析表头获取节次信息
	// 修正：表头在 <thead id="thead1"> 中，第二行包含节次信息，且使用的是 td 标签而不是 th
	nodeColMap := make(map[int]int)

	// 查找 <thead id="thead1"> 下的所有 tr
	// 第一个 tr 是 "星期"，"星期一"...
	// 第二个 tr 包含具体节次 "01\n02", "03\n04"...
	doc.Find("table#dataList thead#thead1 tr").Each(func(rowIdx int, tr *goquery.Selection) {
		// 我们只关心第二行（索引为 1），它包含具体的节次信息
		// 注意：如果页面结构变化，这里可能需要调整
		// 也可以通过判断内容来识别
		if rowIdx != 1 {
			return
		}

		tr.Find("td").Each(func(colIdx int, td *goquery.Selection) {
			// 第一列通常是空的或者占位符，跳过
			if colIdx == 0 {
				return
			}

			// 获取 tdvalue 属性，如 "0102"
			val, exists := td.Attr("tdvalue")
			nodeName := ""
			if exists {
				nodeName = val
			} else {
				// 如果没有 tdvalue，尝试获取文本并处理换行
				text := strings.TrimSpace(td.Text())
				nodeName = strings.ReplaceAll(text, "\n", "")
			}

			nodeIdx := len(nodeList)
			// 注意：tbody 中的列索引需要与这里的列索引对应
			// 在 tbody 中，第一列是 checkbox/教室名，之后是各节次状态
			// 在 thead 第二行中，第一列也是空/占位，之后是各节次
			// 所以 colIdx 直接对应即可
			nodeColMap[colIdx] = nodeIdx

			nodeList = append(nodeList, model.NodeInfo{
				NodeIndex: nodeIdx + 1,
				NodeName:  nodeName,
			})
		})
	})

	// 解析 tbody 中的教室状态
	doc.Find("table#dataList tbody tr").Each(func(rowIdx int, tr *goquery.Selection) {
		// 获取教室名称（第一列）
		firstTd := tr.Find("td").First()
		text := strings.TrimSpace(firstTd.Text())

		roomName := ""
		idx := strings.Index(text, "(")
		if idx > 0 {
			roomName = strings.TrimSpace(text[:idx])
		}
		if roomName == "" {
			return
		}

		// 初始化该教室的状态列表
		if _, exists := classroomMap[roomName]; !exists {
			classroomMap[roomName] = &model.ClassroomFullStatus{
				RoomName: roomName,
				Status:   make([]model.RoomStatus, len(nodeList)),
			}
		}

		// 遍历每个节次列
		tr.Find("td").Each(func(colIdx int, td *goquery.Selection) {
			if colIdx == 0 {
				return // 跳过第一列（教室名）
			}

			nodeIdx, ok := nodeColMap[colIdx]
			if !ok {
				return // 非节次列
			}

			statusCode := strings.TrimSpace(td.Text())
			if statusCode == "" {
				statusCode = "空闲" // 空单元格表示空闲
			}

			statusID := mapStatusCodeToID(statusCode)

			classroomMap[roomName].Status[nodeIdx] = model.RoomStatus{
				NodeIndex:  nodeIdx + 1, // 节次从1开始
				StatusID:   statusID,
				StatusCode: statusCode,
			}
		})
	})

	// 将 map 转换为切片
	var classrooms []model.ClassroomFullStatus
	for _, cs := range classroomMap {
		classrooms = append(classrooms, *cs)
	}

	// 按教室名称排序
	sort.Slice(classrooms, func(i, j int) bool {
		return classrooms[i].RoomName < classrooms[j].RoomName
	})

	return nodeList, classrooms, nil
}

// mapStatusCodeToID 将状态码映射到ID
func mapStatusCodeToID(code string) int {
	switch code {
	case "◆":
		return 1
	case "Ｊ":
		return 2
	case "Ｘ":
		return 3
	case "Κ":
		return 4
	case "空闲":
		return 5
	case "Ｇ":
		return 6
	case "Ｌ":
		return 7
	case "完全空闲":
		return 8
	case "M":
		return 9
	default:
		return 5 // 默认空闲
	}
}
