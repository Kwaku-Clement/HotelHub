from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analysis_report/', views.inventory_analysis_report, name='analysis_report'),
]
