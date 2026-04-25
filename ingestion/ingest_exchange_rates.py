import requests
import pandas as pd
import psycopg2 as pg
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

try:
    conn = pg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
    )
    print("Connected successfully!")
    api_key = os.getenv("API_KEY")
    response = requests.get(f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD")
    data = response.json()
    print("Exchange rate data fetched successfully")

    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS bronze_exchange_rates( 
                id SERIAL PRIMARY KEY,
                currency_code TEXT, 
                rate_vs_usd NUMERIC, 
                base_currency TEXT, 
                rate_last_updated TEXT, 
                ingested_at TIMESTAMP,
                source_file TEXT)""")
    
    cur.execute("TRUNCATE bronze_exchange_rates")

    currencies_needed = ["GBP", "USD", "SAR", "AED", "KWD", "QAR", "PKR"]
    rate = data["conversion_rates"]
    values = []
    for currency in currencies_needed:
        if currency in rate:
            values.append((currency, rate[currency], "USD", data["time_last_update_utc"],datetime.now(), "exchangerate_api"))

    cur.executemany("""INSERT INTO bronze_exchange_rates(
                currency_code, 
                rate_vs_usd, 
                base_currency, 
                rate_last_updated, 
                ingested_at,
                source_file
                ) VALUES( 
                %s,%s,%s,%s,%s,%s
                )""", values)
    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print("Connection failed:")
    print(e)