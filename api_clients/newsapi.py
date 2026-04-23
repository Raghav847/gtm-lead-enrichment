import os
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

BASE_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MARKET_KEYWORDS = (
    "property",
    "real estate",
    "housing",
    "apartment",
    "commercial",
    "leasing",
    "development",
    "construction",
)


def _clean_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _build_company_query(company: str, city: str, state: str) -> str:
    company = _clean_text(company)
    city = _clean_text(city)
    state = _clean_text(state)

    if not company:
        return ""

    location_parts = [part for part in (city, state) if part]
    if location_parts:
        return f'"{company}" AND ({" OR ".join(f"\"{part}\"" for part in location_parts)})'

    return f'"{company}"'


def _build_location_query(city: str, state: str) -> str:
    city = _clean_text(city)
    state = _clean_text(state)

    location_parts = [part for part in (city, state) if part]
    if not location_parts:
        return ""

    location_query = " AND ".join(f'"{part}"' for part in location_parts)
    market_query = " OR ".join(MARKET_KEYWORDS)
    return f"({location_query}) AND ({market_query})"


def _article_text(article: dict) -> str:
    return " ".join(
        _clean_text(article.get(field)) for field in ("title", "description")
    ).lower()


def _filter_articles(articles: list[dict], company: str, city: str, state: str) -> list[dict]:
    company = _clean_text(company).lower()
    location_terms = [
        _clean_text(part).lower() for part in (city, state) if _clean_text(part)
    ]

    filtered_articles = []

    for article in articles:
        if article.get("title") == "[Removed]":
            continue

        text = _article_text(article)
        if not text:
            continue

        has_company_match = company and company in text
        has_location_match = location_terms and any(term in text for term in location_terms)
        has_market_match = any(keyword in text for keyword in MARKET_KEYWORDS)

        if has_company_match or (has_location_match and has_market_match):
            filtered_articles.append(article)

    return filtered_articles


def _clean_articles(articles: list[dict]) -> list[dict]:
    cleaned_articles = []

    for article in articles:
        cleaned_articles.append(
            {
                "title": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "description": article.get("description"),
            }
        )

    return cleaned_articles


def _request_articles(query: str) -> tuple[list[dict], int]:
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    return payload.get("articles", []), payload.get("totalResults", 0)


def fetch_news_context(company: str, city: str = "", state: str = "") -> dict:
    if not NEWS_API_KEY:
        return {
            "source": "NewsAPI",
            "status": "skipped",
            "reason": "Missing NEWS_API_KEY",
            "articles": [],
        }

    company_query = _build_company_query(company, city, state)
    location_query = _build_location_query(city, state)
    queries = [query for query in (company_query, location_query) if query]

    if not queries:
        return {
            "source": "NewsAPI",
            "status": "skipped",
            "reason": "Missing company and location context",
            "articles": [],
        }

    try:
        attempted_queries = []

        for query in queries:
            articles, total_results = _request_articles(query)
            filtered_articles = _filter_articles(articles, company, city, state)

            attempted_queries.append(
                {
                    "query": query,
                    "raw_results": total_results,
                    "filtered_results": len(filtered_articles),
                }
            )

            if filtered_articles:
                cleaned_articles = _clean_articles(filtered_articles[:3])
                return {
                    "source": "NewsAPI",
                    "status": "success",
                    "query": query,
                    "attempted_queries": attempted_queries,
                    "total_results": total_results,
                    "articles": cleaned_articles,
                }

        return {
            "source": "NewsAPI",
            "status": "no_results",
            "attempted_queries": attempted_queries,
            "articles": [],
        }

    except requests.RequestException as exc:
        return {
            "source": "NewsAPI",
            "status": "error",
            "query": queries[0],
            "articles": [],
            "error": str(exc),
        }
