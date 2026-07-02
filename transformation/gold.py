import pandas as pd
import psycopg2 as pg
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
load_dotenv()

try:
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:")
    print(e)

def gold_transaction_volume():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)
    gold_df = df.groupby(["source_country", "destination_country"]).agg(
        total_transactions = ("transaction_id", "count"),
        total_amount = ("transaction_amount", "sum"),
        total_converted_amount=("converted_amount", "sum")
    ).reset_index()
    print("Transaction Volume Successfully Done")

    gold_df.to_sql("gold_transaction_volume", con=engine, if_exists="replace", index=False)



def gold_fraud_aml_summary():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)
    gold_df = df.groupby("source_country").agg(
        total_transactions = ("transaction_id", "count"),
        total_fraud_flagged = ("fraud_flag", "sum"),
        total_aml_flagged = ("aml_flag", "sum")
    ).reset_index()

    gold_df["fraud_rate"] = (gold_df["total_fraud_flagged"] / gold_df["total_transactions"] * 100).round(2)
    gold_df["aml_rate"] = (gold_df["total_aml_flagged"] / gold_df["total_transactions"] * 100).round(2)

    print("Fraud & AML Summary Successfully Done!")

    gold_df.to_sql("gold_fraud_aml_summary", con=engine, if_exists="replace", index=False)

def gold_revenue_summary():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)
    gold_df = df.groupby(["transaction_type", "channel"]).agg(
        total_transactions = ("transaction_id", "count"),
        total_fees_collected = ("fee_charged", "sum"),
        total_tax_collected = ("tax_applied", "sum"),
        total_revenue = ("total_deduction", "sum")
    ).sort_values("total_revenue", ascending=False).reset_index()

    gold_df["avg_fee"] = gold_df["total_fees_collected"]/gold_df["total_transactions"]

    print("Revenue Summary Successfully Done!")
    gold_df.to_sql("gold_revenue_summary", con=engine, if_exists="replace", index=False)


def gold_risk_distribution():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)

    df["risk_band"] = pd.cut(
        df["risk_score"],
        bins=[0, 33, 66, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True
    )

    gold_df = df.groupby("risk_band").agg(
        total_transactions = ("transaction_id", "count"),
        total_amount = ("transaction_amount", "sum"),
        total_risk_score = ("risk_score", "sum")
    ).reset_index()
    gold_df["avg_risk_score"] = gold_df["total_risk_score"]/gold_df["total_transactions"]

    print("Risk Distribution Successfully Done!")
    gold_df.to_sql("gold_risk_distribution", con=engine, if_exists="replace", index=False)

def gold_exchange_rate_competitiveness():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)
    gold_df = df.groupby(["source_currency", "destination_currency"]).agg(
        total_transactions = ("transaction_id", "count"),
        avg_converted_amount = ("converted_amount", "mean"),
        avg_exchange_rate = ("exchange_rate", "mean"),
        avg_rate_difference = ("rate_difference", "mean"),
        avg_live_converted_amount = ("live_converted_amount", "mean")
    ).reset_index()

    print("Exchange Rate Competitiveness Successfully Done!")
    gold_df.to_sql("gold_exchange_rate_competitiveness", con=engine, if_exists="replace", index=False)


def gold_kyc_compliance():
    df = pd.read_sql("SELECT * FROM silver_kyc", engine)
    df["is_verified"] = (df["kyc_status"] == "Verified").astype(int)
    df["is_needs_review"] = (df["kyc_status"] == "Needs Review").astype(int)

    gold_df = df.groupby("country").agg(
        total_customers = ("customer_id", "count"),
        total_verified = ("is_verified", "sum"),
        total_needs_review = ("is_needs_review", "sum")
    ).reset_index()
    gold_df["Verification Rate"] = ((gold_df["total_verified"]/gold_df["total_customers"])*100).round(2)
    
    print("KYC Compliance Successfully Done!")
    gold_df.to_sql("gold_kyc_compliance", con=engine, if_exists="replace", index=False)
