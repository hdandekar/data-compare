from django.urls import path

from testplan import views

urlpatterns = [
    path("projects", views.project_index, name="projects"),
    path("project/create/", views.ProjectCreateView.as_view(), name="create_project"),
    path("project/<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="edit_project"),
    path("project/", views.ProjectListView.as_view(), name="list_project"),
    path("project/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="delete_project"),
    path("project/<int:pk>", views.ProjectDetailView.as_view(), name="project_details"),

    path("project/<int:project_id>/module/create", views.ModuleCreateView.as_view(), name="create_module"),
    path("project/<int:project_id>/modules", views.ModuleListView.as_view(), name="list_modules"),
    path("project/<int:project_id>/module/<int:module_id>/edit", views.ModuleUpdateView.as_view(), name="edit_module"),
    path("project/<int:project_id>/module/<int:module_id>/delete", views.module_delete, name="delete_module"),
]
