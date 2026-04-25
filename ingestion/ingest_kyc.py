import pandas as pd
import psycopg2 as pg
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()


try:
    df = pd.read_excel("data/raw/kyc_records.xlsx")
    conn = pg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
    )
    print("Connected successfully!")

    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS bronze_kyc(
                id SERIAL PRIMARY KEY,
                customer_id TEXT,
                full_name TEXT,
                date_of_birth TEXT,
                country TEXT,
                risk_category TEXT,
                kyc_status TEXT,
                ingested_at TIMESTAMP,
                source_file TEXT)"""
                )
    cur.execute("TRUNCATE TABLE bronze_kyc;")
    df_to_load = df.copy()
    df_to_load["ingested_at"] = datetime.now()
    df_to_load["source_file"] = "kyc_records"

    values = [(row["Customer_ID"], row["Full_Name"], row["Date_of_Birth"], row["Country"], row["Risk_Category"],
               row["KYC_Status"], row["ingested_at"], row["source_file"]) 
               for index, row in df_to_load.iterrows()]
    
    cur.executemany("""INSERT INTO bronze_kyc(
                customer_id,
                full_name,
                date_of_birth,
                country,
                risk_category,
                kyc_status,
                ingested_at,
                source_file
                ) VALUES(
                %s,%s,%s,%s,%s,%s,%s,%s
                )""", values)
    
    conn.commit()
    cur.close()
    conn.close()

except Exception as e:
    print("Connection failed:")
    print(e)