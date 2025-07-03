
from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.candidate_list, name='list'),
    path('add/', views.candidate_create, name='create'),
    path('<int:pk>/', views.candidate_detail, name='detail'),
    path('<int:pk>/edit/', views.candidate_edit, name='edit'),
    path('<int:pk>/delete/', views.candidate_delete, name='delete'),
    path('review-queue/', views.review_queue, name='review_queue'),
]
