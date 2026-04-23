from copy import deepcopy
from datetime import datetime, UTC


def normalize_input_lead(lead: dict) -> dict:
    """
    Normalize incoming lead fields so the rest of the pipeline
    can rely on consistent keys and trimmed string values.
    """
    return {
        "name": str(lead.get("name", "")).strip(),
        "email": str(lead.get("email", "")).strip(),
        "company": str(lead.get("company", "")).strip(),
        "property_address": str(lead.get("property_address", "")).strip(),
        "city": str(lead.get("city", "")).strip(),
        "state": str(lead.get("state", "")).strip(),
        "country": str(lead.get("country", "")).strip(),
    }


def build_empty_processed_lead(input_lead: dict) -> dict:
    """
    Return the base processed lead object.
    Every lead should follow this structure.
    """
    normalized = normalize_input_lead(input_lead)

    return {
        "input": normalized,
        "enriched_data": {
            "location": {
                "city": normalized["city"],
                "state": normalized["state"],
                "country": normalized["country"],
                "property_address": normalized["property_address"],
            },
            "demographics": {},
            "economics": {},
            "company_context": {},
            "local_context": {},
            "news": [],
        },
        "score": {
            "value": 0,
            "label": "Low",
            "reasons": [],
        },
        "sales_insights": [],
        "draft_email": "",
        "meta": {
            "status": "success",
            "processed_at": datetime.now(UTC).isoformat(),
            "errors": [],
        },
    }


def clone_processed_lead(processed_lead: dict) -> dict:
    """
    Useful if you want to safely copy before modifying.
    """
    return deepcopy(processed_lead)