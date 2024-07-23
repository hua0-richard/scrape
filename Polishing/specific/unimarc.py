from util.mappings import mappings
import re

def contains_only_digits_and_period(s):
    pattern = re.compile(r'^[0-9.]+$')
    return bool(pattern.match(s))
def remove_non_numeric_except_period(string):
    return re.sub(r'[^0-9.]', '', string)
def remove_numbers(string):
    return re.sub(r'\d+', '', string)

def has_substring(main_string, substring):
    return substring in main_string

container_pattern = r'\b(?:botella|lata|tetra|caja|bidón|botellón|pack)\b(?:\s+(?:de|retornable|no\s+retornable))?\s*(?:\d+(?:\.\d+)?)?\s*(?:cc|ml|L|Lt)?'
container_pattern_milk = r'\b(?:L|Lt|ml|g|Kg|cc|un)\b|\b(?:bolsa|botella|caja|pote|tarro|bandeja|pan|bidón|doypack|lata|tetra|cajita|pouch|squeeze)\b'

class unimarc(mappings):
    @staticmethod
    def preprocess(clean):
        try:
            df = clean.drop(columns=['City'])
            df = df.drop(columns=['Region'])
            df = df.drop(columns=['Store'])
            print("PREPROCESS")
            return df
        except Exception as e:
            None
    @staticmethod
    def country(index, clean):
        try:
            clean.loc[index, 'Country'] = 'Chile'
        except Exception as e:
            None

    @staticmethod
    def city(index, dirty, clean):
        try:
            index_number = int(dirty.loc[index, 'idx'][:2])
            city = ""
            if (index_number == 41):
                city = "Maipú"
            elif (index_number == 42):
                city = "Viña del Mar"
            elif (index_number == 43):
                city = "Concepción"
            elif (index_number == 44):
                city = "Talca"
            clean.loc[index, "City_CHI"] = city
        except Exception as e:
            None

    @staticmethod
    def region(index, dirty, clean):
        try:
            index_number = int(dirty.loc[index, 'idx'][:2])
            region = ""
            if (index_number == 41):
                region = "Región Metropolitana"
            elif (index_number == 42):
                region = "Región de Valparaíso"
            elif (index_number == 43):
                region = "Región del Bío Bío"
            elif (index_number == 44):
                region = "Región del Maule"
            clean.loc[index, "Region_CHI"] = region
        except Exception as e:
            None
    
    @staticmethod
    def store(index, clean):
        try:
            clean.loc[index, 'Store_CHI'] = 'Unimarc'
        except Exception as e:
            None

    @staticmethod
    def item_label(index, dirty, clean):
        try:
            lines = dirty.loc[index, 'item_label']
            clean.loc[index, 'NutrInfo_org'] = lines
            lines = lines.split('\n')
            servings_cont = 0

            for l in lines:
                PORTION = "Porción por envase:"
                PORTION_IND = "Porción individual:"
                ENERGY = "Energía (kCal)"
                SUGAR_TOTALS = "Azúcares totales (g)"
                CARBS = "H. de C. disponibles (g)"
                PACK = "Pack"

                if has_substring(l, PORTION):
                    tmp = l.replace(PORTION,"").strip()
                    clean.loc[index, 'Servings_cont'] = tmp
                    servings_cont = tmp
                elif has_substring(l, PORTION_IND):
                    tmp = l.replace(PORTION_IND,"").strip()
                    tmp_val = remove_non_numeric_except_period(tmp)
                    serv_ind = float(tmp_val)
                    tmp_unit = remove_numbers(tmp)
                    clean.loc[index, 'Servsize_portion_org'] = tmp
                    clean.loc[index, 'Servsize_portion_val'] = tmp_val
                    clean.loc[index, 'Servsize_portion_unit'] = tmp_unit


                    clean.loc[index, 'Containersize_org'] = f"{servings_cont} portion(s) x {tmp_val} {tmp_unit} per portion "
                    clean.loc[index, 'Containersize_val'] = float(servings_cont) * float(tmp_val)
                    clean.loc[index, 'Containersize_unit'] = tmp_unit
                    servings_cont = 0
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

        try:
            clean.loc[index, 'SKU'] = dirty.loc[index, 'SKU']
        except Exception as e:
            None

        try:
            tokens = dirty.loc[index, 'name'].split()
            if (tokens[0] == PACK):
                for i in range(len(tokens)):
                    if tokens[i] == 'un':
                        clean.loc[index, 'Unitpp'] = tokens[i - 1]
                        packsize_org = ""
                        for j in range(i - 1, len(tokens)):
                            packsize_org += tokens[j] + " "
                        packsize_org = packsize_org.strip()
                        clean.loc[index, 'Packsize_org'] = packsize_org
                        break
        except Exception as e:
            None

        try:
            matches = re.findall(container_pattern, dirty.loc[index, 'name'])
            matches_milk = re.findall(container_pattern_milk, dirty.loc[index, 'name'])
            if matches:
                clean.loc[index, 'Pack_type'] = matches[0]
            elif matches_milk:
                clean.loc[index, 'Pack_type'] = matches_milk[0]
        except Exception as e:
            None

        try:
            size = dirty.loc[index, 'size']
            clean.loc[index, 'Netcontent_org'] = size
            clean.loc[index, 'Netcontent_val'] = remove_non_numeric_except_period(size)
            clean.loc[index, 'Netcontent_unit'] = remove_numbers(size).replace('.', '')
        except Exception as e:
            None



