import os
import shutil
import tempfile
from celery import shared_task
from celery.utils.log import get_task_logger
from generator.models import GenerationJob
from analysis.utils import analyze_repo
from git import Repo, GitCommandError
from readme.utils import generate_readme_markdown_with_llm

logger = get_task_logger(__name__)

def extract_repo_name(repo_url: str) -> str:
    """
    Extract repository name from URL.
    Example: https://github.com/user/repo -> repo
    """
    return repo_url.rstrip("/").split("/")[-1]


@shared_task(bind=True, max_retries=5, soft_time_limit=300)
def process_repo_task(self, job_id):
    """
    Process a README generation job with retries and idempotency.

    - Retries on GitCommandError with exponential backoff.
    - Skips if job is already processing or completed (idempotency).
    - Updates job status to 'failed' on non-retryable errors.
    """
    tmp_dir = None

    try:
        job = GenerationJob.objects.get(id=job_id)

        #idempotency: skip if already processing or completed
        if job.status in ("processing", "completed"):
            logger.info(f"Job {job_id} is already {job.status}, skipping processing.")
            return

        job.status = "processing"
        job.save()

        #create temporary directory for cloning
        tmp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning repo {job.repo_url} into {tmp_dir}")
        Repo.clone_from(job.repo_url, tmp_dir)

        #extract repo name and analyze
        repo_name = extract_repo_name(job.repo_url)
        analysis_data = analyze_repo(tmp_dir)
        analysis_data["project_name"] = repo_name

        #generate README
        readme_md = generate_readme_markdown_with_llm(
    analysis_data,
    repo_url=job.repo_url
)


        job.result = readme_md
        job.status = "completed"
        job.save()
        logger.info(f"Job {job_id} completed successfully.")

    except GitCommandError as e:
        logger.warning(f"Git error for job {job_id}: {e}")
        #retry with exponential backoff
        try:
            countdown = 2 ** self.request.retries
            self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            job.status = "failed"
            job.result = f"Git error after max retries: {str(e)}"
            job.save()
            logger.error(f"Job {job_id} failed after max retries.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job.status = "failed"
        job.result = str(e)
        job.save()

    finally:
        #clean up temporary directory
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            logger.info(f"Cleaned up temporary directory {tmp_dir}")
