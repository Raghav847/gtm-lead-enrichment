def generate_sales_insights(processed_lead: dict) -> list[str]:
    """
    Convert lead data into simple rep-friendly bullets.
    This first version uses only raw input and score.
    Later versions will use enriched API data.
    """
    lead_input = processed_lead["input"]
    score = processed_lead["score"]

    insights = []

    if lead_input["company"]:
        insights.append(f"Lead is associated with {lead_input['company']}.")

    if lead_input["city"] and lead_input["state"]:
        insights.append(
            f"Property is located in {lead_input['city']}, {lead_input['state']}."
        )

    if lead_input["property_address"]:
        insights.append("Exact property address is available for location-based research.")

    if score["label"] == "High":
        insights.append("Lead has strong input completeness and is ready for enrichment.")
    elif score["label"] == "Medium":
        insights.append("Lead is usable, but some missing fields may limit personalization.")
    else:
        insights.append("Lead needs more data before it can be strongly prioritized.")

    return insights