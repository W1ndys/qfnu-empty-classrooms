package model

// QueryRequest 前端查询请求参数
type QueryRequest struct {
	BuildingName string `json:"building"`     // 教学楼名称 (如 "老文史楼")
	StartNode    string `json:"start_node"`   // 起始节次 (如 "01")
	EndNode      string `json:"end_node"`     // 终止节次 (如 "02")
	DateOffset   int    `json:"date_offset"`  // 日期偏移 (0=今天, 1=明天...)
}

// ClassroomResponse 返回给前端的响应
type ClassroomResponse struct {
	Date       string   `json:"date"`        // 查询日期 (YYYY-MM-DD)
	Week       int      `json:"week"`        // 教学周
	DayOfWeek  int      `json:"day_of_week"` // 星期几
	Classrooms []string `json:"classrooms"`  // 空教室列表
}

// CalendarInfo 内部使用的日历信息
type CalendarInfo struct {
	Xnxqh string // 学年学期 (2025-2026-1)
	Zc    string // 周次 (字符串格式，用于请求)
	Xq    string // 星期 (1-7)
}
