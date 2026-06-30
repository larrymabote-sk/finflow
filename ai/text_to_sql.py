from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
import os
load_dotenv()

try:
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('AGENT_DB_USER')}:{os.getenv('AGENT_DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:")
    print(e)

api_key = os.getenv('GROQ_API_KEY')
llm = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile",temperature=0)
sql_db = SQLDatabase(engine)
prefix = """
You are an agent designed to interact with a SQL database for a fintech company called FinFlow.

Business terminology:
- "Corridor" refers to a source_country and destination_country pair in transaction data.
- "Volume" refers to total_transactions or total_amount, depending on context.
- "Revenue" refers to total_deduction (fees + tax collected).
- "Risk band" refers to Low, Medium, or High risk categories based on risk_score.

Given an input question, create a syntactically correct SQL query to run, then look at the results and return the answer in plain English.
"""

agent = create_sql_agent(llm, db=sql_db, agent_type="tool-calling", verbose=True, prefix=prefix)