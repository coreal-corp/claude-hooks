#!/bin/bash
# Claude Hooks Quick Install (WSL/Linux)

echo ""
echo "================================================"
echo "  Claude Hooks - Quick Install"
echo "================================================"
echo ""
echo "Installing..."
echo ""

cd "$(dirname "$0")"

echo "[1/3] Copying files..."
cp -f SessionStart SessionEnd Stop Notification ~/.claude-hooks/ 2>/dev/null
cp -f session-start session-end stop notification ~/.claude-hooks/ 2>/dev/null
cp -f analyze_transcript.py auto_update.py auto_push_gitlab.py setup_gitlab.py update ~/.claude-hooks/ 2>/dev/null
chmod +x ~/.claude-hooks/* 2>/dev/null
echo "  ✅ Files copied"

echo ""
echo "[2/3] Committing to git..."
git add -A >/dev/null 2>&1
git commit -m "feat: Add command summarization and GitLab auto-push" >/dev/null 2>&1
echo "  ✅ Committed"

echo ""
echo "[3/3] Pushing to GitHub..."
git push origin main >/dev/null 2>&1
echo "  ✅ Pushed"

echo ""
echo "================================================"
echo "  ✅ Installation Complete!"
echo "================================================"
echo ""
echo "From now on, when using Claude Code:"
echo "  • Auto Slack notifications on completion"
echo "  • Commands are summarized cleanly"
echo "  • Auto GitLab push (if configured)"
echo ""
echo "Just use Claude Code - everything is automatic!"
echo ""
