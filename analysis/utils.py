import os
import json

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
}

def analyze_repo(repo_path: str) -> dict:
    """
    Main entry point for repository analysis.
    """
    return {
        "project_name": get_project_name(repo_path),
        "languages": detect_languages(repo_path),
        "dependencies": get_dependencies(repo_path),
        "docker": has_docker(repo_path),
        "file_tree": build_file_tree(repo_path),
    }

def get_project_name(repo_path):
    return os.path.basename(repo_path)


def detect_languages(repo_path):
    languages = []

    if os.path.exists(os.path.join(repo_path, "requirements.txt")):
        languages.append("Python")

    if os.path.exists(os.path.join(repo_path, "package.json")):
        languages.append("JavaScript")

    return languages


def get_dependencies(repo_path):
    dependencies = {}

    req_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file) as f:
            dependencies["python"] = [
                line.strip() for line in f if line.strip()
            ]

    pkg_file = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_file):
        with open(pkg_file) as f:
            data = json.load(f)
            dependencies["node"] = list(data.get("dependencies", {}).keys())

    return dependencies


def has_docker(repo_path):
    return {
        "dockerfile": os.path.exists(os.path.join(repo_path, "Dockerfile")),
        "docker_compose": os.path.exists(
            os.path.join(repo_path, "docker-compose.yml")
        ),
    }


def build_file_tree(repo_path, max_depth=3):
    tree = []

    for root, dirs, files in os.walk(repo_path):
       
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        depth = root.replace(repo_path, "").count(os.sep)
        if depth > max_depth:
            continue

        for d in dirs:
            tree.append(os.path.relpath(os.path.join(root, d), repo_path))

        for f in files:
            tree.append(os.path.relpath(os.path.join(root, f), repo_path))

    return sorted(tree)

