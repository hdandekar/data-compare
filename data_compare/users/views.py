from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = [
        "name",
        "designation",
        "email",
        "avatar",
        "website",
        "github_link",
        "twitter_link",
        "mobile_number",
        "address",
    ]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        assert self.request.user.is_authenticated  # for mypy to know that the user is authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


def check_username(request):
    email = request.POST.get("email")
    login_url = reverse("account_login")
    email_registered_response = """
                <div class='smaller text-danger-emphasis' id='username-error'>
                    This email address is already registered, please
                    <a xlass='small' href='{url}'>Sign In</a>
                </div>""".format(
        url=login_url
    )
    email_absent_response = """
                <div class='smaller text-success' id='username-error'>
                    This email address is not registered yet,
                </div>""".format()
    if get_user_model().objects.filter(email=email).exists():
        return HttpResponse(email_registered_response)
    else:
        return HttpResponse(email_absent_response)
