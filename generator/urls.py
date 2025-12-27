from django.urls import path
from .views import (
    GenerateReadmeView,
    JobStatusView,
    DownloadReadmeView,
    HealthCheckView,
    ListJobsView,
    LLMHealthCheckView,
    PreviewReadmeHTMLView,
    RetryJobView,
    DeleteJobView
)

urlpatterns = [
    path("health/", HealthCheckView.as_view()),
    path("generate/", GenerateReadmeView.as_view()),
    path("jobs/", ListJobsView.as_view()),
    path("jobs/<int:job_id>/", JobStatusView.as_view()),
    path("jobs/<int:job_id>/download/", DownloadReadmeView.as_view()),
    path("jobs/<int:job_id>/preview/", PreviewReadmeHTMLView.as_view()),
    path("jobs/<int:job_id>/retry/", RetryJobView.as_view()),
    path("jobs/<int:job_id>/delete/", DeleteJobView.as_view()),
    path("health/llm/", LLMHealthCheckView.as_view()),
]

