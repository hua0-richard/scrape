import os
import re
import pandas as pd

# addresses = [
#     "4000 Monument Rd, Philadelphia, PA 19131, United States	United States	Target",
#     "3245 Sports Arena Blvd, San Diego, CA 92110, United States	United States	Target",
#     "4323 San Felipe St, Houston, TX 77027, United States	United States	Target",
#     "6331 Roosevelt Blvd, Jacksonville, FL 32244, United States	United States	Target"
# ]
# def get_region_and_city(address):
#     address_mapping = {
#         "4000 Monument Rd, Philadelphia, PA 19131, United States	United States	Target": ("PA", "Philadelphia"),
#         "3245 Sports Arena Blvd, San Diego, CA 92110, United States	United States	Target": ("CA", "San Diego"),
#         "4323 San Felipe St, Houston, TX 77027, United States	United States	Target": ("TX", "Houston"),
#         "6331 Roosevelt Blvd, Jacksonville, FL 32244, United States	United States	Target": ("FL", "Jacksonville")
#     }
#     return address_mapping.get(address, ("Unknown", "Unknown"))

directory = 'v1'
for filename in os.listdir(directory):
    buffer = []
    if filename.endswith('_data.csv'):
        buffer.append(filename)
    for b in buffer:
        prefix = filename[:8].split('_')[1]
        df = pd.read_csv(f'{directory}/{filename}')
        for index, row in df.iterrows():
            if not pd.isnull(row['item_label']):
                tmp = row['item_label'].split('\n')
                complete = []
                for t in tmp:
                    trow = t.split('\t')
                    r = []
                    for s in trow:
                        r.append(s)
                    complete.append(r)



                print(complete)






