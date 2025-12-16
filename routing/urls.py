from django.urls import path
from .views import upload_gpx, find_path

urlpatterns = [
    path('calculate/', views.calculate_routes, name='calculate_routes'),
    path('upload_gpx/', views.upload_gpx, name='upload_gpx'),
]


