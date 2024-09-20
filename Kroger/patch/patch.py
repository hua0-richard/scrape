import os
import re
import urllib

import pandas as pd


def get_region_and_city(address):
    address_mapping = {
        "1401 Broadway Seattle, WA 98122": ("WA", "Seattle"),
        "4000 Polk St, Houston, TX 77023, United States": ("TX", "Houston"),
        "1419 W Carroll Ave Chicago, IL 60607": ("IL", "Chicago"),
        "5429 Hollywood Blvd Los Angeles, CA 90027": ("CA", "Los Angeles")
    }

    return address_mapping.get(address, ("Unknown", "Unknown"))

# Example usage
addresses = [
    "1401 Broadway Seattle, WA 98122",
    "4000 Polk St, Houston, TX 77023, United States",
    "1419 W Carroll Ave Chicago, IL 60607",
    "5429 Hollywood Blvd Los Angeles, CA 90027"
]


directory = 'v1'
for filename in os.listdir(directory):
    buffer = []
    if filename.endswith('_data.csv'):
        buffer.append(filename)
    for b in buffer:
        prefix = filename[:8].split('_')[1]
        df = pd.read_csv(f'{directory}/{filename}')
        loc_result = get_region_and_city(addresses[int(prefix) - 14])
        df['Region'] = loc_result[0]
        df['City'] = loc_result[1]
        df['url'] = df['url'].astype(str).str.strip().str.lower()
        df['url'] = df['url'].apply(lambda x: urllib.parse.unquote(x))
        df_no_duplicates = df.drop_duplicates(subset='url', keep='first')

        df_no_duplicates['ID'] = df_no_duplicates.apply(
            lambda row: f"{row['ID'].split('-')[0]}-{row.name + 1}-{row['ID'].split('-')[2]}", axis=1)

        df_no_duplicates.to_csv(f'{directory}/{filename}', index = False)


