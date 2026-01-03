from django.urls import path
from .views import monument_list
from .views import filter_monuments
from .views import monuments_map

urlpatterns = [
    path('monuments/', monument_list, name='monument_list'),
     path("map/", monuments_map, name="monuments_map"),
    path("filter/", filter_monuments, name="filter_monuments")
]
