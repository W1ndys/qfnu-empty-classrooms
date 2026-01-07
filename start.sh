#!/bin/bash
#
# 曲阜师范大学空教室查询系统 - Linux 启动脚本
# 用法: ./start.sh [--debug] [--host HOST] [--port PORT]
#

set -e

# 输出颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEBUG_MODE=false
HOST="0.0.0.0"
PORT="5000"
THREADS=4

# 国内镜像源配置
UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
PIP_TRUSTED_HOST="mirrors.aliyun.com"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug|-d)
            DEBUG_MODE=true
            shift
            ;;
        --host|-h)
            HOST="$2"
            shift 2
            ;;
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --threads|-t)
            THREADS="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -d, --debug         调试模式运行 (Flask 开发服务器)"
            echo "  -h, --host HOST     绑定地址 (默认: 0.0.0.0)"
            echo "  -p, --port PORT     绑定端口 (默认: 5000)"
            echo "  -t, --threads N     线程数 (默认: 4)"
            echo "      --help          显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     曲阜师范大学空教室查询系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python 版本
echo -e "${YELLOW}[1/4] 检查 Python 版本...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}错误: 未安装 Python${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}  Python 版本: $PYTHON_VERSION${NC}"

# 检查虚拟环境
echo -e "${YELLOW}[2/4] 检查虚拟环境...${NC}"
if [ -d ".venv" ]; then
    echo -e "${GREEN}  已找到虚拟环境${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}  正在创建虚拟环境...${NC}"
    $PYTHON_CMD -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}  虚拟环境创建完成${NC}"
fi

# 安装/更新依赖
echo -e "${YELLOW}[3/4] 检查依赖...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}  使用 uv 包管理器 (国内镜像源)${NC}"
    UV_INDEX_URL="$UV_INDEX_URL" uv sync --quiet
else
    echo -e "${YELLOW}  使用 pip 包管理器 (国内镜像源)${NC}"
    pip install -q -e . -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST"
fi
echo -e "${GREEN}  依赖安装完成${NC}"

# 检查 .env 文件
echo -e "${YELLOW}[4/4] 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}  未找到 .env，从 .env.example 复制${NC}"
        cp .env.example .env
        echo -e "${RED}  请编辑 .env 文件填写您的凭据${NC}"
        exit 1
    else
        echo -e "${RED}  错误: 未找到 .env 文件${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}  配置加载完成${NC}"
echo ""

# 启动服务
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${YELLOW}正在以调试模式启动...${NC}"
    echo -e "${GREEN}服务地址: http://$HOST:$PORT${NC}"
    echo ""
    export FLASK_DEBUG=1
    # 优先使用 uv run
    if command -v uv &> /dev/null; then
        uv run python app.py
    else
        .venv/bin/python app.py
    fi
else
    echo -e "${YELLOW}正在以生产模式启动...${NC}"
    echo -e "${GREEN}服务地址: http://$HOST:$PORT${NC}"
    echo -e "${GREEN}线程数: $THREADS${NC}"
    echo ""

    # 确保 gunicorn 安装在虚拟环境中
    if [ ! -f ".venv/bin/gunicorn" ]; then
        echo -e "${YELLOW}正在安装 gunicorn (国内镜像源)...${NC}"
        if command -v uv &> /dev/null; then
            uv pip install gunicorn --quiet
        else
            .venv/bin/pip install -q gunicorn -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST"
        fi
    fi

    # 使用虚拟环境中的 gunicorn (单进程多线程模式)
    if command -v uv &> /dev/null; then
        exec uv run gunicorn \
            --bind "$HOST:$PORT" \
            --workers 1 \
            --threads "$THREADS" \
            --worker-class gthread \
            --access-logfile - \
            --error-logfile - \
            --capture-output \
            "app:app"
    else
        exec .venv/bin/gunicorn \
            --bind "$HOST:$PORT" \
            --workers 1 \
            --threads "$THREADS" \
            --worker-class gthread \
            --access-logfile - \
            --error-logfile - \
            --capture-output \
            "app:app"
    fi
fi
