from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ConnectionForm
from .models import Connection

CONNECTION_LIST_VIEW = "connection:list"


@login_required
def connection_create(request):
    if request.method == "POST":
        form = ConnectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(CONNECTION_LIST_VIEW)
    else:
        form = ConnectionForm(data=request.GET)
    return render(request, "create.html", {"form": form})


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
        if form.is_valid():
            form.save()
            messages.success(request, "Connection Updated successfully")
            return redirect("connection:list")
    else:
        form = ConnectionForm(instance=connection)
    return render(request, "edit.html", {"form": form})


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def connection_delete(request, pk):
    conn = get_object_or_404(Connection, id=pk)
    conn.delete()
    return redirect(CONNECTION_LIST_VIEW)
