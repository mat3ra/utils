import pytest
from pathlib import Path

from jinja2 import TemplateError
from mat3ra.utils.extra import jinja as utils

FILE_JINJA_TEMPLATE_PATH = Path(__file__).parent / "./fixtures/file_jinja_template.jinja"

TEXT_SIMPLE_VAR = "{{ variable_name }}"
TEXT_DOTTED_VAR = "{{ scope.variable_name }}"
EXPECTED_RAW_SIMPLE = "{% raw %}{{ variable_name }}{% endraw %}"
EXPECTED_RAW_DOTTED = "{% raw %}{{ scope.variable_name }}{% endraw %}"

CONTENT_NUMERIC_VALUE = "variable_name = 0.005\n"
CONTENT_JINJA_VALUE = "variable_name = {{ scope.variable_name }}\n"
CONTENT_NO_MATCH = "no_match = value\n"

PATTERN_NUMERIC_VALUE = r"variable_name\s*=\s*[\d.e+\-]+"
PATTERN_JINJA_VALUE = r"variable_name\s*=\s*\{\{[^}]+\}\}"
PATTERN_OTHER_NUMERIC = r"other\s*=\s*[\d.e+\-]+"

REPLACEMENT_RAW_VALUE = "variable_name = {% raw %}{{ variable_name }}{% endraw %}"
REPLACEMENT_OTHER = "other = x"

EXPECTED_NUMERIC_REPLACED = "variable_name = {% raw %}{{ variable_name }}{% endraw %}\n"
EXPECTED_JINJA_REPLACED = "variable_name = {% raw %}{{ variable_name }}{% endraw %}\n"


def test_render_template():
    context = {"name": "World"}
    rendered = utils.render_template_file(FILE_JINJA_TEMPLATE_PATH, **context)
    assert rendered == "Hello, World!"


def test_render_template_string():
    context = {"name": "World"}
    rendered = utils.render_template_string("Hello, {{ name }}!", **context)
    assert rendered == "Hello, World!"


@pytest.mark.parametrize("render", [utils.render_template_string, utils.render_jinja_with_error_handling])
def test_custom_filters_are_local_and_keep_builtins(render):
    filters = {"sprintf": lambda value, pattern: pattern % value}
    rendered = render('{{ value | sprintf("%.2f") }} {{ name | upper }}', filters=filters, value=1.25, name="silicon")
    assert rendered == "1.25 SILICON"
    with pytest.raises(TemplateError):
        utils.render_template_string('{{ value | sprintf("%.2f") }}', value=1.25)
    assert list(filters) == ["sprintf"]


def test_output_formatter_and_raw_runtime_placeholder():
    rendered = utils.render_jinja_with_error_handling(
        "{{ value }} {% raw %}{{ JOB_WORK_DIR }}{% endraw %}",
        finalize=lambda value: int(value) if isinstance(value, float) and value.is_integer() else value,
        value=4.0,
    )
    assert rendered == "4 {{ JOB_WORK_DIR }}"
    assert utils.render_jinja_with_error_handling("{{ value }}", value=4.0) == "4.0"


def test_default_error_text_and_opt_in_exception():
    template = "{{ value | missing_filter }}"
    assert utils.render_jinja_with_error_handling(template, value=1).startswith("Error rendering template:")
    with pytest.raises(TemplateError):
        utils.render_jinja_with_error_handling(template, raise_errors=True, value=1)


@pytest.mark.parametrize(
    "text,expected",
    [
        (TEXT_SIMPLE_VAR, EXPECTED_RAW_SIMPLE),
        (TEXT_DOTTED_VAR, EXPECTED_RAW_DOTTED),
    ],
)
def test_wrap_text_in_raw_block(text, expected):
    assert utils.wrap_text_in_raw_block(text) == expected


@pytest.mark.parametrize(
    "content,pattern,replacement,expected",
    [
        (CONTENT_NUMERIC_VALUE, PATTERN_NUMERIC_VALUE, REPLACEMENT_RAW_VALUE, EXPECTED_NUMERIC_REPLACED),
        (CONTENT_JINJA_VALUE, PATTERN_JINJA_VALUE, REPLACEMENT_RAW_VALUE, EXPECTED_JINJA_REPLACED),
        (CONTENT_NO_MATCH, PATTERN_OTHER_NUMERIC, REPLACEMENT_OTHER, CONTENT_NO_MATCH),
    ],
)
def test_replace_in_text(content, pattern, replacement, expected):
    assert utils.replace_in_text(content, pattern, replacement) == expected
