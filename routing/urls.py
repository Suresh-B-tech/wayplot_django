from django.urls import path
from .views import calculate_routes, upload_gpx

urlpatterns = [
    path('calculate/', calculate_routes, name='calculate_routes'),
    path('upload_gpx/', upload_gpx, name='upload_gpx'),
]


