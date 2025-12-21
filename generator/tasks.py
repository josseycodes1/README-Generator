import os
import shutil
import tempfile
from celery import shared_task
from generator.models import GenerationJob
from analysis.utils import analyze_repo
from readme.utils import generate_readme_markdown

@shared_task
def process_repo_task(job_id):
    job = GenerationJob.objects.get(id=job_id)
    job.status = 'processing'
    job.save()

    try:
        tmp_dir = tempfile.mkdtemp()
        from git import Repo
        Repo.clone_from(job.repo_url, tmp_dir)

        analysis_data = analyze_repo(tmp_dir)
        readme_md = generate_readme_markdown(analysis_data)

        job.result = readme_md
        job.status = 'completed'
        job.save()
    except Exception as e:
        job.status = 'failed'
        job.result = str(e)
        job.save()
    finally:
        shutil.rmtree(tmp_dir)
