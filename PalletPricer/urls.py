from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='main'),
    #path('pallet', views.pallet, name='pallet'),
    #path('pallet', include('PalletPicker.urls')),
]