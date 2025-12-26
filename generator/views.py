from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GenerationJob
from .serializers import GenerationJobSerializer
from .tasks import process_repo_task
from drf_spectacular.utils import extend_schema, OpenApiExample,  OpenApiParameter
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import GenerationJob
import markdown2
from django.http import HttpResponse



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
    
    
class DownloadReadmeView(APIView):
    """
    Download the generated README.md file for a completed generation job.

    This endpoint returns the README content as a Markdown file
    (`text/markdown`) and forces a file download in the browser.

    The job must exist and must have a status of `completed`.
    """

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Successfully generated README.md file returned as a download"
            ),
            404: OpenApiResponse(
                description="Job not found or README not yet generated"
            ),
        },
        description=(
            "Download the generated README.md file for a completed job. "
            "If the job is still processing or does not exist, a 404 error is returned."
        ),
    )
    def get(self, request, job_id):
        try:
            job = GenerationJob.objects.get(id=job_id, status="completed")
        except GenerationJob.DoesNotExist:
            return Response(
                {"error": "README not available"},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = HttpResponse(
            job.result,
            content_type="text/markdown",
        )
        response["Content-Disposition"] = 'attachment; filename="README.md"'
        return response

class HealthCheckView(APIView):
    """
    Health check endpoint.

    Used to verify that the API service is running and reachable.
    This endpoint does not require authentication.
    """

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                },
            }
        },
        description="Health check endpoint to confirm the API is running.",
    )
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class ListJobsView(APIView):
    """
    Retrieve all README generation jobs.

    Supports optional filtering by job status using a query parameter.
    """

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
        description=(
            "Retrieve all README generation jobs. "
            "Optionally filter results by job status."
        ),
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
            return Response(
                {"error": "README not available"},
                status=status.HTTP_404_NOT_FOUND
            )

        html = markdown2.markdown(
            job.result,
            extensions=["fenced_code", "tables", "toc"]
        )

        return HttpResponse(html, content_type="text/html")

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
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

