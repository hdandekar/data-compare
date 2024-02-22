from django.urls import path

from . import views

app_name = "settings"

urlpatterns = [
    path("connections", views.index, name="connections"),
    path("connection/create/", views.connection_create, name="create_connection"),
    path("connection/list/", views.connection_list, name="list_connection"),
    path("connection/<int:pk>/edit/", views.connection_edit, name="edit_connection"),
    path("connection/<int:pk>/delete/", views.connection_delete, name="delete_connection"),
]
