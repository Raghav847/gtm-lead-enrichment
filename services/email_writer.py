PLACEHOLDER_VALUES = {
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
    "not provided",
    "tbd",
    "nan",
    "-",
    "--",
}


def _clean_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if not text or text.lower() in PLACEHOLDER_VALUES else text


def _parse_population(population: object) -> int | None:
    if isinstance(population, (int, float)):
        return int(population)

    text = _clean_text(population).replace(",", "")

    if not text:
        return None

    try:
        return int(float(text))
    except ValueError:
        return None


def generate_draft_email(processed_lead: dict) -> str:
    """
    Generate a lightweight personalized outreach draft.
    """
    lead_input = processed_lead["input"]
    demographics = processed_lead["enriched_data"]["demographics"]

    name = _clean_text(lead_input.get("name")) or "there"
    company = _clean_text(lead_input.get("company")) or "your team"

    location_parts = [
        _clean_text(lead_input.get("city")),
        _clean_text(lead_input.get("state")),
    ]
    location = ", ".join(part for part in location_parts if part)

    datausa = demographics.get("datausa", {})
    population = _parse_population(datausa.get("population"))
    datausa_state = _clean_text(datausa.get("state"))

    if location and population:
        location_line = (
            f"I noticed the property you manage is in {location}. "
            f"DataUSA reports {datausa_state or 'that state'} has roughly {population:,} residents."
        )
    elif location:
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
