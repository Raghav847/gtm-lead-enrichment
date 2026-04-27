# GTM Lead Enrichment Tool

Streamlit-based MVP for automating inbound lead enrichment for SDRs using public APIs.

## What The Tool Does

This project takes inbound lead data and turns it into rep-ready output:

- input lead capture through CSV upload or Google Sheets
- enrichment using public APIs
- lead scoring with documented assumptions
- sales insights for prioritization
- personalized draft outreach email
- automation through a Google Sheets trigger flow and a scheduler-ready script

## APIs Used

### 1. DataUSA
Used for state-level population context.

Why:
- gives a simple market-size proxy
- useful for prioritizing large property markets

### 2. NewsAPI
Used for recent company or market news.

Why:
- helps personalize outreach
- gives SDRs quick context on local real-estate or property activity

### 3. OpenWeather
Used for current local operating conditions.

Why:
- adds local context for onsite property operations
- only meaningfully influences scoring or messaging when conditions are operationally notable

## Inputs

Required input shape:

```text
name,email,company,property_address,city,state,country
```

For Google Sheets automation, the sheet can also include:

```text
status,score,priority,top_insight,draft_email,processed_at,error_message
```

## Outputs

For each lead, the tool produces:

- `score`: numeric lead score
- `priority`: High / Medium / Low
- `sales_insights`: rep-friendly enrichment takeaways
- `draft_email`: personalized outreach draft
- enriched API payloads for debugging and QA

## Scoring Assumptions

The scoring model assumes EliseAI is more likely to care about leads that are:

- contactable: valid email and usable contact information
- attributable: clear company and location data
- in meaningful markets: larger state-level population via DataUSA
- personalization-ready: recent relevant news or notable local operating conditions

Scoring behavior:

- base score comes from lead completeness and outreach readiness
- DataUSA adds stronger points because market size is a durable prioritization signal
- NewsAPI adds points when relevant company or location-market news exists
- OpenWeather adds only small points, and only when conditions are operationally notable

This intentionally makes weather weaker than market size and relevant news.

## Automation Options

This repo supports both trigger-style and schedule-style automation.

### Trigger: Google Sheets Button

Use the `Process New Sheet Leads` button in Streamlit.

Behavior:

- reads rows with blank `status` or `status = new`
- processes them through the shared pipeline
- writes back outputs to the same sheet row
- marks successful rows as `done`
- marks failed rows as `error`

### Schedule: CLI Runner

Use `run_sheet_sync.py` for scheduled execution.

Example:

```bash
python run_sheet_sync.py --sheet-name gtm_lead_enrichment
```

This can be attached to:

- cron
- GitHub Actions
- Google Cloud Scheduler / Cloud Run job

## Streamlit App

Run locally:

```bash
streamlit run app.py
```

The app supports:

- CSV upload with progress feedback
- Google Sheets enrichment trigger
- downloadable enriched CSV
- detailed enrichment inspection for DataUSA, NewsAPI, and OpenWeather

## Google Sheets Setup

The sheet header row must begin exactly with:

```text
name,email,company,property_address,city,state,country
```

Recommended full header row:

```text
name,email,company,property_address,city,state,country,status,score,priority,top_insight,draft_email,processed_at,error_message
```

Sample sheet data is available in:

```text
sample_data/leads_sheets_test.csv
```

## Testing The MVP

Recommended MVP test cases:

1. complete US lead with valid email
2. complete non-US lead
3. lead missing company
4. sparse lead with weak input quality
5. already processed sheet row with `status = done`

Success criteria:

- pipeline runs without crashing
- rows with `new` or blank status are processed
- rows marked `done` are skipped
- output columns are written back correctly
- score, insights, and email remain readable and useful to SDRs

## Rollout Plan

### Phase 1: Internal MVP Validation

Timeline: 2-3 days

Stakeholders:

- GTM engineer
- one SDR manager
- one SDR user

Actions:

- test with 10-20 sample leads
- validate score distribution
- review whether top insights are genuinely useful
- check that draft emails are acceptable with and without LLM generation

### Phase 2: SDR Pilot

Timeline: 1 week

Stakeholders:

- SDR manager
- 1-2 SDRs
- RevOps or GTM Ops

Actions:

- use one shared Google Sheet as the inbound queue
- run the Streamlit button workflow daily
- gather SDR feedback on prioritization and personalization quality

Metrics:

- enrichment success rate
- number of processed rows per day
- percentage of rows with useful top insights
- SDR acceptance of suggested draft emails

### Phase 3: Scheduled Production Workflow

Timeline: 1 week

Stakeholders:

- GTM engineer
- RevOps / GTM Ops

Actions:

- attach `run_sheet_sync.py` to a daily 9am schedule
- monitor API reliability and writeback errors
- refine score thresholds if needed

### Phase 4: Broader Rollout

Timeline: 1-2 weeks

Stakeholders:

- SDR leadership
- Sales Ops / RevOps
- GTM engineering

Actions:

- expand to more inbound queues or SDR users
- standardize sheet templates
- add monitoring and retry handling for scheduled runs

## Deliverables Checklist

Assignment requirement status:

- working tool: yes
- input lead list: yes
- at least two public APIs: yes
- lead scoring: yes
- draft outreach email: yes
- sales insights: yes
- automation via trigger or schedule: yes
- rollout project plan: yes, documented here
- code/script: yes
- explanation video: not included in repo and still needs to be recorded manually

## Environment Variables

Expected `.env` values:

```text
NEWS_API_KEY=
OPENWEATHER_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=
```

Google Sheets uses a service account JSON file under `credentials/`, which should remain gitignored.
