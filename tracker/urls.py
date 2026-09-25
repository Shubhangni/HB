# tracker/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_habit, name='add_habit'),
    path('toggle/', views.toggle, name='toggle'),
    path('reset/', views.reset, name='reset'),
    path('delete/<int:habit_id>/', views.delete_habit, name='delete_habit'),
    path('analytics/', views.analytics, name='analytics'),
    path('copy-prev/', views.copy_previous_month, name='copy_prev'),
    
]