import os
import subprocess
import requests
import json

# Fetch GitHub credentials and repo details from environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "oran_modules_repo")  # Default repo name if not set
LOCAL_PATH = os.getenv("ORAN_LOCAL_PATH", r"C:\Users\Ramesh1\PycharmProjects\PythonProject2\.venv\oran_modules")
GITHUB_API_URL = "https://api.github.com/user/repos"

if not GITHUB_USERNAME or not GITHUB_TOKEN:
    print("❌ Error: Please set GITHUB_USERNAME and GITHUB_TOKEN as environment variables.")
    exit(1)

def create_github_repo():
    """Create a new GitHub repository using the GitHub API."""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": REPO_NAME,
        "private": False,  # Change to True if you want a private repo
    }

    response = requests.post(GITHUB_API_URL, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        print(f"✅ GitHub repository '{REPO_NAME}' created successfully!")
        return f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    elif response.status_code == 422:
        print(f"⚠️ Repository '{REPO_NAME}' already exists. Using existing repo.")
        return f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    else:
        print(f"❌ Failed to create repository: {response.json()}")
        return None

def initialize_local_repo(repo_url):
    """Initialize local git repository and push contents to GitHub."""
    if not os.path.exists(LOCAL_PATH):
        print(f"❌ Error: Local path '{LOCAL_PATH}' does not exist.")
        return

    os.chdir(LOCAL_PATH)  # Change directory to oran_modules

    commands = [
        "git init",
        "git branch -m main",
        "git add .",
        'git commit -m "Initial commit with ORAN modules"',
        f"git remote add origin {repo_url}",
        "git push -u origin main"
    ]

    for cmd in commands:
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if process.returncode == 0:
            print(f"✅ Successfully executed: {cmd}")
        else:
            print(f"❌ Error in: {cmd}\n{process.stderr}")

if __name__ == "__main__":
    repo_url = create_github_repo()
    if repo_url:
        initialize_local_repo(repo_url)
