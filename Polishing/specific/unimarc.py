from util.mappings import mappings
import re
'''
Datos de Nutrici√≥n
Porci√≥n por envase: 38
Porci√≥n individual: 24g
Nutrientes 100 g 1 porci√≥n

Nutrition Facts
Serving per container: 38
Individual serving: 24g
Nutrients 100 g 1 serving
'''


nutrition_label_mappings_unimarc = {
    "Energía (kCal)": "Cals",
    "Hidratos de Carbono Disp.": "TotalCarb",
    "Azúcares Totales": "TotalSugars",
}

def contains_only_digits_and_period(s):
    pattern = re.compile(r'^[0-9.]+$')
    return bool(pattern.match(s))

class unimarc(mappings):
    @staticmethod
    def country(index, clean):
        try:
            clean.loc[index, 'Country'] = '3'
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
            lines = dirty.loc[index, 'item_label'].split('\n')
            # Loop through each line   
            for i in range(4, len(lines)):
                l = lines[i]
                # check for keywords in dict
                # label first, standard second
                try:
                    tokens = l.strip().split()
                    tokens = [str(element) for element in tokens]
                except Exception as e:
                    print(e)
                for key, value in nutrition_label_mappings_unimarc.items():
                    if key in l:
                        count = 0
                        for t in tokens:
                            # Check first token in line
                            if (contains_only_digits_and_period(t) and count == 0):
                                if (value == 'Cals'):
                                    col1 = "Cals_value_pp"
                                    col2 = "Cals_unit_pp"
                                    col3 = "Cals_org_pp"
                                    clean.loc[index, col1] = t
                                    clean.loc[index, col2] = 'kCal'
                                    clean.loc[index, col3] = l
                                if (value == 'TotalCarb'):
                                    col1 = "TotalCarb_g_pp"
                                    clean.loc[index, col1] = t
                                if (value == 'TotalSugars'):
                                    col1 = "TotalSugars_g_pp"
                                    clean.loc[index, col1] = t
                                count = count + 1
                            # Check second token in line
                            elif (contains_only_digits_and_period(t) and count == 1):
                                if (value == 'Cals'):
                                    col1 = "Cals_value_p100g"
                                    col2 = "Cals_unit_p100g"
                                    clean.loc[index, col1] = t
                                    clean.loc[index, col2] = 'kCal'

                                if (value == 'TotalCarb'):
                                    col1 = "TotalCarb_g_p100g"
                                    clean.loc[index, col1] = t
                                if (value == 'TotalSugars'):
                                    col1 = "TotalSugars_g_p100g"
                                    clean.loc[index, col1] = t

        except Exception as e:
            None
        return 0
