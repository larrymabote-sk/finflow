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
llm = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile")
sql_db = SQLDatabase(engine)
agent = create_sql_agent(llm, db=sql_db, agent_type="tool-calling", verbose=True)


response = agent.invoke("show me a customer with KYC status needs review")
print(response)