from django.urls import path

from . import views

app_name = 'search'

urlpatterns = [
    path('', views.GlobalSearchView.as_view(), name='global-search'),
    path('advanced/', views.AdvancedSearchView.as_view(), name='advanced-search'),
    path('suggestions/', views.SearchSuggestionsView.as_view(), name='search-suggestions'),
]
