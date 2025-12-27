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

This sets up the generator app: it handles job creation, stores the README result, and triggers the Celery task for asynchronous processing.

2️⃣ Analysis App — Clones the repository & parses files

Responsibilities:
Clone the GitHub repository.
Read key files (requirements.txt, package.json, Dockerfile, etc.).
Generate project structure tree.
Return structured data for README generation.

it should:
Detect languages & frameworks
Read dependency files
Detect Docker usage
Build file tree structure
Return structured data (Python dict)
This dict is later passed to the readme app.

3️⃣ Readme App — Generates Markdown from parsed data

Responsibilities:
Take the analysis data from analysis.
Convert it into a nicely formatted Markdown README.
Optional: support templates or customization.



backend now has:

Job lifecycle management:
Create a job: GenerateReadmeView → POST /generate/
List jobs: ListJobsView → GET /jobs/
Job status/details: JobStatusView → GET /jobs/<id>/
Download README: DownloadReadmeView → GET /jobs/<id>/download/
Preview HTML: PreviewReadmeHTMLView → GET /jobs/<id>/preview/

Retries for failed jobs:
RetryJobView → POST /jobs/<id>/retry/
Only allows retry if status == 'failed', sets pending, clears previous result, triggers Celery task.

Deletion of jobs:
DeleteJobView → DELETE /jobs/<id>/delete/
Can delete any job regardless of status, with proper logging.

Health checks:
API health: HealthCheckView
LLM health: LLMHealthCheckView

Logging:
Every major step is logged (job created, retry triggered, job deleted, errors).

Idempotency:
Retrying respects only failed jobs.
Celery task respects processing/completed states.