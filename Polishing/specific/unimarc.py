from util.mappings import mappings
import re

nutrition_label_mappings_unimarc = {
    "Energía (kCal)": "Cals",
    "Hidratos de Carbono Disp.": "TotalCarb",
    "Azúcares Totales": "TotalSugars",
}

def contains_only_digits_and_period(s):
    pattern = re.compile(r'^[0-9.]+$')
    return bool(pattern.match(s))
def remove_non_numeric_except_period(string):
    return re.sub(r'[^0-9.]', '', string)
def remove_numbers(string):
    return re.sub(r'\d+', '', string)

def has_substring(main_string, substring):
    return substring in main_string

class unimarc(mappings):
    @staticmethod
    def country(index, clean):
        try:
            clean.loc[index, 'Country'] = 'Mexico'
        except Exception as e:
            None

    @staticmethod
    def city(index, clean):
        try:
            clean.loc[index, 'City_CHI'] = 7
        except Exception as e:
            None

    @staticmethod
    def region(index, clean):
        try:
            clean.loc[index, 'Region_CHI'] = 12
        except Exception as e:
            None
    
    @staticmethod
    def store(index, clean):
        try:
            clean.loc[index, 'Store_CHI'] = 3
        except Exception as e:
            None

    @staticmethod
    def item_label(index, dirty, clean):
        try:
            lines = dirty.loc[index, 'item_label']
            clean.loc[index, 'Nutr_label'] = lines
            lines = lines.split('\n')
            for l in lines:
                PORTION = "Porción por envase:"
                PORTION_IND = "Porción individual:"
                ENERGY = "Energía (kCal)"
                SUGAR_TOTALS = "Azúcares totales (g)"
                CARBS = "H. de C. disponibles (g)"

                if has_substring(l, PORTION):
                    tmp = l.replace(PORTION,"").strip()
                    clean.loc[index, 'Servings_cont'] = tmp
                elif has_substring(l, PORTION_IND):
                    tmp = l.replace(PORTION_IND,"").strip()
                    tmp_val = remove_non_numeric_except_period(tmp)
                    tmp_unit = remove_numbers(tmp)
                    clean.loc[index, 'Servsize_portion_org'] = tmp
                    clean.loc[index, 'Servsize_portion_val'] = tmp_val
                    clean.loc[index, 'Servsize_portion_unit'] = tmp_unit
                elif has_substring(l,ENERGY):
                    clean.loc[index, 'Cals_org_pp'] = l
                    tmp = l.replace(ENERGY,"").strip()
                    tokens = tmp.split()
                    clean.loc[index, 'Cals_value_p100g'] = tokens[0]
                    clean.loc[index, 'Cals_unit_p100g'] = 'kCal'
                    clean.loc[index, 'Cals_value_pp'] = tokens[1]
                    clean.loc[index, 'Cals_unit_pp'] = 'kCal'
                elif has_substring(l, CARBS):
                    tmp = l.replace(CARBS,"").strip()
                    tokens = tmp.split()
                    clean.loc[index, 'TotalCarb_g_p100g'] = tokens[0]
                    clean.loc[index, 'TotalCarb_g_pp'] = tokens[1]
                elif has_substring(l, SUGAR_TOTALS):
                    tmp = l.replace(SUGAR_TOTALS,"").strip()
                    tokens = tmp.split()
                    clean.loc[index, 'TotalSugars_g_p100g'] = tokens[0]
                    clean.loc[index, 'TotalSugars_g_pp'] = tokens[1]


        except Exception as e:
            None



