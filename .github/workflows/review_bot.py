import json
import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_EVENT_PULL_REQUEST_NUMBER")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_pr_files():
    """Fetches changed files in the PR"""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def parse_flake8_report():
    """Parses Flake8 linting results"""
    comments = []
    with open("flake8_report.json") as f:
        data = json.load(f)
        for file, errors in data.items():
            for error in errors:
                comments.append({
                    "path": file,
                    "position": 1,  # GitHub requires a valid line number
                    "body": f"[Flake8] {error['message']} (line {error['line_number']})"
                })
    return comments

def parse_bandit_report():
    """Parses Bandit security scan results"""
    comments = []
    with open("bandit_report.json") as f:
        data = json.load(f)
        for issue in data.get("results", []):
            comments.append({
                "path": issue["filename"],
                "position": 1,
                "body": f"[Bandit] {issue['issue_text']} (Severity: {issue['issue_severity']})"
            })
    return comments

def post_review_comments(comments):
    """Posts review comments to the PR"""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"
    for comment in comments:
        requests.post(url, headers=HEADERS, json=comment)

if __name__ == "__main__":
    comments = parse_flake8_report() + parse_bandit_report()
    if comments:
        post_review_comments(comments)
    else:
        print("No issues found.")
