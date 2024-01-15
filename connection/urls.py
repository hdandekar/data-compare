from django.urls import path

from . import views

app_name = 'connection'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.connection_create, name='create'),
    path('list/', views.connection_list, name='list'),
    path('<int:pk>/edit/', views.connection_edit, name='edit'),
    path('<int:pk>/delete/', views.connection_delete, name='delete'),
]
