package logger

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"sync"
)

// ANSI Color Codes
const (
	ColorReset  = "\033[0m"
	ColorRed    = "\033[31m"
	ColorGreen  = "\033[32m"
	ColorYellow = "\033[33m"
	ColorBlue   = "\033[34m"
	ColorPurple = "\033[35m"
	ColorCyan   = "\033[36m"
	ColorGray   = "\033[37m"
)

type GeekHandler struct {
	w  io.Writer
	mu sync.Mutex
}

func NewGeekHandler(w io.Writer) *GeekHandler {
	return &GeekHandler{w: w}
}

func (h *GeekHandler) Enabled(ctx context.Context, level slog.Level) bool {
	return true
}

func (h *GeekHandler) Handle(ctx context.Context, r slog.Record) error {
	h.mu.Lock()
	defer h.mu.Unlock()

	var prefix, color string

	switch r.Level {
	case slog.LevelDebug:
		prefix = "[DEBUG]"
		color = ColorGray
	case slog.LevelInfo:
		prefix = "[INFO ]"
		color = ColorCyan
	case slog.LevelWarn:
		prefix = "[WARN ]"
		color = ColorYellow
	case slog.LevelError:
		prefix = "[ERROR]"
		color = ColorRed
	case slog.Level(12): // Custom Fatal Level
		prefix = "[FATAL]"
		color = ColorPurple
	default:
		prefix = "[?????]"
		color = ColorReset
	}

	// Format timestamp
	timeStr := r.Time.Format("2006-01-02 15:04:05.000")

	// Main log message
	// Format: [COLOR]TIME [LEVEL] >> Message[RESET]
	msg := fmt.Sprintf("%s%s %s >> %s%s", color, timeStr, prefix, r.Message, ColorReset)

	// Handle attributes (if any)
	// We append them as key=value pairs after the message, in gray
	if r.NumAttrs() > 0 {
		msg += fmt.Sprintf(" %s{", ColorGray)
		r.Attrs(func(a slog.Attr) bool {
			msg += fmt.Sprintf(" %s=%v", a.Key, a.Value.Any())
			return true
		})
		msg += fmt.Sprintf(" }%s", ColorReset)
	}

	_, err := fmt.Fprintln(h.w, msg)
	return err
}

func (h *GeekHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	// For simplicity in this geek implementation, we return same handler
	// In a full implementation, we'd copy handler and add pre-formatted attrs
	return h
}

func (h *GeekHandler) WithGroup(name string) slog.Handler {
	return h
}
