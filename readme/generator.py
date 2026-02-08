import os

def generate_base_readme(analysis_data: dict) -> str:
    llm_context = analysis_data.get("llm_context", {})
    project_name = analysis_data.get("project_name", "Project")
    project_type = llm_context.get("project_type", "Unknown")
    
    sections = []
    
    sections.append(f"# {project_name}\n")
    
    overview = generate_overview(llm_context)
    if overview:
        sections.append(f"## Project Overview\n\n{overview}\n")
    
    features = generate_features(llm_context)
    if features:
        sections.append(f"## Features\n\n{features}\n")
    
    tech_stack = generate_tech_stack(llm_context)
    if tech_stack:
        sections.append(f"## Tech Stack\n\n{tech_stack}\n")
    
    getting_started = generate_getting_started(llm_context)
    if getting_started:
        sections.append(f"## Getting Started\n\n{getting_started}\n")
    
    sections.append("## Project Structure\n\n*File structure will be shown here*\n")
    
    configuration = generate_configuration(llm_context)
    if configuration:
        sections.append(f"## Configuration\n\n{configuration}\n")
    
    development = generate_development(llm_context)
    if development:
        sections.append(f"## Development\n\n{development}\n")
    
    api_docs = generate_api_docs(llm_context)
    if api_docs:
        sections.append(f"## API Documentation\n\n{api_docs}\n")
    
    deployment = generate_deployment(llm_context)
    if deployment:
        sections.append(f"## Deployment\n\n{deployment}\n")
    
    sections.append("## Contributing\n\nContributions are welcome! Please read our contributing guidelines.\n")
    
    sections.append("## License\n\n*License information*\n")
    
    return "\n".join(sections)

def generate_overview(llm_context: dict) -> str:
    project_type = llm_context.get("project_type", "")
    
    descriptions = {
        "Django": "A Django web application",
        "Django REST Framework": "A Django REST API",
        "Flask": "A Flask web application",
        "FastAPI": "A FastAPI web application",
        "Go": "A Go application",
        "Node.js": "A Node.js application",
        "Python": "A Python application",
    }
    
    base = descriptions.get(project_type, "A software project")
    
    specifics = []
    if llm_context.get("has_docker"):
        specifics.append("containerized with Docker")
    if llm_context.get("has_celery"):
        specifics.append("with Celery for background tasks")
    if llm_context.get("database"):
        specifics.append("with database integration")
    
    if specifics:
        base += " " + ", ".join(specifics)
    
    return base + "."

def generate_features(llm_context: dict) -> str:
    features = llm_context.get("key_features", [])
    
    if not features:
        return ""
    
    lines = []
    for feature in features:
        lines.append(f"- {feature}")
    
    return "\n".join(lines)

def generate_tech_stack(llm_context: dict) -> str:
    lines = []
    
    languages = llm_context.get("languages", [])
    if languages:
        lines.append("### Languages")
        for lang in languages:
            lines.append(f"- {lang}")
    
    framework = llm_context.get("framework", "")
    if framework and framework != "Unknown":
        lines.append("\n### Framework")
        lines.append(f"- {framework}")
    
    dep_files = llm_context.get("dependency_files", [])
    if dep_files:
        lines.append("\n### Dependency Management")
        for dep_file in dep_files:
            lines.append(f"- `{dep_file}`")
    
    infra_files = llm_context.get("infra_files", [])
    if infra_files:
        lines.append("\n### Infrastructure")
        for infra in infra_files:
            lines.append(f"- `{infra}`")
    
    if llm_context.get("database"):
        lines.append("\n### Database")
        lines.append("- Database models detected")
    
    return "\n".join(lines)

def generate_getting_started(llm_context: dict) -> str:
    project_type = llm_context.get("project_type", "")
    
    if project_type == "Django":
        return """### Prerequisites
- Python 3.8+
- pip
- (Optional) Virtual environment

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### Running Locally
```bash
python manage.py runserver
```
Visit http://localhost:8000"""
    
    elif project_type == "Go":
        return """### Prerequisites
- Go 1.16+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Build the project
go build

# Run the application
./<project-name>
```"""
    
    elif project_type == "Node.js":
        return """### Prerequisites
- Node.js 14+
- npm or yarn

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Install dependencies
npm install

# Run the application
npm start
```"""
    
    return ""

def generate_configuration(llm_context: dict) -> str:
    config_files = llm_context.get("config_files", [])
    
    if not config_files:
        return ""
    
    lines = ["### Configuration Files"]
    
    for config in config_files:
        if "settings.py" in config:
            lines.append(f"- `{config}`: Django project settings")
        elif ".env" in config:
            lines.append(f"- `{config}`: Environment variables")
        else:
            lines.append(f"- `{config}`: Configuration file")
    
    lines.append("\n### Environment Setup")
    lines.append("```bash")
    lines.append("# Copy example environment file")
    lines.append("cp .env.example .env")
    lines.append("")
    lines.append("# Edit with your settings")
    lines.append("nano .env  # or use your preferred editor")
    lines.append("```")
    
    return "\n".join(lines)

def generate_development(llm_context: dict) -> str:
    project_type = llm_context.get("project_type", "")
    
    if project_type == "Django":
        lines = [
            "### Running Tests",
            "```bash",
            "python manage.py test",
            "```",
            "",
            "### Database Migrations",
            "```bash",
            "# Create new migrations",
            "python manage.py makemigrations",
            "",
            "# Apply migrations",
            "python manage.py migrate",
            "```",
            "",
            "### Development Server",
            "```bash",
            "python manage.py runserver",
            "```",
        ]
        
        if llm_context.get("has_celery"):
            lines.extend([
                "",
                "### Celery Worker",
                "```bash",
                "celery -A your_project worker --loglevel=info",
                "```",
            ])
        
        if llm_context.get("has_tests"):
            lines.extend([
                "",
                "### Test Coverage",
                "```bash",
                "coverage run manage.py test",
                "coverage report",
                "```",
            ])
        
        return "\n".join(lines)
    
    return ""

def generate_api_docs(llm_context: dict) -> str:
    project_type = llm_context.get("project_type", "")
    
    if project_type in ["Django REST Framework", "FastAPI"]:
        return """### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API root |
| `/api/docs/` | GET | API documentation |

### Example Request
```bash
curl -X GET http://localhost:8000/api/
```"""
    
    elif "api" in str(llm_context.get("key_features", [])).lower():
        return "REST API endpoints are available. Check the source code for specific endpoints."
    
    return ""

def generate_deployment(llm_context: dict) -> str:
    if not llm_context.get("has_docker"):
        return ""
    
    lines = ["### Docker Deployment"]
    
    docker_info = llm_context.get("docker_info", {})
    
    if docker_info.get("base_image"):
        lines.append(f"Base image: `{docker_info['base_image']}`")
    
    if docker_info.get("exposed_ports"):
        ports = ", ".join(docker_info["exposed_ports"])
        lines.append(f"Exposed ports: `{ports}`")
    
    lines.append("\n### Build and Run")
    lines.append("```bash")
    lines.append("# Build Docker image")
    lines.append("docker build -t myapp .")
    lines.append("")
    lines.append("# Run container")
    if docker_info.get("exposed_ports"):
        lines.append(f"docker run -p {docker_info['exposed_ports'][0]} myapp")
    else:
        lines.append("docker run myapp")
    lines.append("```")
    
    if "docker-compose" in str(llm_context.get("infra_files", [])):
        lines.append("\n### Docker Compose")
        lines.append("```bash")
        lines.append("docker-compose up -d")
        lines.append("```")
    
    return "\n".join(lines)
