# FinFlow — Fintech Data Pipeline

>An end-to-end data engineering portfolio project simulating a production-grade fintech pipeline for a multi-currency financial company. Built on Medallion Architecture with cloud-native ingestion, a managed cloud database, a Streamlit dashboard, Prefect orchestration, and a LangChain AI agent.

---

## What This Project Does

FinFlow models the data infrastructure of a fintech company processing cross-border transactions across 7 currencies and 7 countries. Raw data arrives from three sources: a CSV of 15,000 transactions, a messy Excel KYC file, and a live exchange rate API, and flows through Bronze, Silver, and Gold layers into an analytics dashboard and a natural language query interface.

The pipeline runs end-to-end via a single Prefect-orchestrated command.

---

## Stack

Python · Google Cloud Storage · Cloud SQL (PostgreSQL 16) · Cloud SQL Auth Proxy · SQLAlchemy · Pandas · Prefect · Streamlit · Plotly · LangChain · Groq (Llama 3.3) · REST APIs

---

## Architecture
Raw Sources — CSV & Excel from GCS, exchange rates from live REST API

│

▼

┌─────────────────────────────────────────────┐

│  BRONZE — Raw Ingestion                      │

│  Transactions  → incremental (watermark)     │

│  KYC records   → full refresh                │

│  Exchange rates → live API pull              │

└─────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────┐

│  SILVER — Cleaning, Validation, Enrichment   │

│  KYC standardisation & quality flagging      │

│  Transaction validation against business     │

│  rules (immutability preserved)              │

│  Live exchange rate enrichment via USD join  │

└─────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────┐

│  GOLD — Analytical Tables                    │

│  Transaction volume by corridor              │

│  Fraud & AML summary by country              │

│  Revenue by transaction type & channel       │

│  Risk band distribution                      │

│  Exchange rate competitiveness               │

│  KYC compliance by country                   │

└─────────────────────────────────────────────┘

│

▼

┌─────────────────────────────────────────────┐

│  DASHBOARD & AI AGENT                        │

│  Streamlit — 5-page analytics dashboard      │

│  LangChain SQL agent — natural language      │

│  queries via Groq with read-only access      │

└─────────────────────────────────────────────┘

---

## Cloud Infrastructure

FinFlow runs against Google Cloud Platform rather than a purely local stack:

**Google Cloud Storage** (`gs://finflow-raw-data-lm`) holds the raw source files (`meezan_transactions.csv`, `kyc_records.xlsx`). Ingestion scripts read directly from GCS using `google-cloud-storage`, rather than local disk.

**Cloud SQL (PostgreSQL 16)** hosts the `finbase` database in `us-central1`, replacing the local Postgres instance for all Bronze/Silver/Gold tables.

**Cloud SQL Auth Proxy** provides a secure, encrypted local tunnel to Cloud SQL, avoiding the need to expose the database on a public IP. The pipeline connects to the proxy on `127.0.0.1`, which forwards traffic to the instance under authenticated, encrypted connections.

**Least-privilege access** is enforced at the database level: a dedicated `finflow_agent` PostgreSQL user exists on Cloud SQL with `SELECT`-only access to Silver and Gold tables, mirroring the security model used locally.

---

## Key Design Decisions

**Incremental loading for transactions, full refresh for KYC**
Transactions grow continuously, so reloading 15,000 rows every run would be wasteful and fragile at scale. A watermark on `transaction_id` means only new rows load. KYC records update in place rather than append, so full refresh guarantees the latest version of every record is always present.

**Bronze never enforces primary keys**
Bronze is an audit layer, so it must capture everything including duplicates and malformed records. A primary key constraint on `transaction_id` would silently reject duplicates, which defeats the purpose. Constraints belong in Silver.

**Transactions are validated, not corrected**
Financial records are immutable. Changing a converted amount or exchange rate or even to fix a data quality issue would be falsifying records. Silver flags bad transactions with `is_valid` and `invalid_reason` and leaves the original values untouched.

**Two timestamps on exchange rates**
`rate_last_updated` is when the provider updated the rate. `ingested_at` is when the pipeline ran. The gap between them reveals data staleness which is critical in a live multi-currency system.

**Read-only PostgreSQL user for the AI agent**
The LangChain agent connects via a dedicated `finflow_agent` PostgreSQL user with `SELECT` privileges only on Silver and Gold tables. No Bronze access, no write access anywhere. Defense in depth — even a malformed AI-generated query cannot modify or delete data.

**SQLAlchemy over raw psycopg2**
Pandas `read_sql()` and `to_sql()` require a SQLAlchemy engine. Using raw psycopg2 causes placeholder syntax conflicts that crash the pipeline silently.

**Bulk inserts via `execute_values`, not `executemany`**
Once ingestion moved to Cloud SQL, every row insert became a network round trip instead of a same-machine call. `cursor.executemany()` sends one row per round trip for 15,000 transaction rows, that meant minutes of silent, opaque execution. Switching to `psycopg2.extras.execute_values()` batches rows into a single multi-row `INSERT`, cutting round trips by roughly 100x and making runtime predictable.

**Failures are raised, not just logged**
Ingestion functions originally caught exceptions, printed them, and returned normally which meant Prefect saw a "successful" task even when a network failure (e.g. GCS auth timeout) meant zero rows were written. Exceptions are now re-raised after logging, so a real failure surfaces as a failed Prefect task instead of silently cascading into downstream errors like a missing table.

---

## Project Structure
finflow/

│

├── ingestion/

│   ├── ingest_transactions.py

│   ├── ingest_kyc.py

│   └── ingest_exchange_rates.py

│

├── transformation/

│   ├── silver.py

│   └── gold.py

│

├── dashboard/

│   └── app.py

│

├── ai/

│   └── text_to_sql.py

│

├── data/

│   ├── raw/

│   │   ├── meezan_transactions.csv

│   │   └── kyc_records.xlsx

│   └── generators/

│       └── generate_kyc.py

│

├── tests/

│   └── quality_checks.py

│

├── main.py

├── .env

├── .gitignore

└── requirements.txt

---

## Setup

**Prerequisites**: Python 3.10+, a GCP project with a Cloud SQL PostgreSQL 16 instance and a GCS bucket, the Cloud SQL Auth Proxy binary, and gcloud CLI authenticated (gcloud auth application-default login)

```bash
git clone https://github.com/larrymabote-sk/finflow.git
cd finflow
pip install -r requirements.txt
```

Create a `.env` file in the project root:
DB_HOST=127.0.0.1
DB_PORT=5434
DB_NAME=finbase
DB_USER=postgres
DB_PASSWORD=your_cloud_sql_password
AGENT_DB_USER=finflow_agent
AGENT_DB_PASSWORD=your_agent_password
GROQ_API_KEY=your_groq_key
API_KEY=your_exchangerate_api_key
GCS_BUCKET_NAME=finflow-raw-data-lm

Start the Cloud SQL Auth Proxy in a separate terminal (leave it running):

```bash
./cloud-sql-proxy PROJECT_ID:REGION:finflow-db --port=5434
```

Run the full pipeline:

```bash
python main.py
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

---

## What Gets Built

Running `main.py` creates and populates these tables in PostgreSQL:

**Bronze:** `bronze_transactions` · `bronze_kyc` · `bronze_exchange_rates`

**Silver:** `silver_transactions` · `silver_kyc`

**Gold:** `gold_transaction_volume` · `gold_fraud_aml_summary` · `gold_revenue_summary` · `gold_risk_distribution` · `gold_exchange_rate_competitiveness` · `gold_kyc_compliance`

---

## Roadmap

- [x] Bronze — Raw ingestion layer
- [x] Silver — Cleaning, validation, enrichment
- [x] Gold — 6 analytical reporting tables
- [x] Prefect orchestration — dependency-aware pipeline execution
- [x] Streamlit dashboard — 5-page analytics interface
- [x] LangChain AI agent — natural language SQL queries with read-only security
- [x] GCP migration — GCS ingestion, Cloud SQL, Auth Proxy, least-privilege cloud DB user

---

Built by Larry Mabote · [GitHub](https://github.com/larrymabote-sk)
