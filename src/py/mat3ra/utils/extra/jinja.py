import os
import re
from typing import Any, Callable, Dict, Optional

from jinja2 import Environment, FileSystemLoader, TemplateError


def render_template_file(template_file_path: str, **kwargs):
    """
    Renders a given template file.

    Args:
        template_file_path (str): template file path
        kwargs: variables passed to the template

    Returns:
        str
    """
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_file_path)))
    template = env.get_template(os.path.basename(template_file_path))
    return template.render(**kwargs)


def render_template_string(
    template_string: str,
    *,
    filters: Optional[Dict[str, Callable]] = None,
    finalize: Optional[Callable[[Any], Any]] = None,
    **kwargs,
):
    """
    Renders a given template string.

    Args:
        template_string (str): template string
        filters: additional Jinja filters, scoped to this call
        finalize: optional Jinja output-value formatter
        kwargs: variables passed to the template

    Returns:
        str
    """
    environment = Environment(finalize=finalize)
    environment.filters.update(filters or {})
    template = environment.from_string(template_string)
    return template.render(**kwargs)


def render_jinja_with_error_handling(
    template_string: str,
    *,
    filters: Optional[Dict[str, Callable]] = None,
    finalize: Optional[Callable[[Any], Any]] = None,
    raise_errors: bool = False,
    **kwargs,
):
    """
    Renders a given template string with error handling.

    Args:
        template_string (str): template string
        filters: additional Jinja filters, scoped to this call
        finalize: optional Jinja output-value formatter
        raise_errors: propagate TemplateError instead of returning diagnostic text
        kwargs: variables passed to the template

    Returns:
        str
    """
    try:
        return render_template_string(template_string, filters=filters, finalize=finalize, **kwargs)
    except TemplateError as e:
        if raise_errors:
            raise
        return (
            f"Error rendering template: {str(e)}\nTemplate content:\n{template_string}\nTemplate variables:\n{kwargs}"
        )


NUMERIC_VALUE_PATTERN = r"[\d.e+\-]+"
JINJA_EXPRESSION_PATTERN = r"\{\{[^}]+\}\}"


def wrap_text_in_raw_block(text: str) -> str:
    return f"{{% raw %}}{text}{{% endraw %}}"


def replace_in_text(content: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, content)
