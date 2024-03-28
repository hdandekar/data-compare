from django.urls import path

from testplan import views

urlpatterns = [
    # Project URLs
    path("projects", views.project_index, name="projects"),
    path("project/list/<int:page>", views.ProjectListView.as_view(), name="list_project"),
    path("project/create", views.ProjectCreateView.as_view(), name="create_project"),
    path("project/<int:pk>/edit", views.ProjectUpdateView.as_view(), name="edit_project"),
    path("project/<int:pk>/delete", views.ProjectDeleteView.as_view(), name="delete_project"),
    path("project/<int:pk>", views.ProjectDetailView.as_view(), name="project_details"),
    # Module URLs
    path("project/<int:project_id>/module/<int:page>", views.ModuleListView.as_view(), name="list_module"),
    path("project/<int:project_id>/module/create", views.ModuleCreateView.as_view(), name="create_module"),
    path("project/<int:project_id>/module/<int:module_id>/edit", views.ModuleUpdateView.as_view(), name="edit_module"),
    path("project/<int:project_id>/module/<int:module_id>/delete", views.module_delete, name="delete_module"),
    # Test Case URLs
    path("project/<int:project_id>/testcase/create", views.TestCaseCreateView.as_view(), name="create_testcase"),
    path("project/<int:project_id>/testcases", views.TestCaseListView.as_view(), name="list_testcase"),
    path(
        "project/<int:project_id>/testcase/<int:testcase_id>/edit",
        views.TestCaseUpdateView.as_view(),
        name="edit_testcase",
    ),
    # Test Run URLs
    path("project/<int:project_id>/testrun/create", views.TestRunCreateView.as_view(), name="create_testrun"),
    path(
        "project/<int:project_id>/testrun/<int:testrun_id>/update",
        views.TestRunUpdateView.as_view(),
        name="update_testrun",
    ),
    path("project/<int:project_id>/testruns", views.testrun_index, name="testruns"),
    path("project/<int:project_id>/testrun/list", views.TestRunListView.as_view(), name="list_testruns"),
    path(
        "project/<int:project_id>/testruns/<int:testrun_id>/testcaserun/<int:testcase_id>",
        views.TestRunCaseDeleteView.as_view(),
        name="delete_testrun_testcase",
    ),
    path("project/<int:project_id>/testrun/<int:testrun_id>", views.TestRunDetails.as_view(), name="detail_testrun"),
    path(
        "project/<int:project_id>/<int:testrun_id>/get_project_testcases",
        views.get_project_testcases,
        name="get_project_testcases",
    ),
    # TestRun Cases URLs
    path(
        "project/<int:project_id>/testrun/<int:testrun_id>/testcases",
        views.get_testrun_testcases,
        name="get_testrun_testcases",
    ),
]
