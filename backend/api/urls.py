from django.urls import path
from .views import *

urlpatterns = [
    path('benchmark/', get_benchmark, name="benchmark_results"),
   
]
