

def build_readme_prompt(analysis_data: dict, base_readme: str) -> str:
    tone_hint = infer_project_tone(analysis_data)

    return f"""
You are a senior software engineer writing a high-quality README.md.

TONE GUIDANCE:
{tone_hint}

RULES:
- Do NOT invent features.
- Do NOT assume project type.
- Use only provided analysis.
- File structure section is mandatory.
- Use proper Markdown headings (#, ##, ###).
- Add hashtags where appropriate.
- Suggest (not fabricate) visuals and demo links.

INPUT DATA:
Project name: {analysis_data.get("project_name")}
Languages: {analysis_data.get("languages")}
Dependencies: {analysis_data.get("dependencies")}
Docker support: {analysis_data.get("docker")}
File tree: {analysis_data.get("file_tree")}

EXISTING README (AUTO-GENERATED):
{base_readme}

REQUIRED SECTIONS:
- Project Purpose
- Functionality
- How to Use
- File Structure
- Visuals (suggest only)
- Demo Links (suggest only)
- Tech Stack
- Contribution Guidelines
- License

Return ONLY valid Markdown.
"""


def infer_project_tone(analysis_data: dict) -> str:
    languages = analysis_data.get("languages", [])
    deps = analysis_data.get("dependencies", {})
    docker = analysis_data.get("docker", {})

    if any(lang.lower() in ["python", "go", "java"] for lang in languages):
        return (
            "Use a backend-engineering tone. "
            "Emphasize APIs, services, data flow, background processing, "
            "configuration, and deployment considerations."
        )

    if any(lang.lower() in ["javascript", "typescript"] for lang in languages):
        return (
            "Use a product-focused tone. "
            "Emphasize usability, user interaction, components, and developer experience."
        )

    return (
        "Use a neutral engineering tone. "
        "Focus on clarity, structure, and maintainability."
    )
