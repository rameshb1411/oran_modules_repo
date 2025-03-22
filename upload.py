import os
import subprocess
import requests
import json

# Fetch GitHub credentials and repo details from environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "oran_modules_repo")  # Default repo name if not set
LOCAL_PATH = os.getenv("ORAN_LOCAL_PATH", r"C:\Users\Ramesh1\PycharmProjects\PythonProject2\.venv\oran_modules")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}"

if not GITHUB_USERNAME or not GITHUB_TOKEN:
    print("❌ Error: Please set GITHUB_USERNAME and GITHUB_TOKEN as environment variables.")
    exit(1)

def run_command(command, cwd=None):
    """Run a shell command and return its output."""
    try:
        process = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        if process.stdout.strip():
            print(f"✅ {process.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing: {command}\n{e.stderr}")

def repo_exists():
    """Check if the GitHub repository exists."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    return response.status_code == 200

def create_github_repo():
    """Create a new GitHub repository if it doesn't exist."""
    if repo_exists():
        print(f"⚠️ Repository '{REPO_NAME}' already exists. Using existing repo.")
        return f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"name": REPO_NAME, "private": False}  # Change to True for a private repo

    response = requests.post("https://api.github.com/user/repos", headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        print(f"✅ GitHub repository '{REPO_NAME}' created successfully!")
        return f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    else:
        print(f"❌ Failed to create repository: {response.json()}")
        exit(1)

def setup_git_repo(repo_url):
    """Initialize or update a Git repository and push changes."""
    if not os.path.exists(LOCAL_PATH):
        print(f"❌ Error: Local path '{LOCAL_PATH}' does not exist.")
        exit(1)

    os.chdir(LOCAL_PATH)  # Change directory to oran_modules

    if os.path.exists(os.path.join(LOCAL_PATH, ".git")):
        print("🔄 Existing Git repository found. Pulling latest changes...")
        run_command("git pull origin main", cwd=LOCAL_PATH)
    else:
        print("🚀 Initializing new Git repository...")
        run_command("git init", cwd=LOCAL_PATH)
        run_command("git branch -m main", cwd=LOCAL_PATH)
        run_command(f"git remote add origin {repo_url}", cwd=LOCAL_PATH)

    run_command("git add .", cwd=LOCAL_PATH)

    # Check for uncommitted changes
    status_output = subprocess.run("git status --porcelain", shell=True, cwd=LOCAL_PATH, capture_output=True, text=True)
    if status_output.stdout.strip():
        run_command('git commit -m "Updated ORAN modules"', cwd=LOCAL_PATH)
        run_command("git push -u origin main", cwd=LOCAL_PATH)
        print("✅ Changes pushed successfully!")
    else:
        print("✅ No changes to commit. Repository is up to date.")

if __name__ == "__main__":
    repo_url = create_github_repo()
    setup_git_repo(repo_url)
