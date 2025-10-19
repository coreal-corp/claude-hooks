#!/usr/bin/env python3
"""
Auto Push to GitLab Module
Automatically commits and pushes changes to GitLab when file changes are detected
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime


def log_debug(message):
    """Write debug log"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    debug_log = Path(tempfile.gettempdir()) / 'claude-hook-debug.log'
    try:
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [GITLAB] {message}\n")
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


def is_git_repo():
    """Check if current directory is a git repository"""
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except:
        return False


def has_changes():
    """Check if there are uncommitted changes"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return len(result.stdout.strip()) > 0
    except:
        return False


def get_change_summary():
    """Get summary of file changes"""
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5
        )

        lines = result.stdout.strip().split('\n')
        modified = []
        added = []
        deleted = []

        for line in lines:
            if not line:
                continue
            status = line[:2]
            filename = line[3:].strip()

            if 'M' in status:
                modified.append(filename)
            elif 'A' in status or '??' in status:
                added.append(filename)
            elif 'D' in status:
                deleted.append(filename)

        summary = []
        if modified:
            summary.append(f"수정: {len(modified)}개")
        if added:
            summary.append(f"추가: {len(added)}개")
        if deleted:
            summary.append(f"삭제: {len(deleted)}개")

        return ', '.join(summary) if summary else '변경 없음'
    except:
        return '변경사항 확인 실패'


def get_gitlab_remote():
    """Check if GitLab remote is configured"""
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )

        for line in result.stdout.split('\n'):
            if 'gitlab' in line.lower() and '(push)' in line:
                remote_name = line.split()[0]
                return remote_name

        return None
    except:
        return None


def add_gitlab_remote(gitlab_url, remote_name='gitlab'):
    """Add GitLab remote to git repository"""
    try:
        subprocess.run(
            ['git', 'remote', 'add', remote_name, gitlab_url],
            capture_output=True,
            check=True,
            timeout=10
        )
        log_debug(f"GitLab remote added: {remote_name} -> {gitlab_url}")
        return True
    except subprocess.CalledProcessError as e:
        log_debug(f"Failed to add GitLab remote: {e.stderr.decode()}")
        return False


def remove_git_lock():
    """Remove git index.lock if it exists"""
    import os
    lock_file = '.git/index.lock'
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            log_debug("Removed stale index.lock file")
            return True
        except Exception as e:
            log_debug(f"Failed to remove index.lock: {str(e)}")
            return False
    return True


def commit_changes(commit_message=None):
    """Commit all changes with auto-generated message"""
    try:
        # Remove stale lock file if exists
        remove_git_lock()

        # Add all changes
        subprocess.run(
            ['git', 'add', '-A'],
            capture_output=True,
            check=True,
            timeout=10
        )

        # Generate commit message if not provided
        if not commit_message:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            summary = get_change_summary()
            commit_message = f"Auto-commit: {summary} ({timestamp})"

        # Commit
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            check=True,
            timeout=10
        )

        log_debug(f"Changes committed: {commit_message}")
        return True
    except subprocess.CalledProcessError as e:
        log_debug(f"Commit failed: {e.stderr.decode()}")
        return False


def push_to_gitlab(remote_name='gitlab', branch=None):
    """Push commits to GitLab"""
    try:
        # Get current branch if not specified
        if not branch:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            branch = result.stdout.strip()

        # Push to GitLab
        result = subprocess.run(
            ['git', 'push', remote_name, branch],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            log_debug(f"Successfully pushed to {remote_name}/{branch}")
            return True, f"Pushed to {remote_name}/{branch}"
        else:
            error_msg = result.stderr.strip()
            log_debug(f"Push failed: {error_msg}")
            return False, error_msg
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        log_debug(f"Push error: {error_msg}")
        return False, error_msg


def run_gitlab_setup():
    """Run GitLab setup wizard"""
    import subprocess

    script_dir = Path(__file__).parent
    setup_script = script_dir / 'setup_gitlab.py'

    if not setup_script.exists():
        log_debug("Setup wizard not found")
        return False

    try:
        # Run setup wizard interactively
        result = subprocess.run(
            [sys.executable, str(setup_script)],
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0
    except Exception as e:
        log_debug(f"Setup wizard error: {str(e)}")
        return False


def auto_push_to_gitlab(auto_setup=True):
    """
    Main function: Check for changes and auto-push to GitLab if enabled
    Args:
        auto_setup: If True, run setup wizard when GitLab is not configured
    Returns: (success: bool, message: str)
    """
    # Load environment variables
    env_file = Path.home() / '.ultrathink.env'
    env_vars = load_env_file(env_file)

    # Check if auto-push is enabled
    auto_push_enabled = env_vars.get('GITLAB_AUTO_PUSH_ENABLED', 'false').lower() == 'true'

    if not auto_push_enabled:
        log_debug("GitLab auto-push disabled")
        return False, "GitLab auto-push disabled"

    # Check if in git repository
    if not is_git_repo():
        log_debug("Not a git repository")
        return False, "Not a git repository"

    # Check for changes
    if not has_changes():
        log_debug("No file changes detected")
        return False, "No changes to push"

    # Get GitLab configuration
    gitlab_url = env_vars.get('GITLAB_REPO_URL', '').strip()
    gitlab_token = env_vars.get('GITLAB_ACCESS_TOKEN', '').strip()
    remote_name = env_vars.get('GITLAB_REMOTE_NAME', 'gitlab')

    # If GitLab URL not configured, offer to run setup
    if not gitlab_url:
        log_debug("GitLab URL not configured")

        if auto_setup and sys.stdin.isatty():
            # Interactive terminal - run setup wizard
            print("\n⚠️  GitLab repository not configured")
            print("Would you like to set up GitLab auto-push now?")
            response = input("Run setup wizard? [Y/n]: ").strip().lower()

            if response != 'n':
                if run_gitlab_setup():
                    # Reload environment variables after setup
                    env_vars = load_env_file(env_file)
                    gitlab_url = env_vars.get('GITLAB_REPO_URL', '').strip()
                    gitlab_token = env_vars.get('GITLAB_ACCESS_TOKEN', '').strip()

                    if not gitlab_url:
                        return False, "Setup incomplete - GitLab URL still not set"
                else:
                    return False, "Setup wizard failed or cancelled"
            else:
                return False, "GitLab not configured. Run: python3 ~/.claude-hooks/setup_gitlab.py"
        else:
            return False, "GitLab URL not configured. Run: python3 ~/.claude-hooks/setup_gitlab.py"

    # Check/add GitLab remote
    current_remote = get_gitlab_remote()
    if not current_remote:
        # Add GitLab remote with token if provided
        if gitlab_token:
            # Insert token into URL
            if 'https://' in gitlab_url:
                gitlab_url_with_token = gitlab_url.replace('https://', f'https://oauth2:{gitlab_token}@')
            else:
                gitlab_url_with_token = gitlab_url
        else:
            gitlab_url_with_token = gitlab_url

        if not add_gitlab_remote(gitlab_url_with_token, remote_name):
            return False, "Failed to add GitLab remote"
        current_remote = remote_name

    # Commit changes
    commit_message = env_vars.get('GITLAB_AUTO_COMMIT_MESSAGE')
    if not commit_changes(commit_message):
        return False, "Failed to commit changes"

    # Push to GitLab
    success, message = push_to_gitlab(current_remote)

    if success:
        log_debug(f"Auto-push completed: {message}")
        return True, f"✅ {message}"
    else:
        log_debug(f"Auto-push failed: {message}")
        return False, f"❌ Push failed: {message}"


if __name__ == '__main__':
    # Can be called standalone for testing
    success, message = auto_push_to_gitlab()
    print(message)
    sys.exit(0 if success else 1)
