from services.schema import build_empty_processed_lead
from services.enrichment import enrich_lead
from services.scoring import score_lead
from services.insights import generate_sales_insights
from services.email_writer import generate_draft_email


def process_lead(lead: dict) -> dict:
    """
    Main orchestration function for processing one lead.
    This version normalizes input, applies available enrichment,
    then generates score, insights, and a draft email.
    """
    processed_lead = build_empty_processed_lead(lead)

    try:
        processed_lead = enrich_lead(processed_lead)
        processed_lead["score"] = score_lead(processed_lead)
        processed_lead["sales_insights"] = generate_sales_insights(processed_lead)
        processed_lead["draft_email"] = generate_draft_email(processed_lead)
    except Exception as exc:
        processed_lead["meta"]["status"] = "error"
        processed_lead["meta"]["errors"].append(str(exc))

    return processed_lead
