"""
backend/schema/schema_loader.py

Responsible for loading, validating, and querying the CPQ schema JSON.
This is the single source of truth for which Salesforce objects and fields
the agent is allowed to work with.
"""

import json
import os
from pathlib import Path
from typing import Optional

from utils.logger import get_logger

logger = get_logger("schema_loader")

_schema_cache: dict = {}


def load_schema(path: Optional[str] = None) -> dict:
    """
    Load the schema JSON from disk into the in-process cache.
    Subsequent calls return the cached version unless force=True.
    """
    global _schema_cache

    if _schema_cache:
        return _schema_cache

    path_str = path or os.getenv("SCHEMA_PATH", "config/schema.json")
    schema_path = Path(path_str)

    # If relative path and does not exist in current working directory, 
    # check relative to the project root (which is 3 levels up from this file: backend/schema/schema_loader.py)
    if not schema_path.is_absolute() and not schema_path.exists():
        project_root = Path(__file__).resolve().parent.parent.parent
        alternate_path = project_root / path_str
        if alternate_path.exists():
            schema_path = alternate_path

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path.resolve()}")

    with open(schema_path, "r", encoding="utf-8") as fh:
        _schema_cache = json.load(fh)

    logger.info("schema_loaded", path=str(schema_path), objects=list(_schema_cache.keys()))
    return _schema_cache


def get_object_schema(object_name: str) -> Optional[dict]:
    """
    Return the full schema definition for a single Salesforce object.
    Returns None if the object is not in scope.
    """
    schema = load_schema()
    result = schema.get(object_name)
    logger.tool_call(
        tool="get_object_schema",
        inputs={"object_name": object_name},
        result="found" if result else "not_found",
    )
    return result


def list_objects() -> list[str]:
    """Return all object names present in the schema."""
    return list(load_schema().keys())


def get_field_names(object_name: str) -> list[str]:
    """Return the list of field API names for a given object."""
    obj = get_object_schema(object_name)
    if not obj:
        return []
    return [f["name"] for f in obj.get("fields", [])]


def get_field_meta(object_name: str, field_name: str) -> Optional[dict]:
    """Return metadata for a specific field on an object."""
    obj = get_object_schema(object_name)
    if not obj:
        return None
    for field in obj.get("fields", []):
        if field["name"] == field_name:
            return field
    return None


def get_required_fields(object_name: str) -> list[str]:
    """Return field names that are marked as required in the schema."""
    obj = get_object_schema(object_name)
    if not obj:
        return []
    return [f["name"] for f in obj.get("fields", []) if f.get("required")]


def get_reference_fields(object_name: str) -> list[dict]:
    """Return all reference (lookup/master-detail) fields for an object."""
    obj = get_object_schema(object_name)
    if not obj:
        return []
    return [f for f in obj.get("fields", []) if f.get("type") == "reference"]


def build_empty_payload(object_name: str) -> dict:
    """
    Build an empty record payload with all schema fields set to None.
    The agent fills these in progressively.
    """
    obj = get_object_schema(object_name)
    if not obj:
        return {}
    payload = {}
    for field in obj.get("fields", []):
        name = field["name"]
        if name == "Id":
            continue  # skip auto-generated ID field
        payload[name] = None
    return payload