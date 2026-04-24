from services.llm_email_writer import generate_llm_draft_email


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


def _format_temperature(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{round(float(value))}F"

    text = _clean_text(value)
    if not text:
        return ""

    try:
        return f"{round(float(text))}F"
    except ValueError:
        return text


def _parse_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)

    text = _clean_text(value).replace(",", "")
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _build_weather_line(weather: dict, fallback_city: str) -> str:
    weather_status = weather.get("status")
    if weather_status != "success":
        return ""

    weather_city = _clean_text(weather.get("city")) or fallback_city
    weather_condition = _clean_text(weather.get("condition")).lower()
    weather_description = _clean_text(weather.get("description"))
    weather_temp = _format_temperature(weather.get("temperature_f"))
    wind_speed = _parse_number(weather.get("wind_speed"))

    if weather_condition in {"thunderstorm", "snow", "rain"} and weather_city:
        detail = weather_description or weather_condition
        return f"Current conditions in {weather_city} include {detail}, which may affect onsite operations."

    if weather_temp:
        try:
            temp_value = float(weather_temp[:-1])
        except ValueError:
            temp_value = None

        if temp_value is not None and (temp_value >= 90 or temp_value <= 35) and weather_city:
            return f"Current conditions in {weather_city} are around {weather_temp}, which may affect day-to-day property operations."

    if wind_speed is not None and wind_speed >= 20 and weather_city:
        return f"Current wind conditions in {weather_city} may also be relevant for property operations."

    return ""


def _generate_template_draft_email(processed_lead: dict) -> str:
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

    news = processed_lead.get("enriched_data", {}).get("news", {})
    articles = news.get("articles", [])
    news_status = news.get("status")

    if news_status == "success" and articles and articles[0].get("title"):
        news_line = f"I also noticed recent news related to your market: {articles[0]['title']}."
    else:
        news_line = ""

    weather = processed_lead.get("enriched_data", {}).get("local_context", {}).get("weather", {})
    weather_line = _build_weather_line(weather, _clean_text(lead_input.get("city")))

    context_line = " ".join(part for part in (location_line, weather_line, news_line) if part)

    return (
        f"Hi {name},\n\n"
        f"I’m reaching out because {company} may be a strong fit for solutions that help "
        f"streamline property operations and improve response workflows. {context_line}\n\n"
        f"I’d love to share how teams in similar markets are using automation to improve "
        f"leasing and resident communication.\n\n"
        f"Would you be open to a quick conversation?\n\n"
        f"Best,\n"
        f"[Your Name]"
    )


def generate_draft_email(processed_lead: dict) -> str:
    llm_email = generate_llm_draft_email(processed_lead).strip()
    if llm_email:
        return llm_email

    return _generate_template_draft_email(processed_lead)
