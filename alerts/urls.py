
from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alerts_list, name='alerts_list'),
    path('update/<int:pk>/', views.update_contractor, name='update_contractor'),
    path('resolve/<int:alert_id>/', views.resolve_alert, name='resolve_alert'),
]
