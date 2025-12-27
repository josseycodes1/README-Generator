import os
import shutil
import tempfile
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from git import Repo, GitCommandError

from generator.models import GenerationJob
from analysis.utils import analyze_repo
from readme.utils import generate_readme_markdown_with_llm
from readme.exceptions import LLMGenerationError

logger = get_task_logger(__name__)


def extract_repo_name(repo_url: str) -> str:
    """
    Extract repository name from URL.
    Example: https://github.com/user/repo -> repo
    """
    return repo_url.rstrip("/").split("/")[-1]


@shared_task(bind=True, max_retries=5, soft_time_limit=300)
def process_repo_task(self, job_id: int):
    """
    Process a README generation job with retries, caching, and idempotency.

    Steps:
    1. Skip if job is already 'processing' or 'completed'.
    2. Clone the repo into a temporary directory.
    3. Analyze the repository structure and dependencies.
    4. Generate a README using local generator + Gemini LLM.
    5. Save result to job and mark as 'completed'.
    6. Retry Git errors with exponential backoff.
    7. Fail gracefully on other errors.
    """

    tmp_dir = None

    try:
        job = GenerationJob.objects.get(id=job_id)

        if job.status in ("processing", "completed"):
            logger.info(f"Job {job_id} already {job.status}, skipping.")
            return

    
        job.status = "processing"
        job.save()
        logger.info(f"Job {job_id} marked as processing.")

       
        tmp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning repo {job.repo_url} into {tmp_dir}")
        Repo.clone_from(job.repo_url, tmp_dir)

      
        repo_name = extract_repo_name(job.repo_url)
        analysis_data = analyze_repo(tmp_dir)
        analysis_data["project_name"] = repo_name

        try:
            readme_md = generate_readme_markdown_with_llm(
                analysis_data,
                repo_url=job.repo_url
            )
        except LLMGenerationError as e:
            logger.error(f"LLM generation failed for job {job_id}: {e}")
            job.status = "failed"
            job.result = f"LLM generation failed: {str(e)}"
            job.save()
            return

   
        job.result = readme_md
        job.status = "completed"
        job.save()
        logger.info(f"Job {job_id} completed successfully.")

    except GitCommandError as e:
        logger.warning(f"Git error for job {job_id}: {e}")
        try:
            countdown = 2 ** self.request.retries
            self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            job.status = "failed"
            job.result = f"Git error after max retries: {str(e)}"
            job.save()
            logger.error(f"Job {job_id} failed after max retries.")

    except GenerationJob.DoesNotExist:
        logger.error(f"Job {job_id} does not exist.")

    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}: {e}")
        if 'job' in locals():
            job.status = "failed"
            job.result = str(e)
            job.save()

    finally:
   
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            logger.info(f"Cleaned up temporary directory {tmp_dir}")
