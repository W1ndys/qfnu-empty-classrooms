package web

import "embed"

//go:embed index.html css
var StaticFS embed.FS
