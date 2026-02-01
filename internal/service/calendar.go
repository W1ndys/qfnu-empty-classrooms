package service

import (
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/W1ndys/qfnu-cas-go/internal/model"
	"github.com/W1ndys/qfnu-cas-go/pkg/cas"
	"github.com/W1ndys/qfnu-cas-go/pkg/logger"
)

type CalendarService struct {
	client         *cas.Client
	currentYearStr string    // 学年学期 e.g. "2025-2026-1"
	baseTime       time.Time // 获取周次的时间点
	baseWeek       int       // 获取到的当前周次
	hasPermission  bool      // 是否有权限访问
	mu             sync.RWMutex
}

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

// Refresh 从教务系统刷新当前周次信息
func (s *CalendarService) Refresh() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 尝试解析学期 (通常可以通过另一个接口获取，或者从其他页面获取)
	// 这里为了简化，我们调用 jsjy_query 接口获取学年学期
	// http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query
	termUrl := "http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query"
	termReq, _ := http.NewRequest("GET", termUrl, nil)
	termResp, err := s.client.Do(termReq)
	if err == nil {
		defer termResp.Body.Close()

		// 读取响应体内容以检查是否有权限
		bodyBytes, _ := io.ReadAll(termResp.Body)
		bodyString := string(bodyBytes)

		// 检查是否包含 "非法访问"
		if strings.Contains(bodyString, "非法访问") {
			s.hasPermission = false
			logger.Warn("警告：该账号无权限访问空教室查询接口 (jsjy_query)，请检查账号权限或登录状态。")
		} else {
			s.hasPermission = true
		}

		termDoc, _ := goquery.NewDocumentFromReader(strings.NewReader(bodyString))
		// 查找包含学期的文本，例如 <td>学期：2025-2026-1 ...
		// 简单粗暴正则匹配 d{4}-d{4}-\d
		termText := termDoc.Text()
		reTerm := regexp.MustCompile(`\d{4}-\d{4}-\d`)
		termMatch := reTerm.FindString(termText)
		if termMatch != "" {
			s.currentYearStr = termMatch
		}
	} else {
		// 如果请求失败，也认为是无权限的一种表现，或者是网络问题
		// 默认设置为有权限，让用户去重试；或者根据错误类型判断
		// 这里暂不修改 hasPermission，让后续逻辑处理
		logger.Warn("警告：无法查询学期信息：%v", err)
	}

	// 1. 获取教学周信息
	// 接口：http://zhjw.qfnu.edu.cn/jsxsd/framework/jsMain_new.jsp?t1=1
	// 响应示例：$("#li_showWeek").html("<span class=\"main_text main_color\">第18周</span>/20周");
	url := "http://zhjw.qfnu.edu.cn/jsxsd/framework/jsMain_new.jsp?t1=1"
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}

	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("fetch calendar failed: %w", err)
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return err
	}

	htmlContent, _ := doc.Html()

	// 解析周次
	// 正则匹配：第(\d+)周
	reWeek := regexp.MustCompile(`第(\d+)周`)
	matches := reWeek.FindStringSubmatch(htmlContent)
	if len(matches) < 2 {
		// 尝试匹配 "当前日期不在教学周历内"
		// 增加对 "非法访问" 的检查，如果是非法访问，则不认为是解析失败，而是权限不足或Session过期
		if strings.Contains(htmlContent, "非法访问") {
			s.baseWeek = 0
			// 只有在还没有被 jsjy_query 标记为无权限时才打印，避免重复
			if s.hasPermission {
				logger.Warn("警告：访问首页周次接口检测到'非法访问'，可能无权限或 Session 过期。")
				s.hasPermission = false
			}
		} else if strings.Contains(htmlContent, "不在教学周历内") {
			// 这种情况下，可能需要默认一个值或报错，这里暂定为0
			s.baseWeek = 0
			logger.Warn("警告：当前日期不在教学周历内。")
		} else {
			// 解析失败，但我们可以尝试容错，特别是当 hasPermission 为 false 时
			// 如果已经确认无权限，那么解析失败是正常的，不要报错阻断服务
			if !s.hasPermission {
				logger.Warn("注意：因无权限访问，无法解析周次信息，服务将以受限模式运行。")
				s.baseWeek = 0
			} else {
				// 真正无法解析的错误
				return fmt.Errorf("无法从响应中解析周次信息，内容长度：%d", len(htmlContent))
			}
		}
	} else {
		week, _ := strconv.Atoi(matches[1])
		s.baseWeek = week
	}

	if s.currentYearStr == "" {
		// 根据当前时间推算一个默认值，或者报错
		// 假设当前是 2025-2026-1
		s.currentYearStr = "2025-2026-1"
	}

	s.baseTime = time.Now()
	logger.Info("日历已初始化：学期=%s，周次=%d，基准时间=%s", s.currentYearStr, s.baseWeek, s.baseTime.Format("2006-01-02"))
	return nil
}

// IsInTeachingCalendar 检查当前是否在教学周历内
func (s *CalendarService) IsInTeachingCalendar() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.baseWeek > 0
}

// GetBaseWeek 获取当前基准周次
func (s *CalendarService) GetBaseWeek() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.baseWeek
}

// GetCurrentYearStr 获取当前学年学期字符串
func (s *CalendarService) GetCurrentYearStr() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.currentYearStr
}

// GetDateInfo 根据偏移量计算目标日期的信息
func (s *CalendarService) GetDateInfo(offset int) (info model.CalendarInfo, dateStr string) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	targetDate := time.Now().AddDate(0, 0, offset)
	dateStr = targetDate.Format("2006-01-02")

	// 计算周次差
	// 简单算法：计算两个日期相差的天数，除以7
	// 注意：这里假设 Refresh 是最近调用的。为了更准确，应该用 baseTime
	// 实际上，baseTime 所在的周就是 baseWeek
	// 我们需要计算 baseTime 所在周的周一，和 targetDate 所在周的周一，相差几周

	// 跨年处理比较麻烦，简化逻辑：
	// 直接计算天数差 / 7
	// daysDiff := int(targetDate.Sub(s.baseTime).Hours() / 24)
	// weeksDiff := daysDiff / 7

	// 修正：如果 baseTime 是周日(0)，target 是下周一(1)，虽然差1天，但是差1周
	// Go 的 Weekday: Sunday=0, Monday=1
	// 强智教务系统通常 Monday=1, Sunday=7
	baseWeekday := int(s.baseTime.Weekday())
	if baseWeekday == 0 {
		baseWeekday = 7
	}

	targetWeekday := int(targetDate.Weekday())
	if targetWeekday == 0 {
		targetWeekday = 7
	}

	// 计算当前周的周一日期
	// ... 比较繁琐，这里采用简单近似：
	// 如果 offset 是小范围（0-7），基本周次 = baseWeek + (offset + baseWeekday - 1) / 7
	// 这里暂且认为 offset 不会太大

	// 更严谨的计算周次偏移：
	// 1. 算出 BaseTime 距离本周一过去了几天 (baseWeekday - 1)
	// 2. 算出 TargetTime 距离 BaseTime 的绝对天数 (offset)
	// 3. 总偏移天数 = (baseWeekday - 1) + offset
	// 4. 周增量 = 总偏移天数 / 7

	weekIncrement := (baseWeekday - 1 + offset) / 7
	currentWeek := s.baseWeek + weekIncrement

	info = model.CalendarInfo{
		Xnxqh: s.currentYearStr,
		Zc:    strconv.Itoa(currentWeek),
		Xq:    strconv.Itoa(targetWeekday),
	}

	return
}

// HasPermission 返回是否有权限访问
func (s *CalendarService) HasPermission() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.hasPermission
}
