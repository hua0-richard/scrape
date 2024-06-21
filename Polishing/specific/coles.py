from util.mappings import mappings
import re

nutrition_label_mappings_coles = {
    "Energy": "Cals",
    "Protein": "Protein",
    "TotalFat": "Total Fat",
    "SatFat": "Saturated Fat",
    "Carbohydrate": "TotalCarb",
    "Sugars": "TotalSugars",
    "Saturated": "SatFat",
    "Fat": "Total Fat",
    "Energy KJ": "Cals",
}


def look_ahead(input):
    result = {}
    entry = ''
    pattern = re.compile(r'^[a-zA-Z\s\[\]\(\)]+$')
    pattern_vit = re.compile('vitamin', re.IGNORECASE)
    for i in range(3, len(input)):
        if (re.match(pattern, input[i].strip()) or re.match(pattern_vit, input[i].strip())):
            entry = input[i]
            result[entry] = []
        else:
            result[entry].append(input[i])
    return result


def extract_container_size(product_description):
    # Regular expression pattern to find container size with unit and quantity in different orders
    pattern = r'(\d+)\s*(mL|ml|L|l|g|G)\s*[Xx]\s*(\d+)|(\d+)\s*[Xx]\s*(\d+)\s*(mL|ml|L|l|g|G)'
    match = re.search(pattern, product_description)

    if match:
        if match.group(1):  # Handles pattern with size first, then quantity
            container_size = int(match.group(1))
            unit = match.group(2)
            num_containers = int(match.group(3))
        else:  # Handles pattern with quantity first, then size
            num_containers = int(match.group(4))
            container_size = int(match.group(5))
            unit = match.group(6)
        return num_containers, container_size, unit
    else:
        return None

def extract_container_type(product_description):
    # Define keywords for container types
    keywords = [
        'cans', 'bottles', 'tea bags', 'beans', 'ground',
        'sachets', 'capsules', 'jar', 'cordial', 'powder'
    ]

    # Construct regular expression pattern dynamically
    pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'

    # Search for the pattern in the product description
    match = re.search(pattern, product_description, re.IGNORECASE)

    if match:
        container_type = match.group()
        return container_type.strip()
    else:
        return None

class Coles(mappings):
    @staticmethod
    def name(index, dirty, clean):
        try:
            raw = dirty.loc[index, 'name'].strip()
        except:
            raw = ''
        try:
            prefix = dirty.loc[index, 'brand'].strip()
        except:
            prefix = None

        split = raw.find("|")
        result = raw[split + 1:].strip()

        con = extract_container_size(raw)
        if (con):
            clean.loc[index, 'Netcontent_unit'] = con[2]
            clean.loc[index, 'Netcontent_val'] = str(con[0]*con[1])
        else:
            clean.loc[index, 'Netcontent_org'] = result
            clean.loc[index, 'Netcontent_unit'] = ''.join(filter(str.isalpha, result))
            clean.loc[index, 'Netcontent_val'] = ''.join(filter(lambda char: char.isdigit() or char == '.', result))

        pack = extract_container_type(raw)
        if pack:
            clean.loc[index, 'Pack_type'] = pack

        if (index != -1):
            raw = raw[:split].strip()
        if (prefix != None and raw.startswith(prefix)):
            raw = raw[len(prefix):].strip()

        clean.loc[index, 'ProductName'] = raw.strip()

    @staticmethod
    def item_ingredients(index, dirty, clean):
        try:
            raw_ingredients = dirty.loc[index, 'item_ingredients']
            if raw_ingredients.startswith('INGREDIENTS:'):
                raw_ingredients = raw_ingredients[len('INGREDIENTS:'):]
        except:
            raw_ingredients = ''

        clean.loc[index, 'Ingredients'] = raw_ingredients
        tokenized_raw_ingredients = raw_ingredients.split(',')
        for index in range(len(tokenized_raw_ingredients)):
            tokenized_raw_ingredients[index] = tokenized_raw_ingredients[index].strip()
        if (len(tokenized_raw_ingredients) > 1):
            tokenized_raw_ingredients[-1] = tokenized_raw_ingredients[-1][:-1]

    @staticmethod
    def item_label(index, dirty, clean):
        try:
            lines = dirty.loc[index, 'item_label'].split('\n')
            lines = [s.strip() for s in lines]

            for i, l in enumerate(lines):
                if (l.strip()[0] == '*'):
                    lines.pop(i)
            cleand_nutr = ''
            saved = look_ahead(lines)

            for i, l in enumerate(lines):
                if (i == len(lines) - 1):
                    cleand_nutr += l
                    break
                cleand_nutr += (l + "\n")

            clean.loc[index, 'Nutr_label'] = cleand_nutr

            for item in nutrition_label_mappings_coles:
                if item in saved:
                    try:
                        for col in clean.columns:
                            # print(saved)
                            pattern100g = rf'{nutrition_label_mappings_coles[item]}_g_p100g'
                            pattern100gValue = rf'{nutrition_label_mappings_coles[item]}_value_p100g'

                            patternServingValue = rf'{nutrition_label_mappings_coles[item]}_value_pp'
                            patternServingGram = rf'{nutrition_label_mappings_coles[item]}_g_pp'
                            patternPercentage = rf'{nutrition_label_mappings_coles[item]}_pct_pp'
                            if (re.search(pattern100g, col) or re.search(pattern100gValue, col)):
                                try:
                                    res = saved[item]
                                    clean.loc[index, col] = res[0]
                                    if (pattern100gValue == 'Cals_value_p100g'):
                                        clean.loc[index, col] = ''.join(filter(str.isdigit, res[0]))
                                        None
                                except:
                                    None
                            if (re.search(patternServingValue, col) or re.search(patternServingGram, col)):
                                try:
                                    res = saved[item]
                                    clean.loc[index, col] = res[1]
                                    if (patternServingValue == 'Cals_value_pp'):
                                        clean.loc[index, col] = ''.join(filter(str.isdigit, res[1]))
                                        clean.loc[index, 'Cals_org_pp'] = res[1]
                                except:
                                    None
                            if (re.search(patternPercentage, col)):
                                try:
                                    res = saved[item]
                                    clean.loc[index, col] = res[2]
                                except:
                                    None
                    except Exception as e:
                        print(e)
            clean.loc[index, 'Cals_unit_p100g'] = "kJ"
            clean.loc[index, 'Cals_unit_pp'] = "kJ"
        except Exception as e:
            None

    @staticmethod
    def servsize_portion_org(index, dirty, clean):
        try:
            item_label = dirty.loc[index, 'item_label']
            lines = item_label.split('\n')
            if len(lines) > 1:
                tmp1 = "".join(filter(str.isdigit, lines[4]))
                tmp2 = "".join(filter(str.isdigit, lines[5]))



                if item_label[4] and item_label[5]:
                    result = round(int(tmp2) * 100 / int(tmp1), 1)
                    clean.loc[index, 'Servsize_portion_org'] = result
                    clean.loc[index, 'Servsize_portion_unit'] = 'g'

        except Exception as e:
            None

    @staticmethod
    def containersize_org(index, dirty, clean):
        try:
            name = dirty.loc[index, 'name']
            end = name.split("|", 1)[1].strip()
            clean.loc[index, 'Containersize_org'] = end
        except Exception as e:
            None


