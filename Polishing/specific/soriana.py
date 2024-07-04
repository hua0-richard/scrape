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
    default = ""

    for l in lines:
        if net_content in l:
            tmp = l
            val = tmp.replace(net_content, "").strip()
            default = val
            unit = re.sub(r'[^a-zA-Z]', '', val)
            val = re.sub(r'[^0-9.]', '', val)
            net_content_num = float(val)
            clean.loc[index, type_a] =  (net_content_num / 100) * float(clean.loc[index, type_b])
            clean.loc[index, 'Netcontent_val'] = net_content_num
            clean.loc[index, 'Netcontent_unit'] = unit
            clean.loc[index, 'Netcontent_org'] = default
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
            clean.loc[index, 'Unit_pp'] = val
            return

def container_type(input, index, clean):
    lines = input.split('\n')
    presentation = "Presentación"

    for l in lines:
        if presentation in l:
            tmp = l
            val = tmp.replace(presentation, "").strip()
            clean.loc[index, 'Pack_type'] = val
            return

def container_size(input, index, clean):
    lines = input.split('\n')
    servings_per_container = 'Porciones por Envase'
    serving_size = 'Tamaño de la Porción'

    servings_per_container_val = -1
    serving_size_val = -1
    default = ""

    for l in lines:
        if servings_per_container in l:
            tmp = l
            val = tmp.replace(servings_per_container, "").strip()
            val = re.sub(r'[^0-9.]', '', val)
            servings_per_container_val = float(val)
        if serving_size in l:
            tmp = l
            val = tmp.replace(serving_size, "").strip()
            default = val
            val = re.sub(r'[^0-9.]', '', val)
            serving_size_val = float(val)

    contval = servings_per_container_val * serving_size_val

    if (serving_size_val > 0 and servings_per_container_val > 0):
        clean.loc[index, 'Containersize_val'] = contval
        clean.loc[index, 'Containersize_unit'] = 'ml'
        clean.loc[index, 'Containersize_org'] = default

        

            
class Soriana(mappings):
    @staticmethod
    def item_label(index, dirty, clean):
        basics(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        serving(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        container_type(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        container_size(input = dirty.loc[index, 'item_label'], index = index, clean = clean)

        clean.loc[index, 'NutrInfo_org'] = dirty.loc[index, 'item_label']
        if (pd.isnull(clean.loc[index, 'TotalCarb_g_pp']) == False):
            p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalCarb_g_pp', type_b = 'TotalCarb_g_p100g')
        if (pd.isnull(clean.loc[index, 'TotalSugars_g_pp']) == False):
            p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalSugars_g_pp', type_b = 'TotalSugars_g_p100g')

        
        
