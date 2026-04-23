from api_clients.datausa import fetch_state_population


US_COUNTRY_VALUES = {
    "us",
    "usa",
    "u.s.",
    "u.s.a.",
    "united states",
    "united states of america",
}


def enrich_lead(processed_lead: dict) -> dict:
    lead_input = processed_lead["input"]

    state = lead_input.get("state", "")
    country = lead_input.get("country", "").strip().lower()

    if country and country not in US_COUNTRY_VALUES:
        processed_lead["enriched_data"]["demographics"]["datausa"] = {
            "source": "DataUSA",
            "status": "skipped",
            "state": state,
            "reason": "State population enrichment is only available for US leads.",
        }
        return processed_lead

    result = fetch_state_population(state)

    processed_lead["enriched_data"]["demographics"]["datausa"] = result

    if result.get("status") == "error" and result.get("error"):
        processed_lead["meta"]["errors"].append(result["error"])

    return processed_lead
