import json

def build_readme_prompt(analysis_data: dict, base_readme: str) -> str:
    """
    Build a smart prompt for README generation WITHOUT file tree.
    """
    llm_context = analysis_data.get("llm_context", {})
    

    project_type = llm_context.get("project_type", "Unknown")
    framework = llm_context.get("framework", "Unknown")
    
   
    clean_context = {
        "project_type": project_type,
        "framework": framework,
        "languages": llm_context.get("languages", []),
        "key_features": llm_context.get("key_features", []),
        "dependency_files": llm_context.get("dependency_files", []),
        "infra_files": llm_context.get("infra_files", []),
        "config_files": llm_context.get("config_files", []),
        "entry_points": llm_context.get("entry_points", []),
        "docker_info": llm_context.get("docker_info", {}),
        "versions": llm_context.get("versions", {}),
        "has_celery": llm_context.get("has_celery", False),
        "has_redis": llm_context.get("has_redis", False),
        "has_docker": llm_context.get("has_docker", False),
        "has_tests": llm_context.get("has_tests", False),
        "database": llm_context.get("database", None),
    }
    
   
    language_instructions = ""
    if project_type == "Go":
        language_instructions = """
For Go projects, use commands like:
- "go mod download" to install dependencies
- "go build" to build the project  
- "go run main.go" to run the application
- "go test ./..." to run tests
"""
    elif project_type == "Node.js":
        language_instructions = """
For Node.js projects, use commands like:
- "npm install" or "yarn install" to install dependencies
- "npm start" or "yarn start" to run the application
- "npm test" or "yarn test" to run tests
"""
    elif project_type in ["Django", "Python"]:
        language_instructions = """
For Python/Django projects, use commands like:
- "pip install -r requirements.txt" to install dependencies
- "python manage.py runserver" to run Django
- "python manage.py test" to run tests
- "python -m pytest" for pytest
"""
    
    prompt = f"""
SYSTEM:
You are an expert technical writer and senior software engineer specializing in {project_type} projects.
Your task is to enhance and complete a README.md file for a {project_type} project using {framework}.

IMPORTANT RULES:
1. DO NOT include the file tree - it will be added separately
2. DO NOT use placeholders like "TODO", "TBD", "will be added"
3. DO NOT invent features or technologies not present in the analysis
4. BE SPECIFIC and ACTIONABLE - provide exact commands and steps
5. WRITE for developers who need to USE the project immediately
6. USE CORRECT COMMANDS for {project_type} projects

{language_instructions}

PROJECT ANALYSIS (authoritative facts only):
```json
{json.dumps(clean_context, indent=2)}
```

BASE README (generated from static analysis):
{base_readme}

YOUR TASK:
Enhance this README to be production-ready. Focus on:

1. **Improve descriptions** - Make them specific to this {project_type} project
2. **Add concrete examples** - Real commands, real code snippets for {project_type}
3. **Fill in missing details** - Based on the {project_type} ecosystem
4. **Improve structure** - Make it logical and easy to follow
5. **Add practical advice** - Troubleshooting, common issues for {project_type}
6. **Use proper Markdown** - Headers, code blocks, lists

CRITICAL: Do NOT include the "Project Structure" section - it will be added automatically with the actual file tree.

EXAMPLE OF CONCRETE VS GENERIC:
- Generic: "Install dependencies"
- Concrete for Python: "pip install -r requirements.txt"
- Concrete for Node.js: "npm install"
- Concrete for Go: "go mod download"

- Generic: "Run the server"
- Concrete for Django: "python manage.py runserver 0.0.0.0:8000"
- Concrete for Go: "go run main.go"
- Concrete for Node.js: "npm start"

OUTPUT REQUIREMENTS:
- Return ONLY the enhanced README.md content in valid Markdown
- Keep all existing section headers from the base README
- Improve content under each section
- Add missing sections if needed
- Make it look like a professional open-source project README
- Use emojis in section headers (as shown in base README)

Now enhance the README:
"""
    
    return prompt
