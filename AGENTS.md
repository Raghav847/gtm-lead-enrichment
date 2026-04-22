# GTM Lead Enrichment Project — Codex Handoff

## Goal
Build a working MVP for a **GTM Engineer practical assignment** focused on automating / augmenting the inbound lead process using public APIs.

The tool should:
1. Take lead inputs
2. Enrich each lead using at least **two public free APIs**
3. Produce useful outputs for sales reps:
   - Lead score
   - Sales insights
   - Draft outreach email
4. Support automation via:
   - a schedule, or
   - a trigger such as a button / new row in a sheet
5. Include a rollout / project plan for how this could be tested and deployed in a sales org

This is based on the assignment brief, which specifically asks for a working tool, code, and a 5–15 minute explanation covering API choices, enrichment/scoring logic, assumptions, and rollout plan. :contentReference[oaicite:1]{index=1}

---

## Assignment Context
A sales development rep currently receives inbound leads with only basic data:
- Person: name, email, company
- Building: property address, city, state, country

The rep then manually researches the lead, prioritizes it, and drafts outreach.

The purpose of this project is to **automate the top-of-funnel enrichment + prioritization workflow**.

The suggested APIs in the assignment include:
- U.S. Census API
- DataUSA API
- FRED
- OpenWeather API
- Walk Score API
- NewsAPI
- Wikipedia API :contentReference[oaicite:2]{index=2}

---

## Product Framing
This should feel like a **GTM workflow tool**, not just an API demo.

Primary user:
- SDR / sales rep handling inbound leads

Desired outcome:
- Turn raw leads into **enriched, scored, outreach-ready leads**
- Save manual research time
- Improve prioritization
- Give reps better personalization signals

---

## Build Strategy
Design **one reusable Python enrichment pipeline** and expose it in two ways:

### 1. Streamlit app
Purpose:
- primary interactive demo
- upload CSV or enter single lead
- inspect enriched output
- show score, insights, outreach

### 2. Google Sheets integration
Purpose:
- operational workflow for SDRs
- read new rows from a sheet
- process them
- write back score / insights / email
- optionally support trigger or scheduled run

Important:
Do **not** build two separate systems.
Build **one shared backend pipeline** with two entry points.

---

## Local Stack
Use Python for the core system.

Recommended packages:
- streamlit
- pandas
- requests
- python-dotenv
- optionally:
  - openai
  - gspread
  - oauth2client or google-auth

Use a modular structure like:

```text
gtm-lead-enrichment/
├── app.py
├── main.py
├── requirements.txt
├── .env
├── api_clients/
│   ├── census.py
│   ├── datausa.py
│   ├── news.py
│   ├── wikipedia.py
│   ├── weather.py            # or walkscore.py
├── services/
│   ├── enrich.py
│   ├── score.py
│   ├── insights.py
│   ├── email_writer.py
├── integrations/
│   ├── google_sheets.py
│   ├── scheduler.py
├── utils/
│   ├── config.py
│   ├── helpers.py
├── sample_data/
│   └── leads.csv