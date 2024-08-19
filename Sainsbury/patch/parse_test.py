import re
import csv


def parse_nutrition_label(label_data):
    parsed_data = {
        "Servsize_container_type_org": "",
        "Servsize_container_type_val": "",
        "Servsize_container_type_unit": "",
        "Servsize_portion_org": "",
        "Servsize_portion_val": "",
        "Servsize_portion_unit": "",
        "Servings_cont": "",
        "Nutr_label": "Nutrition Facts",
        "Cals_org_pp": "",
        "Cals_value_pp": "",
        "Cals_unit_pp": "",
        "TotalCarb_g_pp": "",
        "TotalCarb_pct_pp": "",
        "TotalSugars_g_pp": "",
        "TotalSugars_pct_pp": "",
        "AddedSugars_g_pp": "",
        "AddedSugars_pct_pp": "",
        "Cals_value_p100g": "",
        "Cals_unit_p100g": "",
        "TotalCarb_g_p100g": "",
        "TotalCarb_pct_p100g": "",
        "TotalSugars_g_p100g": "",
        "TotalSugars_pct_p100g": "",
        "AddedSugars_g_p100g": "",
        "AddedSugars_pct_p100g": "",
    }

    # Extract serving size information
    serving_size_match = re.search(r"Per (\d+)\s*(ml|g)", label_data, re.IGNORECASE)
    if serving_size_match:
        parsed_data["Servsize_portion_org"] = serving_size_match.group(0)
        parsed_data["Servsize_portion_val"] = serving_size_match.group(1)
        parsed_data["Servsize_portion_unit"] = serving_size_match.group(2)

    # Extract calories (Energy)
    energy_patterns = [
        r"Energy.*?(\d+)\s*(kJ|kcal)",
        r"Energy\s*\(kJ\)\s*(\d+)",
        r"Energy\s*\(kcal\)\s*(\d+)",
        r"E=\s*(\d+)(kj|kcal)",
    ]
    for pattern in energy_patterns:
        energy_match = re.search(pattern, label_data, re.IGNORECASE)
        if energy_match:
            parsed_data["Cals_org_pp"] = energy_match.group(0)
            parsed_data["Cals_value_pp"] = energy_match.group(1)
            parsed_data["Cals_unit_pp"] = energy_match.group(2) if len(energy_match.groups()) > 1 else "kJ"
            break

    # Function to extract nutrient information
    def extract_nutrient(nutrient_name, gram_key, pct_key):
        gram_pattern = rf"{nutrient_name}.*?(\d+\.?\d*)\s*g"
        pct_pattern = rf"{nutrient_name}.*?\(?(\d+)%\)?"

        gram_match = re.search(gram_pattern, label_data, re.IGNORECASE)
        pct_match = re.search(pct_pattern, label_data, re.IGNORECASE)

        if gram_match:
            parsed_data[gram_key] = gram_match.group(1)
        if pct_match:
            parsed_data[pct_key] = pct_match.group(1)

    # Extract carbohydrates
    extract_nutrient("Carbohydrate|Total Carbohydrate|Carbohydrates?", "TotalCarb_g_pp", "TotalCarb_pct_pp")

    # Extract sugars
    extract_nutrient("of which sugars|Sugars|Total Sugars", "TotalSugars_g_pp", "TotalSugars_pct_pp")

    # Extract added sugars
    extract_nutrient("Added Sugars", "AddedSugars_g_pp", "AddedSugars_pct_pp")

    # Extract per 100g/ml information
    per_100_match = re.search(r"Per 100(ml|g)", label_data, re.IGNORECASE)
    if per_100_match:
        # Extract calories per 100g/ml
        for pattern in energy_patterns:
            calories_100_match = re.search(pattern, label_data, re.IGNORECASE)
            if calories_100_match:
                parsed_data["Cals_value_p100g"] = calories_100_match.group(1)
                parsed_data["Cals_unit_p100g"] = calories_100_match.group(2) if len(
                    calories_100_match.groups()) > 1 else "kJ"
                break

        # Extract nutrients per 100g/ml
        extract_nutrient("Carbohydrate|Total Carbohydrate|Carbohydrates?", "TotalCarb_g_p100g", "TotalCarb_pct_p100g")
        extract_nutrient("of which sugars|Sugars|Total Sugars", "TotalSugars_g_p100g", "TotalSugars_pct_p100g")
        extract_nutrient("Added Sugars", "AddedSugars_g_p100g", "AddedSugars_pct_p100g")

    return parsed_data


def process_file(file_content):
    # Split the content into individual nutrition labels
    labels = re.split(r'\n"Nutrient', file_content)

    parsed_labels = []
    for label in labels[1:]:  # Skip the first empty split
        label_data = '"Nutrient' + label  # Add back the split text
        parsed_labels.append(parse_nutrition_label(label_data))

    return parsed_labels


# Read the entire file content
with open('nutrition_label.txt', 'r') as file:
    file_content = file.read()

# Process all labels in the file
all_parsed_data = process_file(file_content)

# Write to CSV
with open('nutrition_label_data.csv', 'w', newline='') as csvfile:
    if all_parsed_data:
        writer = csv.DictWriter(csvfile, fieldnames=all_parsed_data[0].keys())
        writer.writeheader()
        for parsed_data in all_parsed_data:
            writer.writerow(parsed_data)

print(f"Data has been parsed and written to nutrition_label_data.csv. Total labels processed: {len(all_parsed_data)}")