from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_assignment, name='submit_assignment'),
    path('download/<str:token>/', views.download_assignment, name='download_assignment'),
]
