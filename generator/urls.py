from django.urls import path
from .views import GenerateReadmeView, JobStatusView

urlpatterns = [
    path("generate/", GenerateReadmeView.as_view()),
    path("jobs/<int:job_id>/", JobStatusView.as_view()),
]
