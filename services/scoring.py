def score_lead(processed_lead: dict) -> dict:
    """
    First-pass scoring logic based on input completeness.
    Later we will add API-based signals here.
    """
    lead_input = processed_lead["input"]

    value = 0
    reasons = []

    if lead_input["name"]:
        value += 10
        reasons.append("Contact name is available")

    if lead_input["email"]:
        value += 15
        reasons.append("Contact email is available")

    if lead_input["company"]:
        value += 15
        reasons.append("Company information is available")

    if lead_input["city"] and lead_input["state"]:
        value += 20
        reasons.append("City and state are available for market enrichment")

    if lead_input["property_address"]:
        value += 20
        reasons.append("Property address is available for location-based enrichment")

    if lead_input["country"]:
        value += 10
        reasons.append("Country information is available")

    if value >= 70:
        label = "High"
    elif value >= 40:
        label = "Medium"
    else:
        label = "Low"

    return {
        "value": min(value, 100),
        "label": label,
        "reasons": reasons,
    }