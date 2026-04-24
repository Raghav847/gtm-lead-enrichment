from api_clients.datausa import fetch_state_population
from api_clients.newsapi import fetch_news_context
from api_clients.openweather import fetch_weather_context


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
    raw_country = lead_input.get("country", "")
    country = raw_country.strip().lower()
    company = lead_input.get("company", "")
    city = lead_input.get("city", "")

    if country and country not in US_COUNTRY_VALUES:
        datausa_result = {
            "source": "DataUSA",
            "status": "skipped",
            "state": state,
            "reason": "State population enrichment is only available for US leads.",
        }
    else:
        datausa_result = fetch_state_population(state)

    newsapi_result = fetch_news_context(company=company, city=city, state=state)
    weather_result = fetch_weather_context(city=city, state=state, country=raw_country)

    processed_lead["enriched_data"]["demographics"]["datausa"] = datausa_result
    processed_lead["enriched_data"]["news"] = newsapi_result
    processed_lead["enriched_data"]["local_context"]["weather"] = weather_result

    for result in [datausa_result, newsapi_result, weather_result]:
        if result.get("status") == "error":
            processed_lead["meta"]["errors"].append(
                f"{result.get('source')} error: {result.get('error')}"
            )


    return processed_lead
