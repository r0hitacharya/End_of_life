# # Libraries

import urllib.request as req
import bs4
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import pandas as pd
import datetime as dt
import re 



url_pal = "https://www.paloaltonetworks.com/services/support/end-of-life-announcements/hardware-end-of-life-dates"
userAgent_pal = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"

# Create a request object
request_pal = req.Request(url_pal, headers={
    "user-agent": userAgent_pal
})

# Create an empty DataFrame
df_pal = pd.DataFrame(columns=['Label', 'EOS', 'EOL'])

# Send the request and get the response
with req.urlopen(request_pal) as res_pal:
    # Decode the response content
    webCode_pal = res_pal.read().decode("utf-8")

# Parse the response content
root_pal = bs4.BeautifulSoup(webCode_pal, "html.parser")
table_pal = root_pal.find_all("td")

# Iterate over the table rows and extract the data
data_pal = []
for i in range(0, len(table_pal), 5):
    label = table_pal[i].text.strip()
    eos = table_pal[i+1].text.strip()
    eol = table_pal[i+2].text.strip()
    data_pal.append([label, eos, eol])
 
# Concatenate the DataFrames, if the data_pal list is not empty
if data_pal:
    df_pal = pd.concat([pd.DataFrame(data) for data in data_pal], axis=1, ignore_index=True)




#df_pal_transposed
df_pal = df_pal.T


# # Data Cleaning




# Rename the columns
df_pal = df_pal.rename(columns={0: 'Product_T', 1: 'EOS', 2: 'EOL'})





# Remove all whitespaces
df_pal['EOS'] = df_pal['EOS'].str.replace(r'\s+', '')
df_pal['EOL'] = df_pal['EOL'].str.replace(r'\s+', '')
df_pal['Product_T'] = df_pal['Product_T'].str.replace(r'\s+', '')
df_pal['Product_T'] = df_pal['Product_T'].str.replace('(', '').str.replace(')', '')
df_pal['Product_T'] = df_pal['Product_T'].str.replace('\n', ',')





df_pal['Product'] = df_pal['Product_T'].str.split('and ')
df_pal['Product'] = df_pal['Product_T'].str.split(',')




df_pal = df_pal.explode('Product')
df_pal = df_pal.drop('Product_T', axis=1)





# Export the df_pal DataFrame to a CSV file
df_pal.to_csv('Fortinet_EOL.csv', index=False)





get_ipython().system('jupyter nbconvert --to script Fortinet_EOL.ipynb')

