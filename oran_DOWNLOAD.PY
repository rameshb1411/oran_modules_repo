import os
import subprocess
import shutil
import concurrent.futures
from datetime import datetime


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    try:
        process = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        if process.stdout:
            log(process.stdout.strip(), "SUCCESS")
        if process.stderr:
            log(process.stderr.strip(), "ERROR")
    except subprocess.CalledProcessError as e:
        log(f"Error executing command: {command}\nError: {e.stderr}", "ERROR")


def setup_git_access():
    """Setup SSH or HTTPS access for ORAN Gerrit repositories."""
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    gerrit_username = os.getenv("GERRIT_USERNAME", "your_username")
    gerrit_email = os.getenv("GERRIT_EMAIL", "your_email@example.com")

    if not os.path.exists(ssh_key_path):
        log("Generating SSH Key...")
        run_command(f"ssh-keygen -t rsa -b 4096 -C \"{gerrit_email}\" -f ~/.ssh/id_rsa -N \"\"")
    else:
        log("SSH key already exists, skipping key generation.")

    if os.path.exists(ssh_key_path):
        with open(ssh_key_path, "r") as file:
            log("Add this SSH key to Gerrit:")
            log(file.read())
    else:
        log("SSH key not found. Please generate one and add it to Gerrit.", "ERROR")

    log("Testing SSH connection...")
    ssh_test_cmd = f"ssh -p 29418 {gerrit_username}@gerrit.o-ran-sc.org gerrit ls-projects"
    run_command(ssh_test_cmd)


def list_available_repos():
    """List available repositories in Gerrit."""
    gerrit_username = os.getenv("GERRIT_USERNAME", "your_username")
    ssh_list_cmd = f"ssh -p 29418 {gerrit_username}@gerrit.o-ran-sc.org gerrit ls-projects"
    result = subprocess.run(ssh_list_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        repos = result.stdout.strip().split("\n")
        log(f"Available repositories: {repos}")  # Debug log
        return repos
    else:
        log("Failed to retrieve repository list.", "ERROR")
        return []


def fix_permissions(path):
    """Fix permissions for cloned repositories."""
    log(f"Fixing permissions for {path}...")
    run_command(f"icacls \"{path}\" /grant Everyone:F /t /c /q")


def clone_repository(repo_name):
    """Clone a single ORAN repository and retry if empty."""
    gerrit_username = os.getenv("GERRIT_USERNAME", "your_username")
    repo_url = f"ssh://{gerrit_username}@gerrit.o-ran-sc.org:29418/{repo_name}.git"
    repo_path = os.path.join("oran_modules", repo_name.replace("/", "-"))

    def is_repo_empty(path):
        return not os.listdir(path) if os.path.exists(path) else True

    if os.path.exists(repo_path) and not is_repo_empty(repo_path):
        log(f"Updating {repo_name}...")
        run_command("git pull", cwd=repo_path)
        return

    log(f"Cloning {repo_name}...")
    run_command(f"GIT_CLONE_PROTECTION_ACTIVE=false git clone {repo_url} {repo_path}")
    if is_repo_empty(repo_path):
        log(f"Repository {repo_name} is empty. Retrying...")
        shutil.rmtree(repo_path, ignore_errors=True)
        run_command(f"GIT_CLONE_PROTECTION_ACTIVE=false git clone {repo_url} {repo_path}")

    fix_permissions(repo_path)
    run_command("git switch -c main || git checkout main", cwd=repo_path)


def clone_oran_modules():
    """Clone ORAN open-source modules from Gerrit repositories in parallel."""
    available_repos = list_available_repos()
    os.makedirs("oran_modules", exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(clone_repository, available_repos)


def setup_environment():
    """Set required environment variables for ORAN."""
    env_vars = {
        "ORAN_HOME": os.path.abspath("oran_modules"),
        "ORAN_REPO": "https://gerrit.o-ran-sc.org/r/",
        "GIT_SSL_NO_VERIFY": "1"
    }

    for key, value in env_vars.items():
        os.environ[key] = value
        log(f"Set {key}={value}")


def create_new_repo():
    """Create a new Git repository and upload ORAN modules."""
    new_repo_url = os.getenv("NEW_REPO_URL", "https://your-default-repository-url.git")
    new_repo_dir = "oran_repo"

    if os.path.exists(new_repo_dir):
        shutil.rmtree(new_repo_dir)

    os.makedirs(new_repo_dir)
    run_command("git init", cwd=new_repo_dir)
    run_command("git branch -m main", cwd=new_repo_dir)
    run_command(f"git remote add origin {new_repo_url}", cwd=new_repo_dir)

    for module in os.listdir("oran_modules"):
        shutil.move(os.path.join("oran_modules", module), new_repo_dir)

    run_command("git add .", cwd=new_repo_dir)
    run_command("git commit -m 'Initial commit with ORAN modules'", cwd=new_repo_dir)
    run_command("git push -u origin main", cwd=new_repo_dir)


if __name__ == "__main__":
    try:
        setup_git_access()
        clone_oran_modules()
        setup_environment()
        create_new_repo()
        log("ORAN modules downloaded and pushed to your new repository successfully!", "SUCCESS")
    except Exception as e:
        log(f"An error occurred: {e}", "ERROR")
