import os
import re
import csv
from io import StringIO
import pandas as pd

def get_region_and_city(address):
    address_mapping = {
        "Oxford Rd, High Wycombe HP11 2DN, United Kingdom": ("Buckinghamshire", "High Wycombe"),
        "66 E Barnet Rd, London, Barnet EN4 8RQ, United Kingdom": ("Greater London", "Barnet"),
        "Heaton Park Rd, Manchester M9 0QS, United Kingdom": ("Greater Manchester", "Manchester"),
        "Felixstowe Rd, Ipswich IP3 8TQ, United Kingdom": ("Suffolk", "Ipswich")
    }

    return address_mapping.get(address, ("Unknown", "Unknown"))

addresses = [
    "Oxford Rd, High Wycombe HP11 2DN, United Kingdom",
    "66 E Barnet Rd, London, Barnet EN4 8RQ, United Kingdom",
    "Heaton Park Rd, Manchester M9 0QS, United Kingdom",
    "Felixstowe Rd, Ipswich IP3 8TQ, United Kingdom"
]


def separate_numbers_and_letters(text):
    # Use regex to find sequences of digits or letters
    pattern = r'([0-9]+|[a-zA-Z]+)'

    # Find all matches
    matches = re.findall(pattern, text)

    # Separate numbers and letters
    numbers = [match for match in matches if match.isdigit()]
    letters = [match for match in matches if match.isalpha()]

    return numbers, letters
def tsv_string_to_2d_array(tsv_string):
    with StringIO(tsv_string) as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        return [row for row in tsv_reader]
def extract_unit_per_pack(description):
    desc_arr = description.split()
    result = desc_arr.pop()
    pattern = r'\b(\d+)\s*x'
    match = re.search(pattern, result, re.IGNORECASE)
    if match:
        Packsize_org = result
        return int(match.group(1))
    result = desc_arr.pop()
    pattern = r'\bx\s*(\d+)\b'
    match = re.search(pattern, result, re.IGNORECASE)
    if match:
        Packsize_org = result
        return int(match.group(1))
    return 1


directory = 'v1'
for filename in os.listdir(directory):
    buffer = []
    if filename.endswith('_data.csv'):
        buffer.append(filename)
    for b in buffer:
        prefix = filename[:8].split('_')[1]
        df = pd.read_csv(f'{directory}/{filename}')
        loc_result = get_region_and_city(addresses[int(prefix) - 66])
        new_df = pd.DataFrame()
        for index, row in df.iterrows():
            # Variables
            Cals_org_pp = None
            Cals_value_pp = None
            Cals_unit_pp = None

            TotalSugars_g_p100g = None
            TotalCarb_g_p100g = None

            Containersize_org = None
            Containersize_val = None
            Containersize_unit = None
            Packsize_org = None

            Netcontent_val = None
            Netcontent_org = None
            Netcontent_unit = None

            TotalSugars_g_pp = None
            TotalCarb_g_pp = None

            Servsize_portion_org = None
            Servsize_portion_val = None
            Servsize_portion_unit = None

            Cals_value_p100g = None
            Cals_unit_p100g = None

            TotalSugars_pct_pp = None
            TotalCarb_pct_pp = None

            ProductVariety = None
            ProductFlavor = None

            if (not pd.isna(row['item_label'])):
                arr = tsv_string_to_2d_array(row['item_label'])
                # 100 ml/g
                for line in arr:
                    if 'energy' in line[0].lower():
                        Cals_value_p100g = line[1]
                        Cals_value_p100g, Cals_unit_p100g = separate_numbers_and_letters(line[1])
                        Cals_value_p100g = ','.join(Cals_value_p100g)
                        Cals_unit_p100g = ','.join(Cals_unit_p100g)
                    elif 'sugar' in line[0].lower():
                        TotalSugars_g_p100g = line[1]
                    elif 'carbohydrate' in line[0].lower():
                        TotalCarb_g_p100g = line[1]

                if len(arr[0]) > 2:
                    Servsize_portion_org = arr[0][2]
                    Servsize_portion_unit = arr[0][2]
                    Servsize_portion_val = arr[0][2]

                    for line in arr:
                        if 'energy' in line[0].lower():
                            try:
                                Cals_org_pp = line[2]
                                Cals_value_pp, Cals_unit_pp = separate_numbers_and_letters(line[2])
                                Cals_value_pp = ','.join(Cals_value_pp)
                                Cals_unit_pp = ','.join(Cals_unit_pp)
                            except:
                                None
                        elif 'sugar' in line[0].lower():
                            try:
                                TotalSugars_g_pp = line[2]
                            except:
                                None
                        elif 'carbohydrate' in line[0].lower():
                            try:
                                TotalCarb_g_pp = line[2]
                            except:
                                None

                if len(arr[0]) > 3 and '%RI' in arr[0][3]:
                    for line in arr:
                        if 'sugar' in line[0].lower():
                            try:
                                TotalSugars_pct_pp = line[3]
                            except:
                                None
                        elif 'carbohydrate' in line[0].lower():
                            try:
                                TotalCarb_pct_pp = line[3]
                            except:
                                None

            try:
                size_pattern = r'(\d+(?:\.\d+)?)\s*(fl\s*oz|oz|ml|l|pk|pack|g|)\b'
                focus_arr = row['name'].split()
                focus_string = focus_arr.pop()
                match = re.search(size_pattern, focus_string, re.IGNORECASE)
                if match:
                    volume = match.group(1)
                    unit = match.group(2).lower()
                    Containersize_org = f"{volume}{unit}"
                    Containersize_val = volume
                    Containersize_unit = unit
                focus_string = focus_arr.pop()
            except Exception as e:
                print('Failed to get Container Size')
                print(e)

            try:
                Unitpp = extract_unit_per_pack(row['name'])
            except:
                print('err')

            try:
                Netcontent_val = float(Containersize_val) * float(Unitpp)
                Netcontent_unit = Containersize_unit
                Netcontent_org = f'{Containersize_val} x {Containersize_unit}'
            except:
                None

            try:
                pattern = r'\b(zero\s?sugar|no\s?sugar|sugar\s?free|unsweetened|' \
                          r'low\s?sugar|reduced\s?sugar|less\s?sugar|half\s?sugar|' \
                          r'no\s?added\s?sugar|naturally\s?sweetened|artificially\s?sweetened|' \
                          r'sweetened\s?with\s?stevia|aspartame\s?free|' \
                          r'diet|light|lite|skinny|slim|' \
                          r'low\s?calorie|calorie\s?free|zero\s?calorie|no\s?calorie|' \
                          r'low\s?carb|no\s?carb|zero\s?carb|carb\s?free|' \
                          r'keto\s?friendly|diabetic\s?friendly|' \
                          r'decaf|caffeine\s?free|low\s?caffeine|' \
                          r'regular|original|classic|traditional|' \
                          r'extra\s?strong|strong|bold|intense|' \
                          r'mild|smooth|mellow|light\s?roast|medium\s?roast|dark\s?roast|' \
                          r'organic|non\s?gmo|all\s?natural|100%\s?natural|no\s?artificial|' \
                          r'gluten\s?free|dairy\s?free|lactose\s?free|vegan|' \
                          r'low\s?fat|fat\s?free|no\s?fat|skim|skimmed|' \
                          r'full\s?fat|whole|creamy|rich|' \
                          r'fortified|enriched|vitamin\s?enhanced|' \
                          r'probiotic|prebiotic|gut\s?health|' \
                          r'high\s?protein|protein\s?enriched|' \
                          r'low\s?sodium|sodium\s?free|no\s?salt|salt\s?free|' \
                          r'sparkling|carbonated|still|flat|' \
                          r'flavored|unflavored|unsweetened|' \
                          r'concentrate|from\s?concentrate|not\s?from\s?concentrate|' \
                          r'fresh\s?squeezed|freshly\s?squeezed|cold\s?pressed|' \
                          r'raw|unpasteurized|pasteurized|' \
                          r'premium|luxury|gourmet|artisanal|craft|' \
                          r'limited\s?edition|seasonal|special\s?edition|' \
                          r'low\s?alcohol|non\s?alcoholic|alcohol\s?free|virgin|mocktail|' \
                          r'sugar\s?alcohol|sugar\s?alcohols|' \
                          r'high\s?fiber|fiber\s?enriched|' \
                          r'antioxidant|superfood|nutrient\s?rich|' \
                          r'energy|energizing|revitalizing|' \
                          r'relaxing|calming|soothing|' \
                          r'hydrating|isotonic|electrolyte|' \
                          r'fermented|cultured|living|active|' \
                          r'ultra\s?filtered|micro\s?filtered|nano\s?filtered|' \
                          r'distilled|purified|spring|mineral|' \
                          r'fair\s?trade|ethically\s?sourced|sustainably\s?sourced|' \
                          r'local|imported|authentic|genuine)\b'

                matches = re.findall(pattern, row['name'], re.IGNORECASE)
                if matches:
                    ProductVariety = ", ".join(sorted(set(match.lower() for match in matches)))
            except:
                print('Failed to find Product Variety')

            try:
                pattern = r'\b(vanilla|chocolate|strawberry|raspberry|blueberry|blackberry|' \
                          r'berry|mixed berry|wild berry|acai berry|goji berry|cranberry|' \
                          r'apple|green apple|cinnamon apple|caramel apple|pear|peach|apricot|' \
                          r'mango|pineapple|coconut|passion fruit|guava|papaya|lychee|' \
                          r'orange|blood orange|tangerine|clementine|mandarin|grapefruit|' \
                          r'lemon|lime|lemon-lime|key lime|cherry|black cherry|wild cherry|' \
                          r'grape|white grape|concord grape|watermelon|honeydew|cantaloupe|' \
                          r'kiwi|fig|pomegranate|dragonfruit|star fruit|jackfruit|durian|' \
                          r'banana|plantain|avocado|almond|hazelnut|walnut|pecan|pistachio|' \
                          r'peanut|cashew|macadamia|coffee|espresso|mocha|cappuccino|latte|' \
                          r'caramel|butterscotch|toffee|cinnamon|nutmeg|ginger|turmeric|' \
                          r'cardamom|clove|anise|licorice|fennel|mint|peppermint|spearmint|' \
                          r'eucalyptus|lavender|rose|jasmine|hibiscus|chamomile|earl grey|' \
                          r'bergamot|lemongrass|basil|rosemary|thyme|sage|oregano|' \
                          r'green tea|black tea|white tea|oolong tea|pu-erh tea|rooibos|' \
                          r'cola|root beer|cream soda|ginger ale|birch beer|sarsaparilla|' \
                          r'bubblegum|cotton candy|marshmallow|toasted marshmallow|' \
                          r'cookies and cream|cookie dough|birthday cake|red velvet|' \
                          r'pumpkin spice|pumpkin pie|apple pie|pecan pie|key lime pie|' \
                          r'cheesecake|tiramisu|creme brulee|custard|pudding|' \
                          r'butter pecan|butter toffee|butterscotch ripple|' \
                          r'salted caramel|sea salt caramel|dulce de leche|' \
                          r'maple|maple syrup|honey|agave|molasses|brown sugar|' \
                          r'vanilla bean|french vanilla|madagascar vanilla|' \
                          r'dark chocolate|milk chocolate|white chocolate|cocoa|' \
                          r'strawberries and cream|peaches and cream|berries and cream|' \
                          r'tropical|tropical punch|fruit punch|citrus|citrus blend|' \
                          r'melon|mixed melon|berry medley|forest fruits|' \
                          r'blue raspberry|sour apple|sour cherry|sour patch|' \
                          r'lemonade|pink lemonade|cherry lemonade|strawberry lemonade|' \
                          r'iced tea|sweet tea|arnold palmer|' \
                          r'horchata|tamarind|hibiscus|jamaica|' \
                          r'pina colada|mojito|margarita|sangria|' \
                          r'bubble tea|boba|taro|matcha|chai|masala chai|' \
                          r'cucumber|celery|carrot|beet|tomato|' \
                          r'vegetable|mixed vegetable|green vegetable|' \
                          r'aloe vera|noni|acerola|guarana|yerba mate|' \
                          r'bourbon vanilla|tahitian vanilla|mexican vanilla|' \
                          r'dutch chocolate|swiss chocolate|belgian chocolate|' \
                          r'neapolitan|spumoni|rocky road|' \
                          r'unflavored|original|classic|traditional|' \
                          r'mystery flavor|surprise flavor|limited edition flavor)\b'
                matches = re.findall(pattern, row['name'], re.IGNORECASE)
                if matches:
                    ProductFlavor = ", ".join(sorted(set(match.lower() for match in matches)))
            except:
                print('Failed to get Product Flavour')

            new_row = {
                'ID': row['idx'],
                'Country': 'United Kingdom',
                'Store': 'Sainsbury',
                'Region': loc_result[0],
                'City':  loc_result[1],
                'ProductName': row['name'],
                'ProductVariety': ProductVariety,
                'ProductFlavor': ProductFlavor,
                'Unitpp': Unitpp,
                'ProductBrand': row['brand'],
                'ProductAisle': row['aisle'],
                'ProductCategory': row['subaisle'],
                'ProductSubCategory': row['subsubaisle'],
                'ProductImages': row['img_urls'],
                'Containersize_org': Containersize_org,
                'Containersize_val': Containersize_val,
                'Containersize_unit': Containersize_unit,
                'Cals_org_pp': Cals_org_pp,
                'Cals_value_pp': Cals_value_pp,
                'Cals_unit_pp': Cals_unit_pp,
                'TotalCarb_g_pp': TotalCarb_g_pp,
                'TotalCarb_pct_pp': TotalCarb_pct_pp,
                'TotalSugars_g_pp': TotalSugars_g_pp,
                'TotalSugars_pct_pp': TotalSugars_pct_pp,
                'AddedSugars_g_pp': None,
                'AddedSugars_pct_pp': None,
                'Cals_value_p100g': Cals_value_p100g,
                'Cals_unit_p100g': Cals_unit_p100g,
                'TotalCarb_g_p100g': TotalCarb_g_p100g,
                'TotalCarb_pct_p100g': None,
                'TotalSugars_g_p100g': TotalSugars_g_p100g,
                'TotalSugars_pct_p100g': None,
                'AddedSugars_g_p100g': None,
                'AddedSugars_pct_p100g': None,
                'Packsize_org': Packsize_org,
                'Pack_type': None,
                'Netcontent_val': Netcontent_val,
                'Netcontent_org': Netcontent_org,
                'Netcontent_unit': Netcontent_unit,
                'Price': row['old_price'],
                'Description': row['description'],
                'Nutr_label': row['item_label'],
                'Ingredients': row['item_ingredients'],
                'NutrInfo_org': None,
                'Servsize_container_type_org': None,
                'Servsize_container_type_val': None,
                'Servsize_container_type_unit': None,
                'Servsize_portion_org': Servsize_portion_org,
                'Servsize_portion_val': Servsize_portion_val,
                'Servsize_portion_unit': Servsize_portion_unit,
                'Servings_cont': None,
                'ProdType': 'N/A',
                'StorType': 'N/A',
                'ItemNum': row['itemNum'],
                'SKU': 'N/A',
                'UPC': 'UPC',
                'url': row['url'],
                'DataCaptureTimeStamp': row['timeStamp'],
                'Notes': 'Notes'
            }
            new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)

        new_df.to_csv(f'{directory}/done/{filename}', index = False)
