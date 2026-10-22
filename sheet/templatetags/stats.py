from django import template
from django.utils.html import format_html

from sheet.stats import Stat

register = template.Library()


@register.simple_tag
def stat(value, compact=False):
    """Print a Stat with its citation. Anything else is refused."""
    if not isinstance(value, Stat):
        raise template.TemplateSyntaxError(f"stat tag needs a Stat, got {type(value).__name__}")
    source = value.source
    classes = "stat" + (" blank" if value.blank else "") + ("" if value.checked else " unchecked")
    label = source.short.rsplit(" ", 1)[-1] if compact else source.short
    return format_html(
        '<span class="{}"><span class="v">{}</span>'
        '<a class="cite" href="{}" title="{}" rel="noopener">{}</a></span>',
        classes,
        value.text(),
        source.url,
        source.full,
        label,
    )


@register.simple_tag
def parts(sentence):
    """Print a sentence built from strings and Stats."""
    out = []
    for part in sentence:
        out.append(stat(part) if isinstance(part, Stat) else format_html("{}", part))
    return format_html("".join(["{}"] * len(out)), *out)
