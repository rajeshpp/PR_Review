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


def get_latest_commit():
    """Fetch the latest commit SHA from the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/commits"
    response = requests.get(url, headers=HEADERS)
    commits = response.json()

    if response.status_code == 200 and commits:
        return commits[-1]["sha"]  # Get the latest commit SHA

    print(f"❌ Failed to fetch commits: {commits}")
    return None


COMMIT_ID = get_latest_commit()

if not COMMIT_ID:
    exit(1)  # Stop execution if commit ID is unavailable


def get_pr_files():
    """Fetch the list of modified files in the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()

    print(f"❌ Failed to fetch PR files: {response.json()}")
    return []


PR_FILES = get_pr_files()

# Mapping of file paths to their diff hunks
DIFF_HUNKS = {file["filename"]: file["patch"] for file in PR_FILES}


def parse_flake8_report():
    """Parse Flake8 report and generate PR comments."""
    comments = []
    try:
        with open("flake8_report.json") as f:
            data = json.load(f)

        for file, errors in data.items():
            print(1, file, errors)
            if file in DIFF_HUNKS:  # Ensure file exists in PR
                print(2, DIFF_HUNKS)
                for error in errors:
                    print(3, error)
                    comments.append(
                        {
                            "path": file,
                            "commit_id": COMMIT_ID,
                            "position": 1,  # Default position
                            "body": f"🔍 **Flake8 Warning:** {error['text']}",
                            "diff_hunk": DIFF_HUNKS[file],  # Attach diff context
                        }
                    )
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Flake8 report not found or invalid format.")

    return comments


def parse_bandit_report():
    """Parse Bandit security scan results and generate PR comments."""
    comments = []
    try:
        with open("bandit_report.json") as f:
            data = json.load(f)

        for issue in data.get("results", []):
            file = issue["filename"]
            if file in DIFF_HUNKS:
                comments.append(
                    {
                        "path": file,
                        "commit_id": COMMIT_ID,
                        "position": 1,
                        "body": (
                            f"🚨 **Bandit Security Issue:** {issue['issue_text']} "
                            f"(Severity: {issue['issue_severity']})"
                        ),
                        "diff_hunk": DIFF_HUNKS[file],
                    }
                )
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Bandit report not found or invalid format.")

    return comments


def post_review_comments(comments):
    """Post review comments to the GitHub PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"

    for comment in comments:
        response = requests.post(url, headers=HEADERS, json=comment)
        if response.status_code == 201:
            print(f"✅ Comment posted: {comment['body']}")
        else:
            print(f"❌ Failed to post comment: {response.json()}")


def post_general_pr_comment(comment):
    """Post a general PR comment if no line-specific issues exist."""
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
