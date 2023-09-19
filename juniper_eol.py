# Juniper End of Life
# 
# - Extracts the URL pattern for Juniper end-of-life (EOL) pages and uses regular expressions to extract the product lines from each page.
# - Loops through each EOL page and extracts the tables containing hardware or product information.
# - Transforms the data to get a unique SKU per row using the `assign`, `explode`, and `reset_index` methods.
# - Cleans the data by removing unwanted characters and converting data types.
# - Outputs the cleaned data to a CSV file for further analysis.
# 
# The script is designed to extract hardware or product information for Juniper products and prepare the data for further analysis.

# # Libraries

import requests
import re
from bs4 import BeautifulSoup
import pandas as pd

# Send a GET request to the URL
url = "https://support.juniper.net/support/eol/"
response = requests.get(url)

# Extract all Hardware URL in the Juniper EOL page
url_pattern = r'"/support/eol/product/.*?"'
product_urls = re.findall(url_pattern, response.text)

# Extract all Software URL in the Juniper EOL page
url_pattern_software = r'"/support/eol/software/.*?"'
software_urls = re.findall(url_pattern_software, response.text)


# ## Scraping individual Product Lines

# Define regular expression patterns

pattern_table = re.compile(r'<table\b[^>]*>(.*?)</table>', re.DOTALL)
pattern_tr = re.compile(r'<tr>(.*?)</tr>', re.DOTALL)
pattern_td = re.compile(r'<td>(.*?)</td>', re.DOTALL)
pattern_th = re.compile(r'<th>(.*?)</th>', re.DOTALL)
pattern_a = re.compile(r'<a href="(.*?)">(.*?)</a>', re.DOTALL)

# Please note corero_tdd products are not in the same format as the rest of the products hence not included in the final dataframe
holder_df = pd.DataFrame()
final_df = pd.DataFrame()

for url in product_urls:
    url = ('https://support.juniper.net'+url.strip('\"'))
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract the table contents using regular expressions
    match_table = pattern_table.search(response.text)
    if match_table:
        tbody_html = match_table.group(1)
        rows = pattern_tr.findall(tbody_html)
        header = pattern_th.findall(rows[0])
        header = [re.sub('<br />', ' ', h) for h in header]
        data = []
        for row in rows[1:]:
            cols = pattern_td.findall(row)
            cols = [pattern_a.sub(r'\2', col) for col in cols]
            data.append(dict(zip(header, cols)))
            print(url,"---->",len(data))
            holder_df = pd.DataFrame(data) #a holder dataframe to hold the URL in contention
            final_df = pd.concat([final_df, holder_df], ignore_index=True)
            
    else:
        print('Table not found, Something went wrong')


# Remove values within brackets and trim whitespace in 'Product' and SKU column
final_df['Product'] = final_df['Product'].str.replace(r'\(.*\)', '').str.strip()
final_df['SKU'] = final_df['SKU'].str.replace(r'\(.*\)', '').str.strip()

#coalescing all headings to product
final_df['Product'].fillna(final_df['SKU'], inplace=True)
final_df['Product'].fillna(final_df['Product/SKU(s)'], inplace=True)

# Convert the 'Product' column to string type
final_df['Product'] = final_df['Product'].astype(str)

# Delete SKU Transformation Rows
final_df = final_df[~final_df['Product'].str.contains("SKU Transformation Announcement")]

final_df.drop(['SKU'], axis=1, inplace=True)
final_df.drop(['Product/SKU(s)'], axis=1, inplace=True)

# Transpose values in 'Product' column to separate rows
final_df = final_df.assign(Product = final_df['Product'].str.split(',')).explode('Product').reset_index(drop=True)

# Remove all unwanted HTML Tags present in the Products column
final_df['Product'] = final_df['Product'].apply(lambda x: re.sub('<[^<]+?>', '', x))

# Convert date columns to yyyy-mm-dd format
date_cols = ['EOL Announced', 'Last Order', 'Last Date to Convert Warranty', 'Same Day Support Discontinued', 'Next Day Support Discontinued', 'End of Support']
for col in date_cols:
    final_df[col] = pd.to_datetime(final_df[col], format='%m/%d/%Y', errors='coerce').dt.strftime('%Y-%m-%d')


# ### Cleaning

#remove white spaces
final_df['Product'] = final_df['Product'].str.strip()

#Add refreshed date
final_df['refreshed_date']=pd.to_datetime('today')
final_df['refreshed_date']=final_df['refreshed_date'].dt.date

#remove empty products
final_df = final_df.dropna(subset=['Product'], how='any')

#remove empty products
final_df = final_df[final_df['Product'].apply(lambda x: str(x).strip()) != '']

#Export to Flat file
final_df.to_csv('Juniper_EOL.csv',index=False)
