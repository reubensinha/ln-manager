"""Validation and secret masking for plugin settings (see BasePlugin.get_settings_schema)."""

from typing import Any

from backend.core.exceptions import ValidationError

# Returned in place of a stored secret, and accepted on write to mean "keep what's stored".
SECRET_SENTINEL = "__unchanged__"

_PY_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "boolean": (bool,),
}


def defaults_for(schema: dict[str, Any]) -> dict[str, Any]:
    """Values a plugin should see before the user has saved anything."""
    return {
        field: spec["default"]
        for field, spec in schema.items()
        if isinstance(spec, dict) and "default" in spec
    }


def mask_secrets(schema: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Replace stored secrets with the sentinel so they never reach the browser."""
    masked = dict(values)
    for field, spec in schema.items():
        if not isinstance(spec, dict) or not spec.get("secret"):
            continue
        masked[field] = SECRET_SENTINEL if values.get(field) else None
    return masked


def validate_and_merge(
    schema: dict[str, Any], incoming: dict[str, Any], stored: dict[str, Any]
) -> dict[str, Any]:
    """Check `incoming` against `schema` and merge it over `stored`.

    Unknown keys and wrong types are rejected rather than silently dropped, so a typo in
    a settings form surfaces instead of being ignored. A secret left as the sentinel
    keeps its stored value.
    """
    unknown = set(incoming) - set(schema)
    if unknown:
        raise ValidationError(f"Unknown setting(s): {', '.join(sorted(unknown))}")

    merged = dict(stored)
    for field, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        if field not in incoming:
            continue

        value = incoming[field]
        if spec.get("secret") and value == SECRET_SENTINEL:
            continue  # keep the stored secret

        if value is None:
            merged.pop(field, None)
            continue

        expected = _PY_TYPES.get(spec.get("type", "string"))
        # bool is a subclass of int, so a checkbox value would pass a "number" check.
        if expected and (not isinstance(value, expected) or (expected != (bool,) and isinstance(value, bool))):
            raise ValidationError(
                f"Setting '{field}' must be of type {spec.get('type', 'string')}"
            )

        allowed = spec.get("enum")
        if allowed and value not in allowed:
            raise ValidationError(
                f"Setting '{field}' must be one of: {', '.join(map(str, allowed))}"
            )

        merged[field] = value

    missing = [
        field
        for field, spec in schema.items()
        if isinstance(spec, dict) and spec.get("required") and merged.get(field) in (None, "")
    ]
    if missing:
        raise ValidationError(f"Missing required setting(s): {', '.join(sorted(missing))}")

    return merged
