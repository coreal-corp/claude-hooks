#!/bin/bash
# Claude Hooks Quick Install (WSL/Linux)

cd "$(dirname "$0")"

echo ""
echo "================================================"
echo "  Claude Hooks - Interactive Setup"
echo "================================================"
echo ""

# Run interactive setup
python3 setup-complete.py

# If setup successful, commit and push
if [ $? -eq 0 ]; then
    echo ""
    echo "Committing changes to GitHub..."
    git add -A >/dev/null 2>&1
    git commit -m "feat: Add command summarization and GitLab auto-push" >/dev/null 2>&1
    git push origin main >/dev/null 2>&1
    echo "✅ Pushed to GitHub"
    echo ""
fi
