import pandas as pd
import parse_test_cals_servsize
import parse_test_carbs
import parse_test_sugars



filepath = '/home/richard/projects/scrape/Sainsbury/output/tmp/index_66_Drinks_sainsbury_data.csv'

raw_df = pd.read_csv(filepath)

for index, row in raw_df.iterrows():
    try:

        tsv_string = row['item_label']
        lines = tsv_string.strip().split('\n')
        nutrient_dict = {}

        # Process each line
        for line in lines:  # Skip the header line
            parts = line.split('\t')
            key = parts[0].strip()
            value = parts[1:] if len(parts) > 1 else ''
            nutrient_dict[key] = value

        print(row['idx'])
        print(row['item_label'])
        print('')
        print(nutrient_dict)
        # case 1
        # case 2
        # case 3

    except:
        print(row['idx'])
        print('Error')

