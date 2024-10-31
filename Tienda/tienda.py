import glob
import os

import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
from bs4 import BeautifulSoup

# Special Package to scrap and aids in avoiding more stringent sites

import time
import datetime
import pytz

import random

import re

FAVNUM = 22222
GEN_TIMEOUT = 3
STORE_NAME = 'tesco'
LOCATION = ''
MAX_RETRY = 10


def extract_number_of_units(product_name):
    # Regular expression patterns
    patterns = [
        # Pattern for "NxM unit" format (e.g., 18x330ml, 6 X 2 Litre)
        r'(\d+)\s*(?:x|X)\s*\d+(?:\.\d+)?\s*(?:ml|l|litr?e?|cl|fl\.?\s*oz|oz|gal|pt|kg|g|lb)',

        # Pattern for "N pack" or "pack of N" format
        r'(\d+)(?:\s*-?\s*pack|pack\s+of\s+\d+)',

        # Pattern for "N cans/bottles" format
        r'(\d+)\s+(?:cans?|bottles?)'
    ]

    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # If no multi-pack information is found, assume it's a single unit
    return 1

def extract_serving_size(text):
    # Regular expression pattern to match serving size
    pattern = r'(?:per|each|one|a serving contains)?\s*(?:can|glass)?\s*\(?(\d+(?:\.\d+)?)\s*(ml|g)\)?'

    # Find all matches in the text
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        value = match.group(1)
        unit = match.group(2).lower()
        return {
            'serving_size_value': float(value),
            'serving_size_unit': unit
        }
    else:
        return {
            'serving_size_value': None,
            'serving_size_unit': None
        }

def extract_container_info(product_name):
    # Comprehensive list of possible units
    units = r'ml|l|litr?e?|cl|fl\.?\s*oz|oz|gal|pt|kg|g|lb'

    # Regular expression patterns
    patterns = [
        # Pattern for "NxM unit" format (e.g., 18x330ml)
        rf'(\d+\s*x\s*\d+(?:\.\d+)?)\s*({units})',

        # Pattern for single value with unit (e.g., 2L, 750ml, 1 Litre)
        rf'(\d+(?:\.\d+)?)\s*({units})',

        # Pattern for fractional values (e.g., 1/2 gallon)
        rf'(\d+/\d+)\s*({units})',

        # Pattern for value with unit and pint equivalent (e.g., 1.13L, 2 Pints)
        rf'(\d+(?:\.\d+)?)\s*({units})(?:\s*,\s*(\d+(?:\.\d+)?)\s*pints?)?'
    ]

    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            container_size = match.group(0)
            container_value = match.group(1)
            container_unit = match.group(2)

            # Standardize units
            container_unit = standardize_unit(container_unit)

            return {
                'product_name': product_name,
                'container_size': container_size,
                'container_value': container_value,
                'container_unit': container_unit
            }

    # If no match is found
    return {
        'product_name': product_name,
        'container_size': None,
        'container_value': None,
        'container_unit': None
    }

def standardize_unit(unit):
    unit = unit.lower()
    if unit in ['l', 'litr', 'litre', 'liter']:
        return 'L'
    elif unit in ['ml', 'milliliter', 'millilitre']:
        return 'ml'
    elif unit in ['kg', 'kilogram']:
        return 'kg'
    elif unit in ['g', 'gram']:
        return 'g'
    elif unit in ['oz', 'ounce']:
        return 'oz'
    elif unit in ['fl oz', 'fl. oz', 'fluid ounce']:
        return 'fl oz'
    elif unit in ['gal', 'gallon']:
        return 'gal'
    elif unit in ['pt', 'pint']:
        return 'pt'
    else:
        return unit

def parse_net_content(content):
    # Regular expression to match quantity, unit, and optional multiplier
    pattern = r'^(\d+(?:\.\d+)?)\s*x?\s*(\d+(?:\.\d+)?)?\s*([a-zA-Z]+)?\s*(e|℮)?$'

    match = re.match(pattern, content, re.IGNORECASE)

    if not match:
        return None, None  # Return None if the content doesn't match expected format

    quantity = match.group(1)
    multiplier = match.group(2)
    unit = match.group(3)

    # Calculate total quantity
    if multiplier:
        quantity = float(quantity) * float(multiplier)
    else:
        quantity = float(quantity)

    # Standardize units
    if unit:
        unit = unit.lower()
        if unit in ['l', 'litre', 'liter']:
            unit = 'L'
        elif unit == 'ml':
            quantity /= 1000
            unit = 'L'
        elif unit == 'cl':
            quantity /= 100
            unit = 'L'
        elif unit == 'g':
            unit = 'g'
        elif unit == 'kg':
            quantity *= 1000
            unit = 'g'
        elif unit in ['pint', 'pints']:
            quantity *= 0.568261
            unit = 'L'
    else:
        unit = ''  # If no unit is specified

    return round(quantity, 3), unit

def extract_pack_size(text):
    # Regular expression pattern to match "Pack size:" followed by a number and optional unit
    pattern = r"Pack size:\s*(\d+(?:\.\d+)?(?:\s*[A-Za-z]+)?)"

    # Search for the pattern in the text
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        return None

def extract_city_and_region(address):
    parts = address.split(', ')
    if len(parts) >= 3:
        city = parts[-3]
        region = parts[-2].split()[0]
        return [city, region]
    else:
        return ["Invalid", "Address"]

def format_nutrition(nutritional_info):
    result = []

    # Get the maximum width for each column
    col_widths = [max(len(str(row[i])) for row in [nutritional_info['headers']] + nutritional_info['data'])
                  for i in range(len(nutritional_info['headers']))]

    # Add headers
    header = " | ".join(h.ljust(w) for h, w in zip(nutritional_info['headers'], col_widths))
    result.append(header)

    # Add a separator line
    result.append("-" * len(header))

    # Add data rows
    for row in nutritional_info['data']:
        formatted_row = " | ".join(str(item).ljust(w) for item, w in zip(row, col_widths))
        result.append(formatted_row)

    return "\n".join(result)

def extract_info(heading, content):
    soup = BeautifulSoup(content, 'html.parser')
    h3 = soup.find('h3', string=heading)
    if h3:
        div = h3.find_next('div', class_='styled__Content-mfe-pdp__sc-1od89q4-2')
        if div:
            return div.text.strip()
    return None

def remove_empty_lines(text):
    return '\n'.join(line for line in text.splitlines() if line.strip())

def custom_sort_key(value):
    parts = value.split('-')
    return int(parts[1])

def cache_strategy():
    folder_path = 'output/tmp'
    item_urls_csvs = glob.glob(os.path.join(folder_path, '*data.csv'))
    reference_df_list = []
    for file in item_urls_csvs:
        df = pd.read_csv(file)
        reference_df_list.append(df)
    combined_reference_df = pd.concat(reference_df_list, ignore_index=True)
    combined_reference_df.drop_duplicates(subset='url', keep='first', inplace=True)
    return combined_reference_df
def setup_tesco(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_tesco(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)

def setLocation_tesco(driver, address, EXPLICIT_WAIT_TIME):
    global LOCATION
    LOCATION = address
    input('Manually set Location?')
    print('Set Location Complete')
def scrapeSite_tienda(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    items = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')
        driver.get('https://www.chedraui.com.mx/supermercado/bebidas')
        categories_drinks = ['https://www.chedraui.com.mx/supermercado/bebidas/jugos', 'https://www.chedraui.com.mx/supermercado/bebidas/refrescos', 'https://www.chedraui.com.mx/supermercado/bebidas/agua', 'https://www.chedraui.com.mx/supermercado/bebidas/rehidratantes-y-energizantes', 'https://www.chedraui.com.mx/supermercado/bebidas/te-y-cafe-bebibles']

        for cat in categories_drinks:
            driver.get(cat)
            try:
                for i in range(50):
                    gallery_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "gallery-layout-container"))
                    )
                    links = gallery_container.find_elements(By.TAG_NAME, "a")

                    for link in links:
                        href = link.get_attribute("href")
                        if href:
                            items.append(href)  # Append href instead of link object

                    scroll_amount = 500
                    scroll_script = f"window.scrollBy(0, {scroll_amount});"
                    driver.execute_script(scroll_script)
                    time.sleep(2)

                items = list(set(items))  # Remove duplicates after all scrolling
                print(f'items so far... {len(items)}')

            except Exception as e:
                print(f'error: {str(e)}')
            pd.DataFrame(items).to_csv(f'output/tmp/index_{str(ind)}_{aisle}_item_urls.csv', index=False, header=None, encoding='utf-8-sig')

        pd.DataFrame(items).to_csv(f'output/tmp/index_{str(ind)}_{aisle}_item_urls.csv', index=False, header=None, encoding='utf-8-sig')
        print(f'items so far... {len(items)}')

    df_data = pd.DataFrame()
    site_items_df = pd.DataFrame()

    # Cache Strategy
    try:
        seen_items = cache_strategy()
        new_rows = []
        for cache_index in range(len(items)):
            item_url = items[cache_index]
            print(f"{cache_index} x {item_url}")
            matching_rows = seen_items[seen_items['url'] == item_url]
            if len(matching_rows) > 0:
                row = matching_rows.iloc[0].copy()
                row['ID'] = f'{ind}-{cache_index}-{aisle.upper()[:3]}'
                index_for_here = f'{ind}-{cache_index}-{aisle.upper()[:3]}'
                print(f'Found Cached Entry {cache_index}')
                new_rows.append(row)
                try:
                    full_path = 'output/images/' + str(ind) + '/' + str(row['ID']) + '/' + str(
                        index_for_here) + '-' + str(0) + '.png'
                    if not os.path.isfile(full_path):
                        response = requests.get(row['img_urls'])
                        if response.status_code == 200:
                            with open(full_path, 'wb') as file:
                                file.write(response.content)
                except:
                    print('Images Error Cache')
        if new_rows:
            new_rows_df = pd.DataFrame(new_rows)
            df_data = pd.concat([df_data, new_rows_df], ignore_index=True)
            df_data = df_data.drop_duplicates(subset=['url'], keep='last')
            site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
            site_items_df = site_items_df.sort_values(by='ID', key=lambda x: x.map(custom_sort_key))
            site_items_df = site_items_df.reset_index(drop=True)
    except Exception as e:
        print(e)
        print('Cache Failed')

    # scrape items and check for already scraped
    try:
        df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_{STORE_NAME}_data.csv")
        site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
    except:
        print('No Prior Data Found... ')

    for item_index in range(len(items)):
        item_url = items[item_index]
        print(item_url)
        if not df_data.empty and items[item_index] in df_data['url'].values:
            print(f'{ind}-{item_index} Item Already Exists!')
            continue

        for v in range(5):
            try:
                time.sleep(GEN_TIMEOUT)
                driver.get(item_url)
                new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index)
                if new_row is None:
                    break
                site_items_df = pd.concat([site_items_df, pd.DataFrame([new_row])], ignore_index=True)
                site_items_df = site_items_df.drop_duplicates(subset=['url'], keep='last')
                print(new_row)
                break
            except Exception as e:
                print(f'Failed to scrape item. Attempt {v}. Trying Again... ')
                print(e)

        if (item_index % 10 == 0):
            site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_{STORE_NAME}_data.csv', index=False)

    site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_{STORE_NAME}_data.csv', index=False)


def scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, index):
    time.sleep(GEN_TIMEOUT)
    ID = f'{ind}-{index}-{aisle.upper()[:3]}'
    Region = None
    City = None

    ProductName = None
    ProductBrand = None
    ProductCategory = None
    ProductSubCategory = None

    ProductImages = None
    Description = None
    Price = None
    Nutr_label = None
    Ingredients = None
    Unitpp = None
    Netcontent_val = None
    Netcontent_org = None
    Netcontent_unit = None
    NutrInfo_org = 'N/A'
    Servsize_container_type_org = 'N/A'
    Servsize_container_type_val = 'N/A'
    Servsize_container_type_unit = 'N/A'
    Servsize_portion_org = None
    Servsize_portion_val = None
    Servsize_portion_unit = None
    Servings_cont = None
    Containersize_org = None
    Containersize_val = None
    Containersize_unit = None
    Packsize_org = None
    Pack_type = None
    ProductVariety = None
    ProductFlavor = None
    Cals_org_pp = None
    Cals_value_pp = None
    Cals_unit_pp = None
    TotalCarb_g_pp = None
    TotalCarb_pct_pp = 'N/A'
    TotalSugars_g_pp = None
    TotalSugars_pct_pp = 'N/A'
    AddedSugars_g_pp = 'N/A'
    AddedSugars_pct_pp = 'N/A'
    Cals_value_p100g = 'N/A'
    Cals_unit_p100g = 'N/A'
    TotalCarb_g_p100g = 'N/A'
    TotalCarb_pct_p100g = 'N/A'
    TotalSugars_g_p100g = 'N/A'
    TotalSugars_pct_p100g = 'N/A'
    AddedSugars_g_p100g = 'N/A'
    AddedSugars_pct_p100g = 'N/A'
    UPC = None
    Notes = 'OK'

    global LOCATION
    print(LOCATION)
    result = extract_city_and_region(LOCATION)
    City = result[0]
    Region = result[1]

    for p_name in range(1):
        try:
            element = driver.find_element(By.CSS_SELECTOR, "h1[data-auto='pdp-product-title']")
            ProductName = element.text
            break
        except Exception as e:
            print(f'Failed to get Product Name Attempt {p_name} of 2')
            for timer in range(30):
                print(f'Resuming in... {30 - timer}')
                time.sleep(1)
                Notes = 'ERR'
    try:
        ProductBrand = ProductName.split()[0]
    except:
        print('Failed to get Product Brand')

    try:
        Unitpp = extract_number_of_units(ProductName)
    except:
        print('Failed to get Unitpp')

    try:
        ol_element = driver.find_element(By.CSS_SELECTOR, "ol.ddsweb-breadcrumb__list")
        li_elements = ol_element.find_elements(By.TAG_NAME, "li")
        breadcrumb_texts = []
        for li in li_elements:
            text_element = li.find_element(By.CSS_SELECTOR, "span.ddsweb-link__text, span.ddsweb-text, a.ddsweb-link__anchor")
            text = text_element.text.strip()
            if text:
                breadcrumb_texts.append(text)
        breadcrumb_texts.pop(0)
        ProductCategory = breadcrumb_texts.pop(0)
        ProductSubCategory = breadcrumb_texts.pop(0)
    except:
        print('Failed to get Product Categories')

    try:
        img_element = driver.find_element(By.CSS_SELECTOR, "picture img.ddsweb-responsive-image__image")
        ProductImages = img_element.get_attribute('src')
    except:
        print('Failed to get Product Images')

    try:
        cont_result = extract_container_info(ProductName)
        Containersize_org = cont_result['container_size']
        Containersize_val = cont_result['container_value']
        Containersize_unit = cont_result['container_unit']
    except:
        print('Failed to get Container Size')

    try:
        focus_string = ProductName.split('-')[1].strip()
        match = re.search(r'(\d+x\d+(?:\.\d+)?(?:ml|l|g|kg|fl oz))', focus_string, re.IGNORECASE)
        if match:
            full_quantity = match.group(1)
            pack_size_match = re.search(r'(\d+)x', full_quantity)
            if pack_size_match:
                Unitpp = int(pack_size_match.group(1))
                Packsize_org = f"{full_quantity}"
    except:
        print("Failed to get Packsize")

    try:
        pattern = r'\b(?:(\d+(?:\.\d+)?)\s*(?:fl\s*oz|oz|ml|l(?:iter)?s?|gal(?:lon)?s?|pt|qt|cup|tbsp|tsp|cl|dl|kg|g|lb|pint|quart))?\s*' \
                  r'(bottles?|cans?|cartons?|boxe?s?|pouche?s?|sachets?|' \
                  r'flasks?|jugs?|pitchers?|tetra\s?paks?|kegs?|barrels?|casks?|' \
                  r'cups?|glass(?:es)?|mugs?|tumblers?|goblets?|steins?|' \
                  r'canisters?|thermos(?:es)?|vacuum\s?flasks?|' \
                  r'six-packs?|twelve-packs?|cases?|packs?|' \
                  r'tins?|containers?|tubs?|packets?|' \
                  r'single-serves?|multi-packs?|variety\s?packs?|' \
                  r'miniatures?|minis?|nips?|shooters?|' \
                  r'pints?|quarts?|gallons?|liters?|' \
                  r'growlers?|crowlers?|howlers?|' \
                  r'magnums?|jeroboams?|rehoboams?|methusela(?:hs?)?|' \
                  r'salmanazars?|balthazars?|nebuchadnezzars?|' \
                  r'melchiors?|solomons?|primats?|melchizedeks?|' \
                  r'splits?|half\s?bottles?|standard\s?bottles?|double\s?magnums?|' \
                  r'bags?-in-boxe?s?|beverage\s?dispensers?|soda\s?fountains?|' \
                  r'kegerators?|draft\s?systems?|taps?|spouts?|nozzles?|' \
                  r'straws?|lids?|caps?|corks?|stoppers?|seals?|' \
                  r'wine\s?boxe?s?|beer\s?boxe?s?|soda\s?boxe?s?|juice\s?boxe?s?|' \
                  r'aluminum\s?bottles?|plastic\s?bottles?|glass\s?bottles?|' \
                  r'slim\s?cans?|tall\s?cans?|stubby\s?bottles?|longneck\s?bottles?|' \
                  r'twist-off\s?caps?|pull-tabs?|pop-tops?|' \
                  r'screw\s?caps?|crown\s?caps?|cork\s?closures?|' \
                  r'sport\s?caps?|flip-tops?|push-pull\s?caps?|' \
                  r'droppers?|pumps?|sprays?|misters?|atomizers?|' \
                  r'wine\s?glass(?:es)?|champagne\s?flutes?|beer\s?glass(?:es)?|' \
                  r'shot\s?glass(?:es)?|highball\s?glass(?:es)?|lowball\s?glass(?:es)?|' \
                  r'collins\s?glass(?:es)?|martini\s?glass(?:es)?|margarita\s?glass(?:es)?|' \
                  r'hurricane\s?glass(?:es)?|pilsner\s?glass(?:es)?|weizen\s?glass(?:es)?|' \
                  r'snifters?|glencairns?|tulip\s?glass(?:es)?|' \
                  r'coupe\s?glass(?:es)?|nick\s?and\s?nora\s?glass(?:es)?|' \
                  r'rocks\s?glass(?:es)?|old\s?fashioned\s?glass(?:es)?|' \
                  r'coffee\s?mugs?|tea\s?cups?|espresso\s?cups?|' \
                  r'travel\s?mugs?|sippy\s?cups?|paper\s?cups?|' \
                  r'red\s?solo\s?cups?|disposable\s?cups?|' \
                  r'punch\s?bowls?|decanters?|carafes?|' \
                  r'amphoras?|oak\s?barrels?|stainless\s?steel\s?tanks?|' \
                  r'firkins?|pins?|tuns?|butts?|puncheons?|' \
                  r'hogsheads?|barriques?|goon\s?bags?|' \
                  r'beer\s?bottles?|wine\s?bottles?|liquor\s?bottles?|' \
                  r'soda\s?bottles?|water\s?bottles?|juice\s?bottles?|' \
                  r'energy\s?drink\s?cans?|seltzer\s?cans?|' \
                  r'cocktail\s?shakers?|mixing\s?glass(?:es)?|' \
                  r'water\s?coolers?|water\s?jugs?|dispensers?|' \
                  r'soda\s?stream\s?bottles?|kombucha\s?bottles?|' \
                  r'cold\s?brew\s?pitchers?|french\s?press(?:es)?|' \
                  r'espresso\s?pods?|coffee\s?pods?|k-cups?|' \
                  r'tea\s?bags?|loose\s?leaf\s?tins?|' \
                  r'smoothie\s?bottles?|protein\s?shakers?|' \
                  r'squeeze\s?bottles?|syrup\s?bottles?|' \
                  r'boba\s?cups?|slushie\s?cups?|frozen\s?drink\s?cups?|' \
                  r'wine\s?skins?|hip\s?flasks?|canteens?|' \
                  r'hydration\s?packs?|water\s?bladders?)\b'

        focus_string = ProductName.split('-')[1].strip()
        print(focus_string)
        match = re.search(pattern, focus_string, re.IGNORECASE)
        if match:
            Pack_type = match.group(2)
    except:
        print('Failed to find Pack Type')

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

        matches = re.findall(pattern, ProductName, re.IGNORECASE)
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
        matches = re.findall(pattern, ProductName, re.IGNORECASE)
        if matches:
            ProductFlavor = ", ".join(sorted(set(match.lower() for match in matches)))
    except:
        print('Failed to get Product Flavour')

    try:
        button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "accordion-header-nutritional-information"))
        )
        button.click()

        panel = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "accordion-panel-nutritional-information"))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", panel)

        html_content = panel.get_attribute('outerHTML')
        print(html_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='product__info-table')
        headers = [header.text for header in table.find_all('th', scope='col')]
        nutritional_info = {
            'headers': headers,
            'data': []
        }
        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all(['th', 'td'])
            row_data = [cell.text.strip() for cell in cells]
            nutritional_info['data'].append(row_data)
        print(nutritional_info)
        Nutr_label = format_nutrition(nutritional_info)

        headers = nutritional_info['headers']
        data = nutritional_info['data']

        num_dec_pattern = r'-?\d+(?:\.\d+)?'
        letters_pattern = r'[a-zA-Z]+'
        percents = r'\((\d+(?:\.\d+)?)%\)'

        if (len(headers) > 3):
            for d in data:
                if 'sugar' in d[0].lower():
                    try:
                        if ("(%*)" in headers[2]):
                            per = re.findall(percents, d[2])
                            TotalSugars_pct_pp = per[0]
                    except:
                        None

                if 'carbohydrate' in d[0].lower():
                    try:
                        if ("(%*)" in headers[2]):
                            per = re.findall(percents, d[2])
                            TotalCarb_pct_pp = per[0]
                    except:
                        None

        if (len(headers) > 2):
            Servsize_portion_org = headers[2]
            for d in data:
                if d[0] == 'Energy':
                    nums = re.findall(num_dec_pattern, d[1])
                    letters = re.findall(letters_pattern, d[1])
                    Cals_value_p100g = nums[0]
                    Cals_unit_p100g = letters[0]

                    nums = re.findall(num_dec_pattern, d[2])
                    letters = re.findall(letters_pattern, d[2])
                    Cals_value_pp = nums[0]
                    Cals_unit_pp = letters[0]
                    Cals_org_pp = d[2]

                if 'sugar' in d[0].lower():
                    try: TotalSugars_g_p100g = d[1]
                    except: None
                    try: TotalSugars_g_pp = d[2]
                    except: None
                    try:
                        if ("(%*)" in headers[2]):
                            per = re.findall(percents, d[2])
                            TotalSugars_pct_pp = per[0]
                    except:
                        None

                if 'carbohydrate' in d[0].lower():
                    try: TotalCarb_g_p100g = d[1]
                    except: None
                    try: TotalCarb_g_pp = d[2]
                    except: None
                    try:
                        if ("(%*)" in headers[2]):
                            per = re.findall(percents, d[2])
                            TotalCarb_pct_pp = per[0]
                    except:
                        None

        # only for 100ml servings
        elif (len(headers) > 1):
            Servsize_portion_org = headers[1]
            Servsize_portion_val = extract_serving_size(headers[1])['serving_size_value']
            Servsize_portion_unit = extract_serving_size(headers[1])['serving_size_unit']

            for d in data:
                if d[0] == 'Energy':
                    nums = re.findall(num_dec_pattern, d[1])
                    letters = re.findall(letters_pattern, d[1])
                    Cals_value_p100g = nums[0]
                    Cals_unit_p100g = letters[0]
                if 'sugar' in d[0].lower():
                    TotalSugars_g_p100g = d[1]
                if 'carbohydrate' in d[0].lower():
                    TotalCarb_g_p100g = d[1]


    except:
        print('Failed to get Ingredients and/or Nutrition Label')

    try:
        div_element = driver.find_element(By.CSS_SELECTOR, 'div.styled__Container-sc-110ics9-0.jBrOke').get_attribute('outerHTML')
        Ingredients = extract_info('Ingredients', div_element)
        Servings_cont = extract_info('Number of uses', div_element)
        Netcontent_org = extract_info('Net Contents', div_element)
        soup = BeautifulSoup(div_element, 'html.parser')
        description_divs = soup.find_all('div', class_='styled__Content-mfe-pdp__sc-1od89q4-2')
        description = ""
        for div in description_divs:
            if div.find_previous('h3'):
                break
            description += div.text.strip() + " "
        Description = description.strip()

    except:
        print('Failed to get Ingredients / Servings Per Cont / Net Contents')

    try:
        Packsize_org = extract_pack_size(Description)
    except:
        print('Failed to get Pack Size')

    try:
        Netcontent_val, Netcontent_unit = parse_net_content(Netcontent_org)
    except:
        print('Failed to parse net content')

    new_row = {
        'ID': ID,
        'Country': 'United Kingdom',
        'Store': 'Tienda',
        'Region': Region,
        'City': City,
        'ProductName': ProductName,
        'ProductVariety': ProductVariety,
        'ProductFlavor': ProductFlavor,
        'Unitpp': Unitpp,
        'ProductBrand': ProductBrand,
        'ProductAisle': aisle,
        'ProductCategory': ProductCategory,
        'ProductSubCategory': ProductSubCategory,
        'ProductImages': ProductImages,
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
        'AddedSugars_g_pp': AddedSugars_g_pp,
        'AddedSugars_pct_pp': AddedSugars_pct_pp,
        'Cals_value_p100g': Cals_value_p100g,
        'Cals_unit_p100g': Cals_unit_p100g,
        'TotalCarb_g_p100g': TotalCarb_g_p100g,
        'TotalCarb_pct_p100g': TotalCarb_pct_p100g,
        'TotalSugars_g_p100g': TotalSugars_g_p100g,
        'TotalSugars_pct_p100g': TotalSugars_pct_p100g,
        'AddedSugars_g_p100g': AddedSugars_g_p100g,
        'AddedSugars_pct_p100g': AddedSugars_pct_p100g,
        'Packsize_org': Packsize_org,
        'Pack_type': Pack_type,
        'Netcontent_val': Netcontent_val,
        'Netcontent_org': Netcontent_org,
        'Netcontent_unit': Netcontent_unit,
        'Price': Price,
        'Description': Description,
        'Nutr_label': Nutr_label,
        'Ingredients': Ingredients,
        'NutrInfo_org': NutrInfo_org,
        'Servsize_container_type_org': Servsize_container_type_org,
        'Servsize_container_type_val': Servsize_container_type_val,
        'Servsize_container_type_unit': Servsize_container_type_unit,
        'Servsize_portion_org': Servsize_portion_org,
        'Servsize_portion_val': Servsize_portion_val,
        'Servsize_portion_unit': Servsize_portion_unit,
        'Servings_cont': Servings_cont,
        'ProdType': 'N/A',
        'StorType': 'N/A',
        'ItemNum': 'N/A',
        'SKU': 'N/A',
        'UPC': 'N/A',
        'url': item_url,
        'DataCaptureTimeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        'Notes': Notes
    }
    return new_row
