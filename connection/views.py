from django.shortcuts import render
from .forms import ConnectionForm
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Connection
from django.http.response import HttpResponseRedirect
from testcase.models import TestCase


@login_required
def connection_create(request):
    if request.method == "POST":
        form = ConnectionForm(request.POST)
        if form.is_valid():
            form.save()
            # return HttpResponse('New Connection created successfully')
            return redirect('connection:list')
    else:
        form = ConnectionForm(data=request.GET)
    return render(request, 'create.html', {'form': form})


@ login_required
def connection_list(request):
    conn_list = Connection.objects.all()
    connection_count = conn_list.count()
    return render(request, 'list.html', {'conn_list': conn_list, 'connection_count': connection_count})


@ login_required
def connection_edit(request, pk):
    connection = get_object_or_404(Connection, id=pk)
    if request.method == "POST":
        form = ConnectionForm(request.POST, instance=connection)
        if form.is_valid():
            form.save()
            # message.success(request, 'Connection Updated successfully')
            return redirect('connection:list')
            # return render(request, 'edit.html', {'form': form})
    else:
        form = ConnectionForm(instance=connection)
    return render(request, 'edit.html', {'form': form})


@ login_required
def dashboard(request):
    tc_count = TestCase.objects.count()
    return render(request, 'dashboard.html', {'count': tc_count})


@ login_required
def connection_delete(request, pk):
    conn = get_object_or_404(Connection, id=pk)
    conn.delete()
    return redirect('connection:list')
