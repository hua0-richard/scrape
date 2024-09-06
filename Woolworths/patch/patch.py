import os
import re
import pandas as pd


def get_region_and_city(address):
    address_mapping = {
        "shop 1248/Cnr Park street &, George St, Sydney NSW 2000, Australia": ("NSW", "Sydney"),
        "Pakington Strand, 95/113 Pakington St, Geelong West VIC 3218, Australia": ("VIC", "Geelong West"),
        "Macarthur Central 259 Queen Street, Brisbane QLD 4000": ("QLD", "Brisbane"),
        "166 Murray St, Perth WA 6000, Australia": ("WA", "Perth")
    }

    return address_mapping.get(address, ("Unknown", "Unknown"))

# Example usage
addresses = [
    "shop 1248/Cnr Park street &, George St, Sydney NSW 2000, Australia",
    "Pakington Strand, 95/113 Pakington St, Geelong West VIC 3218, Australia",
    "Macarthur Central 259 Queen Street, Brisbane QLD 4000",
    "166 Murray St, Perth WA 6000, Australia"
]

directory = 'v1'
for filename in os.listdir(directory):
    buffer = []
    if filename.endswith('_data.csv'):
        buffer.append(filename)
    for b in buffer:
        prefix = filename[:8].split('_')[1]
        df = pd.read_csv(f'{directory}/{filename}')
        loc_result = get_region_and_city(addresses[int(prefix) - 50])
        df['Region'] = loc_result[0]
        df['City'] = loc_result[1]
        df.to_csv(f'{directory}/{filename}', index = False)


