import pandas as pd
import psycopg2 as pg
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import storage
from psycopg2.extras import execute_values
import io
import os
load_dotenv()
def ingest_transactions_f():
    try:
        print("Connecting to GCS")
        client = storage.Client()
        bucket = client.bucket("finflow-raw-data-lm")
        blob = bucket.blob("raw/meezan_transactions.csv")

        print("Starting GCS download")
        content = blob.download_as_bytes()
        print(f"GCS download complete — {len(content)} bytes")

        df = pd.read_csv(io.BytesIO(content))
        print(f"CSV parsed into DataFrame — {len(df)} rows")

        print("Connecting to Postgres")
        conn = pg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        print("Connected successfully!")

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        print(cursor.fetchone())

        cursor.execute("""CREATE TABLE IF NOT EXISTS bronze_transactions (
                    id SERIAL PRIMARY KEY,
                    transaction_id TEXT,
                    customer_id TEXT,
                    transaction_type TEXT,
                    source_country TEXT,
                    destination_country TEXT,
                    source_city TEXT,
                    destination_city TEXT,
                    source_currency TEXT,
                    destination_currency TEXT,
                    exchange_rate NUMERIC,
                    transaction_amount NUMERIC,
                    converted_amount NUMERIC,
                    fee_charged NUMERIC,
                    tax_applied NUMERIC,
                    total_deduction NUMERIC,
                    sharia_compliant TEXT,
                    contract_type TEXT,
                    transaction_date TEXT,
                    transaction_time TEXT,
                    processing_time_seconds NUMERIC,
                    fraud_flag INTEGER,
                    aml_flag INTEGER,
                    risk_score INTEGER,
                    channel TEXT,
                    device_type TEXT,
                    ingested_at TIMESTAMP,
                    source_file TEXT
                )""")
    
        cursor.execute("""SELECT MAX(CAST(SUBSTRING(transaction_id FROM 4) as INTEGER)) FROM bronze_transactions""")
        max_id = cursor.fetchone()[0]

        if max_id is None:
            df_to_load = df.copy()
        else:
            df_extract = df["Transaction_ID"].str[3:].astype(int)
            df_to_load = df[df_extract > max_id].copy()

        df_to_load["ingested_at"] = datetime.now()
        df_to_load["source_file"] = "meezan_transactions"

        values = [
            (row["Transaction_ID"], row["Customer_ID"], row["Transaction_Type"], row["Source_Country"], row["Destination_Country"],
            row["Source_City"], row["Destination_City"], row["Source_Currency"], row["Destination_Currency"],
            row["Exchange_Rate"], row["Transaction_Amount"], row["Converted_Amount"], row["Fee_Charged"],
            row["Tax_Applied"], row["Total_Deduction"], row["Sharia_Compliant"], row["Contract_Type"], row["Transaction_Date"],
            row["Transaction_Time"], row["Processing_Time_Seconds"], row["Fraud_Flag"], row["AML_Flag"],
            row["Risk_Score"], row["Channel"], row["Device_Type"], row["ingested_at"], row["source_file"])
            for index, row in df_to_load.iterrows()           
        ]

        print(f"Rows to insert: {len(df_to_load)}")
        print("Starting insert into bronze_transactions")

        insert_query = """
            INSERT INTO bronze_transactions (
                transaction_id, customer_id, transaction_type, source_country, destination_country,
                source_city, destination_city, source_currency, destination_currency,
                exchange_rate, transaction_amount, converted_amount, fee_charged,
                tax_applied, total_deduction, sharia_compliant, contract_type, transaction_date,
                transaction_time, processing_time_seconds, fraud_flag, aml_flag,
                risk_score, channel, device_type, ingested_at, source_file
            ) VALUES %s
        """
        execute_values(cursor, insert_query, values)

        print("Insert complete, committing")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Connection failed:")
        print(e)
        raise