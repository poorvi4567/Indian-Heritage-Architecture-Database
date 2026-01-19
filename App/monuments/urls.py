from django.urls import path
from .views import monument_list
from .views import filter_monuments
from .views import monuments_map, home, monument_detail, nlp_search

urlpatterns = [
    path('', home, name='home'),
    path('monuments/', monument_list, name='monument_list'),
    path('monument/<int:monument_id>/', monument_detail, name='monument_detail'),
    path("map/", monuments_map, name="monuments_map"),
    path("filter/", filter_monuments, name="filter_monuments"),
    path("search/nlp/", nlp_search, name="nlp_search"),
    

]
