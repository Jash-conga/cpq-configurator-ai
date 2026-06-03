"""
backend/state/running_json.py

Manages the in-memory running JSON — the single source of truth for all
records created during a conversation session.

Structure:
{
    "ObjectName": [
        { "uuid": "...", "field1": "value", ... },
        ...
    ]
}
"""

import json
import uuid as uuid_lib
from copy import deepcopy
from typing import Any, Optional

from utils.logger import get_logger

logger = get_logger("running_json")

# ── In-memory store ───────────────────────────────────────────────────────────
_store: dict[str, list[dict]] = {}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _generate_uuid() -> str:
    return str(uuid_lib.uuid4())


def _snapshot() -> dict:
    return deepcopy(_store)


# ── Public API ────────────────────────────────────────────────────────────────

def get_state() -> dict:
    """Return a deep copy of the current running JSON."""
    return _snapshot()


def add_record(object_name: str, payload: dict) -> str:
    """
    Add a new record for the given object.
    Assigns a UUID and stores it.
    Returns the generated UUID.
    """
    record_uuid = _generate_uuid()
    record = {"uuid": record_uuid, **{k: v for k, v in payload.items() if k != "uuid"}}

    _store.setdefault(object_name, [])
    _store[object_name].append(record)

    logger.json_mutation(
        operation="add_record",
        object_name=object_name,
        uuid=record_uuid,
        snapshot=_snapshot(),
    )
    return record_uuid


def update_record(object_name: str, record_uuid: str, updates: dict) -> bool:
    """
    Update fields on an existing record.
    Returns True on success, False if record not found.
    """
    records = _store.get(object_name, [])
    for record in records:
        if record.get("uuid") == record_uuid:
            for key, value in updates.items():
                if key != "uuid":
                    record[key] = value
            logger.json_mutation(
                operation="update_record",
                object_name=object_name,
                uuid=record_uuid,
                snapshot=_snapshot(),
            )
            return True

    logger.warning("update_record_not_found", object_name=object_name, uuid=record_uuid)
    return False


def get_record(object_name: str, record_uuid: str) -> Optional[dict]:
    """Retrieve a single record by object name and UUID."""
    for record in _store.get(object_name, []):
        if record.get("uuid") == record_uuid:
            return deepcopy(record)
    return None


def get_records_by_object(object_name: str) -> list[dict]:
    """Return all records for a given object."""
    return deepcopy(_store.get(object_name, []))


def delete_record(object_name: str, record_uuid: str) -> bool:
    """Remove a record from the running JSON. Returns True if deleted."""
    records = _store.get(object_name, [])
    original_len = len(records)
    _store[object_name] = [r for r in records if r.get("uuid") != record_uuid]
    deleted = len(_store[object_name]) < original_len
    if deleted:
        logger.json_mutation(
            operation="delete_record",
            object_name=object_name,
            uuid=record_uuid,
            snapshot=_snapshot(),
        )
    return deleted


def find_records_by_field(object_name: str, field_name: str, value: Any) -> list[dict]:
    """Search records of an object by a specific field value."""
    return [
        deepcopy(r)
        for r in _store.get(object_name, [])
        if r.get(field_name) == value
    ]


def resolve_reference(object_name: str, ref_field: str, display_value: str) -> Optional[str]:
    """
    Given a reference field and a human-readable value (e.g. a Name),
    try to find the UUID of the matching record in the running JSON.
    Returns the UUID string or None.
    """
    ref_records = _store.get(object_name, [])
    for rec in ref_records:
        if rec.get("Name") == display_value or rec.get("uuid") == display_value:
            return rec["uuid"]
    return None


def clear_state():
    """Wipe the entire running JSON. Used for testing or session reset."""
    global _store
    _store = {}
    logger.info("running_json_cleared")


def pretty_print() -> str:
    """Return a human-readable JSON string of the current state."""
    return json.dumps(_snapshot(), indent=2)


def print_state():
    """Print the running JSON to stdout with a clear header."""
    print("\n" + "═" * 60)
    print("  📦  RUNNING JSON STATE")
    print("═" * 60)
    print(pretty_print())
    print("═" * 60 + "\n")
