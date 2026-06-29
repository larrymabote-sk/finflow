import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

st.title("FinFlow Analytics Dashboard")
st.write("Welcome to the FinFlow Fintech Analytics Dashboard.")

page = st.sidebar.selectbox("Navigate", [
    "Transaction Volume",
    "Revenue",
    "Risk & Compliance",
    "KYC Compliance",
    "Exchange Rate Competitiveness"
])

if page == "Transaction Volume":
    st.header("Transaction Volume by Corridor")
    
    df = pd.read_sql("SELECT * FROM gold_transaction_volume", engine)
    st.dataframe(df)

    fig = px.bar(
        df.sort_values("total_transactions", ascending=False).head(10),
        x="source_country",
        y="total_transactions",
        color="destination_country",
        title="Top 10 Corridors by Transaction Volume"
    )
    st.plotly_chart(fig)

elif page == "Revenue":
    st.header("Revenue Summary")
    
    df = pd.read_sql("SELECT * FROM gold_revenue_summary", engine)
    
    st.dataframe(df)
    
    fig = px.bar(
        df,
        x="transaction_type",
        y="total_revenue",
        color="channel",
        title="Total Revenue by Transaction Type and Channel"
    )
    st.plotly_chart(fig)

elif page == "Risk & Compliance":
    st.header("Risk & Compliance")
    
    risk_df = pd.read_sql("SELECT * FROM gold_risk_distribution", engine)
    fraud_df = pd.read_sql("SELECT * FROM gold_fraud_aml_summary", engine)
    
    st.subheader("Risk Band Distribution")
    st.dataframe(risk_df)
    fig1 = px.pie(
        risk_df,
        names="risk_band",
        values="total_transactions",
        title="Transactions by Risk Band"
    )
    st.plotly_chart(fig1)
    
    st.subheader("Fraud & AML by Country")
    st.dataframe(fraud_df)
    fig2 = px.bar(
        fraud_df,
        x="source_country",
        y=["fraud_rate", "aml_rate"],
        title="Fraud & AML Rates by Country",
        barmode="group"
    )
    st.plotly_chart(fig2)
elif page == "KYC Compliance":
    st.header("KYC Compliance")

    df = pd.read_sql("SELECT * FROM gold_kyc_compliance", engine)
    st.dataframe(df)

    fig = px.bar(
        df.sort_values("total_customers", ascending=False).head(10),
        x="country",
        y=["total_verified", "total_needs_review"],
        title="Top 10 Countries by Customer Count - Verified vs Needs Review",
        barmode="stack"
    )
    st.plotly_chart(fig)
elif page == "Exchange Rate Competitiveness":
    df = pd.read_sql("SELECT * FROM gold_exchange_rate_competitiveness", engine)
    st.dataframe(df)
    df["currency_pair"] = df["source_currency"] + " → " + df["destination_currency"]

    fig = px.bar(
        #Sorting so that we only get the countries with the most transactions
        df.sort_values("total_transactions", ascending=False).head(10),
        x="currency_pair",
        y= "avg_rate_difference",
        title = "Top 10 Country Corridors With The Most Competitve Exchange Rates"
    )
    st.plotly_chart(fig)