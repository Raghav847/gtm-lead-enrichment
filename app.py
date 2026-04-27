import  streamlit as st
import pandas as pd
from integrations.google_sheets import get_worksheet, read_lead_rows, write_processed_lead, update_row_status
from main import process_lead


def _lead_label(lead: dict) -> str:
    name = str(lead.get("name", "")).strip()
    company = str(lead.get("company", "")).strip()
    city = str(lead.get("city", "")).strip()

    if name and company:
        return f"{name} at {company}"
    if company and city:
        return f"{company} in {city}"
    if name:
        return name
    if company:
        return company
    if city:
        return city

    return "Unnamed lead"


def _build_summary_row(result: dict) -> dict:
    lead_input = result["input"]
    score = result["score"]
    insights = result["sales_insights"]

    return {
        "Name": lead_input.get("name", ""),
        "Email": lead_input.get("email", ""),
        "Company": lead_input.get("company", ""),
        "City": lead_input.get("city", ""),
        "State": lead_input.get("state", ""),
        "Score": score.get("value", 0),
        "Priority": score.get("label", "Low"),
        "Top Insight": insights[0] if insights else "",
        "Draft Email": result.get("draft_email", ""),
    }


def _render_processed_results(results: list[dict]) -> None:
    summary_df = pd.DataFrame([_build_summary_row(result) for result in results])

    st.subheader("Sales Rep Output")
    st.dataframe(summary_df, use_container_width=True)

    csv = summary_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Enriched Leads CSV",
        data=csv,
        file_name="enriched_leads.csv",
        mime="text/csv",
    )

    st.subheader("Processed Leads")

    for idx, result in enumerate(results, start=1):
        st.markdown(f"## Lead {idx}")
        demographics = result["enriched_data"].get("demographics", {})
        local_context = result["enriched_data"].get("local_context", {})
        datausa = demographics.get("datausa", {})
        news = result["enriched_data"].get("news", {})
        weather = local_context.get("weather", {})

        st.write("### Input")
        st.json(result["input"])

        st.write("### Enrichment")

        with st.expander("DataUSA", expanded=True):
            st.json(datausa)

        with st.expander("NewsAPI", expanded=True):
            st.write(f"Status: `{news.get('status', 'unknown')}`")

            if news.get("reason"):
                st.write(f"Reason: {news['reason']}")

            if news.get("query"):
                st.write(f"Selected query: `{news['query']}`")

            attempted_queries = news.get("attempted_queries", [])
            if attempted_queries:
                st.write("Attempted queries")
                st.json(attempted_queries)

            articles = news.get("articles", [])
            if articles:
                st.write("Matched articles")
                for article_idx, article in enumerate(articles, start=1):
                    title = article.get("title") or "Untitled article"
                    source = article.get("source") or "Unknown source"
                    published_at = article.get("published_at") or "Unknown date"

                    st.markdown(f"**{article_idx}. {title}**")
                    st.write(f"Source: {source}")
                    st.write(f"Published: {published_at}")

                    if article.get("description"):
                        st.write(article["description"])

                    if article.get("url"):
                        st.write(article["url"])
            else:
                st.write("No relevant articles returned.")

        with st.expander("OpenWeather", expanded=True):
            st.write(f"Status: `{weather.get('status', 'unknown')}`")

            if weather.get("reason"):
                st.write(f"Reason: {weather['reason']}")

            if weather.get("location_query"):
                st.write(f"Location query: `{weather['location_query']}`")

            if weather.get("status") == "success":
                weather_summary = {
                    "city": weather.get("city"),
                    "country": weather.get("country"),
                    "condition": weather.get("condition"),
                    "description": weather.get("description"),
                    "temperature_f": weather.get("temperature_f"),
                    "feels_like_f": weather.get("feels_like_f"),
                    "humidity": weather.get("humidity"),
                    "wind_speed": weather.get("wind_speed"),
                }
                st.json(weather_summary)

            if weather.get("raw"):
                st.write("Raw weather payload")
                st.json(weather["raw"])

        st.write("### Score")
        st.json(result["score"])

        st.write("### Sales Insights")
        for insight in result["sales_insights"]:
            st.write(f"- {insight}")

        st.write("### Draft Email")
        st.code(result["draft_email"])

        st.write("### Meta")
        st.json(result["meta"])

        st.divider()

st.set_page_config(page_title="GTM Lead Enrichment Tool", layout="wide")

st.title("GTM Lead Enrichment Tool")
st.write("Upload a CSV or trigger Google Sheets enrichment to process inbound leads.")

with st.expander("Google Sheets Automation", expanded=False):
    sheet_name = st.text_input("Spreadsheet name", value="gtm_lead_enrichment")
    worksheet_name = st.text_input("Worksheet name (optional)", value="")

    if st.button("Process New Sheet Leads", use_container_width=True):
        sheet_status = st.empty()
        sheet_progress = st.progress(0)
        sheet_preview = st.empty()

        try:
            worksheet = get_worksheet(sheet_name, worksheet_name or None)
            pending_rows = read_lead_rows(sheet_name, worksheet_name or None, status_filter="new")

            if not pending_rows:
                sheet_status.info("No new sheet leads found.")
            else:
                sheet_status.info(f"Found {len(pending_rows)} new sheet lead(s).")
                processed_results = []
                preview_rows = []

                for idx, row in enumerate(pending_rows, start=1):
                    lead_input = row["lead_input"]
                    row_number = row["row_number"]
                    lead_label = _lead_label(lead_input)

                    sheet_status.info(
                        f"Processing sheet row {row_number} ({idx} of {len(pending_rows)}): {lead_label}"
                    )
                    update_row_status(worksheet, row_number, "processing")

                    result = process_lead(lead_input)
                    write_processed_lead(worksheet, row_number, result)

                    processed_results.append(result)
                    preview_rows.append(_build_summary_row(result))

                    sheet_progress.progress(idx / len(pending_rows))
                    sheet_preview.write("### Sheet Processing Preview")
                    sheet_preview.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

                sheet_status.success(f"Finished processing {len(processed_results)} sheet lead(s).")
                _render_processed_results(processed_results)
        except Exception as exc:
            sheet_status.error(f"Google Sheets automation failed: {exc}")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Raw Leads")
    st.dataframe(df)

    results = []
    summary_rows = []
    total_leads = len(df)

    status_box = st.empty()
    progress_bar = st.progress(0)
    preview_box = st.empty()

    if total_leads:
        status_box.info(f"Starting enrichment for {total_leads} lead(s)...")

    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        lead_dict = row.to_dict()
        lead_label = _lead_label(lead_dict)

        status_box.info(
            f"Processing lead {idx} of {total_leads}: {lead_label}"
        )

        result = process_lead(lead_dict)
        results.append(result)

        summary_rows.append(_build_summary_row(result))

        progress_bar.progress(idx / total_leads)
        preview_box.write("### Processing Preview")
        preview_box.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    if total_leads:
        status_box.success(f"Finished processing {total_leads} lead(s).")

    _render_processed_results(results)
