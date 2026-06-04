"""
backend/salesforce/sf_lookupclient.py

Salesforce connection management and query helpers.
All direct Salesforce API calls live here — tools call these functions,
never the simple_salesforce API directly.
"""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from simple_salesforce import Salesforce, SalesforceLogin, SFType
from simple_salesforce.exceptions import SalesforceError

from utils.logger import get_logger

load_dotenv()
logger = get_logger("sf_lookupclient")


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

_sf_instance: Optional[Salesforce] = None


def get_sf() -> Salesforce:
    """
    Return a cached Salesforce connection.
    Prefers access-token auth (SF_INSTANCE_URL + SF_ACCESS_TOKEN) when both
    are present; falls back to username/password/security-token auth.
    Re-raises on failure so callers can surface the error to the agent.
    """
    global _sf_instance
    if _sf_instance is not None:
        return _sf_instance

    instance_url = os.getenv("SF_INSTANCE_URL", "").strip()
    access_token = os.getenv("SF_ACCESS_TOKEN", "").strip()

    if instance_url and access_token and not access_token.startswith("<"):
        logger.info("sf_connect_token", instance_url=instance_url)
        _sf_instance = Salesforce(
            instance_url=instance_url,
            session_id=access_token,
        )
    else:
        username = os.getenv("SF_USERNAME", "")
        password = os.getenv("SF_PASSWORD", "")
        token = os.getenv("SF_SECURITY_TOKEN", "")
        domain = os.getenv("SF_DOMAIN", "login")

        logger.info("sf_connect_password", username=username, domain=domain)
        _sf_instance = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain=domain,
        )

    logger.info("sf_connected")
    return _sf_instance


def reset_connection():
    """Force re-authentication on the next call (useful after token expiry)."""
    global _sf_instance
    _sf_instance = None
    logger.info("sf_connection_reset")


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _soql(query: str) -> list[dict]:
    """Run a SOQL query and return all records as plain dicts."""
    sf = get_sf()
    logger.info("soql_query", query=query)
    result = sf.query_all(query)
    records = result.get("records", [])
    # Strip the Salesforce metadata keys from each record
    cleaned = [
        {k: v for k, v in r.items() if k not in ("attributes",)}
        for r in records
    ]
    logger.info("soql_result", count=len(cleaned))
    return cleaned


def _build_field_list(sf_object: str, extra_fields: list[str] | None = None) -> str:
    """
    Return a comma-separated field list that always includes Id and Name
    (or the object's name-equivalent) plus any caller-specified extras.
    Falls back to 'Id, Name' if describe fails.
    """
    base = ["Id", "Name"]
    if extra_fields:
        for f in extra_fields:
            if f not in base:
                base.append(f)
    return ", ".join(base)


# ─────────────────────────────────────────────────────────────────────────────
# Public query functions (called by agent_tools.py)
# ─────────────────────────────────────────────────────────────────────────────

def lookup_records_by_name(
    object_name: str,
    name_value: str,
    extra_fields: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Search for records of *object_name* whose Name field contains *name_value*.
    Returns a list of matching records with at least Id and Name.

    Args:
        object_name:  Salesforce API object name, e.g. 'Apttus_Config2__PriceList__c'.
        name_value:   Substring to search for (case-insensitive LIKE).
        extra_fields: Additional field API names to include in the result.
        limit:        Max records to return (default 10).
    """
    fields = _build_field_list(object_name, extra_fields)
    safe_name = name_value.replace("'", "\\'")
    query = (
        f"SELECT {fields} FROM {object_name} "
        f"WHERE Name LIKE '%{safe_name}%' "
        f"LIMIT {limit}"
    )
    try:
        return _soql(query)
    except SalesforceError as exc:
        logger.error("lookup_by_name_failed", object_name=object_name, error=str(exc))
        return [{"error": str(exc)}]


def lookup_record_by_id(
    object_name: str,
    record_id: str,
    extra_fields: list[str] | None = None,
) -> dict:
    """
    Fetch a single record by its 15- or 18-character Salesforce Id.
    Returns the record dict, or a dict with an 'error' key on failure.

    Args:
        object_name:  Salesforce API object name.
        record_id:    The Salesforce record Id.
        extra_fields: Additional field API names to retrieve.
    """
    fields = _build_field_list(object_name, extra_fields)
    safe_id = record_id.strip().replace("'", "\\'")
    query = (
        f"SELECT {fields} FROM {object_name} "
        f"WHERE Id = '{safe_id}' "
        f"LIMIT 1"
    )
    try:
        rows = _soql(query)
        if not rows:
            return {"error": f"No record found with Id '{record_id}' in '{object_name}'."}
        return rows[0]
    except SalesforceError as exc:
        logger.error("lookup_by_id_failed", object_name=object_name, error=str(exc))
        return {"error": str(exc)}


def get_full_record_by_id(
    object_name: str,
    record_id: str,
) -> dict:
    """
    Retrieve ALL fields for a record using the REST describe + query path.
    Useful when the agent needs to inspect an existing Salesforce record in full
    before referencing it in a new payload.

    Args:
        object_name: Salesforce API object name.
        record_id:   The Salesforce record Id.
    """
    try:
        sf = get_sf()
        # Use simple_salesforce's per-object API to GET by Id
        sf_obj: SFType = getattr(sf, object_name)
        record = sf_obj.get(record_id)
        # Strip internal SF metadata
        cleaned = {k: v for k, v in record.items() if k != "attributes"}
        logger.info("get_full_record", object_name=object_name, record_id=record_id)
        return cleaned
    except SalesforceError as exc:
        logger.error("get_full_record_failed", object_name=object_name, error=str(exc))
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Deployment (existing stub — kept here for co-location)
# ─────────────────────────────────────────────────────────────────────────────

def deploy_running_json() -> dict:
    """
    Deploy all records in the running JSON to Salesforce.
    Returns a result summary dict.
    """
    from state import running_json  # local import to avoid circular deps

    sf = get_sf()
    state = running_json.get_state()
    results: dict[str, list] = {}

    for object_name, records in state.items():
        results[object_name] = []
        sf_obj: SFType = getattr(sf, object_name)
        for record in records:
            payload = {k: v for k, v in record.items() if k != "_uuid"}
            try:
                response = sf_obj.create(payload)
                results[object_name].append(
                    {"uuid": record.get("_uuid"), "sf_id": response.get("id"), "status": "created"}
                )
                logger.salesforce_op("create", object_name, payload, response)
            except SalesforceError as exc:
                results[object_name].append(
                    {"uuid": record.get("_uuid"), "error": str(exc), "status": "failed"}
                )
                logger.error("deploy_record_failed", object_name=object_name, error=str(exc))

    return results

if __name__ == "__main__":
    import json
    import sys

    # ── Config — change these two values before running ──────────────────────
    NAME_FILTER = "Test"          # partial name to search for (case-insensitive)
    # ─────────────────────────────────────────────────────────────────────────

    def _pretty(label: str, data) -> None:
        print(f"\n{'─' * 60}")
        print(f"  {label}")
        print('─' * 60)
        print(json.dumps(data, indent=2, default=str))

    # ── 1. Connection check ───────────────────────────────────────────────────
    print("\n[1] Connecting to Salesforce...")
    try:
        sf = get_sf()
        print(f"    ✓ Connected  |  base_url: {sf.base_url}")
    except Exception as exc:
        print(f"    ✗ Connection failed: {exc}")
        sys.exit(1)

    # ── 2. Lookup Account by name ─────────────────────────────────────────────
    print(f"\n[2] Account  — lookup by name containing '{NAME_FILTER}'")
    account_results = lookup_records_by_name(
        object_name="Account",
        name_value=NAME_FILTER,
        extra_fields=["Phone", "BillingCity", "Type"],
        limit=5,
    )
    _pretty(f"Account name LIKE '%{NAME_FILTER}%'  (max 5)", account_results)

    # ── 3. Lookup Product2 by name ────────────────────────────────────────────
    print(f"\n[3] Product2 — lookup by name containing '{NAME_FILTER}'")
    product_results = lookup_records_by_name(
        object_name="Product2",
        name_value=NAME_FILTER,
        extra_fields=["ProductCode", "IsActive", "Family"],
        limit=5,
    )
    _pretty(f"Product2 name LIKE '%{NAME_FILTER}%'  (max 5)", product_results)

    # ── 4. Validate by Id (uses first Account result if one was found) ────────
    first_account = next(
        (r for r in account_results if "Id" in r),
        None,
    )
    if first_account:
        record_id = first_account["Id"]
        print(f"\n[4] Validate Account Id  →  {record_id}")
        validated = lookup_record_by_id(
            object_name="Account",
            record_id=record_id,
            extra_fields=["Phone", "BillingCity"],
        )
        _pretty(f"lookup_record_by_id('Account', '{record_id}')", validated)

        # ── 5. Full record details for the same Account ───────────────────────
        print(f"\n[5] Full record details for Account  →  {record_id}")
        full = get_full_record_by_id(object_name="Account", record_id=record_id)
        _pretty(f"get_full_record_by_id('Account', '{record_id}')", full)
    else:
        print(f"\n[4] Skipping Id validation — no Account matched '{NAME_FILTER}'")
        print(f"[5] Skipping full record fetch — no Account matched '{NAME_FILTER}'")

    # ── 6. Validate by Id (uses first Product2 result if one was found) ───────
    first_product = next(
        (r for r in product_results if "Id" in r),
        None,
    )
    if first_product:
        record_id = first_product["Id"]
        print(f"\n[6] Full record details for Product2  →  {record_id}")
        full_product = get_full_record_by_id(object_name="Product2", record_id=record_id)
        _pretty(f"get_full_record_by_id('Product2', '{record_id}')", full_product)
    else:
        print(f"\n[6] Skipping Product2 full fetch — no Product2 matched '{NAME_FILTER}'")

    print(f"\n{'═' * 60}")
    print("  All tests complete.")
    print('═' * 60)
