import os
import re
import urllib

import pandas as pd


def get_region_and_city(address):
    address_mapping = {
        "19 London Rd W, Amersham HP7 0HA, United Kingdom": ("Buckinghamshire", "Amersham"),
        "Tilling Rd, Brent Cross, London NW2 1LZ, United Kingdom": ("Greater London", "London"),
        "Msu, 46 Hanover St, Liverpool L1 4AF, United Kingdom": ("Merseyside", "Liverpool"),
        "Coniston Rd, Flitwick, Bedford MK45 1LX, United Kingdom": ("Bedfordshire", "Flitwick")
    }

    return address_mapping.get(address, ("Unknown", "Unknown"))

# Example usage
addresses = [
    "19 London Rd W, Amersham HP7 0HA, United Kingdom",
    "Tilling Rd, Brent Cross, London NW2 1LZ, United Kingdom",
    "Msu, 46 Hanover St, Liverpool L1 4AF, United Kingdom",
    "Coniston Rd, Flitwick, Bedford MK45 1LX, United Kingdom"
]


directory = 'v1'
for filename in os.listdir(directory):
    buffer = []
    if filename.endswith('_data.csv'):
        buffer.append(filename)
    for b in buffer:
        prefix = filename[:8].split('_')[1]
        df = pd.read_csv(f'{directory}/{filename}')
        loc_result = get_region_and_city(addresses[int(prefix) - 62])
        df['Region'] = loc_result[0]
        df['City'] = loc_result[1]
        df['url'] = df['url'].astype(str).str.strip().str.lower()
        df['url'] = df['url'].apply(lambda x: urllib.parse.unquote(x))
        df_no_duplicates = df.drop_duplicates(subset='url', keep='first')

        # df_no_duplicates['ID'] = df_no_duplicates.apply(
        #     lambda row: f"{row['ID'].split('-')[0]}-{row.name + 1}-{row['ID'].split('-')[2]}", axis=1)

        df_no_duplicates.to_csv(f'{directory}/{filename}', index = False)


