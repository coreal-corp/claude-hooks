#!/bin/bash
# Claude Code Hooks - Automated Setup Script
# Supports: Linux, macOS, WSL
# Automatically checks and installs Python 3.6+ if needed

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emojis for visual feedback
STEP="🎯"
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$HOME/.claude-hooks"

# Required Python version
REQUIRED_PYTHON_VERSION="3.6"

echo ""
echo "======================================"
echo "  Claude Code Hooks - Setup Script"
echo "======================================"
echo ""

# Function: Print colored message
print_msg() {
    local type=$1
    shift
    case $type in
        success) echo -e "${GREEN}${SUCCESS} $*${NC}" ;;
        error)   echo -e "${RED}${ERROR} $*${NC}" ;;
        warning) echo -e "${YELLOW}${WARNING} $*${NC}" ;;
        info)    echo -e "${BLUE}${INFO} $*${NC}" ;;
        step)    echo -e "${BLUE}${STEP} $*${NC}" ;;
    esac
}

# Function: Check Python version
check_python_version() {
    local python_cmd=$1

    if ! command -v "$python_cmd" &> /dev/null; then
        return 1
    fi

    local version=$($python_cmd --version 2>&1 | awk '{print $2}')
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -eq 3 ] && [ "$minor" -ge 6 ]; then
        echo "$python_cmd"
        return 0
    fi

    return 1
}

# Function: Detect OS and package manager
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian) echo "debian" ;;
            centos|rhel)   echo "rhel" ;;
            fedora)        echo "fedora" ;;
            *)             echo "linux" ;;
        esac
    else
        echo "unknown"
    fi
}

# Function: Install Python on Debian/Ubuntu
install_python_debian() {
    print_msg step "Debian/Ubuntu 시스템에서 Python 설치 중..."

    if ! command -v sudo &> /dev/null; then
        print_msg error "sudo 명령어를 찾을 수 없습니다. 관리자 권한이 필요합니다."
        return 1
    fi

    print_msg info "패키지 목록 업데이트 중..."
    sudo apt update || return 1

    print_msg info "Python 3 설치 중..."
    sudo apt install -y python3 python3-pip || return 1

    return 0
}

# Function: Install Python on RHEL/CentOS
install_python_rhel() {
    print_msg step "RHEL/CentOS 시스템에서 Python 설치 중..."

    if ! command -v sudo &> /dev/null; then
        print_msg error "sudo 명령어를 찾을 수 없습니다. 관리자 권한이 필요합니다."
        return 1
    fi

    print_msg info "Python 3 설치 중..."
    sudo yum install -y python3 python3-pip || return 1

    return 0
}

# Function: Install Python on Fedora
install_python_fedora() {
    print_msg step "Fedora 시스템에서 Python 설치 중..."

    if ! command -v sudo &> /dev/null; then
        print_msg error "sudo 명령어를 찾을 수 없습니다. 관리자 권한이 필요합니다."
        return 1
    fi

    print_msg info "Python 3 설치 중..."
    sudo dnf install -y python3 python3-pip || return 1

    return 0
}

# Function: Install Python on macOS
install_python_macos() {
    print_msg step "macOS 시스템에서 Python 설치 중..."

    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        print_msg info "Homebrew를 사용하여 Python 설치 중..."
        brew install python3 || return 1
        return 0
    else
        print_msg warning "Homebrew가 설치되어 있지 않습니다."
        print_msg info "다음 중 하나를 선택하세요:"
        echo ""
        echo "  1) Homebrew 설치 후 Python 설치 (권장)"
        echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "     brew install python3"
        echo ""
        echo "  2) Python 공식 사이트에서 다운로드"
        echo "     https://www.python.org/downloads/"
        echo ""
        return 1
    fi
}

# Function: Prompt user for Python installation
prompt_python_install() {
    local os_type=$1

    print_msg warning "Python 3.6 이상이 설치되어 있지 않습니다."
    echo ""
    echo "Python 설치가 필요합니다. 자동으로 설치하시겠습니까? (y/n)"
    read -r response

    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_msg info "수동 설치를 선택하셨습니다."
        echo ""
        print_msg info "Python 3.6 이상을 다음 방법으로 설치하세요:"
        case "$os_type" in
            debian)
                echo "  sudo apt update && sudo apt install python3 python3-pip"
                ;;
            rhel)
                echo "  sudo yum install python3 python3-pip"
                ;;
            fedora)
                echo "  sudo dnf install python3 python3-pip"
                ;;
            macos)
                echo "  brew install python3"
                echo "  또는 https://www.python.org/downloads/ 에서 다운로드"
                ;;
            *)
                echo "  https://www.python.org/downloads/ 에서 다운로드"
                ;;
        esac
        echo ""
        return 1
    fi

    return 0
}

# Step 1: Check Python installation
print_msg step "Step 1: Python 버전 확인 중..."

PYTHON_CMD=""
if python_result=$(check_python_version "python3"); then
    PYTHON_CMD="$python_result"
    print_msg success "Python 3 발견: $(python3 --version)"
elif python_result=$(check_python_version "python"); then
    PYTHON_CMD="$python_result"
    print_msg success "Python 발견: $(python --version)"
else
    print_msg warning "Python 3.6 이상을 찾을 수 없습니다."

    # Detect OS
    OS_TYPE=$(detect_os)
    print_msg info "운영체제: $OS_TYPE"

    # Ask user for installation
    if prompt_python_install "$OS_TYPE"; then
        case "$OS_TYPE" in
            debian)
                if install_python_debian; then
                    PYTHON_CMD="python3"
                    print_msg success "Python 설치 완료!"
                else
                    print_msg error "Python 설치 실패. 수동으로 설치해주세요."
                    exit 1
                fi
                ;;
            rhel)
                if install_python_rhel; then
                    PYTHON_CMD="python3"
                    print_msg success "Python 설치 완료!"
                else
                    print_msg error "Python 설치 실패. 수동으로 설치해주세요."
                    exit 1
                fi
                ;;
            fedora)
                if install_python_fedora; then
                    PYTHON_CMD="python3"
                    print_msg success "Python 설치 완료!"
                else
                    print_msg error "Python 설치 실패. 수동으로 설치해주세요."
                    exit 1
                fi
                ;;
            macos)
                if install_python_macos; then
                    PYTHON_CMD="python3"
                    print_msg success "Python 설치 완료!"
                else
                    print_msg error "Python 설치 실패. 수동으로 설치해주세요."
                    exit 1
                fi
                ;;
            *)
                print_msg error "지원되지 않는 운영체제입니다."
                print_msg info "https://www.python.org/downloads/ 에서 수동 설치해주세요."
                exit 1
                ;;
        esac
    else
        exit 1
    fi
fi

# Verify Python installation
print_msg step "Python 설치 확인 중..."
if $PYTHON_CMD -c "import sys; import json; import os; import urllib.request" 2>/dev/null; then
    print_msg success "필수 Python 모듈 확인 완료"
else
    print_msg error "Python 모듈 확인 실패"
    exit 1
fi

# Step 2: Create hooks directory
print_msg step "Step 2: Hook 디렉토리 생성 중..."

if [ ! -d "$HOOKS_DIR" ]; then
    mkdir -p "$HOOKS_DIR"
    print_msg success "디렉토리 생성: $HOOKS_DIR"
else
    print_msg info "디렉토리 이미 존재: $HOOKS_DIR"
fi

# Step 3: Copy hook files
print_msg step "Step 3: Hook 파일 복사 중..."

HOOK_FILES=("SessionStart" "SessionEnd" "Stop" "Notification" "analyze_transcript.py")

for file in "${HOOK_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp "$SCRIPT_DIR/$file" "$HOOKS_DIR/"
        chmod +x "$HOOKS_DIR/$file"
        print_msg success "복사 완료: $file"
    else
        print_msg warning "파일을 찾을 수 없음: $file"
    fi
done

# Step 4: Create environment file template
print_msg step "Step 4: 환경 변수 파일 생성 중..."

ENV_FILE="$HOME/.ultrathink.env"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# Claude Code Slack Hooks Configuration

# Slack Bot Token (필수 - xoxb-로 시작)
SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-HERE

# Slack Channel ID (필수 - C로 시작하는 11자리, # 없이)
SLACK_CHANNEL_ID=C09J29WDSHK

# 자동 로깅 활성화
ULTRATHINK_AUTO_LOG=true

# 사용자 이름 (선택)
SLACK_USER_NAME=your_name
EOF
    print_msg success "환경 변수 템플릿 생성: $ENV_FILE"
    print_msg warning "⚠️  $ENV_FILE 파일을 편집하여 Slack 토큰을 설정하세요!"
else
    print_msg info "환경 변수 파일 이미 존재: $ENV_FILE"
fi

# Step 5: Verify installation
print_msg step "Step 5: 설치 검증 중..."

VERIFICATION_PASSED=true

# Check hook files
for file in "${HOOK_FILES[@]}"; do
    if [ ! -f "$HOOKS_DIR/$file" ]; then
        print_msg error "파일 없음: $file"
        VERIFICATION_PASSED=false
    elif [ ! -x "$HOOKS_DIR/$file" ]; then
        print_msg warning "실행 권한 없음: $file"
        chmod +x "$HOOKS_DIR/$file"
        print_msg success "권한 수정 완료: $file"
    fi
done

# Check environment file
if [ ! -f "$ENV_FILE" ]; then
    print_msg error "환경 변수 파일 없음: $ENV_FILE"
    VERIFICATION_PASSED=false
fi

if [ "$VERIFICATION_PASSED" = true ]; then
    print_msg success "모든 검증 통과!"
else
    print_msg error "일부 검증 실패. 위 메시지를 확인하세요."
    exit 1
fi

# Installation complete
echo ""
echo "======================================"
print_msg success "설치 완료!"
echo "======================================"
echo ""
print_msg info "다음 단계:"
echo ""
echo "  1. Slack 토큰 설정:"
echo "     nano $ENV_FILE"
echo "     (또는 원하는 에디터 사용)"
echo ""
echo "  2. SLACK_BOT_TOKEN을 실제 토큰으로 교체"
echo ""
echo "  3. 테스트 실행:"
echo "     echo '{\"initial_user_message\":\"테스트\"}' | $HOOKS_DIR/SessionStart"
echo ""
echo "  4. Slack 채널에서 알림 확인"
echo ""
print_msg info "문제 발생 시 로그 확인:"
echo "     tail -f /tmp/claude-hook-debug.log"
echo ""
