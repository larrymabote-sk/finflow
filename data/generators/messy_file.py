import random
import pandas as pd
import datetime
from faker import Faker
def messy_or_clean (clean_value, messy_options, mess_probability=0.3):

    if random.random() <= mess_probability:
        fill_in = random.choice(messy_options)
    else:
        fill_in = clean_value
    return fill_in

#print(messy_or_clean("High", ["HIGH", "high risk"]))
#print(messy_or_clean("Verified", ["Yes", "V", "verified"]))
#print(messy_or_clean("United States", ["US", "USA", "U.S"]))


fake = Faker()

#Defining functions for the clean and messy data
dob = fake.date_of_birth()           
def messy_date(dob):
    clean = dob.strftime("%Y-%m-%d")        # ISO format
    messy_options = [
        dob.strftime("%m/%d/%Y"),           # US format
        dob.strftime("%b %d %Y")            # Human readable
    ]
    return messy_or_clean(clean, messy_options)

name = fake.name()
def messy_name(name):
    clean = name
    messy_options = [name.upper(), " " + name + " "]
    return messy_or_clean(clean, messy_options)

country = fake.country()
def messy_country(country):
    clean = country
    messy_options = [country[:2].upper(), country[:3].upper()]
    return messy_or_clean(clean, messy_options)

def messy_risk():
    clean = ["High", "Low"]
    value = random.choice(clean)
    if value == "High":
        messy_options = ["HIGH", "High risk"]
    else:
        messy_options = ["LOW","Low risk"]
    return messy_or_clean(value, messy_options)

def messy_kyc():
    clean = "Verified"
    messy_options = ["Yes", "V", "verified"]
    return messy_or_clean(clean, messy_options)

#Loading file and sampling through 500 rows
d = pd.read_csv("meezan_transactions.csv")
ids = d["Customer_ID"].unique()
sampled_ids = pd.Series(ids).sample(500)

data = []
for customer_id in sampled_ids:
    row = {
        "Customer_ID": customer_id,
        "Full_Name": messy_name(fake.name()),
        "Date_of_Birth": messy_date(fake.date_of_birth()),
        "Country": messy_country(fake.country()),
        "Risk_Category": messy_risk(),
        "KYC_Status":messy_kyc()
    }
    data.append(row)

#Changing file into a DataFrame
df = pd.DataFrame(data)

#Saving as Excel File
df.to_excel("kyc_records.xlsx", index=False)

