import re
from typing import List, Dict


def extract_carb_data(data: List[str]) -> List[Dict[str, str]]:
    carb_data = []
    for entry in data:
        item = {
            "TotalCarb_g_pp": "",
            "TotalCarb_pct_pp": "",
            "TotalCarb_g_p100g": "",
            "TotalCarb_pct_p100g": "",
        }

        # Extract carbs per 100ml/g
        carb_match = re.search(r'Per 100(?:ml|g).*?Carbohydrate.*?(\d+(?:\.\d+)?)\s*g', entry,
                               re.IGNORECASE | re.DOTALL)
        if carb_match:
            item["TotalCarb_g_p100g"] = carb_match.group(1)

        carb_pct_match = re.search(r'Per 100(?:ml|g).*?Carbohydrate.*?(\d+(?:\.\d+)?)\s*%', entry,
                                   re.IGNORECASE | re.DOTALL)
        if carb_pct_match:
            item["TotalCarb_pct_p100g"] = carb_pct_match.group(1)

        # Extract serving size and carbs per portion
        serving_match = re.search(r'Per (\d+)(ml|g)', entry, re.IGNORECASE)
        if serving_match:
            portion_size = serving_match.group(1)
            portion_unit = serving_match.group(2)

            carb_pp_match = re.search(rf'Per {portion_size}{portion_unit}.*?Carbohydrate.*?(\d+(?:\.\d+)?)\s*g', entry,
                                      re.IGNORECASE | re.DOTALL)
            if carb_pp_match:
                item["TotalCarb_g_pp"] = carb_pp_match.group(1)

            carb_pct_pp_match = re.search(rf'Per {portion_size}{portion_unit}.*?Carbohydrate.*?(\d+(?:\.\d+)?)\s*%',
                                          entry, re.IGNORECASE | re.DOTALL)
            if carb_pct_pp_match:
                item["TotalCarb_pct_pp"] = carb_pct_pp_match.group(1)

        carb_data.append(item)

    return carb_data


# Example usage
sample_data = [
    '"Nutrient\tPer 100ml\tPer 440ml\nEnergy\t165kJ /\t727kJ /\n(kJ / kcal)\t39kcal\t174kcal\nFat\t0g\t0g\nof which saturates\t0g\t0g\nCarbohydrate\t3.2g\t13.9g\nof which sugars\t0.3g\t1.3g\nProtein\t0.4g\t1.6g\nSalt\t0g\t0.02g"',
    '"Nutrient\tPer 100ml\nEnergy\t47kJ / 11kcal\nFat\t0g\nof which Saturates\t0g\nCarbohydrate\t2.4g\nof which Sugars\t2.4g\nProtein\t0g\nSalt\t0.03g"',
    '"Nutrient\tper 100ml\nEnergy:\t157 kJ / 37 kcal\nCarbohydrate\t5.6g (4%)"'
]

# results = extract_carb_data(sample_data)
# for result in results:
#     print(result)