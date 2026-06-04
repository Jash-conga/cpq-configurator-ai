"""
backend/salesforce/sf_client.py

Implementation of the Salesforce CPQ deployment connector using
REST APIs and credentials obtained from the Salesforce CLI.
"""

import os
import requests
from copy import deepcopy
from state import running_json
from utils.logger import get_logger

logger = get_logger("salesforce_client")


def deploy_running_json() -> dict:
    """
    Deploys the running JSON state to Salesforce using the access token and instance URL
    retrieved via SF CLI. Resolves dependencies between records.
    """
    instance_url = os.getenv("SF_INSTANCE_URL")
    access_token = os.getenv("SF_ACCESS_TOKEN")

    if not instance_url or not access_token:
        return {
            "status": "error",
            "message": "Salesforce connection error: Not connected. Please click 'Connect Salesforce' in the Streamlit UI."
        }

    # Validate session first
    val_url = f"{instance_url}/services/data/v58.0/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        val_resp = requests.get(val_url, headers=headers)
        if val_resp.status_code != 200:
            return {
                "status": "error",
                "message": f"Salesforce session expired or invalid. Please re-authenticate. Details: {val_resp.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Salesforce connection failed: {str(e)}"
        }

    state = running_json.get_state()
    total_records = sum(len(records) for records in state.values())

    if total_records == 0:
        return {
            "status": "success",
            "message": "No records in the running JSON to deploy.",
            "deployed_count": 0
        }

    # Define deployment order to respect dependencies
    deploy_order = [
    "Product2",
    "Apttus_Config2__PriceList__c",
    "Apttus_Config2__PriceListItem__c",
    "Apttus_Config2__ClassificationHierarchy__c",
    "Apttus_Config2__ProductOptionGroup__c",
    "Apttus_Config2__ProductOptionComponent__c",
    "Apttus_Config2__ProductOptionPrice__c",
]

    # Map to store local uuid -> Salesforce ID
    uuid_to_sf_id = {}
    deployed_details = {}
    errors = []

    for sobject in deploy_order:
        records = state.get(sobject, [])
        if not records:
            continue

        deployed_details[sobject] = []
        for rec in records:
            local_uuid = rec.get("uuid")
            # Build payload, resolving any references to previously created records
            payload = {}
            for field, val in rec.items():
                if field in ("uuid", "Id"):
                    continue
                # If this field is a reference to a local uuid, resolve it
                if val in uuid_to_sf_id:
                    payload[field] = uuid_to_sf_id[val]
                else:
                    payload[field] = val

            # Send request to Salesforce
            url = f"{instance_url}/services/data/v58.0/sobjects/{sobject}"
            try:
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code in (200, 201):
                    sf_id = response.json()["id"]
                    uuid_to_sf_id[local_uuid] = sf_id
                    
                    # Update local state record in memory
                    running_json.update_record(sobject, local_uuid, {"Id": sf_id})
                    
                    deployed_rec = {**rec, "Id": sf_id}
                    deployed_details[sobject].append(deployed_rec)
                    
                    logger.salesforce_op(
                        operation="create_record",
                        object_name=sobject,
                        payload=rec,
                        result={"status": "success", "id": sf_id}
                    )
                else:
                    err_msg = f"Failed to deploy {sobject} ({rec.get('Name')}): {response.text}"
                    logger.error("salesforce_deploy_error", error=err_msg)
                    errors.append(err_msg)
            except Exception as ex:
                err_msg = f"Exception deploying {sobject} ({rec.get('Name')}): {str(ex)}"
                logger.error("salesforce_deploy_exception", error=err_msg)
                errors.append(err_msg)

    if errors:
        return {
            "status": "partial_success" if uuid_to_sf_id else "error",
            "message": f"Deployment finished with {len(errors)} errors.",
            "errors": errors,
            "deployed_count": len(uuid_to_sf_id),
            "details": deployed_details
        }

    return {
        "status": "success",
        "message": f"Successfully deployed {total_records} records to Salesforce.",
        "deployed_count": total_records,
        "details": deployed_details
    }
