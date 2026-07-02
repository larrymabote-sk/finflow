from prefect import flow, task
from ingestion.ingest_exchange_rates import ingest_exchange_rates_f
from ingestion.ingest_kyc import ingest_kyc_f
from ingestion.ingest_transactions import ingest_transactions_f
from transformation.silver import clean_kyc, validate_transactions, enrich_transactions
from transformation.gold import gold_transaction_volume,gold_fraud_aml_summary,gold_revenue_summary,gold_risk_distribution, gold_exchange_rate_competitiveness, gold_kyc_compliance


@task
def run_ingest_transactions():
    ingest_transactions_f()
@task
def run_ingest_kyc():
    ingest_kyc_f()
@task
def run_exchange_rates():
    ingest_exchange_rates_f()
@task
def run_clean_kyc():
    clean_kyc()
@task
def run_validate_transactions():
    validate_transactions()
@task
def run_enrich_transactions():
    enrich_transactions()
@task
def run_gold_transaction_volume():
    gold_transaction_volume()
@task
def run_gold_fraud_aml_summary():
    gold_fraud_aml_summary()
@task
def run_gold_revenue_summary():
    gold_revenue_summary()
@task
def run_gold_risk_distribution():
    gold_risk_distribution()
@task
def run_gold_exchange_rate_competitiveness():
    gold_exchange_rate_competitiveness()
@task
def run_gold_kyc_compliance():
    gold_kyc_compliance() 


@flow
def finflow_pipeline():
    # Bronze run independently
    t1 = run_ingest_transactions()
    t2 = run_ingest_kyc()
    t3 = run_exchange_rates()
    
    # Silver depends on Bronze
    t4 = run_clean_kyc(wait_for=[t2])
    t5 = run_validate_transactions(wait_for=[t1])
    t6 = run_enrich_transactions(wait_for=[t5, t3])
    
    # Gold depends on Silver
    run_gold_transaction_volume(wait_for=[t6])
    run_gold_fraud_aml_summary(wait_for=[t6])
    run_gold_revenue_summary(wait_for=[t6])
    run_gold_risk_distribution(wait_for=[t6])
    run_gold_exchange_rate_competitiveness(wait_for=[t6])
    run_gold_kyc_compliance(wait_for=[t4])

if __name__ == "__main__":
    finflow_pipeline()