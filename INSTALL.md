# Claude Code Hooks - 팀원 설치 가이드

## 🔧 문제 해결 완료

기존 Bash 버전이 Linux/WSL에서만 작동하는 문제를 해결했습니다.
이제 **Python 크로스 플랫폼 버전**으로 Windows, macOS, Linux 모두에서 동일하게 작동합니다.

---

## 📋 사전 요구사항

### 1. Python 3.6+ 설치 확인
```bash
python3 --version
```
또는 (Windows)
```cmd
python --version
```

**Windows 사용자**: Python 미설치 시 https://python.org 에서 다운로드

### 2. Slack 토큰 준비
- Slack Bot Token (xoxb-로 시작)
- Slack Channel ID (C로 시작하는 11자리)

---

## 🚀 설치 방법

### Step 1: Hook 디렉토리 생성
```bash
mkdir -p ~/.claude-hooks
cd ~/.claude-hooks
```

### Step 2: Hook 파일 복사
다음 4개 파일을 `~/.claude-hooks/` 디렉토리에 복사:
- `SessionStart`
- `SessionEnd`
- `Stop`
- `Notification`
- `analyze_transcript.py` (분석 도구)

### Step 3: 실행 권한 설정 (Linux/macOS만)
```bash
chmod +x ~/.claude-hooks/SessionStart
chmod +x ~/.claude-hooks/SessionEnd
chmod +x ~/.claude-hooks/Stop
chmod +x ~/.claude-hooks/Notification
```

**Windows 사용자**: 실행 권한 설정 불필요 (Python이 자동 처리)

### Step 4: 환경 변수 파일 생성
`~/.ultrathink.env` 파일을 생성하고 아래 내용 입력:

```bash
# Slack Bot Token (필수)
SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-HERE

# Slack Channel ID (필수 - # 없이)
SLACK_CHANNEL_ID=C09J29WDSHK

# 자동 로깅 활성화
ULTRATHINK_AUTO_LOG=true

# 사용자 이름 (선택)
SLACK_USER_NAME=your_name
```

**중요**: `SLACK_BOT_TOKEN`을 실제 토큰으로 교체하세요!

---

## ✅ 설치 검증

### 1. Python 모듈 확인
```bash
python3 -c "import sys, json, os, urllib.request; print('✅ OK')"
```

### 2. Hook 파일 확인
```bash
ls -la ~/.claude-hooks/
```
다음 파일들이 있어야 함:
- SessionStart (실행 권한 있음)
- SessionEnd (실행 권한 있음)
- Stop (실행 권한 있음)
- Notification (실행 권한 있음)

### 3. 환경 변수 확인
```bash
cat ~/.ultrathink.env
```
토큰이 올바르게 설정되었는지 확인

### 4. 테스트 실행
```bash
echo '{"initial_user_message":"테스트"}' | ~/.claude-hooks/SessionStart
```
Slack 채널에 알림이 오면 성공!

---

## 🐛 트러블슈팅

### 문제 1: "python3: command not found"
**Windows**: `python` 명령어 사용 (python3 대신)
```cmd
python --version
```

### 문제 2: Hook이 실행되지 않음
1. Python 버전 확인 (3.6 이상 필요)
2. 파일 경로 확인: `ls -la ~/.claude-hooks/`
3. 실행 권한 확인 (Linux/macOS): `chmod +x ~/.claude-hooks/*`

### 문제 3: Slack 알림이 오지 않음
1. `.ultrathink.env` 파일 존재 확인
2. `SLACK_BOT_TOKEN` 올바른지 확인
3. Channel ID에 `#` 없는지 확인 (C09J29WDSHK ✅, #general ❌)
4. 디버그 로그 확인:
```bash
tail -f /tmp/claude-hook-debug.log
```

### 문제 4: "Permission denied"
**Linux/macOS만 해당**:
```bash
chmod +x ~/.claude-hooks/SessionStart
chmod +x ~/.claude-hooks/SessionEnd
chmod +x ~/.claude-hooks/Stop
chmod +x ~/.claude-hooks/Notification
```

---

## 📊 작동 원리

### 크로스 플랫폼 호환성
- `#!/usr/bin/env python3` → 시스템 PATH에서 Python 자동 탐지
- Python 표준 라이브러리만 사용 (외부 패키지 불필요)
- Windows, macOS, Linux 모두 동일한 코드로 실행

### Hook 트리거
- **SessionStart**: Claude Code 세션 시작 시
- **SessionEnd**: Claude Code 세션 종료 시
- **Stop**: 작업 중단 시
- **Notification**: 중요 이벤트 발생 시

---

## 🔍 디버그 로그

문제 발생 시 로그 확인:
```bash
# 실시간 로그 모니터링
tail -f /tmp/claude-hook-debug.log

# 최근 로그 확인
tail -20 /tmp/claude-hook-debug.log
```

---

## 📦 배포 스크립트 (선택사항)

Hook 파일을 팀원들에게 배포하려면:

```bash
# 현재 디렉토리에 hooks.tar.gz 생성
cd ~/.claude-hooks
tar -czf ~/claude-hooks.tar.gz SessionStart SessionEnd Stop Notification analyze_transcript.py

# 팀원은 이렇게 설치
tar -xzf claude-hooks.tar.gz -C ~/.claude-hooks/
chmod +x ~/.claude-hooks/SessionStart ~/.claude-hooks/SessionEnd ~/.claude-hooks/Stop ~/.claude-hooks/Notification
```

---

## ✉️ 문의

설치 문제 발생 시:
1. 디버그 로그 확인 (`/tmp/claude-hook-debug.log`)
2. Python 버전 확인 (`python3 --version`)
3. 환경 변수 파일 확인 (`~/.ultrathink.env`)
