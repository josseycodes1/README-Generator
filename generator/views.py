from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GenerationJob
from .serializers import GenerationJobSerializer
from .tasks import process_repo_task
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
import markdown2
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class GenerateReadmeView(APIView):
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {'repo_url': {'type': 'string', 'description': 'Public GitHub repository URL'}},
                'required': ['repo_url']
            }
        },
        responses={
            200: {'type': 'object', 'properties': {'job_id': {'type': 'integer'}, 'status': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        },
        examples=[OpenApiExample(
            'Example request',
            summary='Generate README for a repo',
            value={"repo_url": "https://github.com/josseycodes1/Backend-Wallet-Services"}
        )],
        description="Create a job to generate a README for a given public GitHub repository."
    )
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({"error": "Repository URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        job = GenerationJob.objects.create(repo_url=repo_url)
        process_repo_task.delay(job.id)
        logger.info(f"Created README generation job {job.id} for repo {repo_url}")
        return Response({"job_id": job.id, "status": job.status})


class JobStatusView(APIView):
    @extend_schema(
        responses={
            200: GenerationJobSerializer,
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        },
        description="Retrieve the status and result of a README generation job using its ID."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
        except GenerationJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = GenerationJobSerializer(job)
        return Response(serializer.data)


class RetryJobView(APIView):
    """
    Retry a failed job. Only jobs with status 'failed' can be retried.
    """

    @extend_schema(
        responses={
            200: {'type': 'object', 'properties': {'job_id': {'type': 'integer'}, 'status': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        },
        description="Retry a failed README generation job using its ID."
    )
    def post(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
        except GenerationJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        if job.status != "failed":
            return Response({"error": f"Job {job_id} is not failed and cannot be retried."}, status=status.HTTP_400_BAD_REQUEST)

        job.status = "pending"
        job.result = None
        job.save()
        process_repo_task.delay(job.id)
        logger.info(f"Retrying job {job.id}")
        return Response({"job_id": job.id, "status": job.status})


class DeleteJobView(APIView):
    """
    Delete a README generation job by ID. Can delete any job regardless of status.
    """

    @extend_schema(
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        },
        description="Delete a README generation job using its ID."
    )
    def delete(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
        except GenerationJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        job.delete()
        logger.info(f"Deleted job {job_id}")
        return Response({"message": f"Job {job_id} deleted successfully"})


class DownloadReadmeView(APIView):
    """
    Download the generated README.md file for a completed generation job.
    """

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Successfully generated README.md file returned as a download"),
            404: OpenApiResponse(description="Job not found or README not yet generated"),
        },
        description="Download the generated README.md file for a completed job."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id, status="completed")
        except GenerationJob.DoesNotExist:
            return Response({"error": "README not available"}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(job.result, content_type="text/markdown")
        response["Content-Disposition"] = f'attachment; filename="README_{job_id}.md"'
        return response


class ListJobsView(APIView):
    """
    List all jobs, with optional filtering by status.
    """

    @extend_schema(
        parameters=[OpenApiParameter(
            name="status",
            description="Filter jobs by status (pending, processing, completed, failed)",
            required=False,
            type=str,
        )],
        responses={200: GenerationJobSerializer(many=True)},
        description="Retrieve all README generation jobs. Optionally filter by status."
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        queryset = GenerationJob.objects.all().order_by("-created_at")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = GenerationJobSerializer(queryset, many=True)
        return Response(serializer.data)


class PreviewReadmeHTMLView(APIView):
    """
    Render generated README.md as HTML for preview purposes.
    """

    @extend_schema(
        responses={200: OpenApiResponse(description="Rendered HTML preview")},
        description="Render the generated README as HTML for preview."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id, status="completed")
        except GenerationJob.DoesNotExist:
            return Response({"error": "README not available"}, status=status.HTTP_404_NOT_FOUND)

        html = markdown2.markdown(job.result, extensions=["fenced_code", "tables", "toc"])
        return HttpResponse(html, content_type="text/html")


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    """

    @extend_schema(
        responses={200: {"type": "object"}},
        description="Health check endpoint to confirm API is running."
    )
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class LLMHealthCheckView(APIView):
    """
    Health check for Gemini LLM connectivity.
    """

    @extend_schema(
        responses={200: {"type": "object"}},
        description="Health check for Gemini LLM"
    )
    def get(self, request):
        try:
            from readme.llm import GeminiClient
            client = GeminiClient()
            client.generate("Reply with the word OK.")
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
