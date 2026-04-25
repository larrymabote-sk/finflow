import pandas as pd
df = pd.read_csv("data/raw/meezan_transactions.csv")

print(df["Source_Currency"].head(10))
print(df["Source_Currency"].unique())