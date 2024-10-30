from django import template

register = template.Library()


@register.simple_tag
def tc_status_row_class(status_value):
    if status_value == "Error":
        return "table-error"
    elif status_value == "Passed":
        return "table-success"
    elif status_value == "Failed":
        return "table-danger"
    elif status_value == "Skipped":
        return "table-warning"
    elif status_value == "Running":
        return "table-secondary"
