import re
from typing import List, Dict


def extract_sugar_data(data: List[str]) -> List[Dict[str, str]]:
    sugar_data = []
    for entry in data:
        item = {
            "TotalSugars_g_pp": "",
            "TotalSugars_pct_pp": "",
            "TotalSugars_g_p100g": "",
            "TotalSugars_pct_p100g": "",
        }

        # Extract sugars per 100ml/g
        sugar_match = re.search(r'Per 100(?:ml|g).*?sugars.*?(\d+(?:\.\d+)?)\s*g', entry, re.IGNORECASE | re.DOTALL)
        if sugar_match:
            item["TotalSugars_g_p100g"] = sugar_match.group(1)

        sugar_pct_match = re.search(r'Per 100(?:ml|g).*?sugars.*?(\d+(?:\.\d+)?)\s*%', entry, re.IGNORECASE | re.DOTALL)
        if sugar_pct_match:
            item["TotalSugars_pct_p100g"] = sugar_pct_match.group(1)

        # Extract serving size and sugars per portion
        serving_match = re.search(r'Per (\d+)(ml|g)', entry, re.IGNORECASE)
        if serving_match:
            portion_size = serving_match.group(1)
            portion_unit = serving_match.group(2)

            sugar_pp_match = re.search(rf'Per {portion_size}{portion_unit}.*?sugars.*?(\d+(?:\.\d+)?)\s*g', entry,
                                       re.IGNORECASE | re.DOTALL)
            if sugar_pp_match:
                item["TotalSugars_g_pp"] = sugar_pp_match.group(1)

            sugar_pct_pp_match = re.search(rf'Per {portion_size}{portion_unit}.*?sugars.*?(\d+(?:\.\d+)?)\s*%', entry,
                                           re.IGNORECASE | re.DOTALL)
            if sugar_pct_pp_match:
                item["TotalSugars_pct_pp"] = sugar_pct_pp_match.group(1)

        sugar_data.append(item)

    return sugar_data


# Example usage
sample_data = [
    '"Nutrient\tPer 100ml\tPer 440ml\nEnergy\t165kJ /\t727kJ /\n(kJ / kcal)\t39kcal\t174kcal\nFat\t0g\t0g\nof which saturates\t0g\t0g\nCarbohydrate\t3.2g\t13.9g\nof which sugars\t0.3g\t1.3g\nProtein\t0.4g\t1.6g\nSalt\t0g\t0.02g"',
    '"Nutrient\tPer 100ml\nEnergy\t47kJ / 11kcal\nFat\t0g\nof which Saturates\t0g\nCarbohydrate\t2.4g\nof which Sugars\t2.4g\nProtein\t0g\nSalt\t0.03g"',
    '"Nutrient\tper 100ml\nEnergy:\t157 kJ / 37 kcal\nCarbohydrate\t5.6g\nof which Sugars\t0.8g (4%)"'
]

results = extract_sugar_data(sample_data)
for result in results:
    print(result)