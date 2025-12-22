import os
import shutil
import tempfile
from celery import shared_task
from generator.models import GenerationJob
from analysis.utils import analyze_repo
from readme.utils import generate_readme_markdown

def extract_repo_name(repo_url: str) -> str:
    """
    https://github.com/user/repo-name -> repo-name
    """
    return repo_url.rstrip("/").split("/")[-1]


@shared_task
def process_repo_task(job_id):
    job = GenerationJob.objects.get(id=job_id)
    job.status = 'processing'
    job.save()

    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp()
        from git import Repo
        Repo.clone_from(job.repo_url, tmp_dir)

        repo_name = extract_repo_name(job.repo_url)

        analysis_data = analyze_repo(tmp_dir)
        analysis_data["project_name"] = repo_name  

        readme_md = generate_readme_markdown(analysis_data)

        job.result = readme_md
        job.status = 'completed'
        job.save()

    except Exception as e:
        job.status = 'failed'
        job.result = str(e)
        job.save()

    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

