from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def say(context, key):
    return context["ui"][key]


@register.simple_tag(takes_context=True)
def tr(context, row, field):
    lang = context["lang"]
    return row.get(f"{field}_{lang}") or row.get(f"{field}_en") or ""
