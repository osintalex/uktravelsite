from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('outbound', views.outbound, name='outbound'),
    path('inbound', views.inbound, name='inbound'),
    path('about', views.about, name='about'),
    path('search', views.search, name='search'),
]