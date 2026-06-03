"""
backend/tools/agent_tools.py

LangChain-compatible tools used by the CPQ agent.
Each tool is a focused, single-responsibility function that the LLM can call.
"""

from typing import Optional
from langchain_core.tools import tool

from schema import schema_loader
from state import running_json
from utils.logger import get_logger

logger = get_logger("agent_tools")


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_object_schema(object_name: str) -> dict:
    """
    Fetch the full schema definition for a Salesforce object from the CPQ schema.
    Returns object metadata including fields, types, and relationships.
    Use this before building any record payload.

    Args:
        object_name: The Salesforce API name of the object (e.g. 'Product2').
    """
    schema = schema_loader.get_object_schema(object_name)
    if not schema:
        return {
            "error": f"Object '{object_name}' is not in the CPQ schema. "
                     f"Available objects: {schema_loader.list_objects()}"
        }
    logger.tool_call("get_object_schema", {"object_name": object_name}, schema)
    return schema


@tool
def list_available_objects() -> list:
    """
    Return the list of all Salesforce objects available in the CPQ schema.
    Use this to check scope before attempting to create records.
    """
    objects = schema_loader.list_objects()
    logger.tool_call("list_available_objects", {}, objects)
    return objects


@tool
def get_required_fields(object_name: str) -> list:
    """
    Return the required field names for a given Salesforce object.
    Always check required fields before finalising a record payload.

    Args:
        object_name: The Salesforce API name of the object.
    """
    fields = schema_loader.get_required_fields(object_name)
    logger.tool_call("get_required_fields", {"object_name": object_name}, fields)
    return fields


# ─────────────────────────────────────────────────────────────────────────────
# RUNNING JSON TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def create_record(object_name: str, payload: dict) -> dict:
    """
    Create a new record in the running JSON for the given Salesforce object.
    Assigns a UUID automatically. Returns the created record including its UUID.
    Only use fields that exist in the schema.

    Args:
        object_name: The Salesforce API name of the object (e.g. 'Product2').
        payload: A dictionary of field API names to values.
    """
    # Validate object is in schema
    if not schema_loader.get_object_schema(object_name):
        return {"error": f"Object '{object_name}' is not in scope."}

    # Only keep fields that exist in the schema
    valid_fields = schema_loader.get_field_names(object_name)
    filtered = {k: v for k, v in payload.items() if k in valid_fields}
    ignored = set(payload.keys()) - set(valid_fields)
    if ignored:
        logger.warning("create_record_ignored_fields", object_name=object_name, fields=list(ignored))

    record_uuid = running_json.add_record(object_name, filtered)
    record = running_json.get_record(object_name, record_uuid)

    running_json.print_state()
    logger.tool_call("create_record", {"object_name": object_name, "payload": filtered}, record)
    return record


@tool
def update_record(object_name: str, record_uuid: str, updates: dict) -> dict:
    """
    Update fields on an existing record in the running JSON.
    Use the record's UUID to identify which record to update.

    Args:
        object_name: The Salesforce API name of the object.
        record_uuid: The UUID of the record to update.
        updates: Dictionary of field names and new values.
    """
    success = running_json.update_record(object_name, record_uuid, updates)
    if not success:
        return {"error": f"Record with UUID '{record_uuid}' not found in '{object_name}'."}

    record = running_json.get_record(object_name, record_uuid)
    running_json.print_state()
    logger.tool_call("update_record", {"object_name": object_name, "uuid": record_uuid}, record)
    return record


@tool
def get_all_records(object_name: str) -> list:
    """
    Retrieve all records for a given object from the running JSON.

    Args:
        object_name: The Salesforce API name of the object.
    """
    records = running_json.get_records_by_object(object_name)
    logger.tool_call("get_all_records", {"object_name": object_name}, records)
    return records


@tool
def get_running_json() -> dict:
    """
    Return the complete current state of the running JSON.
    Use this to review all records created so far.
    """
    state = running_json.get_state()
    logger.tool_call("get_running_json", {}, state)
    return state


@tool
def delete_record(object_name: str, record_uuid: str) -> dict:
    """
    Delete a record from the running JSON by its UUID.

    Args:
        object_name: The Salesforce API name of the object.
        record_uuid: The UUID of the record to delete.
    """
    success = running_json.delete_record(object_name, record_uuid)
    if not success:
        return {"error": f"Record '{record_uuid}' not found in '{object_name}'."}

    running_json.print_state()
    logger.tool_call("delete_record", {"object_name": object_name, "uuid": record_uuid}, "deleted")
    return {"status": "deleted", "uuid": record_uuid, "object": object_name}


@tool
def build_empty_record_template(object_name: str) -> dict:
    """
    Build an empty record template for a Salesforce object with all schema fields set to null.
    Use this to understand what fields are available before asking the user for values.

    Args:
        object_name: The Salesforce API name of the object.
    """
    template = schema_loader.build_empty_payload(object_name)
    logger.tool_call("build_empty_record_template", {"object_name": object_name}, template)
    return template


# ─────────────────────────────────────────────────────────────────────────────
# SALESFORCE DEPLOYMENT TOOLS (stub — wired in salesforce/sf_client.py)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def deploy_to_salesforce() -> dict:
    """
    Deploy all records in the running JSON to Salesforce.
    This will create real records in the connected Salesforce org.
    Only call this when the user explicitly asks to deploy.
    """
    from backend.salesforce.sf_client import deploy_running_json
    logger.info("deploy_to_salesforce_triggered")
    result = deploy_running_json()
    logger.salesforce_op("deploy_all", "ALL", {}, result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Tool registry — import this list into the agent
# ─────────────────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    get_object_schema,
    list_available_objects,
    get_required_fields,
    create_record,
    update_record,
    get_all_records,
    get_running_json,
    delete_record,
    build_empty_record_template,
    deploy_to_salesforce,
]
