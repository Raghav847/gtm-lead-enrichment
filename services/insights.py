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

    insights = []

    if company:
        insights.append(f"Lead is associated with {company}.")

    if city and state:
        insights.append(f"Property is located in {city}, {state}.")
    elif city:
        insights.append(f"Property is located in {city}.")
    elif state:
        insights.append(f"Property is located in {state}.")

    datausa = demographics.get("datausa", {})
    population = _parse_population(datausa.get("population"))
    year = datausa.get("year")
    datausa_state = _clean_text(datausa.get("state")) or state
    datausa_status = datausa.get("status")
    news = processed_lead.get("enriched_data", {}).get("news", {})
    articles = news.get("articles", [])
    news_status = news.get("status")

    if news_status == "success" and articles:
        top_article = articles[0]
        title = top_article.get("title")
        source = top_article.get("source")

        if title and source:
            insights.append(f"Recent news found from {source}: {title}")
        elif title:
            insights.append(f"Recent news found: {title}")
    elif news_status == "no_results":
        insights.append("No recent news was found, so outreach should rely more on market and property context.")
    elif news_status == "skipped":
        reason = news.get("reason", "news enrichment was skipped")
        insights.append(f"NewsAPI enrichment was skipped: {reason}")
    elif news_status == "error":
        insights.append("NewsAPI enrichment could not be retrieved for this lead.")

    if datausa_status == "success" and population is not None and datausa_state:
        insights.append(
            f"DataUSA reports a population of {population:,} for {datausa_state}"
            + (f" in {year}." if year else ".")
        )
    elif datausa_status == "skipped":
        reason = datausa.get("reason", "state population enrichment was skipped")
        insights.append(f"DataUSA state population enrichment was skipped: {reason}")
    elif datausa_status == "error":
        insights.append("DataUSA population enrichment could not be retrieved for this lead.")
    else:
        insights.append("State population data was not available for this lead.")

    if score["label"] == "High":
        insights.append("This lead should be prioritized because it has strong completeness and available market context.")
    elif score["label"] == "Medium":
        insights.append("This lead is workable, but more enrichment would improve confidence.")
    else:
        insights.append("This lead needs more data before it should be highly prioritized.")

    return insights
