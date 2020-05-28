from django.urls import path
from .import views

app_name = 'testcase'

urlpatterns = [
    path('results/<int:pk>/', views.testcase_result, name='results'),
    path('<int:pk>/execute/', views.execute_testcase, name='execute'),
    path('create/', views.testcase_create, name='create'),
    path('testcases/', views.testcase_list, name='list'),
    path('<int:pk>/edit/', views.testcase_edit, name='edit'),
    path('<int:pk>/delete/', views.testcase_delete, name='delete'),
    path('results/<int:pk>/summary/',
         views.testcase_instance_result, name='instance_result'),


]
