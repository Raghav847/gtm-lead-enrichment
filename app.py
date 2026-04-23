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

    st.subheader("Processed Leads")

    for idx, result in enumerate(results, start=1):
        st.markdown(f"## Lead {idx}")

        st.write("### Input")
        st.json(result["input"])

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