import re
from typing import Dict, Any, List, Tuple


def extract_nutrition_info(nutrition_dict: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "Servsize_container_type_org": "",
        "Servsize_container_type_val": "",
        "Servsize_container_type_unit": "",
        "Servsize_portion_org": "",
        "Servsize_portion_val": "",
        "Servsize_portion_unit": "",
        "Servings_cont": "",
        "Nutr_label": "",
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
        "AddedSugars_pct_p100g": ""
    }

    # Extract serving size and container info
    serving_info = extract_serving_info(nutrition_dict)
    result.update(serving_info)

    # Extract energy information
    energy_info = extract_energy_info(nutrition_dict)
    result.update(energy_info)

    # Extract carbohydrate and sugar information
    carb_sugar_info = extract_carb_sugar_info(nutrition_dict)
    result.update(carb_sugar_info)

    # Extract nutrition label
    result["Nutr_label"] = extract_nutr_label(nutrition_dict)

    return result


def extract_serving_info(nutrition_dict: Dict[str, Any]) -> Dict[str, str]:
    serving_info = {}
    serving_pattern = r'(?:per|Per)\s+(\d+(?:\.\d+)?)\s*(ml|g|oz|fl\s*oz)'
    container_pattern = r'(\d+(?:\.\d+)?)\s*(ml|g|oz|fl\s*oz)(?:\s+(?:bottle|can|pack|container))?'
    servings_pattern = r'(\d+(?:\.\d+)?)\s*servings?'

    for key, value in nutrition_dict.items():
        if isinstance(value, list):
            value = ' '.join(map(str, value))
        elif not isinstance(value, str):
            value = str(value)

        serving_match = re.search(serving_pattern, value, re.IGNORECASE)
        if serving_match:
            serving_info["Servsize_portion_val"] = serving_match.group(1)
            serving_info["Servsize_portion_unit"] = serving_match.group(2)
            serving_info["Servsize_portion_org"] = f"{serving_match.group(1)}{serving_match.group(2)}"

        container_match = re.search(container_pattern, value, re.IGNORECASE)
        if container_match:
            serving_info["Servsize_container_type_val"] = container_match.group(1)
            serving_info["Servsize_container_type_unit"] = container_match.group(2)
            serving_info["Servsize_container_type_org"] = f"{container_match.group(1)}{container_match.group(2)}"

        servings_match = re.search(servings_pattern, value, re.IGNORECASE)
        if servings_match:
            serving_info["Servings_cont"] = servings_match.group(1)

    return serving_info


def extract_energy_info(nutrition_dict: Dict[str, Any]) -> Dict[str, str]:
    energy_info = {}
    energy_pattern = r'(\d+(?:\.\d+)?)\s*(kj|kcal)'

    for key, value in nutrition_dict.items():
        if 'energy' in key.lower():
            if isinstance(value, list):
                value = ' '.join(map(str, value))
            elif not isinstance(value, str):
                value = str(value)

            matches = re.findall(energy_pattern, value.lower())
            if matches:
                for val, unit in matches:
                    if unit == 'kcal':
                        energy_info['Cals_value_p100g'] = val
                        energy_info['Cals_unit_p100g'] = 'kcal'
                        energy_info['Cals_value_pp'] = val
                        energy_info['Cals_unit_pp'] = 'kcal'
                        energy_info['Cals_org_pp'] = val
                    elif 'Cals_value_p100g' not in energy_info:
                        energy_info['Cals_value_p100g'] = str(round(float(val) / 4.184))  # Convert kJ to kcal
                        energy_info['Cals_unit_p100g'] = 'kcal'
                        energy_info['Cals_value_pp'] = str(round(float(val) / 4.184))
                        energy_info['Cals_unit_pp'] = 'kcal'
                        energy_info['Cals_org_pp'] = str(round(float(val) / 4.184))

    return energy_info


def extract_carb_sugar_info(nutrition_dict: Dict[str, Any]) -> Dict[str, str]:
    carb_sugar_info = {}
    nutrient_patterns = {
        'TotalCarb': r'(?:Carbohydrate|carbohydrates?).*?(\d+(?:\.\d+)?)\s*g',
        'TotalSugars': r'(?:Sugars|sugars|of which sugars).*?(\d+(?:\.\d+)?)\s*g',
        'AddedSugars': r'Added Sugars.*?(\d+(?:\.\d+)?)\s*g'
    }
    percent_pattern = r'(\d+(?:\.\d+)?)\s*%'

    for key, value in nutrition_dict.items():
        if isinstance(value, list):
            value = ' '.join(map(str, value))
        elif not isinstance(value, str):
            value = str(value)

        for nutrient, pattern in nutrient_patterns.items():
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                carb_sugar_info[f'{nutrient}_g_p100g'] = match.group(1)
                carb_sugar_info[f'{nutrient}_g_pp'] = match.group(1)

                percent_match = re.search(percent_pattern, value)
                if percent_match:
                    carb_sugar_info[f'{nutrient}_pct_p100g'] = percent_match.group(1)
                    carb_sugar_info[f'{nutrient}_pct_pp'] = percent_match.group(1)

    # Handle cases where TotalSugars_pct_pp is provided directly
    if 'TotalSugars_pct_pp' in nutrition_dict:
        carb_sugar_info['TotalSugars_pct_pp'] = nutrition_dict['TotalSugars_pct_pp']

    return carb_sugar_info


def extract_nutr_label(nutrition_dict: Dict[str, Any]) -> str:
    nutr_label_keys = ['Nutrient', 'Nutrition', 'Nutritional']
    for key in nutr_label_keys:
        if key in nutrition_dict:
            return str(nutrition_dict[key])
    return ""