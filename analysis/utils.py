import os
import json
from collections import defaultdict

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "env",
    "node_modules",
    ".idea",
    ".vscode",
}

IGNORE_FILES = {
    "__init__.py",
    ".DS_Store",
}


def analyze_repo(repo_path: str) -> dict:
    """
    Analyze a repository and return structured, deterministic data.
    """
    return {
        "project_name": os.path.basename(repo_path),
        "llm_context": build_llm_context(repo_path),
        "readme_assets": {
            "file_tree": build_file_tree(repo_path),
        },
    }


# =========================
# LLM CONTEXT (SAFE PAYLOAD)
# =========================

def build_llm_context(repo_path: str) -> dict:
    files_by_dir = defaultdict(list)
    top_level_dirs = set()
    dependency_files = []
    infra_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_root = os.path.relpath(root, repo_path)
        depth = rel_root.count(os.sep)

        if depth == 0:
            top_level_dirs.update(dirs)

        if depth > 1:
            continue  # keep payload shallow

        for file in files:
            if file in IGNORE_FILES:
                continue

            if file in {"requirements.txt", "package.json"}:
                dependency_files.append(file)

            if file in {"Dockerfile", "docker-compose.yml"}:
                infra_files.append(file)

            if depth == 1:
                files_by_dir[os.path.basename(root)].append(file)

    return {
        "languages": detect_languages(repo_path),
        "dependency_files": sorted(set(dependency_files)),
        "top_level_dirs": sorted(top_level_dirs),
        "files_by_dir": dict(files_by_dir),
        "infra_files": sorted(set(infra_files)),
    }


def detect_languages(repo_path: str) -> list[str]:
    languages = []

    if os.path.exists(os.path.join(repo_path, "requirements.txt")):
        languages.append("Python")

    if os.path.exists(os.path.join(repo_path, "package.json")):
        languages.append("JavaScript")

    return languages


# =========================
# README ASSETS (LOCAL ONLY)
# =========================

def build_file_tree(repo_path: str, max_depth: int = 3) -> list[str]:
    tree = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        depth = root.replace(repo_path, "").count(os.sep)
        if depth > max_depth:
            continue

        for d in dirs:
            tree.append(os.path.relpath(os.path.join(root, d), repo_path))

        for f in files:
            if f not in IGNORE_FILES:
                tree.append(os.path.relpath(os.path.join(root, f), repo_path))

    return sorted(tree)
