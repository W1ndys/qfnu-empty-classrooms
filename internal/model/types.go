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

// FullDayQueryRequest 全天状态查询请求
type FullDayQueryRequest struct {
	BuildingName string `json:"building"`    // 教学楼名称 (如 "老文史楼")
	DateOffset   int    `json:"date_offset"` // 日期偏移 (0=今天, 1=明天...)
}

// ClassroomStatus 单个教室在单个节次的状态
type ClassroomStatus struct {
	RoomName   string `json:"room_name"`   // 教室名称 (如 "老文史楼101")
	StatusID   int    `json:"status_id"`   // 状态ID (1-9)
	StatusCode string `json:"status_code"` // 状态码 (如 "◆", "空闲")
}

// NodeInfo 节次信息
type NodeInfo struct {
	NodeIndex int    `json:"node_index"` // 节次索引 (1-11)
	NodeName  string `json:"node_name"`  // 节次名称 (如 "第1节")
}

// RoomStatus 单个教室在单个节次的状态
type RoomStatus struct {
	NodeIndex  int    `json:"node_index"`  // 节次索引
	StatusID   int    `json:"status_id"`   // 状态ID (1-9)
	StatusCode string `json:"status_code"` // 状态码 (如 "◆", "空闲")
}

// ClassroomFullStatus 单个教室的全天状态
type ClassroomFullStatus struct {
	RoomName string       `json:"room_name"` // 教室名称 (如 "老文史楼101")
	Status   []RoomStatus `json:"status"`    // 各节次状态列表
}

// FullDayStatusResponse 全天状态查询响应
type FullDayStatusResponse struct {
	Date       string                `json:"date"`        // 查询日期 (YYYY-MM-DD)
	Week       int                   `json:"week"`        // 教学周
	DayOfWeek  int                   `json:"day_of_week"` // 星期几 (1-7)
	CurrentTerm string               `json:"current_term"` // 当前学期 (2025-2026-1)
	Building   string                `json:"building"`    // 教学楼名称
	NodeList   []NodeInfo            `json:"node_list"`   // 节次列表（用于前端表头）
	Classrooms []ClassroomFullStatus `json:"classrooms"`  // 各教室全天状态列表
}
