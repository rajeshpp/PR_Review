import subprocess

def run_linter(file_path):
    result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
    return result.stdout

def run_security_check(file_path):
    result = subprocess.run(["bandit", "-r", file_path], capture_output=True, text=True)
    return result.stdout

def main():
    file_path = "sample.py"
    print("Linting Results:")
    print(run_linter(file_path))

    print("\nSecurity Scan Results are:")
    print(run_security_check(file_path))

if __name__ == "__main__":
    main()
