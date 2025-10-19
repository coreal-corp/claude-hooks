# Claude Code Hooks - 빠른 시작 가이드

Claude Code 작업을 Slack으로 자동 알림받는 Hook 시스템입니다.
**Python 3.6+가 없어도 자동 설치됩니다!**

## ⚡ 초간단 설치 (단 1개 파일!)

### 모든 OS (Windows, Linux, macOS, WSL) 동일

**Windows (CMD/PowerShell):**
```cmd
cd %USERPROFILE%\.claude-hooks
install
```

**Linux / macOS / WSL:**
```bash
cd ~/.claude-hooks
./install
```

**Slack 토큰 설정:**
```bash
# Linux/macOS/WSL
nano ~/.ultrathink.env

# Windows
notepad %USERPROFILE%\.ultrathink.env
```

그게 전부입니다! Python 설치부터 Hook 설정까지 자동으로 완료됩니다.

---

## 🔧 고급 설치 (개별 스크립트)

OS별로 개별 스크립트를 사용하고 싶다면:

### Linux / macOS / WSL

```bash
./setup.sh
```

### Windows

```cmd
setup.bat
```

## ✨ 자동 설치 기능

설치 스크립트가 자동으로:
- ✅ Python 3.6+ 버전 확인
- ✅ 없으면 자동 설치 (사용자 동의 후)
- ✅ Hook 파일 복사 및 권한 설정
- ✅ 환경 변수 템플릿 생성
- ✅ 설치 검증

**지원 플랫폼 (모두 1번 실행으로 완료):**
- ✅ Linux: Ubuntu, Debian, CentOS, RHEL, Fedora
- ✅ macOS: Homebrew 자동 사용
- ✅ Windows: winget으로 Python 설치 후 자동으로 경로 탐색하여 계속 진행

## 📋 필수 설정

### Slack 토큰 발급

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. Bot Token Scopes 설정:
   - `chat:write`
   - `chat:write.public`
4. "Install to Workspace"
5. Bot Token 복사 (xoxb-로 시작)

### 환경 변수 설정

`~/.ultrathink.env` 파일 편집:

```bash
# Slack Bot Token (필수)
SLACK_BOT_TOKEN=xoxb-YOUR-ACTUAL-TOKEN-HERE

# Slack Channel ID (필수 - C로 시작하는 11자리)
SLACK_CHANNEL_ID=C09J29WDSHK

# 자동 로깅 활성화
ULTRATHINK_AUTO_LOG=true

# 사용자 이름 (선택)
SLACK_USER_NAME=your_name

# GitLab 자동 푸시 (선택 - 활성화하려면 true로 변경)
GITLAB_AUTO_PUSH_ENABLED=false
GITLAB_REPO_URL=https://gitlab.com/your-username/your-repo.git
GITLAB_ACCESS_TOKEN=your-gitlab-token
```

## 🔄 GitLab 자동 푸시 (선택 기능)

작업 완료 시 자동으로 변경사항을 GitLab에 커밋하고 푸시합니다.

### 🚀 빠른 설정 (권장)

**대화형 설정 마법사 실행:**

```bash
python3 ~/.claude-hooks/setup_gitlab.py
```

설정 마법사가 자동으로:
- ✅ GitLab Access Token 확인
- ✅ 기존 저장소 목록 조회
- ✅ 저장소 선택 또는 새로 생성
- ✅ 환경 변수 자동 저장
- ✅ 테스트 푸시 (선택)

### ⚙️ 수동 설정

1. **GitLab Access Token 생성**
   - GitLab > Settings > Access Tokens
   - Scopes: `api`, `write_repository` 선택
   - Token 복사

2. **환경 변수 설정** (`~/.ultrathink.env`):
   ```bash
   # GitLab 자동 푸시 활성화
   GITLAB_AUTO_PUSH_ENABLED=true

   # GitLab 저장소 URL
   GITLAB_REPO_URL=https://gitlab.com/your-username/your-repo.git

   # GitLab Access Token
   GITLAB_ACCESS_TOKEN=glpat-your-token-here

   # Remote 이름 (선택, 기본값: gitlab)
   GITLAB_REMOTE_NAME=gitlab

   # 커밋 메시지 (선택, 비워두면 자동 생성)
   GITLAB_AUTO_COMMIT_MESSAGE=
   ```

### 💡 동작 방식

1. SessionEnd 또는 Stop hook 실행 시
2. 파일 변경사항 자동 감지
3. 변경사항이 있으면 자동 커밋
4. GitLab에 자동 푸시
5. Slack으로 푸시 결과 알림

### ✅ 테스트

```bash
# GitLab 푸시 테스트 (대화형)
cd your-project
python3 ~/.claude-hooks/auto_push_gitlab.py
```

### 🔍 저장소 선택/생성 기능

GitLab 저장소가 설정되지 않은 상태에서 자동 푸시를 시도하면:
- 대화형 터미널: 자동으로 설정 마법사 실행
- 백그라운드 실행: 안내 메시지 로그 출력

## ✅ 설치 테스트

### Linux / macOS / WSL

```bash
echo '{"initial_user_message":"테스트"}' | ~/.claude-hooks/SessionStart
```

### Windows

```cmd
echo {"initial_user_message":"테스트"} | python %USERPROFILE%\.claude-hooks\SessionStart
```

Slack 채널에 알림이 오면 성공!

## 📊 Hook 종류

| Hook | 트리거 | 설명 |
|------|--------|------|
| **SessionStart** | 세션 시작 | 작업 시작 알림 |
| **SessionEnd** | 세션 종료 | 작업 완료 요약 (소요 시간, 변경 파일) |
| **Stop** | 작업 중단 | 중단 알림 및 작업 내용 |
| **Notification** | 중요 이벤트 | Plan 모드, 에러 등 |

## 🐛 문제 해결

### Python을 찾을 수 없음

**Linux/macOS:**
```bash
# 수동 설치
sudo apt install python3        # Ubuntu/Debian
sudo yum install python3        # CentOS/RHEL
brew install python3            # macOS
```

**Windows:**
```cmd
winget install Python.Python.3
```

### Hook이 실행되지 않음

1. Python 버전 확인:
   ```bash
   python3 --version  # 3.6 이상이어야 함
   ```

2. 실행 권한 확인 (Linux/macOS):
   ```bash
   chmod +x ~/.claude-hooks/*
   ```

3. 환경 변수 파일 확인:
   ```bash
   cat ~/.ultrathink.env
   ```

### Slack 알림이 오지 않음

1. Slack Bot Token 확인
   - `xoxb-`로 시작하는지 확인
   - 토큰에 공백이나 따옴표가 없는지 확인

2. Channel ID 확인
   - `#` 없이 `C`로 시작하는 11자리
   - 예: `C09J29WDSHK` ✅, `#general` ❌

3. 디버그 로그 확인:
   ```bash
   # Linux/macOS/WSL
   tail -f /tmp/claude-hook-debug.log

   # Windows
   type %TEMP%\claude-hook-debug.log
   ```

## 📁 파일 구조

```
~/.claude-hooks/
├── setup.sh              # Linux/macOS/WSL 설치 스크립트
├── setup.bat             # Windows 설치 스크립트
├── README.md             # 빠른 시작 가이드 (이 파일)
├── INSTALL.md            # 상세 설치 가이드
├── SessionStart          # Hook: 세션 시작
├── SessionEnd            # Hook: 세션 종료
├── Stop                  # Hook: 작업 중단
├── Notification          # Hook: 중요 이벤트
└── analyze_transcript.py # 분석 도구
```

## 🔧 고급 옵션

### 수동 설치 (자동 설치 실패 시)

```bash
# 1. Python 3.6+ 설치 확인
python3 --version

# 2. Hook 디렉토리 생성
mkdir -p ~/.claude-hooks

# 3. 파일 복사
cp SessionStart SessionEnd Stop Notification analyze_transcript.py ~/.claude-hooks/

# 4. 실행 권한 설정 (Linux/macOS만)
chmod +x ~/.claude-hooks/*

# 5. 환경 변수 파일 생성
cp .ultrathink.env.template ~/.ultrathink.env
nano ~/.ultrathink.env
```

### 팀 배포

```bash
# 압축 파일 생성
cd ~/.claude-hooks
tar -czf claude-hooks.tar.gz \
  setup.sh setup.bat README.md INSTALL.md \
  SessionStart SessionEnd Stop Notification analyze_transcript.py

# 팀원에게 전달
# 팀원은 압축 해제 후 setup.sh 또는 setup.bat 실행
```

## 📚 더 보기

- **상세 설치 가이드**: [INSTALL.md](INSTALL.md)
- **Hook 동작 원리**: [INSTALL.md#작동-원리](INSTALL.md#작동-원리)
- **트러블슈팅**: [INSTALL.md#트러블슈팅](INSTALL.md#트러블슈팅)

## 💡 팁

1. **Python 버전**: 3.6 이상이면 OK, 3.12 권장
2. **Slack 채널**: Bot을 채널에 초대해야 메시지 전송 가능
3. **디버그 로그**: 문제 발생 시 첫 번째로 확인할 것
4. **크로스 플랫폼**: 동일한 파일이 모든 OS에서 작동

## ✉️ 문의

설치 문제 발생 시:
1. 디버그 로그 확인 (`/tmp/claude-hook-debug.log`)
2. Python 버전 확인 (`python3 --version`)
3. 환경 변수 파일 확인 (`~/.ultrathink.env`)
4. [INSTALL.md](INSTALL.md) 참고

---

**버전**: 2.0.0 (크로스 플랫폼 Python)
**호환성**: Windows, macOS, Linux, WSL
**Python**: 3.6+ (자동 설치 지원)
