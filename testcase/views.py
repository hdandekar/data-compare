from django.shortcuts import get_object_or_404, redirect, render
from .models import TestCase, TestCaseResult
from .forms import TestCaseForm

# from django.http import request
from django.contrib.auth.decorators import login_required
from connection.models import Connection
from django.contrib import messages
from .execute import Comparison
import pandas as pd

# import datetime
# @login_required
# def connection_create(request):
#     if request.method == "POST":
#         form = ConnectionForm(request.POST)
#         if form.is_valid():
#             form.save()
#             # return HttpResponse('New Connection created successfully')
#             return redirect('list')
#     else:
#         form = ConnectionForm(data=request.GET)
#     return render(request, 'create.html', {'form': form})


@login_required
def testcase_create(request):
    # connection_name = Connection(request)
    connection_list = Connection.objects.all()
    if request.method == "POST":
        form = TestCaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "TC created successfully")
            return redirect("testcase:list")
        else:
            print("Form is invalid")
            
    else:
        form = TestCaseForm(data=request.GET)
        print("Coming in else")
    return render(
        request,
        "create_testcase.html",
        {"form": form, "connection_list": connection_list},
    )


@login_required
def testcase_list(request):
    testcases_list = TestCase.objects.all()
    testcases_count = testcases_list.count()
    return render(
        request,
        "list_testcases.html",
        {"testcases_list": testcases_list, "testcases_count": testcases_count},
    )


@login_required
def testcase_delete(request, pk):
    tc = get_object_or_404(TestCase, id=pk)
    tc.delete()
    messages.add_message(request, messages.SUCCESS, "TC deleted successfully")
    return redirect("testcase:list")


@login_required
def testcase_edit(request, pk):
    testcase = get_object_or_404(TestCase, id=pk)
    if request.method == "POST":
        form = TestCaseForm(request.POST, instance=testcase)
        if form.is_valid():
            form.save()
            return redirect("testcase:list")
            # return render(request, 'edit.html', {'form': form})
    else:
        form = TestCaseForm(instance=testcase)
    return render(request, "edit_testcase.html", {"form": form})


@login_required
def execute_testcase(request, pk):
    tc = get_object_or_404(TestCase, id=pk)
    result = TestCaseResult(testcase=tc, summary="In Progress")
    result.save()
    srcconn = get_object_or_404(Connection, name=tc.sourcedbid)
    tgtconn = get_object_or_404(Connection, name=tc.targetdbid)
    # conndetail = {"src": srcconn, "tgt": tgtconn}
    compare = Comparison()
    srcdata = compare.get_src_data(srcconn, tc.sourcesql)
    tgtdata = compare.get_src_data(tgtconn, tc.targetsql)
    compare_result = compare.compare_data(srcdata, tgtdata, tc.keycolumns, result.id)
    result.summary = "Completed"
    result.save()
    return redirect("testcase:list")
    # return render(request, 'result_summary.html', {'summary': result.id})


@login_required
def testcase_result(request, pk):
    tc = get_object_or_404(TestCase, id=pk)
    results = TestCaseResult.objects.filter(testcase=tc)
    return render(request, "list_result.html", {"result": results})


@login_required
def testcase_instance_result(request, pk):
    # results = TestCaseResult.objects.filter(id=pk)
    try:
        added_data = pd.read_csv("{}_added.csv".format(pk))
        added_set = added_data.values.tolist()
        removed_data = pd.read_csv("{}_dropped.csv".format(pk))
        removed_set = removed_data.values.tolist()
        changed_data = pd.read_csv("{}_changed.csv".format(pk))
        changed_set = changed_data.values.tolist()
        return render(
            request,
            "result_summary.html",
            {
                "added": added_set,
                "added_data": added_data,
                "removed": removed_set,
                "removed_data": removed_data,
                "changed": changed_set,
                "changed_data": changed_data,
            },
        )
    except:
        message = "No data available"
        return render(request, "result_summary.html", {"message": message})
