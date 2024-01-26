from django.urls import path

from data_compare.users.views import check_username, user_detail_view, user_redirect_view, user_update_view

app_name = "users"
urlpatterns = [
    path("redirect/", view=user_redirect_view, name="redirect"),
    path("update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("check_username/", check_username, name="check-username"),
]
