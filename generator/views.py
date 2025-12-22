from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GenerationJob
from .serializers import GenerationJobSerializer
from .tasks import process_repo_task
from drf_spectacular.utils import extend_schema, OpenApiExample


class GenerateReadmeView(APIView):
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'repo_url': {'type': 'string', 'description': 'Public GitHub repository URL'}
                },
                'required': ['repo_url']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'job_id': {'type': 'integer', 'description': 'ID of the created job'},
                    'status': {'type': 'string', 'description': 'Current status of the job'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Example request',
                summary='Generate README for a repo',
                value={"repo_url": "https://github.com/josseycodes1/Backend-Wallet-Services"}
            )
        ],
        description="Create a job to generate a README for a given public GitHub repository."
    )
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({"error": "Repository URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        job = GenerationJob.objects.create(repo_url=repo_url)
        process_repo_task.delay(job.id)

        return Response({"job_id": job.id, "status": job.status})


class JobStatusView(APIView):
    @extend_schema(
        responses={
            200: GenerationJobSerializer,
            404: {
                'type': 'object',
                'properties': {'error': {'type': 'string'}}
            }
        },
        description="Retrieve the status and result of a README generation job using its ID."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
        except GenerationJob.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GenerationJobSerializer(job)
        return Response(serializer.data)
