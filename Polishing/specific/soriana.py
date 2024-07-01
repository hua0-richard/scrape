from util.mappings import mappings
import re

nutrition_label_mappings_soriana = {
    "Energía por porción" : "Cals_value_pp",
    "Carbohydrates" : "TotalCarb_g_pp",
    "Azúcares Totales": "TotalSugars_g_pp"
}

# Total Calories, Total Carbohydrates, Total Sugars
def basics(input, index, clean, dirty):
    lines = input.split('\n')
    # Nutrition label
    for l in lines:
        # Key words
        for key in nutrition_label_mappings_soriana:
            if key in l:
                tmp = l
                val = tmp.replace(k, "").strip()
                val = re.sub(r'\D', '', val)
                clean.loc[index, nutrition_label_mappings_soriana[key]] = val
                
