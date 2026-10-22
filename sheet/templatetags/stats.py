from django import template
from django.utils.html import format_html

from sheet.stats import Ref, Stat

register = template.Library()


@register.simple_tag
def stat(value, compact=False, bare=False):
    """Print a Stat with its citation. Anything else is refused. `bare` drops the unit, for columns whose header names it."""
    if not isinstance(value, Stat):
        raise template.TemplateSyntaxError(f"stat tag needs a Stat, got {type(value).__name__}")
    source = value.source
    classes = "stat" + (" blank" if value.blank else "") + ("" if value.checked else " unchecked")
    label = source.short.rsplit(" ", 1)[-1] if compact else source.short
    text = value.number() if bare else value.text()
    if compact and value.blank:
        text = "no gap" if value.printed == "derived" else "blank"
    return format_html(
        '<span class="{}"><span class="v" title="{}">{}</span>'
        '<a class="cite" href="{}" title="{}" rel="noopener">{}</a></span>',
        classes,
        value.text(),
        text,
        source.url,
        source.full,
        label,
    )


@register.simple_tag
def parts(sentence):
    """Print a sentence built from strings, Stats, and Refs."""
    out = []
    for part in sentence:
        if isinstance(part, Stat):
            out.append(stat(part))
        elif isinstance(part, Ref):
            out.append(format_html('<span class="ref">{}</span>', part.text))
        else:
            out.append(format_html("{}", part))
    return format_html("".join(["{}"] * len(out)), *out)
