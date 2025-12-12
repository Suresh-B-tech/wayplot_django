# from django.urls import path
# from . import views

# urlpatterns = [
#     path("route/", views.calculate_routes, name="calculate_routes"),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('calculate/', views.calculate_routes, name='calculate_routes'),
]

