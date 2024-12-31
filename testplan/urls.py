from django.urls import path

from testplan import views

urlpatterns = [
    # Test Case URLs
    path(
        "project/<int:project_id>/testcase/create",
        views.TestCaseCreateView.as_view(),
        name="create_testcase",
    ),
    path(
        "project/<int:project_id>/testcases",
        views.TestCaseFolderIndexView.as_view(),
        name="list_testcase",
    ),
    path(
        "project/<int:project_id>/folder/<int:pk>/subfolders/",
        views.TestCaseFolderSubfoldersView.as_view(),
        name="folder_subfolders",
    ),
    path(
        "project/<int:project_id>/folder/create",
        views.TestCaseFolderCreateView.as_view(),
        name="create_folder",
    ),
    path(
        "project/<int:project_id>/testcase/<int:testcase_id>/edit",
        views.TestCaseUpdateView.as_view(),
        name="edit_testcase",
    ),
    path(
        "project/<int:project_id>/testcase/<int:testcase_id>/delete",
        views.TestCaseDeleteView.as_view(),
        name="delete_testcase",
    ),
    # Test Run URLs
    path(
        "project/<int:project_id>/testrun/create",
        views.TestRunCreateView.as_view(),
        name="create_testrun",
    ),
    path(
        "project/<int:project_id>/testrun/<int:testrun_id>/update",
        views.TestRunUpdateView.as_view(),
        name="update_testrun",
    ),
    path("project/<int:project_id>/testruns", views.testrun_index, name="testruns"),
    path(
        "project/<int:project_id>/testrun/list",
        views.TestRunListView.as_view(),
        name="list_testruns",
    ),
    path(
        "project/<int:project_id>/testrun/<int:testrun_id>/testcase/<int:testcase_id>",
        views.TestRunCaseDeleteView.as_view(),
        name="delete_testrun_testcase",
    ),
    path(
        "project/<int:project_id>/testrun/<int:testrun_id>",
        views.TestRunDetails.as_view(),
        name="testrun_detail",
    ),
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
    path(
        "project/<int:project_id>/testruns/<int:testrun_id>/testcaserun/<int:testrun_testcase_id>/execute",
        views.execute_testcase,
        name="execute_testcase",
    ),
    path(
        "project/<int:project_id>/testruns/<int:testrun_id>/testcase/history/<int:testrun_testcase_id>",
        views.testrun_testcase_history_list,
        name="testrun_testcase_history_list",
    ),
    path(
        "project/<int:project_id>/testruns/<int:testrun_id>/testcase/history/<int:testrun_case_id>/log/<int:testrun_case_history_id>",  # noqa: E501
        views.testrun_case_result_summary,
        name="execution_history",
    ),
]
