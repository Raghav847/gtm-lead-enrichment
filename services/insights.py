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


def _build_weather_insight(weather: dict, fallback_city: str) -> str:
    weather_city = _clean_text(weather.get("city")) or fallback_city
    weather_condition = _clean_text(weather.get("condition")).lower()
    weather_description = _clean_text(weather.get("description"))
    weather_temp = _format_temperature(weather.get("temperature_f"))
    wind_speed = _parse_number(weather.get("wind_speed"))

    if weather_condition in {"thunderstorm", "snow", "rain"} and weather_city:
        detail = weather_description or weather_condition
        return f"OpenWeather shows current conditions in {weather_city}: {detail}, which may affect onsite operations."

    if weather_temp and weather_city:
        try:
            temp_value = float(weather_temp[:-1])
        except ValueError:
            temp_value = None

        if temp_value is not None and (temp_value >= 90 or temp_value <= 35):
            return f"OpenWeather shows current conditions in {weather_city}: {weather_temp}, which may create a timely operational outreach angle."

    if wind_speed is not None and wind_speed >= 20 and weather_city:
        return f"OpenWeather shows elevated wind conditions in {weather_city}, which may be relevant for property operations."

    if weather_description and weather_temp and weather_city:
        return f"OpenWeather shows current conditions in {weather_city}: {weather_description} and {weather_temp}."

    if weather_description and weather_city:
        return f"OpenWeather shows current conditions in {weather_city}: {weather_description}."

    return ""


def generate_sales_insights(processed_lead: dict) -> list[str]:
    """
    Convert enriched data into rep-friendly bullets.
    """
    lead_input = processed_lead["input"]
    score = processed_lead["score"]
    demographics = processed_lead["enriched_data"]["demographics"]

    company = _clean_text(lead_input.get("company"))
    city = _clean_text(lead_input.get("city"))
    state = _clean_text(lead_input.get("state"))

    signal_insights = []
    context_insights = []
    diagnostic_insights = []

    datausa = demographics.get("datausa", {})
    population = _parse_population(datausa.get("population"))
    year = datausa.get("year")
    datausa_state = _clean_text(datausa.get("state")) or state
    datausa_status = datausa.get("status")
    news = processed_lead.get("enriched_data", {}).get("news", {})
    articles = news.get("articles", [])
    news_status = news.get("status")
    weather = processed_lead.get("enriched_data", {}).get("local_context", {}).get("weather", {})
    weather_status = weather.get("status")

    if company:
        context_insights.append(f"Lead is associated with {company}.")

    if city and state:
        context_insights.append(f"Property is located in {city}, {state}.")
    elif city:
        context_insights.append(f"Property is located in {city}.")
    elif state:
        context_insights.append(f"Property is located in {state}.")

    if news_status == "success" and articles:
        top_article = articles[0]
        title = top_article.get("title")
        source = top_article.get("source")

        if title and source:
            signal_insights.append(f"Recent news found from {source}: {title}")
        elif title:
            signal_insights.append(f"Recent news found: {title}")
    elif news_status == "skipped":
        reason = news.get("reason", "news enrichment was skipped")
        diagnostic_insights.append(f"NewsAPI enrichment was skipped: {reason}")
    elif news_status == "error":
        diagnostic_insights.append("NewsAPI enrichment could not be retrieved for this lead.")

    if datausa_status == "success" and population is not None and datausa_state:
        signal_insights.append(
            f"DataUSA reports a population of {population:,} for {datausa_state}"
            + (f" in {year}." if year else ".")
        )
    elif datausa_status == "skipped":
        reason = datausa.get("reason", "state population enrichment was skipped")
        diagnostic_insights.append(f"DataUSA state population enrichment was skipped: {reason}")
    elif datausa_status == "error":
        diagnostic_insights.append("DataUSA population enrichment could not be retrieved for this lead.")

    if weather_status == "success":
        weather_insight = _build_weather_insight(weather, city)
        if weather_insight:
            signal_insights.append(weather_insight)
    elif weather_status == "skipped":
        reason = weather.get("reason", "weather enrichment was skipped")
        diagnostic_insights.append(f"OpenWeather enrichment was skipped: {reason}")
    elif weather_status == "error":
        diagnostic_insights.append("OpenWeather enrichment could not be retrieved for this lead.")

    if news_status == "no_results":
        diagnostic_insights.append("No recent news was found, so outreach should rely more on market and property context.")

    insights = signal_insights + context_insights + diagnostic_insights

    if score["label"] == "High":
        insights.append("This lead should be prioritized because it has strong completeness and available market context.")
    elif score["label"] == "Medium":
        insights.append("This lead is workable, but more enrichment would improve confidence.")
    else:
        insights.append("This lead needs more data before it should be highly prioritized.")

    return insights
