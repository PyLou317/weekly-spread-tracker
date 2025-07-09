from django import template

register = template.Library()

@register.filter
def first_last(name):
    if name and ',' in name:
        last, first = name.split(',', 1)
        return f"{first.strip()} {last.strip()}"
    return name 