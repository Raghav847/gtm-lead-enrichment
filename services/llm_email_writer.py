import json
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _build_email_context(processed_lead: dict) -> dict:
    lead_input = processed_lead.get("input", {})
    enriched = processed_lead.get("enriched_data", {})
    score = processed_lead.get("score", {})
    insights = processed_lead.get("sales_insights", [])

    datausa = enriched.get("demographics", {}).get("datausa", {})
    news = enriched.get("news", {})
    weather = enriched.get("local_context", {}).get("weather", {})

    return {
        "lead": lead_input,
        "score": score,
        "sales_insights": insights,
        "market_context": {
            "population": datausa.get("population"),
            "year": datausa.get("year"),
            "state": datausa.get("state"),
        },
        "news_context": {
            "articles": news.get("articles", [])[:2],
        },
        "weather_context": {
            "description": weather.get("description"),
            "temperature_f": weather.get("temperature_f"),
        },
    }


def generate_llm_draft_email(processed_lead: dict) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return ""

    context = _build_email_context(processed_lead)

    prompt = f"""
You are writing a short outbound sales email for an SDR at EliseAI.

EliseAI helps property management teams automate leasing, resident communication,
and operational workflows using AI.

Write one personalized intro email using the lead context below.

Rules:
- Keep it under 120 words.
- Sound natural, not overly salesy.
- Use at most 1 enriched signal.
- Prefer company, location, market, or recent news context.
- Do not mention weather unless it feels natural.
- Do not invent facts.
- If data is missing, write a clean generic version.
- End with a soft call to action.
- Return only the email body.

Lead context:
{json.dumps(context, indent=2)}
"""

    try:
        client = OpenAI()
        response = client.responses.create(
            model=MODEL,
            input=prompt,
        )

        return response.output_text.strip()

    except Exception:
        return ""
