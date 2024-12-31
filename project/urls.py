from django.urls import path

from . import views

urlpatterns = [
    path("projects", views.project_index, name="projects"),
    path("list/<int:page>", views.ProjectListView.as_view(), name="list_project"),
    path("create", views.ProjectCreateView.as_view(), name="create_project"),
    path("<int:pk>/edit", views.ProjectUpdateView.as_view(), name="manage_project"),
    path("<int:pk>/delete", views.ProjectDeleteView.as_view(), name="delete_project"),
    path("<int:project_id>", views.ProjectDetailView.as_view(), name="project_details"),
    path(
        "<int:project_id>/project_members/<int:page>",
        views.project_members,
        name="project_members",
    ),
    path("<int:project_id>/connections", views.index, name="connections"),
    path(
        "<int:project_id>/connection/create/",
        views.connection_create,
        name="create_connection",
    ),
    path(
        "<int:project_id>/connection/list/<int:page>",
        views.connection_list,
        name="list_connection",
    ),
    path(
        "<int:project_id>/connection/<int:pk>/edit/",
        views.connection_edit,
        name="edit_connection",
    ),
    path(
        "<int:project_id>/connection/<int:pk>/delete/",
        views.connection_delete,
        name="delete_connection",
    ),
]
