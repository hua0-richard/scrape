##TODO##
# Added Sugars
# p100g carb, sugar, energy calc
# added sugars

from util.mappings import mappings
import re
import pandas as pd
nutrition_label_mappings_soriana = {
    "Energía por porción" : "Cals_value_pp",
    "Carbohidratos" : "TotalCarb_g_pp",
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
                #val = re.sub(r'\D', '', val)
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
            clean.loc[index, 'Netcontent_org'] = tmp
            val = tmp.replace(net_content, "").strip()
            default = val
            unit = re.sub(r'[^a-zA-Z]', '', val)
            val_unit = re.sub(r'[^a-zA-Z]', '', val)
            val = re.sub(r'[^0-9.]', '', val)
            net_content_num = float(val)
            nums = re.sub(r'\D', '', clean.loc[index, type_b])
            clean.loc[index, type_a] =  (net_content_num / 100) * float(nums)
            clean.loc[index, 'Netcontent_val'] = net_content_num
            clean.loc[index, 'Netcontent_org'] = default
            clean.loc[index, 'Netcontent_unit'] = val_unit
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
            clean.loc[index, 'Servings_cont'] = servings_per_container_val
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

def parse_from_name(index, clean, dirty):
    tmp = dirty.loc[index, 'name']
    pattern = re.compile(r'\b\d+(\.\d+)?\s*(ml|l|L|g|kg|oz|Ml|Lt|fl oz)\b')
    matches = pattern.search(tmp)
    if (matches):
        val = re.sub(r'[^0-9.]', '', matches[0])
        clean.loc[index, 'Containersize_val'] = val
        val = re.sub(r'[^a-zA-Z]', '', matches[0])
        clean.loc[index, 'Containersize_unit'] = val
        

            
class Soriana(mappings):
    @staticmethod
    def item_label(index, dirty, clean):
        basics(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        serving(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        container_type(input = dirty.loc[index, 'item_label'], index = index, clean = clean)
        container_size(input = dirty.loc[index, 'item_label'], index = index, clean = clean)

        if (pd.isnull(clean.loc[index, 'Containersize_val'])):
            parse_from_name(index = index, clean = clean, dirty = dirty)

        clean.loc[index, 'NutrInfo_org'] = dirty.loc[index, 'item_label']
        clean.loc[index, 'NutrLabel'] = dirty.loc[index, 'item_label']

        # if (pd.isnull(clean.loc[index, 'TotalCarb_g_pp']) == False):
        #     p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalCarb_g_p100g', type_b = 'TotalCarb_g_pp')
        # if (pd.isnull(clean.loc[index, 'TotalSugars_g_pp']) == False):
        #     p100g(input = dirty.loc[index, 'item_label'], index = index, clean = clean, type_a = 'TotalSugars_g_p100g', type_b = 'TotalSugars_g_pp')
        
        @staticmethod
        def country(index, clean):
            clean.loc[index, 'Country'] = 'Mexico'
        @staticmethod
        def indices(index, clean):
            INDEX = 30
            clean.loc[index, 'ID'] = 30


        
        

