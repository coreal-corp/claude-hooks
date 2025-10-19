#!/usr/bin/env python3
"""
GitLab Repository Setup Wizard
Interactive tool to select or create GitLab repository for auto-push
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_step(step, text):
    """Print step message"""
    print(f"[{step}] {text}")


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


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


def save_env_var(env_path, key, value):
    """Save or update environment variable in .env file"""
    env_vars = load_env_file(env_path)
    env_vars[key] = value

    # Read existing file to preserve comments and structure
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # Update or add the variable
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            updated = True
            break

    if not updated:
        # Find GitLab section or add at end
        insert_index = len(lines)
        for i, line in enumerate(lines):
            if 'GitLab' in line and line.strip().startswith('#'):
                # Find next empty line or setting
                for j in range(i, len(lines)):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        insert_index = j + 1
                        break
                break
        lines.insert(insert_index, f"{key}={value}\n")

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def get_gitlab_api_url(gitlab_url):
    """Extract GitLab API URL from repository URL"""
    if 'gitlab.com' in gitlab_url:
        return 'https://gitlab.com/api/v4'
    else:
        # Self-hosted GitLab
        # Extract base URL (e.g., https://gitlab.example.com)
        parts = gitlab_url.split('/')
        base_url = f"{parts[0]}//{parts[2]}"
        return f"{base_url}/api/v4"


def test_gitlab_token(api_url, token):
    """Test if GitLab token is valid"""
    try:
        req = urllib.request.Request(
            f"{api_url}/user",
            headers={'PRIVATE-TOKEN': token}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            user_data = json.loads(response.read().decode('utf-8'))
            return True, user_data.get('username', 'Unknown')
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid token"
        return False, f"HTTP Error {e.code}"
    except Exception as e:
        return False, str(e)


def list_user_projects(api_url, token, page=1, per_page=20):
    """List user's GitLab projects"""
    try:
        url = f"{api_url}/projects?membership=true&per_page={per_page}&page={page}&order_by=updated_at"
        req = urllib.request.Request(
            url,
            headers={'PRIVATE-TOKEN': token}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            projects = json.loads(response.read().decode('utf-8'))
            return True, projects
    except Exception as e:
        return False, str(e)


def create_gitlab_project(api_url, token, project_name, visibility='private'):
    """Create new GitLab project"""
    try:
        data = {
            'name': project_name,
            'visibility': visibility,
            'initialize_with_readme': False
        }
        req = urllib.request.Request(
            f"{api_url}/projects",
            data=json.dumps(data).encode('utf-8'),
            headers={
                'PRIVATE-TOKEN': token,
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            project_data = json.loads(response.read().decode('utf-8'))
            return True, project_data
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        return False, error_msg
    except Exception as e:
        return False, str(e)


def interactive_setup():
    """Interactive GitLab setup wizard"""
    print_header("GitLab Auto-Push Setup Wizard")

    env_file = Path.home() / '.ultrathink.env'
    env_vars = load_env_file(env_file)

    # Step 1: Get GitLab instance URL
    print_step(1, "GitLab Instance")
    print("Which GitLab instance do you use?")
    print("  1) gitlab.com (default)")
    print("  2) Self-hosted GitLab")

    choice = input("\nChoice [1]: ").strip() or "1"

    if choice == "2":
        gitlab_base = input("GitLab URL (e.g., https://gitlab.example.com): ").strip()
        if not gitlab_base:
            print_error("GitLab URL is required")
            return False
    else:
        gitlab_base = "https://gitlab.com"

    api_url = get_gitlab_api_url(gitlab_base)
    print_info(f"API URL: {api_url}")

    # Step 2: Get/verify GitLab token
    print("\n" + "="*60)
    print_step(2, "GitLab Access Token")

    existing_token = env_vars.get('GITLAB_ACCESS_TOKEN', '').strip()
    if existing_token:
        print_info("Found existing token in .ultrathink.env")
        use_existing = input("Use existing token? [Y/n]: ").strip().lower()
        if use_existing != 'n':
            token = existing_token
        else:
            token = input("GitLab Access Token: ").strip()
    else:
        print("\nCreate a token at:")
        print(f"  {gitlab_base}/-/profile/personal_access_tokens")
        print("\nRequired scopes:")
        print("  - api (full API access)")
        print("  - write_repository (push code)")
        token = input("\nGitLab Access Token: ").strip()

    if not token:
        print_error("Token is required")
        return False

    # Verify token
    print("\nVerifying token...", end=" ")
    valid, result = test_gitlab_token(api_url, token)
    if not valid:
        print()
        print_error(f"Token verification failed: {result}")
        return False

    print_success(f"Token valid! User: {result}")

    # Save token
    save_env_var(env_file, 'GITLAB_ACCESS_TOKEN', token)

    # Step 3: Select or create project
    print("\n" + "="*60)
    print_step(3, "Select or Create Repository")

    # Get current directory name as default project name
    current_dir = os.path.basename(os.getcwd())

    print("\nOptions:")
    print("  1) Select from existing repositories")
    print("  2) Create new repository")

    choice = input("\nChoice [1]: ").strip() or "1"

    selected_repo_url = None

    if choice == "1":
        # List existing projects
        print("\nFetching your repositories...")
        success, projects = list_user_projects(api_url, token)

        if not success:
            print_error(f"Failed to fetch projects: {projects}")
            return False

        if not projects:
            print_info("No repositories found. Let's create one!")
            choice = "2"  # Fall through to create
        else:
            print(f"\nFound {len(projects)} repositories:\n")
            for i, proj in enumerate(projects, 1):
                visibility = "🔒" if proj['visibility'] == 'private' else "🔓"
                print(f"  {i}) {visibility} {proj['path_with_namespace']}")
                print(f"      {proj['web_url']}")

            print(f"\n  0) Create new repository")

            while True:
                try:
                    selection = input(f"\nSelect repository [1-{len(projects)}, 0 for new]: ").strip()
                    selection = int(selection)

                    if selection == 0:
                        choice = "2"  # Create new
                        break
                    elif 1 <= selection <= len(projects):
                        selected_project = projects[selection - 1]
                        selected_repo_url = selected_project['http_url_to_repo']
                        print_success(f"Selected: {selected_project['path_with_namespace']}")
                        break
                    else:
                        print_error(f"Please enter a number between 0 and {len(projects)}")
                except ValueError:
                    print_error("Please enter a valid number")

    if choice == "2":
        # Create new repository
        print("\n" + "-"*60)
        print("Create New Repository")
        print("-"*60)

        project_name = input(f"\nRepository name [{current_dir}]: ").strip() or current_dir

        print("\nVisibility:")
        print("  1) private (recommended)")
        print("  2) public")
        visibility_choice = input("Choice [1]: ").strip() or "1"
        visibility = 'private' if visibility_choice == "1" else 'public'

        print(f"\nCreating repository '{project_name}' ({visibility})...", end=" ")
        success, result = create_gitlab_project(api_url, token, project_name, visibility)

        if not success:
            print()
            print_error(f"Failed to create repository: {result}")
            return False

        print_success("Created!")
        selected_repo_url = result['http_url_to_repo']
        print_info(f"Repository URL: {result['web_url']}")

    # Step 4: Save configuration
    print("\n" + "="*60)
    print_step(4, "Saving Configuration")

    save_env_var(env_file, 'GITLAB_REPO_URL', selected_repo_url)
    save_env_var(env_file, 'GITLAB_AUTO_PUSH_ENABLED', 'true')

    print_success("Configuration saved to ~/.ultrathink.env")

    # Summary
    print("\n" + "="*60)
    print_header("✅ Setup Complete!")

    print("Configuration:")
    print(f"  GitLab URL: {selected_repo_url}")
    print(f"  Auto-push: Enabled")
    print(f"\nThe hooks will now automatically push changes to GitLab")
    print(f"when SessionEnd or Stop events occur.\n")

    # Test push option
    test = input("Test push now? [y/N]: ").strip().lower()
    if test == 'y':
        print("\nTesting GitLab push...")
        script_dir = Path(__file__).parent
        auto_push_script = script_dir / 'auto_push_gitlab.py'

        if auto_push_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(auto_push_script)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print_error(result.stderr)
        else:
            print_error("auto_push_gitlab.py not found")

    return True


def main():
    """Main entry point"""
    try:
        if not interactive_setup():
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
