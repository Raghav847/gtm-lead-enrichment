import  streamlit as st
import pandas as pd
from main import process_lead

st.title("GTM Lead Enrichment Tool")
st.write("Upload a CSV of leads to begin")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    results = []

    for _, row in df.iterrows():
        result = process_lead(row.to_dict())
        results.append(result)

    st.write("### Processed Leads")
    st.write(results)