import requests

BASE_URL = "https://api-jersey.datausa.io/tesseract/data.jsonrecords"
POPULATION_CUBE = "acs_yg_total_population_5"

STATE_ABBREVIATIONS = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


def _normalize_state_name(state: str) -> str:
    cleaned = state.strip()

    if not cleaned:
        return ""

    upper = cleaned.upper()
    if upper in STATE_ABBREVIATIONS:
        return STATE_ABBREVIATIONS[upper]

    return cleaned

def fetch_state_population(state: str) -> dict:
    """
    Fetch population data for a given US state.
    """
    normalized_state = _normalize_state_name(state)

    if not normalized_state:
        return {
            "source": "DataUSA",
            "status": "skipped",
            "reason": "Missing state",
        }

    params = {
        "cube": POPULATION_CUBE,
        "drilldowns": "State,Year",
        "measures": "Population",
        "sort": "Year.desc",
        "limit": "0",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        data = payload.get("data", [])

        # Find the most recent matching state row
        for row in data:
            if row.get("State", "").lower() == normalized_state.lower():
                return {
                    "source": "DataUSA",
                    "status": "success",
                    "state": row.get("State", normalized_state),
                    "year": row.get("Year"),
                    "population": row.get("Population"),
                    "raw": row,
                }

        return {
            "source": "DataUSA",
            "status": "not_found",
            "state": normalized_state,
            "population": None,
        }

    except requests.RequestException as exc:
        return {
            "source": "DataUSA",
            "status": "error",
            "state": normalized_state,
            "population": None,
            "error": str(exc),
        }
