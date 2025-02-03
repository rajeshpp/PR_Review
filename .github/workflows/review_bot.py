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


def get_pr_files():
    """Fetches changed files in the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def parse_flake8_report():
    """Parses Flake8 linting results and generates comments."""
    comments = []
    try:
        with open("/home/runner/work/PR_Review/PR_Review/flake8_report.json") as f:
            data = json.load(f)
            for file, errors in data.items():
                for error in errors:
                    comments.append(
                        {
                            "path": file,
                            "position": 1,
                            "line_number": error['line_number'],
                            "body": f"[Flake8] {error['text']}",
                        }
                    )
    except (FileNotFoundError, json.JSONDecodeError):
        print("Flake8 report not found or invalid format.")
    return comments


def parse_bandit_report():
    """Parses Bandit security scan results and generates comments."""
    comments = []
    try:
        with open("bandit_report.json") as f:
            data = json.load(f)
            for issue in data.get("results", []):
                comments.append(
                    {
                        "path": issue["filename"],
                        "position": 1,
                        "severity": issue['issue_severity'],
                        "body": f"[Bandit] {issue['issue_text']}",
                    }
                )
    except (FileNotFoundError, json.JSONDecodeError):
        print("Bandit report not found or invalid format.")
    return comments


def post_review_comments(comments):
    """Posts review comments to the PR using the GitHub API."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"
    for comment in comments:
        response = requests.post(url, headers=HEADERS, json=comment)
        if response.status_code != 201:
            print(f"Failed to post comment: {response.text}")


if __name__ == "__main__":
    comments = parse_flake8_report() #+ parse_bandit_report()
    if comments:
        post_review_comments(comments)
    else:
        print("No issues found, skipping comments.")
