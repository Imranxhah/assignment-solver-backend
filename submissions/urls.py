from django.urls import path
from . import views

urlpatterns = [
    path('check-limit/', views.check_submission_limit, name='check_submission_limit'),
    path('reward-ad-watched/', views.reward_ad_watched, name='reward_ad_watched'),
]
