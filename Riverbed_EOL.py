# This script performs the following tasks:
# 
# - Scrapes the Riverbed website to obtain information about product SKUs and their end-of-life (EOL) dates.
# - Cleans the date columns in the dataset to ensure that they are in a consistent format.
# - Cleans the string columns in the dataset to remove any unwanted whitespace or tab characters.
# - Outputs some basic statistics about the dataset, including the maximum and minimum EOL dates for each date column, as well as the total number of unique SKUs and total number of rows in the dataset.
# - Writes the cleaned dataset to a JSON file for further analysis.
# 
# The script is designed to provide a summary of the EOL dates for Riverbed products, as well as some basic statistics about the dataset, and to prepare the data for further analysis.

# # Libraries

import re
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import html5lib
import datetime as dt
from datetime import date

# # Web Scraping

# Scrape the Riverbed end-of-life webpage to obtain product SKU and EOL date information through beautiful soup
url = 'https://support.riverbed.com/content/support/eos_eoa.html'
soup = BeautifulSoup(requests.get(url).content, 'html5lib')


#This code finds the first `<script>` tag in the HTML content of the Riverbed EOL webpage that contains the string 'var EOL_ENTRIES =' 
# and assigns it to the variable `script_tag`.
script_tag = soup.find('script', string=re.compile('var EOL_ENTRIES ='))

# extract string from this script tag
t = re.search(r'var EOL_ENTRIES = (\[.*\]);', script_tag.string, flags=re.S)[1]


# preprocess the string
t = t.replace("'", '"')
t = re.sub(r'^(\s*)(.*?):', r'\1"\2":', t, flags=re.M)


# decode string to Python data
data = json.loads(t)


df = pd.DataFrame()
df = pd.json_normalize(json.loads(t))


# removing unwanted columns
df = df.drop(['dateEoaAnnouncedFormatted', 'limitedAvailabilityFormatted', 'endOfAvailabilityFormatted', 'endOfSupportFeaturesFormatted', 'endOfSupportMaintenanceFormatted','linkOverride'], axis=1)


# # Data Cleaning

# ## Dates Cleaning

# Function to convert date to yyyy-mm-dd format
def convert_date(date_str):
    if "Immediat" in date_str or "EOA" in date_str:
        return date.today().strftime("%Y-%m-%d")
    
    if date_str in ["", "N/A"]:
        return ""
    try:
        # Try parsing with different formats
        for date_format in ["%b %d, %Y", "%a %b %d %H:%M:%S %Z %Y", "%Y-%m-%d"]:
            try:
                pt = dt.datetime.strptime(date_str, date_format)
                return pt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception as e:
        print(f"Error: {e}")
        return ""
    return ""


# Applying the function to all date columns
df['dateEoaAnnounced'] = df['dateEoaAnnounced'].apply(convert_date)
df['endOfAvailability'] = df['endOfAvailability'].apply(convert_date)
df['endOfSupportFeatures'] = df['endOfSupportFeatures'].apply(convert_date)
df['endOfSupportMaintenance'] = df['endOfSupportMaintenance'].apply(convert_date)


df['refreshed_date']=pd.to_datetime('today')
df['refreshed_date']=df['refreshed_date'].dt.date


# ## Textual Cleaning

#Cleaning all whitespaces and tabs for string columns
df['description']=df['description'].str.lstrip().replace('\t','')
df['productFamily']=df['productFamily'].str.lstrip().replace('\t','')
df['shortName']=df['shortName'].str.lstrip().replace('\t','')
df['link']=df['link'].str.lstrip().replace('\t','')


# # Output

# > **Note:** It's important to keep in mind that a single SKU may have multiple model numbers associated with it. Hence unique SKUs will be lesser then the number of rows in the dataset

# use this for JSON output
with open('Riverbed_EOL.json', 'w') as outfile:
     json.dump(data, outfile)

# Summary report for Riverbed_EOL
print("Summary for Riverbed EOL")
print("************************************************")
date_cols = ['dateEoaAnnounced', 'endOfAvailability', 'endOfSupportFeatures', 'endOfSupportMaintenance']

for col in date_cols:
    max_date = df[col].max()
    min_date = df[col][df[col].str.strip() != ''].dropna().min()
    
    print(f"Maximum {col} date: {max_date}")
    print(f"Minimum {col} date: {min_date}")
    print("************************************************")
    
total_skus = df['sku'].nunique()
total_rows = len(df)
print(f"Total number of SKUs: {total_skus}")
print(f"Total number of Rows: {total_rows}")