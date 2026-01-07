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
RESTART_SERVICE=false

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --restart|-r)
            RESTART_SERVICE=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -r, --restart       部署后重启远程服务"
            echo "  -n, --dry-run       仅显示将要执行的操作，不实际执行"
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

# 检查私钥文件
echo -e "${YELLOW}[1/5] 检查 SSH 配置...${NC}"
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo -e "${RED}  错误: 未找到 SSH 私钥文件: $PRIVATE_KEY_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}  SSH 私钥: $PRIVATE_KEY_PATH${NC}"
echo -e "${GREEN}  远程服务器: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT${NC}"
echo -e "${GREEN}  远程路径: $REMOTE_PATH${NC}"

# 测试 SSH 连接
echo -e "${YELLOW}[2/5] 测试 SSH 连接...${NC}"
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
echo -e "${YELLOW}[3/5] 准备远程目录...${NC}"
if [ "$DRY_RUN" = false ]; then
    ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH/templates $REMOTE_PATH/logs $REMOTE_PATH/cache"
    echo -e "${GREEN}  远程目录已准备完成${NC}"
else
    echo -e "${GREEN}  [模拟] 将创建远程目录: $REMOTE_PATH${NC}"
fi

# 上传文件
echo -e "${YELLOW}[4/5] 上传文件...${NC}"

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
echo -e "${YELLOW}[5/5] 设置文件权限...${NC}"
if [ "$DRY_RUN" = false ]; then
    ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "chmod +x $REMOTE_PATH/start.sh 2>/dev/null || true"
    echo -e "${GREEN}  文件权限设置完成${NC}"
else
    echo -e "${GREEN}  [模拟] 将设置 start.sh 为可执行${NC}"
fi

# 重启服务（可选）
if [ "$RESTART_SERVICE" = true ]; then
    echo ""
    echo -e "${YELLOW}正在重启远程服务...${NC}"
    if [ "$DRY_RUN" = false ]; then
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && pkill -f 'python.*app.py' 2>/dev/null || true; sleep 2; nohup ./start.sh > /dev/null 2>&1 &"
        echo -e "${GREEN}服务重启命令已发送${NC}"
    else
        echo -e "${GREEN}[模拟] 将重启远程服务${NC}"
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

if [ "$RESTART_SERVICE" = false ]; then
    echo -e "${YELLOW}提示: 使用 --restart 参数可在部署后自动重启服务${NC}"
    echo -e "      或手动登录服务器执行: cd $REMOTE_PATH && ./start.sh"
fi
