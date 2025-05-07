from django.urls import path
from .views import RSDDataView

urlpatterns = [
    #path("show-json/", RSDDataView.show_data, name="show_rsd_json"),
    path("show-json/", RSDDataView.as_view(), name="show_rsd_json"),
    path('show-network/', RSDDataView.as_view(), name='show_network'),
]
