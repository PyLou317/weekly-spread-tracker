from django.urls import path
from . import views

app_name = 'contractors'

urlpatterns = [
    path('', views.list_view, name='list'),
    path('create/', views.create_view, name='create'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('<int:pk>/edit/', views.edit_view, name='edit'),
    path('<int:pk>/delete/', views.delete_view, name='delete'),
    path('review-queue/', views.review_queue_view, name='review_queue'),
]
