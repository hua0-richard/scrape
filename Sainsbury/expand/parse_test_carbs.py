import re


def extract_carb_info(label_text):
    # Dictionary to store extracted values
    carb_info = {
        "TotalCarb_g_pp": None,
        "TotalCarb_pct_pp": None,
        "TotalCarb_g_p100g": None,
        "TotalCarb_pct_p100g": None
    }

    # Split the label text into lines
    lines = label_text.split('\n')

    # Extract serving size information
    serving_size_match = re.search(r'\(per (\d+)(\w+)\)', label_text)
    serving_size = 100  # Default to 100 if not specified
    if serving_size_match:
        serving_size = float(serving_size_match.group(1))

    # Find the line with carbohydrate information
    for line in lines:
        if "Carbohydrate" in line:
            # Extract the carbohydrate value
            carb_match = re.search(r'(\d+\.?\d*)g', line)
            if carb_match:
                carb_value = float(carb_match.group(1))

                # Set values for 100g/ml
                carb_info["TotalCarb_g_p100g"] = carb_value

                # Calculate values per portion if different from 100g/ml
                if serving_size != 100:
                    carb_info["TotalCarb_g_pp"] = round(carb_value * serving_size / 100, 1)
                else:
                    carb_info["TotalCarb_g_pp"] = carb_value

                # Note: Percent daily values are not provided in this label,
                # so we'll leave those fields as None
            break

    return carb_info