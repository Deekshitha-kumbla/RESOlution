from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Welcome to the Benchmark Platform API</h1>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    #path('', lambda request: HttpResponseRedirect('/api/')),
    path('', home),
    path('scraper/', include('scraper.urls')),
]
