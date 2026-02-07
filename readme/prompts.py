def build_readme_prompt(analysis_data: dict, base_readme: str) -> str:
    """
    Build a strict, production-grade prompt for README generation.
    The LLM must rely ONLY on verified repository signals.
    """

    return f"""
SYSTEM:
You are a senior backend engineer and technical writer.

Your task is to generate a high-quality, production-ready README.md
for a real software repository.

Rules:
- Do NOT use placeholders like "will be updated", "example", or "TBD"
- Do NOT invent technologies, tools, commands, or features
- Do NOT assume project intent beyond detected signals
- Do NOT describe files or folders not present in the provided structure
- Every section must be concrete, actionable, and accurate

Quality bar:
- Comparable to a well-maintained open-source project
- Clear setup steps
- Clear tech stack
- Clear folder structure explanation
- Written for developers actively using the project

---

INPUTS:

Repository name:
{analysis_data.get("project_name")}

Detected repository signals (authoritative facts):
- Languages: {analysis_data.get("languages")}
- Frameworks: {analysis_data.get("frameworks")}
- Dependency files: {analysis_data.get("dependency_files")}
- Entry points: {analysis_data.get("entry_points")}
- Docker support: {analysis_data.get("docker")}
- Task queue: {analysis_data.get("task_queue")}
- Authentication: {analysis_data.get("auth")}

Locally generated file tree:
<PROVIDED SEPARATELY — DO NOT ANALYZE OR INFER FROM IT>

Base README generated from static analysis:
{base_readme}

---

REQUIRED OUTPUT:

Generate a README.md in valid Markdown with the following sections
(in this exact order):

1. Project Overview
2. Features
3. Tech Stack
4. Getting Started
   - Prerequisites
   - Installation
   - Environment Variables
   - Running Locally
5. API Overview
6. Folder Structure
7. Testing
8. Deployment
9. Contributing
10. License

Additional constraints:
- If a section cannot be fully derived from signals, omit the section entirely
- Do not include marketing language
- Do not speculate
- Do not repeat the input verbatim
- Folder Structure section must describe the provided tree clearly and accurately

Return ONLY valid Markdown.
"""
