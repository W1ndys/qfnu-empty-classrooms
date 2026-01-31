package v1

import (
	"net/http"

	"github.com/W1ndys/qfnu-cas-go/internal/model"
	"github.com/W1ndys/qfnu-cas-go/internal/service"
	"github.com/gin-gonic/gin"
)

type Handler struct {
	classroomService *service.ClassroomService
}

func NewHandler(cs *service.ClassroomService) *Handler {
	return &Handler{classroomService: cs}
}

func (h *Handler) QueryClassrooms(c *gin.Context) {
	var req model.QueryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "参数格式错误"})
		return
	}

	// 简单的校验
	if req.BuildingName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请输入教学楼名称"})
		return
	}
	if req.StartNode == "" || req.EndNode == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "请选择起始和终止节次"})
		return
	}

	resp, err := h.classroomService.GetEmptyClassrooms(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, resp)
}
