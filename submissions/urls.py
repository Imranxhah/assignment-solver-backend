from django.urls import path
from . import views

urlpatterns = [
    path('check-limit/', views.check_submission_limit, name='check_submission_limit'),
]
