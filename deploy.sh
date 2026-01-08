#!/bin/bash
#
# 曲阜师范大学空教室查询系统 - 部署脚本
# 用于 Windows Git Bash 环境
# 用法: ./deploy.sh [--restart] [--dry-run]
#

set -e

# 输出颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 远程服务器配置
REMOTE_HOST="frp-mix.com"
REMOTE_PORT="58089"
REMOTE_USER="root"
REMOTE_PATH="/root/qfnu-empty-classrooms"

# SSH 私钥文件路径 (Git Bash 格式)
PRIVATE_KEY_PATH="/c/Users/W1ndys/.ssh/id_rsa"

# Supervisor 进程名称
SUPERVISOR_PROCESS="qfnu-empty-classrooms:qfnu-empty-classrooms_00"



# 需要上传的文件和目录
UPLOAD_FILES=(
    "app.py"
    "services.py"
    "logger.py"
    "pyproject.toml"
    "uv.lock"
    "start.sh"
    ".env.example"
)

UPLOAD_DIRS=(
    "templates"
    "static"
)

# 排除的文件模式
EXCLUDE_PATTERNS=(
    "*.pyc"
    "__pycache__"
    ".git"
    ".venv"
    "*.log"
    ".env"
    "cache/*"
    "logs/*"
)

# 默认选项
DRY_RUN=false
RESTART_SERVICE=true
INSTALL_DEPS=false

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
        --no-restart|-R)
            RESTART_SERVICE=false
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --install|-i)
            INSTALL_DEPS=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -R, --no-restart    部署后不重启服务（默认会重启）"
            echo "  -i, --install       在远程服务器上安装/更新依赖 (使用国内镜像源)"
            echo "  -n, --dry-run       仅显示将要执行的操作，不实际执行"
            echo "      --help          显示帮助信息"
            echo ""
            echo "Supervisor 进程: $SUPERVISOR_PROCESS"
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
echo -e "${BLUE}           部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[模拟运行模式 - 不会实际执行任何操作]${NC}"
    echo ""
fi

# SSH 和 SCP 通用选项
SSH_OPTS="-i $PRIVATE_KEY_PATH -p $REMOTE_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=10"
SCP_OPTS="-i $PRIVATE_KEY_PATH -P $REMOTE_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# 计算总步骤数
TOTAL_STEPS=5
if [ "$INSTALL_DEPS" = true ]; then
    TOTAL_STEPS=6
fi

# 检查私钥文件
echo -e "${YELLOW}[1/$TOTAL_STEPS] 检查 SSH 配置...${NC}"
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo -e "${RED}  错误: 未找到 SSH 私钥文件: $PRIVATE_KEY_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}  SSH 私钥: $PRIVATE_KEY_PATH${NC}"
echo -e "${GREEN}  远程服务器: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT${NC}"
echo -e "${GREEN}  远程路径: $REMOTE_PATH${NC}"

# 测试 SSH 连接
echo -e "${YELLOW}[2/$TOTAL_STEPS] 测试 SSH 连接...${NC}"
if [ "$DRY_RUN" = false ]; then
    if ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "echo '连接成功'" 2>/dev/null; then
        echo -e "${GREEN}  SSH 连接测试通过${NC}"
    else
        echo -e "${RED}  错误: 无法连接到远程服务器${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  [模拟] 将测试 SSH 连接${NC}"
fi

# 确保远程目录存在
echo -e "${YELLOW}[3/$TOTAL_STEPS] 准备远程目录...${NC}"
if [ "$DRY_RUN" = false ]; then
    ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH/templates $REMOTE_PATH/logs $REMOTE_PATH/cache"
    echo -e "${GREEN}  远程目录已准备完成${NC}"
else
    echo -e "${GREEN}  [模拟] 将创建远程目录: $REMOTE_PATH${NC}"
fi

# 上传文件
echo -e "${YELLOW}[4/$TOTAL_STEPS] 上传文件...${NC}"

# 构建 rsync 排除参数
EXCLUDE_ARGS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$pattern"
done

# 检查是否有 rsync（Git Bash 可能没有）
if command -v rsync &> /dev/null; then
    echo -e "${GREEN}  使用 rsync 同步文件${NC}"

    if [ "$DRY_RUN" = false ]; then
        rsync -avz --progress \
            -e "ssh $SSH_OPTS" \
            $EXCLUDE_ARGS \
            "${UPLOAD_FILES[@]}" \
            "${UPLOAD_DIRS[@]}" \
            "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    else
        echo -e "${GREEN}  [模拟] rsync 将同步以下文件:${NC}"
        for file in "${UPLOAD_FILES[@]}"; do
            echo -e "    - $file"
        done
        for dir in "${UPLOAD_DIRS[@]}"; do
            echo -e "    - $dir/"
        done
    fi
else
    echo -e "${YELLOW}  rsync 不可用，使用 scp 上传${NC}"

    # 上传单个文件
    for file in "${UPLOAD_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "  上传: $file"
            if [ "$DRY_RUN" = false ]; then
                scp $SCP_OPTS "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
            fi
        else
            echo -e "${YELLOW}  跳过 (不存在): $file${NC}"
        fi
    done

    # 上传目录
    for dir in "${UPLOAD_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "  上传目录: $dir/"
            if [ "$DRY_RUN" = false ]; then
                scp $SCP_OPTS -r "$dir" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
            fi
        else
            echo -e "${YELLOW}  跳过 (不存在): $dir/${NC}"
        fi
    done
fi

echo -e "${GREEN}  文件上传完成${NC}"

# 设置远程文件权限
echo -e "${YELLOW}[5/$TOTAL_STEPS] 设置文件权限...${NC}"
if [ "$DRY_RUN" = false ]; then
    # 转换换行符 (Windows CRLF -> Linux LF) 并设置可执行权限
    ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && sed -i 's/\r$//' start.sh && chmod +x start.sh"
    echo -e "${GREEN}  文件权限设置完成${NC}"
else
    echo -e "${GREEN}  [模拟] 将转换换行符并设置 start.sh 为可执行${NC}"
fi

# 安装依赖（可选）
if [ "$INSTALL_DEPS" = true ]; then
    echo -e "${YELLOW}[6/$TOTAL_STEPS] 安装依赖 (使用国内镜像源)...${NC}"
    echo -e "${GREEN}  镜像源: $UV_INDEX_URL${NC}"

    if [ "$DRY_RUN" = false ]; then
        # 远程安装依赖的脚本
        INSTALL_SCRIPT="
cd $REMOTE_PATH

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo '错误: 未找到 Python'
    exit 1
fi

echo \"Python 版本: \\\$(\\\$PYTHON_CMD --version)\"

# 创建虚拟环境（如果不存在）
if [ ! -d '.venv' ]; then
    echo '创建虚拟环境...'
    \\\$PYTHON_CMD -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查是否安装了 uv
if command -v uv &> /dev/null; then
    echo '使用 uv 安装依赖...'
    UV_INDEX_URL=$UV_INDEX_URL uv sync
else
    # 尝试安装 uv
    echo '尝试安装 uv...'
    pip install uv -i $PIP_INDEX_URL --trusted-host $PIP_TRUSTED_HOST -q 2>/dev/null || true

    if command -v uv &> /dev/null; then
        echo '使用 uv 安装依赖...'
        UV_INDEX_URL=$UV_INDEX_URL uv sync
    else
        echo '使用 pip 安装依赖...'
        pip install -e . -i $PIP_INDEX_URL --trusted-host $PIP_TRUSTED_HOST
    fi
fi

echo '依赖安装完成'
"
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "$INSTALL_SCRIPT"
        echo -e "${GREEN}  远程依赖安装完成${NC}"
    else
        echo -e "${GREEN}  [模拟] 将在远程服务器上安装依赖${NC}"
        echo -e "${GREEN}  [模拟] 优先使用 uv，回退到 pip${NC}"
        echo -e "${GREEN}  [模拟] 使用镜像源: $UV_INDEX_URL${NC}"
    fi
fi

# 重启服务（可选）- 使用 Supervisor 进程守护
if [ "$RESTART_SERVICE" = true ]; then
    echo ""
    echo -e "${YELLOW}正在通过 Supervisor 重启远程服务...${NC}"
    echo -e "${GREEN}  进程名称: $SUPERVISOR_PROCESS${NC}"
    if [ "$DRY_RUN" = false ]; then
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "supervisorctl restart $SUPERVISOR_PROCESS"
        echo -e "${GREEN}服务已通过 Supervisor 重启${NC}"
    else
        echo -e "${GREEN}[模拟] 将执行: supervisorctl restart $SUPERVISOR_PROCESS${NC}"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}        部署完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "远程服务器: ${GREEN}$REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT${NC}"
echo -e "部署路径:   ${GREEN}$REMOTE_PATH${NC}"
echo ""

if [ "$RESTART_SERVICE" = true ]; then
    echo -e "${GREEN}服务已自动重启${NC}"
    echo -e "${YELLOW}提示: 使用 --no-restart 参数可跳过重启${NC}"
fi
