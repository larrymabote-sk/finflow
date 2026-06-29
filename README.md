# FinFlow — Fintech Data Pipeline

> An end-to-end data engineering portfolio project simulating a production-grade fintech pipeline, from raw ingestion through analytical reporting, entirely built on the Medallion Architecture.

---

## Overview

FinFlow models the data infrastructure of a fintech company handling multi-currency transactions, customer KYC records, and live exchange rate feeds. The pipeline processes raw, messy source data through three structured layers - Bronze, Silver, and Gold - producing clean, analytics-ready tables for fraud detection, revenue reporting, and compliance monitoring.

This project demonstrates practical data engineering patterns such as: incremental loading, full refresh strategies, API ingestion, data quality enforcement, currency normalisation, and multi-table analytical modelling.

Stack: Python · PostgreSQL · SQLAlchemy · Pandas · Faker · REST APIs

---

## Architecture

```
Raw Sources
    │
    ▼
┌─────────────────────────────────────────────┐
│  BRONZE LAYER  — Raw Ingestion               │
│  • Transactions   → incremental (watermark)  │
│  • KYC records    → full refresh (Excel)     │
│  • Exchange rates → live API ingestion       │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  SILVER LAYER  — Cleaning & Enrichment       │
│  • KYC validation & standardisation         │
│  • Transaction validation & deduplication   │
│  • Live exchange rate joins (USD base)       │
│  • Primary key enforcement                  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  GOLD LAYER  — Analytical Tables             │
│  • Transaction volume & trends              │
│  • Fraud & AML summary                      │
│  • Revenue analysis                         │
│  • Risk score distribution                  │
│  • Exchange rate competitiveness            │
│  • KYC compliance overview                  │
└─────────────────────────────────────────────┘
```

---

## Layers in Detail

### Bronze — Raw Ingestion

Responsible for landing raw data into PostgreSQL with minimal transformation. Three ingestion scripts, each reflecting a different real-world pattern:

| Script | Source | Strategy | Why |
|---|---|---|---|
| `ingest_transactions.py` | Generated CSV | Incremental (watermark) | High-volume; only new rows loaded per run |
| `ingest_kyc.py` | Messy Excel file | Full refresh | Low-volume; full replace ensures consistency |
| `ingest_exchange_rates.py` | Live REST API | API pull | Real-time rates; both provider & ingestion timestamps stored |

Bronze never enforces primary keys — that responsibility belongs to Silver.

### Silver — Cleaning & Enrichment

Applies business logic to produce trusted, analysis-ready data:

- KYC: standardises names, parses inconsistent date formats, validates national IDs, flags missing fields
- Transactions: deduplicates, validates amounts and currencies, enriches each transaction with its USD-equivalent value via exchange rate join
- Primary keys enforced at this layer for the first time

Key functions: `modify_kyc()`, `parse_date()`, transaction validation pipeline, exchange rate join logic.

### Gold — Analytical Tables

Six reporting tables built on top of Silver, each targeting a specific analytical domain:

| Table | Purpose |
|---|---|
| `gold_transaction_volume` | Daily/monthly transaction trends by currency and channel |
| `gold_fraud_aml_summary` | Flagged transactions, risk scores, AML pattern detection |
| `gold_revenue_analysis` | Fee revenue, margin breakdown, currency contribution |
| `gold_risk_distribution` | Customer risk tier segmentation |
| `gold_exchange_rate_competitiveness` | Provider rate comparison vs market benchmarks |
| `gold_kyc_compliance` | KYC completeness rates, expiry tracking, compliance status |

---

## Infrastructure

| Component | Detail |
|---|---|
| Database | PostgreSQL 16 |
| Port | 5433 |
| Database name | `finbase` |
| ORM | SQLAlchemy (pandas-compatible) |
| Python | 3.10+ |

---

## Project Structure

```
finflow/
│
├── bronze/
│   ├── ingest_transactions.py
│   ├── ingest_kyc.py
│   └── ingest_exchange_rates.py
│
├── silver/
│   ├── clean_kyc.py
│   └── clean_transactions.py
│
├── gold/
│   ├── gold_transaction_volume.py
│   ├── gold_fraud_aml_summary.py
│   ├── gold_revenue_analysis.py
│   ├── gold_risk_distribution.py
│   ├── gold_exchange_rate_competitiveness.py
│   └── gold_kyc_compliance.py
│
├── data_generator/
│   └── generate_kyc.py
│
└── requirements.txt
```

---

## Setup

**Prerequisites:** Python 3.10+, PostgreSQL 16 running on port 5433

```bash
# Clone the repo
git clone https://github.com/larrymabote-sk/finflow.git
cd finflow

# Install dependencies
pip install -r requirements.txt

# Configure your database connection in each script or via environment variables
# DB: finbase | Port: 5433

# Run Bronze ingestion
python bronze/ingest_transactions.py
python bronze/ingest_kyc.py
python bronze/ingest_exchange_rates.py

# Run Silver cleaning
python silver/clean_kyc.py
python silver/clean_transactions.py

# Run Gold layer
python gold/gold_transaction_volume.py
# ... repeat for other gold scripts
```

---

## Design Decisions

**Why incremental for transactions, full refresh for KYC?**
Transactions grow continuously, hence e-loading the full table every run would be inefficient and fragile at scale. KYC records are low-volume and can change in any field, making a full replace is simpler and safer than tracking field-level deltas.

**Why store two timestamps on exchange rates?**
The provider timestamp tells you when the rate was valid in the market. The ingestion timestamp tells you when your pipeline captured it. The gap between them reveals data staleness which is critical in a multi-currency system.

**Why SQLAlchemy over raw psycopg2?**
SQLAlchemy integrates natively with pandas `to_sql()` and `read_sql()`, eliminating manual cursor management and making the codebase cleaner and more maintainable.

---

## Roadmap

- [x] Bronze — Raw ingestion layer
- [x] Silver — Cleaning & enrichment layer
- [x] Gold — Analytical reporting tables
- [ ] Phase 4 — Streamlit dashboard (in progress)
- [ ] Phase 5 — AI agent layer

---

*Built by Larry Mabote · [GitHub](https://github.com/larrymabote-sk)
