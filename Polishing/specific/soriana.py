from util.mappings import mappings
import re
import pandas as pd
nutrition_label_mappings_soriana = {
    "Energía por porción" : "Cals_value_pp",
    "Carbohydrates" : "TotalCarb_g_pp",
    "Azúcares Totales": "TotalSugars_g_pp"
}

# Total Calories, Total Carbohydrates, Total Sugars
def basics(input, index, clean):
    lines = input.split('\n')
    # Nutrition label
    for l in lines:
        # Key words
        for key in nutrition_label_mappings_soriana:
            if key in l:
                tmp = l
                val = tmp.replace(key, "").strip()
                val = re.sub(r'\D', '', val)
                clean.loc[index, nutrition_label_mappings_soriana[key]] = val
                if (nutrition_label_mappings_soriana[key] == 'Cals_value_pp'):
                    clean.loc[index, 'Cals_unit_pp'] = 'kcal'

def p100g(input, index, clean, type_a, type_b):
    lines = input.split('\n')
    net_content = 'Contenido Neto'
    net_content_num = 0

    for l in lines:
        if net_content in l:
            tmp = l
            val = tmp.replace(net_content, "").strip()
            val = re.sub(r'[^0-9.]', '', val)
            net_content_num = float(val)
            clean.loc[index, type_a] =  (net_content_num / 100) * float(clean.loc[index, type_b])
            return

def serving(input, index, clean):
    lines = input.split('\n')
    serving = 'Tamaño de la Porción'

    for l in lines:
        if serving in l:
            tmp = l
            val = tmp.replace(serving, "").strip()
            clean.loc[index, 'Servsize_portion_org'] = val
            val = re.sub(r'[^0-9.]', '', val)
            clean.loc[index, 'Servsize_portion_val'] = val
            val = tmp.replace(serving, "").strip()
            val = re.sub(r'[^a-zA-Z]', '', val)
            clean.loc[index, 'Servsize_portion_unit'] = val

def container_type(input, index, clean):
    presentation = "PresentaciÃ³n"

            
class Soriana(mappings):
    @staticmethod
    def item_label(index, dirty, clean):
        basics(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        serving(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        clean.loc[index, 'NutrInfo_org'] = dirty.loc[index, 'item_label']
        if (pd.isnull(clean.loc[index, 'TotalCarb_g_pp']) == False):
            p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalCarb_g_pp', type_b = 'TotalCarb_g_p100g')
        if (pd.isnull(clean.loc[index, 'TotalSugars_g_pp']) == False):
            p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalSugars_g_pp', type_b = 'TotalSugars_g_p100g')

        
        
