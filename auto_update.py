#!/usr/bin/env python3
"""
Auto Update Module for Claude Code Hooks
Automatically checks and updates hooks from GitHub repository
"""
import os
import sys
import subprocess
import time
import shutil
from pathlib import Path


def log_debug(message):
    """Write debug log"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    debug_log = Path('/tmp') / 'claude-hook-debug.log'
    try:
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [AUTO_UPDATE] {message}\n")
    except:
        pass


def load_env_file(env_path):
    """Load environment variables from .env file"""
    env_vars = {}
    if not os.path.exists(env_path):
        return env_vars

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def should_check_update(hooks_dir, check_interval):
    """Check if update check is needed based on last check time"""
    last_check_file = hooks_dir / '.last-update-check'

    if not last_check_file.exists():
        return True

    try:
        with open(last_check_file, 'r') as f:
            last_check = int(f.read().strip())

        current_time = int(time.time())
        elapsed = current_time - last_check

        if elapsed < check_interval:
            log_debug(f"Update check skipped ({elapsed}s ago, interval: {check_interval}s)")
            return False

        return True
    except:
        return True


def record_check_time(hooks_dir):
    """Record current time as last update check time"""
    last_check_file = hooks_dir / '.last-update-check'
    try:
        with open(last_check_file, 'w') as f:
            f.write(str(int(time.time())))
    except:
        pass


def is_git_repo(hooks_dir):
    """Check if directory is a git repository"""
    git_dir = hooks_dir / '.git'
    return git_dir.exists() and git_dir.is_dir()


def has_local_changes(hooks_dir):
    """Check if there are uncommitted local changes"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=hooks_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        return len(result.stdout.strip()) > 0
    except:
        return True  # Assume changes if check fails (safer)


def backup_hook_files(hooks_dir):
    """Backup hook files before update"""
    hook_files = ['SessionStart', 'SessionEnd', 'Stop', 'Notification', 'analyze_transcript.py']
    backup_dir = hooks_dir / '.backup'

    try:
        backup_dir.mkdir(exist_ok=True)

        for filename in hook_files:
            src = hooks_dir / filename
            if src.exists():
                dst = backup_dir / filename
                shutil.copy2(src, dst)

        log_debug("Backup created successfully")
        return True
    except Exception as e:
        log_debug(f"Backup failed: {str(e)}")
        return False


def restore_from_backup(hooks_dir):
    """Restore hook files from backup"""
    backup_dir = hooks_dir / '.backup'

    if not backup_dir.exists():
        return False

    try:
        for backup_file in backup_dir.glob('*'):
            if backup_file.is_file():
                dst = hooks_dir / backup_file.name
                shutil.copy2(backup_file, dst)

        log_debug("Restored from backup")
        return True
    except Exception as e:
        log_debug(f"Restore failed: {str(e)}")
        return False


def fetch_updates(hooks_dir):
    """Fetch updates from remote repository"""
    try:
        result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=hooks_dir,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            log_debug(f"Git fetch failed: {result.stderr}")
            return False

        # Check if there are new commits
        result = subprocess.run(
            ['git', 'rev-list', 'HEAD..origin/main', '--count'],
            cwd=hooks_dir,
            capture_output=True,
            text=True,
            timeout=5
        )

        new_commits = int(result.stdout.strip())
        return new_commits > 0
    except Exception as e:
        log_debug(f"Fetch error: {str(e)}")
        return False


def pull_updates(hooks_dir):
    """Pull updates from remote repository"""
    try:
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=hooks_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            log_debug(f"Git pull failed: {result.stderr}")
            return False, result.stderr

        log_debug("Git pull successful")
        return True, result.stdout
    except Exception as e:
        log_debug(f"Pull error: {str(e)}")
        return False, str(e)


def send_update_notification(env_vars, success, message):
    """Send update notification to Slack"""
    slack_token = env_vars.get('SLACK_BOT_TOKEN')
    slack_channel = env_vars.get('SLACK_CHANNEL_ID', 'C09J29WDSHK')

    if not slack_token:
        return

    import urllib.request
    import json

    if success:
        title = "🔄 Claude Hooks 자동 업데이트 완료"
        text = f"최신 버전으로 업데이트되었습니다.\n\n```\n{message[:200]}\n```"
    else:
        title = "⚠️ Claude Hooks 업데이트 실패"
        text = f"수동 업데이트가 필요합니다.\n\n에러: `{message[:200]}`"

    payload = {
        "channel": slack_channel.lstrip('#'),
        "text": title,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        ]
    }

    headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/json'
    }

    try:
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
    except:
        pass


def check_and_update():
    """Main auto-update function"""
    hooks_dir = Path.home() / '.claude-hooks'

    # Load environment variables
    env_file = Path.home() / '.ultrathink.env'
    env_vars = load_env_file(env_file)

    # Check if auto-update is enabled
    auto_update_enabled = env_vars.get('AUTO_UPDATE_ENABLED', 'true').lower() == 'true'

    if not auto_update_enabled:
        log_debug("Auto-update disabled")
        return

    # Check if it's a git repository
    if not is_git_repo(hooks_dir):
        log_debug("Not a git repository, skipping update")
        return

    # Check update interval
    check_interval = int(env_vars.get('UPDATE_CHECK_INTERVAL', '86400'))  # Default: 24 hours

    if not should_check_update(hooks_dir, check_interval):
        return

    log_debug("Starting update check...")

    # Check for local changes
    if has_local_changes(hooks_dir):
        log_debug("Local changes detected, skipping update")
        record_check_time(hooks_dir)  # Record anyway to avoid repeated checks
        return

    # Fetch updates
    has_updates = fetch_updates(hooks_dir)

    if not has_updates:
        log_debug("No updates available")
        record_check_time(hooks_dir)
        return

    log_debug("Updates available, starting pull...")

    # Backup before update
    if not backup_hook_files(hooks_dir):
        log_debug("Backup failed, aborting update")
        record_check_time(hooks_dir)
        return

    # Pull updates
    success, output = pull_updates(hooks_dir)

    if success:
        log_debug("Update successful")
        send_update_notification(env_vars, True, output)
    else:
        log_debug("Update failed, restoring backup")
        restore_from_backup(hooks_dir)
        send_update_notification(env_vars, False, output)

    # Record check time
    record_check_time(hooks_dir)


if __name__ == '__main__':
    # Can be called standalone for testing
    check_and_update()
