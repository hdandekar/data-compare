import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .forms import ConnectionForm
from .models import DbConnection, DbType
from .util import check_db_connection

CONNECTION_LIST_VIEW = "connection:list"


@login_required
def connection_create(request):
    print("request:", request)
    if request.method == "POST":
        if "save" in request.POST:
            form = ConnectionForm(request.POST)
            if form.is_valid():
                db_connection = form.save(commit=False)
                db_connection.created_by = request.user
                db_connection.password = make_password(form.cleaned_data["password"])
                db_connection.save()
                return HttpResponse(
                    status=204,
                    headers={
                        "HX-Trigger": json.dumps(
                            {
                                "connectionListChanged": None,
                                "showMessage": f"{db_connection.name} added.",
                                "eventType": "created",
                            }
                        )
                    },
                )
        if "test" in request.POST:
            get_dbtype = DbType.objects.get(id=request.POST["dbtype"]).__str__()
            db_hostname = request.POST["hostname"]
            db_name = request.POST["dbname"]
            db_username = request.POST["username"]
            db_password = request.POST["password"]
            db_portno = request.POST["portno"]

            sf_ac_nm = request.POST["sf_account_name"]
            sf_wh_nm = request.POST["sf_account_name"]

            conn_sts = check_db_connection(
                get_dbtype,
                db_name,
                db_username,
                db_password,
                db_portno,
                hostname=db_hostname,
                sf_account_name=sf_ac_nm,
                sf_wh_nm=sf_wh_nm,
            )
            if conn_sts["connected"]:
                conn_html = """
                            <div>
                                <p id='connection_result' class='text-small my-1 text-success'>
                                    Success!
                                </p>
                            </div>
                        """

            else:
                error = conn_sts["error"]
                conn_html = """
                            <div>
                                <p id='connection_result' class='smaller my-1 text-danger'>{}:{}, please provide
                                 password to test connection</p>
                            </div>
                        """.format(
                    error.errno, error.msg
                )
            return HttpResponse(conn_html)

    else:
        form = ConnectionForm(data=request.GET)
        dbtypes = DbType.objects.all()
    return render(request, "connection_form.html", {"form": form, "dbtypes": dbtypes})


@login_required
def connection_list(request):
    conn_list = DbConnection.objects.all()
    connection_count = conn_list.count()
    return render(request, "list.html", {"conn_list": conn_list, "connection_count": connection_count})


@login_required
def connection_edit(request, pk):
    connection = get_object_or_404(DbConnection, id=pk)
    dbtypes = DbType.objects.exclude(dbname=connection.dbtype.dbname)
    if request.method == "POST":
        form = ConnectionForm(request.POST, instance=connection)
        if not form["password"].value():
            form.fields.pop("password")

        if form.is_valid():
            db_connection = form.save(commit=False)
            print("form.cleaned_data", form.cleaned_data)
            if "password" in form.cleaned_data:
                db_connection.password = make_password(form.cleaned_data["password"])
                db_connection.save()
            else:
                print("Password not present")
                db_connection.save()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "connectionListChanged": None,
                            "showMessage": f"{connection.name} updated",
                            "eventType": "edited",
                        }
                    )
                },
            )
        else:
            print("Form Errors are", form.errors)
            return HttpResponse(status=400, headers={"HX-Trigger": json.dumps({"errors": form.errors})})
    else:
        form = ConnectionForm(instance=connection)
    return render(request, "connection_form.html", {"form": form, "connection": connection, "dbtypes": dbtypes})


@login_required
def index(request):
    return render(request, "index.html")


@login_required
def connection_delete(request, pk):
    connection = get_object_or_404(DbConnection, id=pk)
    connection.delete()
    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps(
                {
                    "connectionListChanged": None,
                    "showMessage": f"{connection.name} deleted.",
                    "eventType": "deleted",
                }
            )
        },
    )
