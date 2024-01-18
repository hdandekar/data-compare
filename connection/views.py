import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .forms import ConnectionForm
from .models import Connection

CONNECTION_LIST_VIEW = "connection:list"


@login_required
def connection_create(request):
    if request.method == "POST":
        form = ConnectionForm(request.POST)
        if form.is_valid():
            db_connection = form.save(commit=False)
            db_connection.created_by = request.user
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
    else:
        form = ConnectionForm(data=request.GET)
    return render(request, "connection_form.html", {"form": form})


@login_required
def connection_list(request):
    conn_list = Connection.objects.all()
    connection_count = conn_list.count()
    return render(request, "list.html", {"conn_list": conn_list, "connection_count": connection_count})


@login_required
def connection_edit(request, pk):
    connection = get_object_or_404(Connection, id=pk)
    if request.method == "POST":
        form = ConnectionForm(request.POST, instance=connection)
        if form["password"].value:
            form.fields.pop("password")
            print("Removed password before checking is valid")
        else:
            print("Came in else of empty pwd check")

        if form.is_valid():
            form.save()
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
        form = ConnectionForm(instance=connection)
    return render(request, "connection_form.html", {"form": form, "connection": connection})


@login_required
def index(request):
    return render(request, "index.html")


@login_required
def connection_delete(request, pk):
    connection = get_object_or_404(Connection, id=pk)
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
