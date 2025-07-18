from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('polling-unit/', views.polling_unit_result, name='polling_unit_result'),
    path('lga-result/', views.lga_result, name='lga_result'),
    path('api/lgas/', views.api_lgas, name='api_lgas'),
    path('api/wards/', views.api_wards, name='api_wards'),
    path('api/polling-units/', views.api_polling_units, name='api_polling_units'),
    path('polling-unit/new/', views.add_all_party_polling_unit_results, name='add_all_party_polling_unit_results'),
]