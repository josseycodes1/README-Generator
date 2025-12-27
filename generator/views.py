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

# ---------------------------
# Main API Views
# ---------------------------

class GenerateReadmeView(APIView):
    """Create a job to generate a README for a given GitHub repository."""

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
            logger.warning("GenerateReadmeView: repo_url not provided")
            return Response({"error": "Repository URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        job = GenerationJob.objects.create(repo_url=repo_url)
        logger.info(f"Created new GenerationJob id={job.id} for repo {repo_url}")
        process_repo_task.delay(job.id)

        return Response({"job_id": job.id, "status": job.status})


class JobStatusView(APIView):
    """Retrieve the status and result of a README generation job."""

    @extend_schema(
        parameters=[OpenApiParameter(name="job_id", description="ID of the job", required=True, type=int)],
        responses={
            200: GenerationJobSerializer,
            404: OpenApiResponse(description="Job not found")
        },
        description="Retrieve the status and result of a README generation job using its ID."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
            serializer = GenerationJobSerializer(job)
            return Response(serializer.data)
        except GenerationJob.DoesNotExist:
            logger.warning(f"JobStatusView: Job {job_id} not found")
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


class DownloadReadmeView(APIView):
    """Download the generated README.md for a completed job."""

    @extend_schema(
        parameters=[OpenApiParameter(name="job_id", description="ID of the job", required=True, type=int)],
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
            logger.warning(f"DownloadReadmeView: README not available for job {job_id}")
            return Response({"error": "README not available"}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(job.result, content_type="text/markdown")
        response["Content-Disposition"] = 'attachment; filename="README.md"'
        return response


class PreviewReadmeHTMLView(APIView):
    """Render generated README.md as HTML for preview."""

    @extend_schema(
        parameters=[OpenApiParameter(name="job_id", description="ID of the job", required=True, type=int)],
        responses={200: OpenApiResponse(description="Rendered HTML preview")},
        description="Render the generated README as HTML for preview."
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id, status="completed")
        except GenerationJob.DoesNotExist:
            logger.warning(f"PreviewReadmeHTMLView: README not available for job {job_id}")
            return Response({"error": "README not available"}, status=status.HTTP_404_NOT_FOUND)

        html = markdown2.markdown(job.result, extensions=["fenced_code", "tables", "toc"])
        return HttpResponse(html, content_type="text/html")


class HealthCheckView(APIView):
    """API Health check endpoint."""

    @extend_schema(
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
        description="Health check endpoint to confirm the API is running."
    )
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class LLMHealthCheckView(APIView):
    """Check Gemini LLM connectivity."""

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
            logger.error(f"LLMHealthCheckView error: {e}")
            return Response({"status": "error", "detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ListJobsView(APIView):
    """List all README generation jobs, with optional status filter."""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filter jobs by status (pending, processing, completed, failed)",
                required=False,
                type=str,
            )
        ],
        responses={200: GenerationJobSerializer(many=True)},
        description="Retrieve all README generation jobs. Optionally filter results by job status."
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        queryset = GenerationJob.objects.all().order_by("-created_at")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = GenerationJobSerializer(queryset, many=True)
        return Response(serializer.data)


class DeleteJobView(APIView):
    """Delete a README generation job by ID."""

    @extend_schema(
        parameters=[OpenApiParameter(name="job_id", description="ID of the job to delete", required=True, type=int)],
        responses={
            204: OpenApiResponse(description="Job deleted successfully"),
            404: OpenApiResponse(description="Job not found"),
        },
        description="Delete a README generation job."
    )
    def delete(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
            job.delete()
            logger.info(f"DeleteJobView: Job {job_id} deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GenerationJob.DoesNotExist:
            logger.warning(f"DeleteJobView: Job {job_id} not found")
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


class RetryJobView(APIView):
    """Retry a failed README generation job."""

    @extend_schema(
        parameters=[OpenApiParameter(name="job_id", description="ID of the failed job to retry", required=True, type=int)],
        responses={
            200: GenerationJobSerializer,
            400: OpenApiResponse(description="Job cannot be retried (not failed)"),
            404: OpenApiResponse(description="Job not found"),
        },
        description="Retry a failed README generation job."
    )
    def post(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id)
        except GenerationJob.DoesNotExist:
            logger.warning(f"RetryJobView: Job {job_id} not found")
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        if job.status != "failed":
            logger.warning(f"RetryJobView: Job {job_id} is not failed and cannot be retried")
            return Response({"error": "Only failed jobs can be retried"}, status=status.HTTP_400_BAD_REQUEST)

        job.status = "pending"
        job.result = ""
        job.save()
        logger.info(f"RetryJobView: Retrying job {job_id}")
        process_repo_task.delay(job.id)

        serializer = GenerationJobSerializer(job)
        return Response(serializer.data)
