import  streamlit as st
import pandas as pd
from main import process_lead

st.set_page_config(page_title="GTM Lead Enrichment Tool", layout="wide")

st.title("GTM Lead Enrichment Tool")
st.write("Upload a CSV of leads to begin")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Raw Leads")
    st.dataframe(df)

    results = []

    for _, row in df.iterrows():
        result = process_lead(row.to_dict())
        results.append(result)

    summary_rows = []

    for result in results:
        lead_input = result["input"]
        score = result["score"]
        insights = result["sales_insights"]

        summary_rows.append(
            {
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
        )

    summary_df = pd.DataFrame(summary_rows)

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
        datausa = demographics.get("datausa", {})
        news = result["enriched_data"].get("news", {})

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
