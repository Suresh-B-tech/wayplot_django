# from django.urls import path
# from . import views

# urlpatterns = [
#     path("route/", views.calculate_routes, name="calculate_routes"),
# ]

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('calculate/', views.calculate_routes, name='calculate_routes'),
# ]


from django.urls import path
from .views import upload_gpx, find_path

urlpatterns = [
    path("upload-gpx/", upload_gpx),
    path("path/", find_path),
]


