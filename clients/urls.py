
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='list'),
    path('add/', views.client_create, name='create'),
    path('<int:pk>/edit/', views.client_edit, name='edit'),
    path('<int:pk>/delete/', views.client_delete, name='delete'),
]
