import math
import re


EXPECTED_FIELDS = (
    "name",
    "email",
    "company",
    "property_address",
    "city",
    "state",
    "country",
)

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

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

FIELD_LABELS = {
    "name": "name",
    "email": "email",
    "company": "company",
    "property_address": "property address",
    "city": "city",
    "state": "state/region",
    "country": "country",
}


def _to_text(value: object) -> str:
    if value is None:
        return ""

    try:
        if isinstance(value, float) and math.isnan(value):
            return ""
    except TypeError:
        pass

    return str(value).strip()


def _is_placeholder(text: str) -> bool:
    return text.lower() in PLACEHOLDER_VALUES


def _clean_field(value: object) -> str:
    text = _to_text(value)
    return "" if not text or _is_placeholder(text) else text


def _is_valid_email(email: str) -> bool:
    return bool(email) and EMAIL_PATTERN.fullmatch(email) is not None


def _score_label(value: int) -> str:
    if value >= 75:
        return "High"
    if value >= 45:
        return "Medium"
    return "Low"


def _parse_population(population: object) -> int | None:
    if isinstance(population, (int, float)):
        return int(population)

    text = _to_text(population).replace(",", "")

    if not text:
        return None

    try:
        return int(float(text))
    except ValueError:
        return None


def score_lead(processed_lead: dict) -> dict:
    """
    Score how ready a lead is for enrichment and outreach using
    raw input quality plus any available enrichment signals.
    """
    lead_input = processed_lead.get("input", {})

    raw_values = {
        field: _to_text(lead_input.get(field, "")) for field in EXPECTED_FIELDS
    }
    cleaned_values = {
        field: _clean_field(lead_input.get(field, "")) for field in EXPECTED_FIELDS
    }

    placeholder_fields = [
        FIELD_LABELS[field]
        for field, value in raw_values.items()
        if value and _is_placeholder(value)
    ]

    name = cleaned_values["name"]
    email = cleaned_values["email"]
    company = cleaned_values["company"]
    property_address = cleaned_values["property_address"]
    city = cleaned_values["city"]
    state = cleaned_values["state"]
    country = cleaned_values["country"]

    valid_email = _is_valid_email(email)
    meaningful_field_count = sum(bool(value) for value in cleaned_values.values())
    location_field_count = sum(
        bool(cleaned_values[field])
        for field in ("property_address", "city", "state", "country")
    )
    has_location = location_field_count > 0

    value = 0
    reasons = []

    if valid_email:
        value += 12
        reasons.append("Valid contact email is available.")
    elif email:
        reasons.append("Contact email is present but does not appear valid.")
    else:
        reasons.append("Contact email is missing.")

    if name:
        value += 4
        reasons.append("Contact name is available.")

    if company:
        value += 8
        reasons.append("Company name is available.")

    if property_address:
        value += 10
        reasons.append("Property address supports location-based enrichment.")

    if city:
        value += 4
        reasons.append("City is available for local market research.")

    if state:
        value += 4
        reasons.append("State or region is available for geographic segmentation.")

    if country:
        value += 3
        reasons.append("Country is available for regional routing.")

    if not has_location:
        reasons.append("Location data is too sparse for strong market enrichment.")

    if not placeholder_fields:
        value += 5
        reasons.append("Provided fields avoid placeholder values such as N/A or unknown.")
    else:
        field_list = ", ".join(placeholder_fields)
        reasons.append(f"Placeholder values detected in {field_list}.")

    if meaningful_field_count >= 4:
        value += 5
        reasons.append("Lead includes enough usable fields after cleanup.")
    else:
        reasons.append("Lead has too few usable fields after cleanup.")

    if company and has_location:
        value += 5
        reasons.append("Company and location data are both present for enrichment.")
    else:
        reasons.append("Reliable enrichment needs both company and location context.")

    if valid_email and (name or company) and location_field_count >= 2:
        value += 5
        reasons.append("Lead has enough context for downstream outreach drafting.")
    else:
        reasons.append("Lead needs stronger contact and location context for outreach.")

    demographics = processed_lead.get("enriched_data", {}).get("demographics", {})
    datausa = demographics.get("datausa", {})
    population = _parse_population(datausa.get("population"))
    datausa_status = datausa.get("status")

    if datausa_status == "success" and population is not None:
        if population >= 10_000_000:
            value += 15
            reasons.append("DataUSA shows this lead is in a very large state-level market.")
        elif population >= 5_000_000:
            value += 12
            reasons.append("DataUSA shows this lead is in a large state-level market.")
        elif population >= 1_000_000:
            value += 8
            reasons.append("DataUSA shows this lead is in a meaningful state-level market.")
        else:
            value += 4
            reasons.append("DataUSA population signal is available, but the state market appears smaller.")
    elif datausa_status == "success":
        reasons.append("DataUSA returned a population signal, but it could not be parsed.")
    elif datausa_status == "skipped":
        reason = datausa.get("reason", "population enrichment was skipped")
        reasons.append(f"DataUSA state population enrichment was skipped: {reason}")
    elif datausa_status == "error":
        reasons.append("DataUSA population signal was unavailable due to an API error.")
    else:
        reasons.append("DataUSA population signal was unavailable, so market-size scoring was not applied.")

    # API enrichment: NewsAPI context signal
    news = processed_lead.get("enriched_data", {}).get("news", {})
    articles = news.get("articles", [])
    news_status = news.get("status")
    news_query = _to_text(news.get("query")).lower()
    normalized_company = company.lower()

    if news_status == "success" and articles:
        if normalized_company and f'"{normalized_company}"' in news_query:
            value += 10
            reasons.append("Recent company-specific news context is available for personalized outreach.")
        else:
            value += 6
            reasons.append("Recent location-based market news context is available for personalized outreach.")
    elif news_status == "no_results":
        reasons.append("NewsAPI did not find relevant recent coverage for this lead.")
    elif news_status == "skipped":
        reason = news.get("reason", "news enrichment was skipped")
        reasons.append(f"NewsAPI enrichment was skipped: {reason}")
    elif news_status == "error":
        reasons.append("NewsAPI enrichment was unavailable due to an API error.")
    else:
        reasons.append("No recent news context was found for this lead.")

    value = min(value, 100)

    return {
        "value": value,
        "label": _score_label(value),
        "reasons": reasons,
    }
