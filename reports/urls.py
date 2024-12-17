# urls.py
from django.urls import path
from . import views

app_name = "reports"
urlpatterns = [
    path('generate_report/', views.generate_report, name='generate_report'),
]
