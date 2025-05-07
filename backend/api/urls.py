from django.urls import path
from .views import *
from django.urls import path, include

urlpatterns = [
    path('benchmark/', get_benchmark, name="benchmark_results"),
   
]
