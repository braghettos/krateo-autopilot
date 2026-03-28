"""
Pure Python port of krateoctl's internal/schema package.
Parses # @schema annotated YAML files and generates JSON Schema.

Based on:
  https://github.com/krateoplatformops/krateoctl/tree/main/internal/schema

Annotation format (same as krateoctl gen-schema):

  # @schema
  # type: string
  # required: true
  # description: My field
  # @schema
  myKey: myValue

Supported annotations: type, title, description, default, pattern, required,
deprecated, items, enum, const, examples, minimum, exclusiveMinimum, maximum,
exclusiveMaximum, multipleOf, additionalProperties, minLength, maxLength,
minItems, maxItems, anyOf, allOf, oneOf, not, if, then, else, $ref, format,
patternProperties, readOnly, writeOnly, uniqueItems.
"""

from __future__ import annotations

import json
import logging
from io import StringIO
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

log = logging.getLogger(__name__)

SCHEMA_PREFIX = "@schema"

YAML_TYPE_MAP = {
    # ruamel.yaml tag strings
    "tag:yaml.org,2002:null": "null",
    "tag:yaml.org,2002:bool": "boolean",
    "tag:yaml.org,2002:str": "string",
    "tag:yaml.org,2002:int": "integer",
    "tag:yaml.org,2002:float": "number",
    "tag:yaml.org,2002:timestamp": "string",
    "tag:yaml.org,2002:seq": "array",
    "tag:yaml.org,2002:map": "object",
}


# ---- Comment helpers -------------------------------------------------------- #

def _get_head_comment(cm: CommentedMap, key: Any, key_index: int, keys: list) -> str:
    """
    Return the raw comment string that precedes *key* inside CommentedMap *cm*.

    ruamel.yaml stores comments as:
      - First key in a mapping  → cm.ca.comment[1]  (list[CommentToken])
      - Subsequent keys          → cm.ca.items[prev_key][2]  (CommentToken)
    """
    ca = cm.ca
    if key_index == 0:
        if ca.comment and ca.comment[1]:
            return "".join(t.value for t in ca.comment[1] if t)
    else:
        prev_key = keys[key_index - 1]
        if prev_key in ca.items and ca.items[prev_key][2] is not None:
            return ca.items[prev_key][2].value
    return ""


# ---- Annotation parsing ----------------------------------------------------- #

def _parse_annotation(comment: str) -> tuple[dict, str]:
    """
    Parse a raw comment string for a # @schema … # @schema block.

    Returns (schema_dict, plain_description).
    """
    if not comment:
        return {}, ""

    raw_schema: list[str] = []
    description: list[str] = []
    inside = False

    for line in comment.splitlines():
        stripped = line.strip()
        # Strip leading '#' and optional space
        content = stripped.lstrip("#").lstrip(" ")

        if content.strip() == SCHEMA_PREFIX:
            inside = not inside
            continue

        if inside:
            raw_schema.append(content)
        else:
            description.append(content)

    schema_dict: dict = {}
    if raw_schema:
        loader = YAML()
        try:
            parsed = loader.load("\n".join(raw_schema))
            if isinstance(parsed, dict):
                schema_dict = dict(parsed)
        except Exception as exc:
            log.warning("Failed to parse @schema annotation: %s", exc)

    return schema_dict, "\n".join(description).strip()


# ---- Type inference --------------------------------------------------------- #

def _infer_type(value: Any) -> str:
    """Infer JSON Schema type from a ruamel.yaml-loaded Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, CommentedSeq):
        return "array"
    if isinstance(value, CommentedMap):
        return "object"
    return "string"


# ---- Schema builder --------------------------------------------------------- #

def _build_schema(cm: CommentedMap) -> dict:
    """
    Recursively build a JSON Schema properties dict from a CommentedMap.
    """
    properties: dict = {}
    keys = list(cm.keys())

    for idx, key in enumerate(keys):
        value = cm[key]
        comment_text = _get_head_comment(cm, key, idx, keys)
        ann, description = _parse_annotation(comment_text)
        has_annotation = bool(ann)

        prop: dict = {}
        if has_annotation:
            prop.update(ann)
        else:
            prop["type"] = _infer_type(value)

        # Title default
        if "title" not in prop:
            prop["title"] = str(key)

        # Description from plain comment lines
        if "description" not in prop and description:
            prop["description"] = description

        # Default from value (scalars only)
        if "default" not in prop and not isinstance(value, (CommentedMap, CommentedSeq)) and value is not None:
            prop["default"] = value

        # Recurse into nested mappings
        if isinstance(value, CommentedMap) and "properties" not in prop:
            prop.setdefault("type", "object")
            prop.setdefault("additionalProperties", True)
            nested = _build_schema(value)
            prop["properties"] = nested

        # Recurse into sequences (infer items type from first element)
        if isinstance(value, CommentedSeq) and "items" not in prop:
            prop.setdefault("type", "array")
            if value:
                first = value[0]
                if isinstance(first, CommentedMap):
                    prop["items"] = {"type": "object", "properties": _build_schema(first)}
                else:
                    prop["items"] = {"type": _infer_type(first)}

        properties[str(key)] = prop

    return properties


def _fix_required(schema: dict) -> None:
    """
    Convert boolean ``required: true`` annotations into the parent schema's
    ``required`` array (mirrors krateoctl FixRequiredProperties).
    """
    props = schema.get("properties", {})
    if props:
        schema.setdefault("type", "object")
        required_list: list[str] = schema.setdefault("required", [])
        for prop_name, prop_schema in props.items():
            _fix_required(prop_schema)
            if prop_schema.pop("required", False) is True:
                if prop_name not in required_list:
                    required_list.append(prop_name)
        if not schema["required"]:
            del schema["required"]

    for key in ("items", "if", "then", "else", "not"):
        sub = schema.get(key)
        if isinstance(sub, dict):
            _fix_required(sub)

    for key in ("anyOf", "allOf", "oneOf"):
        for sub in schema.get(key, []):
            if isinstance(sub, dict):
                _fix_required(sub)

    ap = schema.get("additionalProperties")
    if isinstance(ap, dict):
        _fix_required(ap)


# ---- Public API ------------------------------------------------------------- #

def from_yaml(values_content: str) -> dict:
    """
    Parse a values.yaml string (with optional # @schema annotations) and
    return a JSON Schema dict compatible with ``krateoctl gen-schema`` output.
    """
    loader = YAML()
    try:
        data = loader.load(StringIO(values_content))
    except Exception as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc

    if data is None:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    if not isinstance(data, CommentedMap):
        raise ValueError("values.yaml root must be a YAML mapping")

    properties = _build_schema(data)

    root: dict = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "additionalProperties": True,
    }
    _fix_required(root)
    return root


def generate_schema_json(values_yaml: str) -> str:
    """
    Generate a values.schema.json string from a values.yaml string.
    Matches the output of ``krateoctl gen-schema``.
    """
    return json.dumps(from_yaml(values_yaml), indent=2)
