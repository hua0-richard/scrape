import re


def parse_nutrition_label(label_data):
    data = {}

    # Helper function to extract numeric values
    def extract_numeric(value):
        value = value.replace(',', '.')  # Replace comma with dot for decimal
        match = re.search(r'([\d.]+)', value)
        return float(match.group(1)) if match else None

    # Find energy values
    energy_patterns = [
        r'Energy[:\s]*([\d,.]+)\s*kJ\s*[/,]?\s*([\d,.]+)\s*kcal',
        r'Energy[:\s]*([\d,.]+)\s*kcal\s*[/,]?\s*([\d,.]+)\s*kJ',
        r'Energy[:\s]*([\d,.]+)\s*kJ',
        r'Energy[:\s]*([\d,.]+)\s*kcal',
        r'Energy \(kJ[/]kcal\)[:\s]*([\d,.]+)[/\s]*([\d,.]+)',
        r'kJ[:\s]*([\d,.]+)[\s\S]+?kcal[:\s]*([\d,.]+)'
    ]

    for pattern in energy_patterns:
        energy_match = re.search(pattern, label_data, re.IGNORECASE)
        if energy_match:
            if len(energy_match.groups()) == 2:
                kj, kcal = map(extract_numeric, energy_match.groups())
                if pattern.startswith('Energy[:\s]*([\d,.]+)\s*kcal'):
                    kj, kcal = kcal, kj
            else:
                value = extract_numeric(energy_match.group(1))
                if 'kJ' in energy_match.group(0):
                    kj, kcal = value, round(value / 4.184, 1)
                else:
                    kcal, kj = value, round(value * 4.184, 1)

            data['Cals_org_pp'] = f"{kj}kJ / {kcal}kcal"
            data['Cals_value_pp'] = str(kcal)
            data['Cals_unit_pp'] = 'kcal'
            data['Cals_value_p100g'] = str(kcal)
            data['Cals_unit_p100g'] = 'kcal'
            break
    else:
        data['Cals_org_pp'] = None
        data['Cals_value_pp'] = None
        data['Cals_unit_pp'] = None
        data['Cals_value_p100g'] = None
        data['Cals_unit_p100g'] = None

    # Find carbohydrate values
    carb_match = re.search(r'Carbohydrate[s]?[:\s]*([\d,.]+)g', label_data, re.IGNORECASE)
    if carb_match:
        carb_value = extract_numeric(carb_match.group(1))
        data['TotalCarb_g_pp'] = str(carb_value)
        data['TotalCarb_g_p100g'] = str(carb_value)
    else:
        data['TotalCarb_g_pp'] = None
        data['TotalCarb_g_p100g'] = None

    # Find carbohydrate percentage, if available
    carb_pct_match = re.search(r'Carbohydrate[s]?[:\s]*([\d,.]+)%', label_data, re.IGNORECASE)
    data['TotalCarb_pct_pp'] = str(extract_numeric(carb_pct_match.group(1))) if carb_pct_match else None
    data['TotalCarb_pct_p100g'] = data['TotalCarb_pct_pp']

    # Find sugar values
    sugar_match = re.search(r'Sugars[:\s]*([\d,.]+)g', label_data, re.IGNORECASE)
    if sugar_match:
        sugar_value = extract_numeric(sugar_match.group(1))
        data['TotalSugars_g_pp'] = str(sugar_value)
        data['TotalSugars_g_p100g'] = str(sugar_value)
    else:
        data['TotalSugars_g_pp'] = None
        data['TotalSugars_g_p100g'] = None

    # Find sugar percentage, if available
    sugar_pct_match = re.search(r'Sugars[:\s]*([\d,.]+)%', label_data, re.IGNORECASE)
    data['TotalSugars_pct_pp'] = str(extract_numeric(sugar_pct_match.group(1))) if sugar_pct_match else None
    data['TotalSugars_pct_p100g'] = data['TotalSugars_pct_pp']

    # Added Sugars (if available)
    added_sugar_match = re.search(r'Added Sugars[:\s]*([\d,.]+)g', label_data, re.IGNORECASE)
    if added_sugar_match:
        added_sugar_value = extract_numeric(added_sugar_match.group(1))
        data['AddedSugars_g_pp'] = str(added_sugar_value)
        data['AddedSugars_g_p100g'] = str(added_sugar_value)
    else:
        data['AddedSugars_g_pp'] = None
        data['AddedSugars_g_p100g'] = None

    # Added Sugars percentage (if available)
    added_sugar_pct_match = re.search(r'Added Sugars[:\s]*([\d,.]+)%', label_data, re.IGNORECASE)
    data['AddedSugars_pct_pp'] = str(extract_numeric(added_sugar_pct_match.group(1))) if added_sugar_pct_match else None
    data['AddedSugars_pct_p100g'] = data['AddedSugars_pct_pp']

    return data


# Function to process multiple labels in a single string
def process_multiple_labels(input_string):
    labels = re.split(r'\n\s*\n', input_string)
    results = []
    for label in labels:
        if label.strip():
            results.append(parse_nutrition_label(label))
    return results


sample_data = '''"Nutrient	Per 100ml:
Energy	188kJ / 45kcal
Fat	0g
Of which Saturates	0g
Carbohydrate	3.7g
Of which Sugars	0.0g
Protein	0.4g
Salt	<0.01g"

"Nutrient	per 100ml:
Energy	153kJ/ 37kcal
Fat	0g
-of which saturates	0g
Carbohydrate	2.5g
0of which sugars	<0.5g
Protein	<0.5g
Salt	<0.01g"'''

results = process_multiple_labels(sample_data)

# Print the results
for i, result in enumerate(results, 1):
    print(f"Label {i}:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    print()

