import re
from typing import List, Dict, Tuple


def extract_nutrition_data(data: List[str]) -> List[Dict[str, str]]:
    nutrition_data = []
    for entry in data:
        item = {
            "Cals_value_p100g": "",
            "Cals_unit_p100g": "",
            "Cals_org_pp": "",
            "Cals_value_pp": "",
            "Cals_unit_pp": "",
            "Servsize_portion_org": "",
            "Servsize_portion_val": "",
            "Servsize_portion_unit": ""
        }

        # Extract calories per 100ml/g
        calorie_match = re.search(r'(\d+(?:\.\d+)?)\s*(kcal|kJ)', entry)
        if calorie_match:
            item["Cals_value_p100g"] = calorie_match.group(1)
            item["Cals_unit_p100g"] = calorie_match.group(2)

        # Extract serving size and calories per portion
        serving_match = re.search(r'Per (\d+)(ml|g)', entry)
        if serving_match:
            item["Servsize_portion_org"] = f"{serving_match.group(1)}{serving_match.group(2)}"
            item["Servsize_portion_val"] = serving_match.group(1)
            item["Servsize_portion_unit"] = serving_match.group(2)

            # Look for calories in the same portion
            calorie_pp_match = re.search(
                rf'{serving_match.group(1)}{serving_match.group(2)}.*?(\d+(?:\.\d+)?)\s*(kcal|kJ)', entry)
            if calorie_pp_match:
                item["Cals_org_pp"] = f"{calorie_pp_match.group(1)} {calorie_pp_match.group(2)}"
                item["Cals_value_pp"] = calorie_pp_match.group(1)
                item["Cals_unit_pp"] = calorie_pp_match.group(2)

        nutrition_data.append(item)

    return nutrition_data


# Example usage
sample_data = [
    '"Nutrient\tPer 100ml\tPer 440ml\nEnergy\t165kJ /\t727kJ /\n(kJ / kcal)\t39kcal\t174kcal\nFat\t0g\t0g\nof which saturates\t0g\t0g\nCarbohydrate\t3.2g\t13.9g\nof which sugars\t0.3g\t1.3g\nProtein\t0.4g\t1.6g\nSalt\t0g\t0.02g"',
    '"Nutrient\tPer 100ml\nEnergy\t47kJ / 11kcal\nFat\t0g\nof which Saturates\t0g\nCarbohydrate\t2.4g\nof which Sugars\t2.4g\nProtein\t0g\nSalt\t0.03g"',
    '"Nutrient\tper 100ml\nEnergy:\t157 kJ / 37 kcal"'
]

results = extract_nutrition_data(sample_data)
for result in results:
    print(result)