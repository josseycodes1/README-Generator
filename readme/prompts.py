import json

def build_readme_prompt(analysis_data: dict, base_readme: str) -> str:
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
    
    purpose_instruction = """
CRITICAL: You MUST explain WHAT THE PROJECT DOES, not just its technical stack.
Look at the project name, file structure, and entry points to infer the actual functionality.

Examples of good vs bad project descriptions:

BAD (only technical):
"This is a Django REST API with Celery and Redis."

GOOD (explains purpose):
"This is a README generator API that automatically creates documentation for GitHub repositories.
Users submit repository URLs, and the system clones, analyzes, and generates professional README files."

BAD (generic):
"A Django web application with database models."

GOOD (specific):
"A wallet management backend service that provides REST APIs for creating wallets,
processing transactions, and managing user balances."

Use this pattern for ALL project descriptions:
1. WHAT it does (the main functionality)
2. WHO it's for (target users)
3. HOW it works (brief workflow)
4. WHY it exists (problem it solves)
"""
    
    prompt = f"""
SYSTEM:
You are an expert technical writer and senior software engineer specializing in {project_type} projects.
Your task is to enhance and complete a README.md file for a {project_type} project using {framework}.

{purpose_instruction}

IMPORTANT RULES:
1. DO NOT include the file tree - it will be added separately
2. DO NOT use placeholders like "TODO", "TBD", "will be added"
3. DO NOT invent features or technologies not present in the analysis
4. BE SPECIFIC and ACTIONABLE - provide exact commands and steps
5. EXPLAIN WHAT THE PROJECT ACTUALLY DOES based on its structure
6. WRITE for developers who need to USE the project immediately
7. USE CORRECT COMMANDS for {project_type} projects
8. USE PROPER MARKDOWN PARAGRAPH FORMATTING: Use TWO newlines between paragraphs

PROJECT ANALYSIS (authoritative facts only):
```json
{json.dumps(clean_context, indent=2)}
```

BASE README (generated from static analysis):
{base_readme}

YOUR TASK:
Enhance this README to be production-ready. Focus on:

Explain the purpose - What does this project actually DO? What problem does it solve?
Infer functionality - Based on folder names (like "generator", "analysis", "readme", "wallet", "api_keys")
Describe workflow - How would someone use this project based on its structure?
Improve descriptions - Make them specific to this {project_type} project
Add concrete examples - Real commands, real code snippets for {project_type}
Fill in missing details - Based on the {project_type} ecosystem
Use proper Markdown - Headers, code blocks, lists, and PARAGRAPHS

HOW TO INFER PURPOSE FROM STRUCTURE:
"generator/" folder suggests something generates content
"analysis/" suggests data analysis or processing
"readme/" suggests README-related functionality
"wallet/" suggests financial/transaction features
"api_keys/" suggests API key management
"users/" suggests user management system
"config/" suggests configuration management

CRITICAL FORMATTING RULES:
Use TWO newlines (empty line) between paragraphs
Use ONE newline within lists, code blocks, and tables
Do NOT include the "Project Structure" section - it will be added automatically

OUTPUT REQUIREMENTS:
Return ONLY the enhanced README.md content in valid Markdown
Start with a clear explanation of WHAT THE PROJECT DOES
Keep all existing section headers from the base README
Improve content under each section
Add missing sections if needed
Make it look like a professional open-source project README
Use emojis in section headers (as shown in base README)
Ensure proper paragraph spacing with TWO newlines between paragraphs

Now enhance the README:
"""
    
    return prompt
