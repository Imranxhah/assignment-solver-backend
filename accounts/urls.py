from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.check_profile_completion, name='check_profile_completion'),
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
]
