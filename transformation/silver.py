import pandas as pd
import psycopg2 as pg
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
load_dotenv()


def parse_date(date_str):
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%b %d %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "Needs Review"  # if no format worked

def modify_kyc(kyc_status):
    formats = ["V", "Yes", "verified", "yes"]

    if kyc_status is None or kyc_status == "":
            return "Needs Review"
    for i in formats:
        if kyc_status == i:
            return "Verified"
    return "Needs Review" 
    

def modify_risk_category(risk_category):
    formats_high = ["HIGH", "high risk"]
    formats_low = ["LOW", "low risk"]

    if risk_category is None or risk_category == "":
        return "Needs Review"
    if risk_category in formats_high:
        return "High"
    if risk_category in formats_low:
        return "Low"
    
    return "Needs Review"

def full_name_f(full_name):
    if full_name is None or full_name == "":
        return "Needs Review"
    else:
        return full_name.title().strip()

def modify_country(country):
    if country is None or country == "":
        return "Needs Review"
    if len(country) <= 3:
        return "Needs Review"
    return country


try:
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:")
    print(e)


def get_invalid_reason(row):
    reasons = []
    if row["full_name"] == "Needs Review":
        reasons.append("Full_Name")
    if row["date_of_birth"] == "Needs Review":
        reasons.append("Date of Birth")
    if row["country"] == "Needs Review":
        reasons.append("Country")
    if row["risk_category"] == "Needs Review":
        reasons.append("Risk Category")
    if row["kyc_status"] == "Needs Review":
        reasons.append("KYC Status")
    return ", ".join(reasons)

def clean_kyc():
    df = pd.read_sql("SELECT * FROM bronze_kyc", engine)

    df["full_name"] = df["full_name"].apply(full_name_f)
    df["date_of_birth"] = df["date_of_birth"].apply(parse_date)
    df["country"] = df["country"].apply(modify_country)
    df["risk_category"] = df["risk_category"].apply(modify_risk_category)
    df["kyc_status"] = df["kyc_status"].apply(modify_kyc)

    df["is_valid"] = ~(
    (df["full_name"] == "Needs Review") |
    (df["date_of_birth"] == "Needs Review") |
    (df["country"] == "Needs Review") |
    (df["risk_category"] == "Needs Review") |
    (df["kyc_status"] == "Needs Review")
    )
    df["invalid_reason"] = df.apply(get_invalid_reason, axis=1)


    df.to_sql("silver_kyc", con=engine, if_exists="replace", index=False)
    print("silver_kyc loaded")


clean_kyc()

#validating Transactions table/database.

def validate_trans(trans):
    if trans[:3] == "TXN" and trans[3:].isdigit() and len(trans[3:]) == 6:
        return ""
    else:
        return "Invalid transaction_id format"
    
def validate_exchange_rate(rate):
    if rate > 0:
        return ""
    else:
        return "Invalid exchange_rate"

def validate_converted_amount(amount):
    if amount > 0:
        return ""
    else:
        return "Invalid converted_amount"

def validate_fee_charged(fee):
    if fee >= 0:
        return ""
    else:
        return "Invalid fee_charged"

def validate_risk_score(risk_score):
    if 0 <= risk_score <= 100:
        return ""
    else:
        return "Invalid risk_score"

def validate_aml_flag(aml):
    if aml in [0,1]:
        return ""
    else:
        return "Invalid aml_flag value"
    
def validate_fraud_flag(fraud):
    if fraud in [0,1]:
        return ""
    else:
        return "Invalid fraud_flag value"
    


def get_invalid_reason_transactions(row):
    reasons = []
    reasons.append(validate_trans(row["transaction_id"]))
    reasons.append(validate_exchange_rate(row["exchange_rate"]))
    reasons.append(validate_converted_amount(row["converted_amount"]))
    reasons.append(validate_fee_charged(row["fee_charged"]))
    reasons.append(validate_risk_score(row["risk_score"]))
    reasons.append(validate_aml_flag(row["aml_flag"]))
    reasons.append(validate_fraud_flag(row["fraud_flag"]))
    reasons = [r for r in reasons if r != ""]
    return ", ".join(reasons)
    
def validate_transactions():
    df = pd.read_sql("SELECT * FROM bronze_transactions", engine)

    df["invalid_reason"] = df.apply(get_invalid_reason_transactions, axis=1)
    df["is_valid"] = df["invalid_reason"] == ""
    
    df.to_sql("silver_transactions", con=engine, if_exists="replace", index=False)
    print("silver_transactions loaded")
    
validate_transactions()

def enrich_transactions():
    df = pd.read_sql("SELECT * FROM silver_transactions", engine)
    exchange_df = pd.read_sql("SELECT * FROM bronze_exchange_rates", engine)

    #Here we are merging the source_currency on the silver_transactions database to the currency code on the other db
    #In this way, all rows will now have the source currency attached to them

    df = df.merge(exchange_df, left_on="source_currency", right_on="currency_code")
    df = df.merge(exchange_df, left_on="destination_currency", right_on="currency_code")
    df["live_converted_amount"] = df["transaction_amount"] * (df["rate_vs_usd_y"] / df["rate_vs_usd_x"])
    df["rate_difference"] = df["live_converted_amount"] - df["converted_amount"]

    df = df.drop(columns=[
    "id_y", "id",
    "currency_code_x", "currency_code_y",
    "base_currency_x", "base_currency_y",
    "rate_vs_usd_x", "rate_vs_usd_y",
    "rate_last_updated_x", "rate_last_updated_y",
    "ingested_at_y", "ingested_at",
    "source_file_y", "source_file",
    "base_currency_x", "base_currency_y"
    ])

    df = df.rename(columns={
    "id_x": "id",
    "ingested_at_x": "ingested_at",
    "source_file_x": "source_file"
    })

    df.to_sql("silver_transactions", con=engine, if_exists="replace", index=False)
    print("silver_transactions reloaded")

enrich_transactions()