package logger

import (
	"context"
	"fmt"
	"log/slog"
	"os"
)

var DefaultLogger *slog.Logger

func init() {
	handler := NewGeekHandler(os.Stdout)
	DefaultLogger = slog.New(handler)
	slog.SetDefault(DefaultLogger)
}

func Info(format string, v ...interface{}) {
	if len(v) == 0 {
		DefaultLogger.Info(format)
	} else {
		DefaultLogger.Info(fmt.Sprintf(format, v...))
	}
}

func Warn(format string, v ...interface{}) {
	if len(v) == 0 {
		DefaultLogger.Warn(format)
	} else {
		DefaultLogger.Warn(fmt.Sprintf(format, v...))
	}
}

func Error(format string, v ...interface{}) {
	if len(v) == 0 {
		DefaultLogger.Error(format)
	} else {
		DefaultLogger.Error(fmt.Sprintf(format, v...))
	}
}

func Fatal(format string, v ...interface{}) {
	msg := format
	if len(v) > 0 {
		msg = fmt.Sprintf(format, v...)
	}
	// Use Output to log with the correct stack depth if needed,
	// but here we just use Log with LevelError (or custom Fatal level if we added one)
	// Slog doesn't have Fatal level by default, usually we log Error then exit.
	// But to keep style consistent:
	// We can manually call Handler.Handle with a custom level or just Error
	// Let's stick to Error level for the log, but with [FATAL] prefix by hacking the level?
	// Slog levels are just ints.
	// LevelError = 8. Let's make Fatal = 12.

	// Actually, let's keep it simple and use a custom log call
	DefaultLogger.Log(context.Background(), slog.Level(12), msg)
	os.Exit(1)
}

// Support structured logging as well
func InfoS(msg string, args ...any) {
	DefaultLogger.Info(msg, args...)
}

func WarnS(msg string, args ...any) {
	DefaultLogger.Warn(msg, args...)
}

func ErrorS(msg string, args ...any) {
	DefaultLogger.Error(msg, args...)
}
