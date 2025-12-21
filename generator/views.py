from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GenerationJob
from .serializers import GenerationJobSerializer
from .tasks import process_repo_task  

class GenerateReadmeView(APIView):
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({"error": "Repository URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        job = GenerationJob.objects.create(repo_url=repo_url)
        process_repo_task.delay(job.id)  

        return Response({"job_id": job.id, "status": job.status})

