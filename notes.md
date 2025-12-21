PHASE 1: INSTALLATIONS

PHASE 2: ASYNC SETUP
Redis configuration
Celery integration with Django
Background task pipeline
Job status tracking model

1️⃣ Generator App — Handles job creation and status tracking

Responsibilities:
Accept the GitHub URL from the frontend form.
Create a GenerationJob in the database with status (pending, processing, completed, failed).
Trigger Celery tasks to process the repository asynchronously.
Return the job ID or status to the frontend.

2️⃣ Analysis App — Clones the repository & parses files

Responsibilities:
Clone the GitHub repository.
Read key files (requirements.txt, package.json, Dockerfile, etc.).
Generate project structure tree.
Return structured data for README generation.

3️⃣ Readme App — Generates Markdown from parsed data

Responsibilities:
Take the analysis data from analysis.
Convert it into a nicely formatted Markdown README.
Optional: support templates or customization.