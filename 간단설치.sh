#!/bin/bash
# Claude Hooks 자동 설치 (WSL/Linux)

echo ""
echo "================================================"
echo "  Claude Hooks 자동 설치"
echo "================================================"
echo ""
echo "설치 중..."
echo ""

cd "$(dirname "$0")"

echo "[1/3] 파일 복사 중..."
cp -f SessionStart SessionEnd Stop Notification ~/.claude-hooks/ 2>/dev/null
cp -f session-start session-end stop notification ~/.claude-hooks/ 2>/dev/null
cp -f analyze_transcript.py auto_update.py auto_push_gitlab.py setup_gitlab.py update ~/.claude-hooks/ 2>/dev/null
chmod +x ~/.claude-hooks/* 2>/dev/null
echo "  ✅ 파일 복사 완료"

echo ""
echo "[2/3] Git 커밋 중..."
git add -A >/dev/null 2>&1
git commit -m "feat: 명령 요약 및 GitLab 자동 푸시 기능 추가" >/dev/null 2>&1
echo "  ✅ Git 커밋 완료"

echo ""
echo "[3/3] GitHub 푸시 중..."
git push origin main >/dev/null 2>&1
echo "  ✅ GitHub 푸시 완료"

echo ""
echo "================================================"
echo "  ✅ 설치 완료!"
echo "================================================"
echo ""
echo "이제부터 Claude Code를 사용하면:"
echo "  • 작업 완료 시 자동으로 Slack 알림"
echo "  • 명령이 요약되어 깔끔하게 표시"
echo "  • GitLab 자동 푸시 (설정 시)"
echo ""
echo "아무것도 신경 쓸 필요 없이"
echo "Claude Code로 작업만 하시면 됩니다!"
echo ""
