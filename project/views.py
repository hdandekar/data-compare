import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django_htmx.http import HttpResponseClientRedirect

from data_compare.users.models import User

from .forms import ConnectionForm
from .models import (PROJECT_MEMBER_ROLE_CHOICES, DbConnection, DbType,
                     Project, ProjectMember)
from .util import check_db_connection

CONNECTION_LIST_VIEW = "connection:list"
_404_Page = "404.html"

logger = logging.getLogger(__name__)


@login_required
def connection_create(request, project_id):
    dbtypes = DbType.objects.all()
    if request.method == "POST":
        if "save" in request.POST:
            form = ConnectionForm(request.POST)
            if form.is_valid():
                db_connection = form.save(commit=False)
                db_connection.created_by = request.user
                db_connection.project = Project.objects.get(id=project_id)
                # db_connection.password = make_password(form.cleaned_data["password"])
                db_connection.password = form.cleaned_data["password"]
                db_connection.save()
                return HttpResponse(
                    status=204,
                    headers={
                        "HX-Trigger": json.dumps(
                            {
                                "listChanged": None,
                                "showMessage": f"{db_connection.name} added.",
                                "eventType": "created",
                            }
                        )
                    },
                )
            else:
                return render(
                    request,
                    "connection/connection_form.html",
                    {"form": form, "dbtypes": dbtypes},
                )
        if "test" in request.POST:
            get_dbtype = DbType.objects.get(id=request.POST["dbtype"]).__str__()
            db_hostname = request.POST["hostname"]
            db_name = request.POST["dbname"]
            db_username = request.POST["username"]
            db_password = request.POST["password"]
            db_portno = request.POST["portno"]

            conn_sts = check_db_connection(
                get_dbtype,
                db_name,
                db_username,
                db_password,
                db_portno,
                hostname=db_hostname,
            )
            if conn_sts["connected"]:
                conn_html = """
                            <div>
                                <p id='connection_result' class='smaller has-text-success'>
                                    Success!
                                </p>
                            </div>
                        """

            else:
                error = conn_sts["error"]
                conn_html = """
                            <div>
                                <p id='connection_result' class='smaller has-text-danger'>{}, please provide
                                 password to test connection</p>
                            </div>
                        """.format(
                    error
                )
            return HttpResponse(conn_html)

    else:
        form = ConnectionForm()
    return render(
        request, "connection/connection_form.html", {"form": form, "dbtypes": dbtypes}
    )


@login_required
def connection_list(request, project_id, page=1):
    project = Project.objects.get(id=project_id)
    connections = DbConnection.objects.filter(project_id=project_id)
    connection_count = connections.count()
    paginator = Paginator(connections, per_page=20)
    try:
        connections = paginator.page(page)
        page_range = paginator.get_elided_page_range(number=page)
    except PageNotAnInteger:
        connections = paginator.page(1)
        page_range = paginator.get_elided_page_range(number=page)
    except EmptyPage:
        # If page is out of range deliver last page of results
        connections = paginator.page(paginator.num_pages)
        page_range = paginator.get_elided_page_range(number=page)
    return render(
        request,
        "connection/connection_list.html",
        {
            "project": project,
            "connections": connections,
            "connection_count": connection_count,
            "page_range": page_range,
        },
    )


@login_required
def connection_edit(request, project_id, pk):
    connection = get_object_or_404(DbConnection, id=pk)
    dbtypes = DbType.objects.exclude(dbname=connection.dbtype.dbname)
    if request.method == "POST":
        form = ConnectionForm(request.POST, instance=connection)
        if not form["password"].value():
            form.fields.pop("password")

        if form.is_valid():
            db_connection = form.save(commit=False)
            if "password" in form.cleaned_data:
                db_connection.password = form.cleaned_data["password"]
                db_connection.save()
            else:
                db_connection.save()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"{connection.name} updated",
                            "eventType": "updated",
                        }
                    )
                },
            )
        else:
            form = ConnectionForm(data=request.GET)
            # return HttpResponse(status=400, headers={"HX-Trigger": json.dumps({"errors": form.errors})})
            return render(
                request,
                "connection/connection_form.html",
                {"form": form, "connection": connection, "dbtypes": dbtypes},
            )
    else:
        form = ConnectionForm(instance=connection)
    return render(
        request,
        "connection/connection_form.html",
        {"form": form, "connection": connection, "dbtypes": dbtypes},
    )


@login_required
def index(request, project_id):
    return render(
        request,
        "connection/connection_index.html",
        {"project": Project.objects.get(id=project_id)},
    )


@login_required
def connection_delete(request, project_id, pk):
    connection = get_object_or_404(DbConnection, id=pk)
    connection.delete()
    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps(
                {
                    "listChanged": None,
                    "showMessage": f"{connection.name} deleted.",
                    "eventType": "deleted",
                }
            )
        },
    )


@login_required
def project_index(request):
    logger.info("Rendering Project Index")
    return render(request, "project/project_index.html")


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name", "project_code", "description"]
    template_name = "project/project_form.html"

    def form_valid(self, form):
        project = form.save(commit=False)
        project.owner = self.request.user
        project.created_by = self.request.user
        project.save()
        ProjectMember.objects.create(
            project=project, user=self.request.user, role="admin"
        )
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{project.name} added.",
                        "eventType": "created",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ["name", "project_code", "description"]
    template_name = "project/manage_project.html"
    project_object = None

    def dispatch(self, request, *args, **kwargs):
        self.project_object = self.get_object()
        if not self.project_object.is_member(
            self.request.user
        ) and not self.project_object.is_admin(self.request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project_object
        context["is_project_admin"] = self.project_object.is_admin(self.request.user)
        try:
            context["project_member"] = ProjectMember.objects.get(
                project=self.project_object, user=self.request.user
            )
        except ProjectMember.DoesNotExist:
            context["project_member"] = None
            context["PROJECT_MEMBER_ROLE_CHOICES"] = PROJECT_MEMBER_ROLE_CHOICES
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.project_object.is_admin(self.request.user):
            for field_name, field in form.fields.items():
                field.widget.attrs["disabled"] = "disabled"
        return form

    def form_valid(self, form):
        if not self.project_object.is_admin(self.request.user):
            messages.error(
                self.request, "You do not have permission to submit this form."
            )
            return self.form_invalid(form)
        # form = super().form_valid(form)
        project = form.save(commit=False)
        project.modified_by = self.request.user
        project.save()
        form.save_m2m()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{project.name} updated.",
                        "eventType": "updated",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_message(self, cleaned_data):
        name = cleaned_data["name"]
        return self.success_message % dict(
            {
                "cleaned_data": cleaned_data,
                "name": name,
                "object_id": self.kwargs["project_id"],
            }
        )

    def get_success_url(self):
        return redirect("projects")

    def test_func(self):
        if self.request.user == self.get_object().owner:
            return True
        return False

    def handle_no_permission(self):
        project = self.get_object()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to edit '{project.name}'",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


def project_members(request, project_id):
    project = Project.objects.get(id=project_id)
    project_members = project.projectmember_set.all().select_related("user")
    is_project_admin = project.is_admin(request.user)
    if request.method == "GET":
        return render(
            request,
            "project/partials/project_members.html",
            {
                "members": project_members,
                "project": project,
                "is_project_admin": is_project_admin,
            },
        )
    elif request.method == "POST":
        action = request.GET.get("action")
        if action == "add":
            email = request.POST.get("email")
            user, created = User.objects.get_or_create(email=email)
            project.members.add(user.id)
            csrf_token = get_token(request)
            conn_html = """
                        <tr class="small" id="member-{userid}">
                            <td class="is-vcentered has-text-centered">{username}</td>
                            <td class="is-vcentered has-text-centered">{useremail}</td>
                            <td class="is-vcentered has-text-centered">{userdatejoined}</td>
                            <td class="is-vcentered has-text-centered">
                            <div class="select">
                                <select class="is-small">
                                <option>Member</option>
                                <option>Admin</option>
                                </select>
                            </div>
                            </td>
                            <td class="has-text-danger is-vcentered has-text-centered">
                            <button class="has-text-danger"
                                hx-post="/project/{projectid}/project_members?action=remove&user_id={userid}"
                                hx-headers='{{"X-CSRFToken":"{csrf_token}"}}'
                                hx-target="#member-{userid}"
                                hx-confirm="Are you sure about removing your member: '{useremail}?'"
                                hx-swap="outerHTML:remove">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                            </td>
                        </tr>
                        """.format(
                userid=user.id,
                projectid=project_id,
                username=user.name,
                useremail=user.email,
                userdatejoined=user.date_joined.strftime("%d-%b-%y"),
                csrf_token=csrf_token,
            )
            return HttpResponse(
                content=conn_html,
                status=201,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "showMessage": f"{user.email} added.",
                            "eventType": "created",
                        }
                    )
                },
            )
        elif action == "remove":
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)
            project.members.remove(user)
            return HttpResponse(
                status=200,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "showMessage": f"{user.email} removed.",
                            "eventType": "deleted",
                        }
                    )
                },
            )
    return JsonResponse({"error": "Invalid request method"}, status=405)


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "project/project_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_num = self.kwargs.get("page")
        member_projects = (
            Project.objects.filter(members__id__exact=self.request.user.id)
            .order_by("-owner")
            .select_related("owner")
        )
        paginator = Paginator(member_projects, per_page=5)
        context["projects"] = paginator.get_page(page_num)
        logger.info("just before returning ProjectListView context")
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project

    def get_object(self, queryset=None):
        project = Project.objects.get(id=self.kwargs.get("pk"))
        return project

    def post(self, *args, **kwargs):
        project = self.get_object()
        try:
            self.get_object().delete()
            messages.error(self.request, f"Successfully deleted {project.name}!")
            return HttpResponseClientRedirect(reverse("projects"))
        except ProtectedError as e:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": "'{}' cannot be deleted as it has {} dependent records".format(
                                project.name, len(e.args[1])
                            ),
                            "eventType": "deleted",
                        }
                    )
                },
            )

    def test_func(self):
        project = self.get_object()
        if project.owner == self.request.user:
            return True
        return False

    def handle_no_permission(self):
        project = self.get_object()
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to delete '{project.name}'",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = "project/project_detail.html"

    def test_func(self):
        if self.request.user in self.get_object().members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)

    def get_object(self, queryset=...):
        object = get_object_or_404(Project, id=self.kwargs.get("pk"))
        return object
