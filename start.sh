#!/usr/bin/env bash
#
# SEA Retailer 项目一键启动脚本
# 用法:
#   ./start.sh              # 启动全部服务（依赖 + 应用）
#   ./start.sh deps         # 仅启动基础设施（数据库等）
#   ./start.sh app          # 仅启动应用层（需依赖已就绪）
#   ./start.sh frontend     # 仅启动前端
#   ./start.sh stop         # 停止所有服务
#   ./start.sh status       # 查看服务状态
#   ./start.sh logs [svc]   # 查看日志
#
set -euo pipefail

# ── 路径 ──
ROOT="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$ROOT/infra-local"
ENV_FILE="$INFRA_DIR/env/.env.local"

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── PID 文件目录 ──
PID_DIR="$ROOT/.pids"
mkdir -p "$PID_DIR"

# ── 辅助函数 ──
log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${CYAN}──── $* ────${NC}"; }

# 检查命令是否存在
require_cmd() {
  command -v "$1" &>/dev/null || { log_err "需要 '$1' 但未找到，请先安装"; exit 1; }
}

# 等待端口可用
wait_for_port() {
  local host="$1" port="$2" name="$3" timeout="${4:-60}"
  local elapsed=0
  log_info "等待 $name ($host:$port) 就绪..."
  while ! nc -z "$host" "$port" 2>/dev/null; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge "$timeout" ]; then
      log_warn "$name 在 ${timeout}s 内未就绪，继续启动..."
      return 1
    fi
  done
  log_ok "$name 已就绪 (${elapsed}s)"
  return 0
}

# 杀死占用指定端口的进程
kill_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    log_info "端口 $port 被占用，正在清理 (PIDs: $pids)..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 1
    log_ok "端口 $port 已释放"
  fi
}

# 停止由 PID 文件记录的进程
stop_pid() {
  local name="$1"
  local pidfile="$PID_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      log_info "停止 $name (PID $pid)..."
      kill "$pid" 2>/dev/null || true
      # 等待进程退出
      for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
      done
      # 强制杀死
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
      log_ok "$name 已停止"
    fi
    rm -f "$pidfile"
  fi
}

# ── 启动基础设施 (Docker) ──
start_deps() {
  log_step "启动基础设施 (ClickHouse / Postgres / Keycloak)"
  require_cmd docker

  cd "$INFRA_DIR"
  docker compose -f docker-compose.deps.yaml up -d

  # 等待依赖就绪
  wait_for_port localhost 5432  "PostgreSQL"  60
  wait_for_port localhost 8123  "ClickHouse"  60
  wait_for_port localhost 8180  "Keycloak"    90

  log_ok "基础设施全部就绪"
}

# ── 启动 API Backend ──
start_api() {
  log_step "启动 API Backend (Spring Boot, 端口 8080)"

  stop_pid "api-backend"
  kill_port 8080

  cd "$ROOT/api-backend"

  if [ ! -f mvnw ]; then
    log_err "mvnw 不存在"; return 1
  fi
  chmod +x mvnw

  # 加载环境变量
  if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
  fi

  nohup ./mvnw spring-boot:run \
    -Dspring-boot.run.profiles=local \
    > "$ROOT/.pids/api-backend.log" 2>&1 &
  echo $! > "$PID_DIR/api-backend.pid"

  log_ok "API Backend 已在后台启动 (PID $(cat "$PID_DIR/api-backend.pid"))"
  log_info "日志: $ROOT/.pids/api-backend.log"
}

# ── 启动 Web Frontend ──
start_frontend() {
  log_step "启动 Web Frontend (Vite + React, 端口 3000)"

  stop_pid "web-frontend"
  kill_port 3000

  cd "$ROOT/web-frontend"

  # 确保依赖已安装
  if [ ! -d node_modules ]; then
    log_info "安装前端依赖..."
    npm install
  fi

  nohup npm run dev > "$ROOT/.pids/web-frontend.log" 2>&1 &
  echo $! > "$PID_DIR/web-frontend.pid"

  log_ok "Web Frontend 已在后台启动 (PID $(cat "$PID_DIR/web-frontend.pid"))"
  log_info "日志: $ROOT/.pids/web-frontend.log"
}

# ── 启动 Streamlit App ──
start_streamlit() {
  log_step "启动 Streamlit Demo App (端口 8501)"

  stop_pid "streamlit"
  kill_port 8501

  cd "$ROOT/app-mvp"

  # 检查虚拟环境
  if [ -d .venv ]; then
    PY_STREAMLIT=".venv/bin/streamlit"
  elif command -v streamlit &>/dev/null; then
    PY_STREAMLIT="streamlit"
  else
    log_warn "未找到 Streamlit，跳过。请先运行: cd app-mvp && python -m venv .venv && .venv/bin/pip install -e ."
    return 0
  fi

  nohup $PY_STREAMLIT run src/app/main.py \
    --server.port 8501 \
    --server.headless true \
    > "$ROOT/.pids/streamlit.log" 2>&1 &
  echo $! > "$PID_DIR/streamlit.pid"

  log_ok "Streamlit 已在后台启动 (PID $(cat "$PID_DIR/streamlit.pid"))"
  log_info "日志: $ROOT/.pids/streamlit.log"
}

# ── 停止所有服务 ──
stop_all() {
  log_step "停止所有服务"

  stop_pid "web-frontend"
  stop_pid "api-backend"
  stop_pid "streamlit"

  # 确保端口也被释放
  kill_port 3000
  kill_port 8080
  kill_port 8501

  # 停止 Docker 容器
  cd "$INFRA_DIR"
  if docker compose -f docker-compose.deps.yaml ps -q 2>/dev/null | grep -q .; then
    log_info "停止 Docker 基础设施..."
    docker compose -f docker-compose.deps.yaml down
    log_ok "Docker 容器已停止"
  fi

  log_ok "全部服务已停止"
}

# ── 查看状态 ──
show_status() {
  log_step "服务状态"

  echo ""
  # Docker 容器
  echo -e "${CYAN}Docker 容器:${NC}"
  cd "$INFRA_DIR"
  docker compose -f docker-compose.deps.yaml ps 2>/dev/null || echo "  (未启动)"

  echo ""
  echo -e "${CYAN}应用进程:${NC}"

  for svc in api-backend web-frontend streamlit; do
    local pidfile="$PID_DIR/$svc.pid"
    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
      echo -e "  ${GREEN}●${NC} $svc (PID $(cat "$pidfile"))"
    else
      echo -e "  ${RED}○${NC} $svc (未运行)"
      rm -f "$pidfile"
    fi
  done

  echo ""
  echo -e "${CYAN}访问地址:${NC}"
  echo "  API Backend:  http://localhost:8080"
  echo "  Web Frontend: http://localhost:3000"
  echo "  Streamlit:    http://localhost:8501"
  echo "  Keycloak:     http://localhost:8180"
  echo "  ClickHouse:   http://localhost:8123"
  echo "  PostgreSQL:   localhost:5432"
}

# ── 查看日志 ──
show_logs() {
  local svc="${1:-}"
  if [ -z "$svc" ]; then
    echo "用法: $0 logs <api-backend|web-frontend|streamlit|docker>"
    return
  fi
  case "$svc" in
    docker|deps)
      cd "$INFRA_DIR" && docker compose -f docker-compose.deps.yaml logs -f --tail=50
      ;;
    *)
      local logfile="$ROOT/.pids/$svc.log"
      if [ -f "$logfile" ]; then
        tail -f "$logfile"
      else
        log_err "日志文件不存在: $logfile"
      fi
      ;;
  esac
}

# ── 启动全部应用 ──
start_app() {
  start_api
  start_frontend
  start_streamlit

  echo ""
  log_ok "所有应用服务已启动！"
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  SEA Retailer 服务地址                   ${CYAN}║${NC}"
  echo -e "${CYAN}╠══════════════════════════════════════════╣${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}Web Frontend${NC}:  http://localhost:3000    ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}API Backend${NC}:   http://localhost:8080    ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}Streamlit${NC}:     http://localhost:8501    ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}Keycloak${NC}:      http://localhost:8180    ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
  echo ""
  echo "使用 './start.sh stop' 停止所有服务"
  echo "使用 './start.sh status' 查看服务状态"
  echo "使用 './start.sh logs <服务名>' 查看日志"
}

# ── 主入口 ──
main() {
  local cmd="${1:-all}"

  case "$cmd" in
    deps)
      start_deps
      ;;
    app)
      start_app
      ;;
    api)
      start_api
      ;;
    frontend)
      start_frontend
      ;;
    streamlit)
      start_streamlit
      ;;
    all)
      start_deps
      start_app
      ;;
    stop)
      stop_all
      ;;
    status)
      show_status
      ;;
    logs)
      show_logs "${2:-}"
      ;;
    help|-h|--help)
      echo "用法: $0 [命令]"
      echo ""
      echo "命令:"
      echo "  all        启动全部服务 (默认)"
      echo "  deps       仅启动基础设施 (Docker)"
      echo "  app        仅启动应用层"
      echo "  api        仅启动 API Backend"
      echo "  frontend   仅启动 Web Frontend"
      echo "  streamlit  仅启动 Streamlit"
      echo "  stop       停止所有服务"
      echo "  status     查看服务状态"
      echo "  logs       查看日志 (logs <服务名>)"
      echo "  help       显示帮助"
      ;;
    *)
      log_err "未知命令: $cmd"
      echo "使用 '$0 help' 查看帮助"
      exit 1
      ;;
  esac
}

main "$@"
