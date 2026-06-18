"""Shared Pydantic-friendly validation helpers.

Centralised here so every schema that accepts a URL or a slug-style
identifier applies the *same* rules — this is what was missing for the
admin Tour schemas (AdminTourCreate/AdminTourUpdate had no validation at
all), which is what allowed quote characters into `name`/`img_url` and
broke the admin panel's HTML attribute escaping (see audit finding #2/#5).
"""

import re

# Slug-style IDs: lowercase/uppercase letters, digits, underscore, hyphen.
# Deliberately excludes spaces, quotes, angle brackets, slashes — anything
# that could break out of an HTML attribute or a URL path segment.
SLUG_PATTERN = r"^[a-zA-Z0-9_\-]+$"

_ALLOWED_URL_SCHEMES = ("https://", "http://")


def validate_http_url(value: str, *, field_name: str = "URL") -> str:
    """Raise ValueError unless `value` is a plain http(s) URL.

    Blocks `javascript:`, `data:`, `vbscript:` and similar pseudo-schemes
    that would otherwise execute when rendered into `src=`/`href=`
    attributes on the admin panel or public site.
    """
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{field_name} не может быть пустым")
    if not value.startswith(_ALLOWED_URL_SCHEMES):
        raise ValueError(f"{field_name} должен быть валидным HTTP(S) URL")
    # Defence in depth: reject characters that have no business in a URL
    # and that would be dangerous if ever echoed into an HTML attribute
    # without escaping.
    if re.search(r"[\"'<>\s]", value):
        raise ValueError(f"{field_name} содержит недопустимые символы")
    return value
