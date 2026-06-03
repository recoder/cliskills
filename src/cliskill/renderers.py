"""Output rendering helpers."""

import json
from typing import Any, Literal

from pydantic import BaseModel

OutputFormat = Literal["json", "markdown", "toon"]
JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def _to_json_value(value: BaseModel | dict[str, Any] | list[Any]) -> JsonValue:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def render_json(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    """Render a JSON-compatible value as stable pretty JSON."""
    return json.dumps(_to_json_value(value), indent=2, sort_keys=True) + "\n"


def render_markdown(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    """Render a JSON-compatible value as readable Markdown."""
    data = _to_json_value(value)
    if not isinstance(data, dict):
        return "```json\n" + json.dumps(data, indent=2, sort_keys=True) + "\n```\n"

    lines = [
        f"# {data.get('name', 'Skill Manifest')}",
        "",
        str(data.get("description", "")),
        "",
        f"- Version: `{data.get('version', '')}`",
        f"- Contract version: `{data.get('contract_version', '')}`",
        "",
        "## Commands",
        "",
    ]

    commands = data.get("commands", [])
    if isinstance(commands, list) and commands:
        lines.extend(["| Name | Description | Formats |", "| --- | --- | --- |"])
        for command in commands:
            if not isinstance(command, dict):
                continue
            formats = command.get("formats", [])
            format_text = ""
            if isinstance(formats, list):
                format_text = ", ".join(f"`{item}`" for item in formats)
            command_name = command.get("name", "")
            description = command.get("description", "")
            lines.append(f"| `{command_name}` | {description} | {format_text} |")
    else:
        lines.append("No commands declared.")

    lines.extend(["", "## Capabilities", ""])
    capabilities = data.get("capabilities", {})
    if isinstance(capabilities, dict):
        for name, enabled in capabilities.items():
            lines.append(f"- `{name}`: `{str(enabled).lower()}`")
    else:
        lines.append("No capabilities declared.")

    return "\n".join(lines).rstrip() + "\n"


def render_toon(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    """Render a JSON-compatible value as a conservative TOON-like document."""
    return "\n".join(_toon_lines(_to_json_value(value), indent=0)).rstrip() + "\n"


def _toon_lines(value: JsonValue, indent: int) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(_toon_lines(child, indent + 1))
            elif isinstance(child, list):
                lines.extend(_toon_list_lines(key, child, indent))
            else:
                lines.append(f"{prefix}{key}: {_toon_scalar(child)}")
        return lines
    if isinstance(value, list):
        lines = []
        for element in value:
            if isinstance(element, dict | list):
                lines.append(f"{prefix}-")
                lines.extend(_toon_lines(element, indent + 1))
            else:
                lines.append(f"{prefix}- {_toon_scalar(element)}")
        return lines
    return [f"{prefix}{_toon_scalar(value)}"]


def _toon_list_lines(key: str, values: list[JsonValue], indent: int) -> list[str]:
    prefix = "  " * indent
    if not values:
        return [f"{prefix}{key}: []"]

    if all(isinstance(value_item, dict) for value_item in values):
        dict_values = [value_item for value_item in values if isinstance(value_item, dict)]
        keys = list(dict_values[0].keys())
        if all(list(dict_value.keys()) == keys for dict_value in dict_values):
            lines = [f"{prefix}{key}[{len(dict_values)}]{{{','.join(keys)}}}:"]
            for dict_value in dict_values:
                row = ",".join(_toon_scalar(dict_value[field]) for field in keys)
                lines.append(f"{prefix}  {row}")
            return lines

    lines = [f"{prefix}{key}:"]
    for value_item in values:
        if isinstance(value_item, dict | list):
            lines.append(f"{prefix}  -")
            lines.extend(_toon_lines(value_item, indent + 2))
        else:
            lines.append(f"{prefix}  - {_toon_scalar(value_item)}")
    return lines


def _toon_scalar(value: JsonValue) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        if value == "":
            return '""'
        if any(character in value for character in [":", ",", "\n", "{", "}", "[", "]", "#"]):
            return json.dumps(value)
        return value
    return json.dumps(value, sort_keys=True)


def render(value: BaseModel | dict[str, Any] | list[Any], output_format: OutputFormat) -> str:
    """Render a value in a supported output format."""
    if output_format == "json":
        return render_json(value)
    if output_format == "markdown":
        return render_markdown(value)
    if output_format == "toon":
        return render_toon(value)
    raise ValueError(f"Unsupported output format: {output_format}")
