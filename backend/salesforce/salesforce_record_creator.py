"""
Salesforce Record Creator
=========================
Creates Salesforce records from a structured JSON payload, following a
strict hierarchy order. UUID fields in the payload are used for
cross-referencing between records (e.g., linking a PriceListItem to a
Product2). After creation, each UUID is mapped to the real Salesforce
record ID.
 
Hierarchy (creation order):
    1. Product2
    2. Apttus_Config2__PriceList__c
    3. Apttus_Config2__PriceListItem__c
    4. Apttus_Config2__ProductOptionGroup__c
    5. Apttus_Config2__ProductOptionComponent__c
    6. Apttus_Config2__ProductOptionPrice__c
 
Usage:
    from simple_salesforce import Salesforce
    from salesforce_record_creator import SalesforceRecordCreator
 
    sf = Salesforce(...)  # auth already handled
    creator = SalesforceRecordCreator(sf)
    result = creator.create_records(payload)
"""
 
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
 
logger = logging.getLogger(__name__)
 
# ── Hierarchy definition ────────────────────────────────────────────────
# Records are created top-down. Objects earlier in this list are created
# first so that their Salesforce IDs are available when later objects
# reference them via UUID.
CREATION_HIERARCHY: List[str] = [
    "Product2",
    "Apttus_Config2__PriceList__c",
    "Apttus_Config2__PriceListItem__c",
    "Apttus_Config2__ClassificationHierarchy__c",
    "Apttus_Config2__ProductOptionGroup__c",
    "Apttus_Config2__ProductOptionComponent__c",
    "Apttus_Config2__ProductOptionPrice__c",
]
 
# Regex pattern for UUID v4 (used to identify UUID references in field values)
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
 
 
class SalesforceRecordCreator:
    """Orchestrates hierarchical Salesforce record creation with UUID resolution.
 
    Parameters
    ----------
    sf_connection : simple_salesforce.Salesforce
        An authenticated ``simple_salesforce.Salesforce`` instance.
    """
 
    def __init__(self, sf_connection) -> None:
        self.sf = sf_connection
 
        # uuid  →  Salesforce 18-char ID  (populated as records are created)
        self._uuid_to_id_map: Dict[str, str] = {}
 
        # Set of every UUID present in the payload (collected up-front so we
        # can distinguish a UUID reference from a regular string value).
        self._all_uuids: Set[str] = set()
 
        # UUIDs whose parent record creation failed – any child that
        # references one of these will be skipped.
        self._failed_uuids: Set[str] = set()
 
        # Per-record creation results (success / skipped / failed).
        self._results: List[Dict[str, Any]] = []
 
    # ── Public API ──────────────────────────────────────────────────────
 
    def create_records(self, payload: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Create Salesforce records from *payload* following the hierarchy.
 
        Parameters
        ----------
        payload : dict
            Keys are Salesforce object API names; values are lists of
            record dicts.  Each record dict **must** contain a ``uuid``
            key used for cross-referencing.  Fields whose string value
            matches another record's UUID will be resolved to the
            corresponding Salesforce ID at creation time.
 
        Returns
        -------
        dict
            ``uuid_to_id_map`` – mapping of every successfully created
            record's UUID to its Salesforce ID.
            ``results`` – ordered list of per-record outcomes.
        """
        # Reset state so the same instance can be reused.
        self._uuid_to_id_map.clear()
        self._all_uuids.clear()
        self._failed_uuids.clear()
        self._results.clear()
 
        # 1. Collect every UUID in the payload for reference detection.
        self._collect_all_uuids(payload)
 
        # 2. Walk the hierarchy and create records level by level.
        for object_name in CREATION_HIERARCHY:
            if object_name not in payload:
                continue
            records = payload[object_name]
            logger.info(
                "Processing %d record(s) for %s", len(records), object_name
            )
            for record in records:
                self._process_record(object_name, record)
 
        # 3. Warn about any objects in the payload that were NOT in the
        #    hierarchy (safety net – should not happen per requirements).
        unknown_objects = set(payload.keys()) - set(CREATION_HIERARCHY)
        if unknown_objects:
            logger.warning(
                "Payload contained objects not in the hierarchy – skipped: %s",
                unknown_objects,
            )
 
        return {
            "uuid_to_id_map": dict(self._uuid_to_id_map),
            "results": list(self._results),
        }
 
    # ── Internal helpers ────────────────────────────────────────────────
 
    def _collect_all_uuids(self, payload: Dict[str, List[Dict[str, Any]]]) -> None:
        """Scan every record in the payload and store its UUID."""
        for records in payload.values():
            for record in records:
                uuid = record.get("uuid")
                if uuid:
                    self._all_uuids.add(uuid)
 
    def _is_uuid_reference(self, value: Any) -> bool:
        """Return ``True`` if *value* is a UUID that exists in the payload.
 
        We rely on set membership rather than regex matching because the
        ``_all_uuids`` set is the authoritative registry of all UUIDs
        collected from the payload during the first pass.
        """
        return isinstance(value, str) and value in self._all_uuids
 
    def _resolve_record_fields(
        self, record: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Replace UUID references with Salesforce IDs.
 
        Returns
        -------
        resolved : dict
            Record dict ready for Salesforce API (``uuid`` key stripped).
        unresolved_refs : list[str]
            UUIDs that could not be resolved (parent failed or not yet
            created – should not happen if hierarchy is correct).
        """
        resolved: Dict[str, Any] = {}
        unresolved_refs: List[str] = []
 
        for field, value in record.items():
            # Never send the synthetic ``uuid`` key to Salesforce.
            if field == "uuid":
                continue
 
            if self._is_uuid_reference(value):
                if value in self._uuid_to_id_map:
                    # Successfully resolved → swap UUID for Salesforce ID.
                    resolved[field] = self._uuid_to_id_map[value]
                elif value in self._failed_uuids:
                    # Parent record failed → this record can't be created.
                    unresolved_refs.append(value)
                else:
                    # UUID exists in payload but hasn't been processed.
                    # This implies a hierarchy ordering issue.
                    logger.warning(
                        "UUID %s referenced but not yet created – "
                        "possible hierarchy misconfiguration.",
                        value,
                    )
                    unresolved_refs.append(value)
            else:
                resolved[field] = value
 
        return resolved, unresolved_refs
 
    def _process_record(
        self, object_name: str, record: Dict[str, Any]
    ) -> None:
        """Resolve UUIDs and create a single record in Salesforce."""
        uuid = record.get("uuid")
 
        # ── Resolve UUID references ─────────────────────────────────────
        resolved_record, unresolved = self._resolve_record_fields(record)
 
        if unresolved:
            msg = (
                f"Skipping {object_name} record (uuid={uuid}) – "
                f"unresolved parent UUID(s): {unresolved}"
            )
            logger.warning(msg)
            if uuid:
                self._failed_uuids.add(uuid)
            self._results.append(
                {
                    "object": object_name,
                    "uuid": uuid,
                    "salesforce_id": None,
                    "status": "skipped",
                    "message": msg,
                }
            )
            return
 
        # ── Create the record in Salesforce ─────────────────────────────
        try:
            sf_object = getattr(self.sf, object_name)
            response = sf_object.create(resolved_record)
 
            if response.get("success"):
                sf_id = response["id"]
                if uuid:
                    self._uuid_to_id_map[uuid] = sf_id
                logger.info(
                    "Created %s  uuid=%s  sf_id=%s", object_name, uuid, sf_id
                )
                self._results.append(
                    {
                        "object": object_name,
                        "uuid": uuid,
                        "salesforce_id": sf_id,
                        "status": "success",
                    }
                )
            else:
                # Salesforce returned success=false with error details.
                errors = response.get("errors", [])
                logger.error(
                    "Failed to create %s (uuid=%s): %s",
                    object_name,
                    uuid,
                    errors,
                )
                if uuid:
                    self._failed_uuids.add(uuid)
                self._results.append(
                    {
                        "object": object_name,
                        "uuid": uuid,
                        "salesforce_id": None,
                        "status": "failed",
                        "errors": errors,
                    }
                )
 
        except Exception as exc:
            logger.error(
                "Exception creating %s (uuid=%s): %s",
                object_name,
                uuid,
                exc,
                exc_info=True,
            )
            if uuid:
                self._failed_uuids.add(uuid)
            self._results.append(
                {
                    "object": object_name,
                    "uuid": uuid,
                    "salesforce_id": None,
                    "status": "failed",
                    "errors": [str(exc)],
                }
            )