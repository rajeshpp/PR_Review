import os
import json
import requests

# GitHub environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# Fetch the latest commit ID
def get_latest_commit():
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/commits"
    response = requests.get(url, headers=HEADERS)
    commits = response.json()
    
    if response.status_code == 200 and commits:
        return commits[-1]["sha"]  # Get the latest commit SHA
    else:
        print(f"❌ Failed to fetch commits: {commits}")
        return None

COMMIT_ID = get_latest_commit()
if not COMMIT_ID:
    exit(1)  # Stop execution if commit ID is unavailable

# Fetch PR files & diff hunks
def get_pr_files():
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch PR files: {response.json()}")
        return []

PR_FILES = get_pr_files()

# Create a mapping of file paths to their diff hunks
DIFF_HUNKS = {file["filename"]: file["patch"] for file in PR_FILES}

# Parse Flake8 linting results
def parse_flake8_report():
    comments = []
    try:
        with open("flake8_report.json") as f:
            data = json.load(f)
            for file, errors in data.items():
                if file in DIFF_HUNKS:  # Ensure file exists in PR
                    for error in errors:
                        comments.append({
                            "path": file,
                            "commit_id": COMMIT_ID,
                            "position": 1,  # Default to first position if exact mapping is unavailable
                            "body": f"🔍 **Flake8 Warning:** {error['text']}",
                            "diff_hunk": DIFF_HUNKS[file],  # Attach diff context
                        })
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Flake8 report not found or has invalid format.")
    return comments

# Parse Bandit security scan results
def parse_bandit_report():
    comments = []
    try:
        with open("bandit_report.json") as f:
            data = json.load(f)
            for issue in data.get("results", []):
                file = issue["filename"]
                if file in DIFF_HUNKS:
                    comments.append({
                        "path": file,
                        "commit_id": COMMIT_ID,
                        "position": 1,
                        "body": f"🚨 **Bandit Security Issue:** {issue['issue_text']} (Severity: {issue['issue_severity']})",
                        "diff_hunk": DIFF_HUNKS[file],
                    })
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Bandit report not found or has invalid format.")
    return comments

# Post review comments to GitHub PR
def post_review_comments(comments):
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"

    for comment in comments:
        response = requests.post(url, headers=HEADERS, json=comment)
        if response.status_code == 201:
            print(f"✅ Comment posted: {comment['body']}")
        else:
            print(f"❌ Failed to post comment: {response.json()}")

# Post a general PR comment if no line-specific issues exist
def post_general_pr_comment(comment):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    data = {"body": comment}

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"✅ General PR comment posted: {comment}")
    else:
        print(f"❌ Failed to post general comment: {response.json()}")

if __name__ == "__main__":
    comments = parse_flake8_report() #+ parse_bandit_report()

    if comments:
        post_review_comments(comments)
    else:
        post_general_pr_comment("🎉 No linting or security issues found! Great job! 🚀")
