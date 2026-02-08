import os
import json
import re
from pathlib import Path
from collections import defaultdict

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "env",
    "node_modules",
    ".idea",
    ".vscode",
    "migrations",
    "static",
    "media",
    ".pytest_cache",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
}

IGNORE_FILES = {
    "__init__.py",
    "__pycache__",
    ".DS_Store",
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".egg",
    ".whl",
    ".cache",
    ".coverage",
}

def analyze_repo(repo_path: str) -> dict:
    """
    Analyze a repository and return detailed, structured data.
    """
    llm_context = build_llm_context(repo_path)
    file_tree = build_file_tree(repo_path)
    
    return {
        "project_name": os.path.basename(repo_path),
        "llm_context": llm_context,
        "readme_assets": {
            "file_tree": file_tree,
            "project_type": llm_context.get("project_type", "Unknown"),
            "framework": llm_context.get("framework", "Unknown"),
        },
    }

def detect_project_type(repo_path: str) -> str:
    """Detect the type of project."""
    files = os.listdir(repo_path)
    
  
    if any(f == 'manage.py' for f in files):
        return "Django"
    
 
    if any(f == 'app.py' and 'flask' in open(os.path.join(repo_path, f)).read().lower() for f in files if f.endswith('.py')):
        return "Flask"
    

    if os.path.exists(os.path.join(repo_path, 'requirements.txt')):
        with open(os.path.join(repo_path, 'requirements.txt'), 'r') as f:
            content = f.read()
            if 'fastapi' in content.lower():
                return "FastAPI"
    
  
    if any(f == 'go.mod' for f in files):
        return "Go"
    
  
    if any(f == 'package.json' for f in files):
        return "Node.js"
    
   
    if any(f == 'requirements.txt' for f in files) or any(f.endswith('.py') for f in files):
        return "Python"
    
    return "General"

def detect_framework(repo_path: str) -> str:
    """Detect specific framework."""
    project_type = detect_project_type(repo_path)
    
    if project_type == "Django":
        
        req_file = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                content = f.read()
                if 'djangorestframework' in content.lower():
                    return "Django REST Framework"
        return "Django"
    
    elif project_type == "Go":
        return "Go Standard Library"
    
    return project_type

def build_llm_context(repo_path: str) -> dict:
    """Build comprehensive LLM context with detailed analysis."""
    context = {
        "project_type": detect_project_type(repo_path),
        "framework": detect_framework(repo_path),
        "languages": [],
        "dependency_files": [],
        "entry_points": [],
        "config_files": [],
        "test_dirs": [],
        "top_level_dirs": [],
        "infra_files": [],
        "docker_info": {},
        "versions": {},
        "key_features": [],
        "database": None,
        "has_celery": False,
        "has_redis": False,
        "has_docker": False,
        "has_tests": False,
    }
    
  
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        rel_root = os.path.relpath(root, repo_path)
        depth = rel_root.count(os.sep)
        
        if depth == 0:
            context["top_level_dirs"] = sorted(dirs)
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            full_path = os.path.join(root, file)
            
        
            if file in {"requirements.txt", "package.json", "go.mod", "Pipfile", "pyproject.toml", "composer.json"}:
                context["dependency_files"].append(file)
                
              
                if file == "requirements.txt":
                    deps = parse_requirements(full_path)
                    if deps.get("django"):
                        context["versions"]["django"] = deps["django"]
                    if deps.get("celery"):
                        context["has_celery"] = True
                    if deps.get("redis"):
                        context["has_redis"] = True
                
                elif file == "go.mod":
                    go_version = parse_gomod(full_path)
                    if go_version:
                        context["versions"]["go"] = go_version
            
         
            if file in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Dockerfile.dev"}:
                context["infra_files"].append(file)
                context["has_docker"] = True
                
                if file == "Dockerfile":
                    docker_info = parse_dockerfile(full_path)
                    context["docker_info"].update(docker_info)
            
         
            if file in {"manage.py", "main.py", "main.go", "app.py", "index.js", "server.js", "application.py"}:
                context["entry_points"].append(os.path.relpath(full_path, repo_path))
            
   
            if file in {"settings.py", ".env", ".env.example", "config.py", "configuration.yaml", "config.yaml", ".config"}:
                context["config_files"].append(os.path.relpath(full_path, repo_path))
            
       
            if "test" in root.lower() or "tests" in root.lower() or file.startswith("test_") or file.endswith("_test.py"):
                context["has_tests"] = True
                if rel_root not in context["test_dirs"]:
                    context["test_dirs"].append(rel_root)
            
        
            if "models.py" in file or "schema.prisma" in file or "migrations" in root:
                context["database"] = "Detected"
    
  
    context["languages"] = detect_languages_from_files(repo_path)
    
 
    context["key_features"] = detect_key_features(context, repo_path)
    
    return context

def detect_languages_from_files(repo_path: str) -> list[str]:
    """Detect programming languages from file extensions."""
    extensions = set()
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                extensions.add(ext)
    
    lang_map = {
        '.py': 'Python',
        '.go': 'Go',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript (React)',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
    }
    
    languages = []
    for ext in extensions:
        if ext in lang_map:
            languages.append(lang_map[ext])
    
   
    seen = set()
    unique_langs = []
    for lang in languages:
        if lang not in seen:
            seen.add(lang)
            unique_langs.append(lang)
    
    return unique_langs

def detect_key_features(context: dict, repo_path: str) -> list[str]:
    """Detect key features of the project."""
    features = []
    project_type = context.get("project_type", "")
    
    if project_type == "Django":
        features.append("Django web framework")
        if context.get("has_celery"):
            features.append("Celery task queue")
        if context.get("has_redis"):
            features.append("Redis caching/messaging")
        if context.get("database"):
            features.append("Database models")
    
    elif project_type == "Go":
        features.append("Go standard library")
    
    if context.get("has_docker"):
        features.append("Docker containerization")
    
    if context.get("has_tests"):
        features.append("Test suite")
    
  
    if any("api" in f.lower() or "rest" in f.lower() for f in os.listdir(repo_path)):
        features.append("REST API")
    
    return features

def parse_dockerfile(path: str) -> dict:
    """Parse Dockerfile for useful information."""
    info = {
        "base_image": None,
        "exposed_ports": [],
        "workdir": None,
        "cmd": None,
    }
    
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('FROM '):
                    info["base_image"] = line[5:].strip()
                elif line.startswith('EXPOSE '):
                    ports = line[7:].strip().split()
                    info["exposed_ports"].extend(ports)
                elif line.startswith('WORKDIR '):
                    info["workdir"] = line[8:].strip()
                elif line.startswith('CMD '):
                    info["cmd"] = line[4:].strip()
    except:
        pass
    
    return info

def parse_gomod(path: str) -> str:
    """Parse go.mod for Go version."""
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('go '):
                    return line[3:].strip()
    except:
        pass
    return None

def parse_requirements(path: str) -> dict:
    """Parse requirements.txt for Python/Django versions."""
    info = {
        "django": None,
        "celery": False,
        "redis": False,
    }
    
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip().lower()
                if 'django' in line:
                    info["django"] = line.split('==')[-1] if '==' in line else line
                elif 'celery' in line:
                    info["celery"] = True
                elif 'redis' in line:
                    info["redis"] = True
    except:
        pass
    
    return info

def build_file_tree(repo_path: str, max_depth: int = 3) -> list[str]:
    """Build a detailed file tree with better formatting."""
    tree_lines = []
    
    def walk_dir(current_path, prefix="", depth=0):
        if depth > max_depth:
            return
        
        try:
            items = sorted(os.listdir(current_path))
        except:
            return
        
      
        items = [item for item in items 
                if item not in IGNORE_DIRS and 
                not item.startswith('.') and 
                not any(ignore in item for ignore in IGNORE_FILES)]
        
        for i, item in enumerate(items):
            item_path = os.path.join(current_path, item)
            rel_path = os.path.relpath(item_path, repo_path)
            is_last = i == len(items) - 1
            
            if os.path.isdir(item_path):
                tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{item}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                walk_dir(item_path, new_prefix, depth + 1)
            else:
                tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{item}")
    
    tree_lines.append(".")
    walk_dir(repo_path)
    
    return tree_lines