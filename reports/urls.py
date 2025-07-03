
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('upload/', views.upload_report, name='upload'),
]
