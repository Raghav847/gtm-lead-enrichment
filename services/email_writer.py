def generate_draft_email(processed_lead: dict) -> str:
    """
    Generate a lightweight personalized outreach draft.
    This first version is template-based.
    """
    lead_input = processed_lead["input"]

    name = lead_input["name"] or "there"
    company = lead_input["company"] or "your team"

    location_parts = [lead_input["city"], lead_input["state"]]
    location = ", ".join(part for part in location_parts if part)

    if location:
        location_line = f"I noticed the property you manage is in {location}."
    else:
        location_line = "I noticed you manage a property in an active market."

    return (
        f"Hi {name},\n\n"
        f"I’m reaching out because {company} may be a strong fit for solutions that help "
        f"streamline property operations and improve response workflows. {location_line}\n\n"
        f"I’d love to share how teams in similar markets are using automation to improve "
        f"leasing and resident communication.\n\n"
        f"Would you be open to a quick conversation?\n\n"
        f"Best,\n"
        f"[Your Name]"
    )