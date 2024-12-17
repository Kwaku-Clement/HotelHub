from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns
    path('activity-log/', views.activity_log_view, name='activity_log'),
]
