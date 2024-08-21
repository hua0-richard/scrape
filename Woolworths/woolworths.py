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
import undetected_chromedriver as uc

import time
import datetime
import pytz

import random

import re

FAVNUM = 22222
GEN_TIMEOUT = 5 * 3
STORE_NAME = 'woolworths'
LOCATION = ''

city_state_map = {
    'Sydney': 'NSW',
    'Melbourne': 'VIC',
    'Brisbane': 'QLD',
    'Perth': 'WA',
    'Adelaide': 'SA',
    'Gold Coast': 'QLD',
    'Newcastle': 'NSW',
    'Canberra': 'ACT',
    'Wollongong': 'NSW',
    'Geelong': 'VIC',
    'Hobart': 'TAS',
    'Townsville': 'QLD',
    'Cairns': 'QLD',
    'Darwin': 'NT',
}

def parse_city_region(address):
    # Regular expression pattern to match state and postcode
    pattern = r'([A-Z]{2,3})\s+(\d{4})'

    # Remove 'Australia' from the end if present
    address = address.replace(', Australia', '').strip()

    match = re.search(pattern, address)
    if match:
        state, postcode = match.groups()
        region = f"{state} {postcode}"

        # Search for known cities in the address
        city = "Unknown"
        for known_city, known_state in city_state_map.items():
            if known_city in address and known_state == state:
                city = known_city
                break

        # If no known city found, try to extract the last location name before the state
        if city == "Unknown":
            city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+' + state, address)
            if city_match:
                city = city_match.group(1)

        return city, region
    else:
        return "Unable to parse", "Unable to parse"

def format_nutrition_label(nutrition_data):
    # Find all unique columns
    columns = set()
    for values in nutrition_data.values():
        columns.update(values.keys())
    columns = sorted(list(columns))

    # Create the header
    label = "Nutrition Information\n"
    label += "=" * (15 + 15 * len(columns)) + "\n"
    header = "Nutrient".ljust(15)
    for col in columns:
        header += col.ljust(15)
    label += header + "\n"
    label += "-" * (15 + 15 * len(columns)) + "\n"

    # Add each nutrient row
    for nutrient, values in nutrition_data.items():
        row = nutrient.ljust(15)
        if nutrient.startswith('–'):
            row = "  " + nutrient.ljust(13)
        for col in columns:
            row += values.get(col, "N/A").ljust(15)
        label += row + "\n"

    return label

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

def setup_woolworths(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_woolworths(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)

def setLocation_woolworths(driver, address, EXPLICIT_WAIT_TIME):
    global LOCATION
    LOCATION = address
    for _ in range(5):
        try:
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.wx-header__drawer-button.signIn"))).click()
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input#signInForm-email"))).send_keys(
                "u2894478@gmail.com")
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input#signInForm-password"))).send_keys("notme123!")
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "span.login-button-label"))).click()
            input("Follow Instructions On-Screen for 2FA")
            try:
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@class, 'edit-button') and contains(text(), 'Edit')]"))
                ).click()
            except:
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "span#wx-label-fulfilment-action"))).click()

            pattern = r'\b(\d{4})(?:\s*,?\s*Australia)?$'
            match = re.search(pattern, address)
            postcode = None
            if match:
                postcode = match.group(1)
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input#pickupAddressSelector"))).send_keys(
                    postcode)
                time.sleep(GEN_TIMEOUT)
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "shared-button.fulfilment-button"))).click()
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".time-slot-line1.mobile"))).click()
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH,
                                                                                            "//shared-button[@buttonclass='shopper-action']//button[contains(text(), 'Reserve time')]"))).click()
                break
        except:
            print(f'Error Setting Location... Trying Again... Attempt {_}')
    print('Set Location Complete')


def scrapeSite_woolworths(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    # i in items
    # i[0] is url
    # i[1] is aisle
    items = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.values.tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')
        time.sleep(GEN_TIMEOUT)
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.hamburger[fetchpriority='high']"))
        ).click()
        aisle_text = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//div[contains(@class, 'description') and contains(text(), '{aisle}')]"))
        )
        aisle_link = aisle_text.find_element(By.XPATH, "..")
        driver.get(aisle_link.get_attribute('href'))

        time.sleep(GEN_TIMEOUT)
        elements = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "wow-category-chip a")))
        sub_aisle_links = [element.get_attribute("href") for element in elements[2:]]
        print(sub_aisle_links)

        sub_sub_aisle_links = []
        for s in sub_aisle_links:
            driver.get(s)
            time.sleep(GEN_TIMEOUT)
            sub_sub_aisle_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "wow-category-chip a")))
            tmp = [element.get_attribute("href") for element in sub_sub_aisle_element[2:]]
            for t in tmp:
                sub_sub_aisle_links.append(t)

        for s in sub_sub_aisle_links:
            print(f"items so far... {len(items)}")
            driver.get(s)
            bread_crumb = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".breadcrumbs-link")))
            breadcrumb_texts = ", ".join([element.text.strip() for element in bread_crumb[2:]])
            while True:
                time.sleep(GEN_TIMEOUT)
                WebDriverWait(driver, EXPLICIT_WAIT_TIME * 3).until(EC.presence_of_element_located((By.CLASS_NAME, "product-grid-v2")))
                # Use JavaScript to extract product information
                script = """
                    const products = [];
                    const tiles = document.querySelectorAll('wc-product-tile');
                    tiles.forEach(tile => {
                        const shadowRoot = tile.shadowRoot;
                        if (shadowRoot) {
                            const link = shadowRoot.querySelector('a');
                            if (link) {
                                products.push({
                                    url: link.href,
                                });
                            }
                        }
                    });
                    return products;
                """
                # This returns an array
                product_info = driver.execute_script(script)
                for product in product_info:
                    for i in items:
                        if product['url'] == i[0]:
                            break
                    else:
                        items.append([product['url'], breadcrumb_texts])
                # Next Page
                try:
                    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[@class='next-marker' and text()='Next']"))
                    ).click()
                    print('Found Next Button')
                except:
                    print('No Next Button')
                    print(items)
                    break

        aisle_item_list = [tuple(s) for s in items]
        items = pd.DataFrame(aisle_item_list)
        items.columns = [None, None]

        pd.DataFrame(items).to_csv(f'output/tmp/index_{str(ind)}_{aisle}_item_urls.csv', index=False, header=None,
                                   encoding='utf-8-sig')
        print(f'items so far... {len(items)}')


    df_data = pd.DataFrame()
    site_items_df = pd.DataFrame()

    # Cache Strategy
    try:
        seen_items = cache_strategy()
        new_rows = []
        for cache_index in range(len(items)):
            item_url = items[cache_index]
            matching_rows = seen_items[seen_items['url'] == item_url]
            if len(matching_rows) > 0:
                row = matching_rows.iloc[0].copy()
                row['idx'] = f'{ind}-{cache_index}-{aisle.upper()[:3]}'
                index_for_here = f'{ind}-{cache_index}-{aisle.upper()[:3]}'
                print(f'Found Cached Entry {cache_index}')
                new_rows.append(row)
                try:
                    full_path = 'output/images/' + str(ind) + '/' + str(index_for_here) + '-' + str(0) + '.png'
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
            site_items_df = site_items_df.sort_values(by='idx', key=lambda x: x.map(custom_sort_key))
            site_items_df = site_items_df.reset_index(drop=True)

    except Exception as e:
        print(e)
        print('Cache Failed')

    try:
        df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_{STORE_NAME}_data.csv")
        site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
    except:
        print('No Prior Data Found... ')

    # scrape items and check for already scraped
    for item_index in range(len(items)):
        item_url = items[item_index][0]
        if not df_data.empty and items[item_index] in df_data['url'].values:
            print(f'{ind}-{item_index} Item Already Exists!')
            continue

        for v in range(5):
            try:
                time.sleep(GEN_TIMEOUT)
                driver.get(item_url)
                new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index, items[item_index][1])
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


def scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, index, sub_aisles_string):
    ID = f'{ind}-{index}-{aisle.upper()[:3]}'
    Region = None
    City = None
    ProductName = None
    ProductBrand = None
    ProductCategory = None
    ProductSubCategory = None
    ProductImages = None
    Description = None
    size = None
    price = None
    multi_price = None
    old_price = None
    pricePerUnit = None
    itemNum = None
    serving = None
    img_urls = []
    Nutr_label = None
    item_warning = None
    Ingredients = None
    pack = None

    Servsize_portion_org = None

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
    Cals_value_p100g = None
    Cals_unit_p100g = None
    TotalCarb_g_p100g = None
    TotalCarb_pct_p100g = 'N/A'
    TotalSugars_g_p100g = None
    TotalSugars_pct_p100g = 'N/A'
    AddedSugars_g_p100g = 'N/A'
    AddedSugars_pct_p100g = 'N/A'

    try:
        global LOCATION
        City, Region = parse_city_region(LOCATION)
    except:
        print('Failed to set Location Data')


    try:
        servings_data = None
        servings_size_data = None

        script = """
        function getElementFromShadowRoot(selector) {
            let element = document.querySelector(selector);
            while (element && element.shadowRoot) {
                element = element.shadowRoot.querySelector(selector);
            }
            return element;
        }
        const element = getElementFromShadowRoot('ar-product-details-nutrition-table.ar-product-details-nutrition-table');
        return element ? element.outerHTML : null;
        """
        try:
            nutrition_table_html = driver.execute_script(script)
            soup = BeautifulSoup(nutrition_table_html, 'html.parser')
            try:
                serving_size_div = soup.find('div', attrs={'*ngif': 'productServingSize'})
                print(serving_size_div.text)
                Servsize_portion_org = serving_size_div.text

            except:
                print('Failed to get Serving Size')

            try:
                pattern = r'([\d.]+)([a-zA-Z]+)'
                nutrition_info = {}
                nutrition_rows = soup.find_all('ul', class_='nutrition-row')
                for row in nutrition_rows:
                    columns = row.find_all('li', class_='nutrition-column')
                    if len(columns) == 3:
                        nutrient = columns[0].text.strip()
                        per_serving = columns[1].text.strip()
                        per_100 = columns[2].text.strip()
                        nutrition_info[nutrient] = {
                            'Per Serving': per_serving,
                            'Per 100g / 100mL': per_100
                        }
                print('Obtained Nutrition Info.')
                print(nutrition_info)
                Nutr_label = format_nutrition_label(nutrition_info)

                try:
                    Cals_org_pp = nutrition_info['Energy']['Per Serving']
                    match = re.match(pattern, Cals_org_pp)
                    if match:
                        Cals_value_pp = match.group(1)
                        Cals_unit_pp = match.group(2)
                except:
                    print('Failed to get Calories')

                try:
                    _cals_org_p100g = nutrition_info['Energy']['Per 100g / 100mL']
                    match = re.match(pattern, _cals_org_p100g)
                    if match:
                        Cals_value_p100g = match.group(1)
                        Cals_unit_p100g = match.group(2)
                except:
                    print('Failed to get Calories')

                try:
                    TotalCarb_g_pp = nutrition_info['Carbohydrate']['Per Serving']
                    TotalCarb_g_p100g = nutrition_info['Carbohydrate']['Per 100g / 100mL']
                except:
                    print('Failed to get Total Carb')

                try:
                    TotalSugars_g_pp = nutrition_info['– Sugars']['Per Serving']
                    TotalSugars_g_p100g = nutrition_info['– Sugars']['Per 100g / 100mL']
                except:
                    print('Failed to get Total Sugars')

            except:
                print('Failed to get Nutrition Label')

        except Exception as e:
            print(f"Error finding Nutrition Label")
            return None
    except:
        print('Failed to Get Nutrition Label')

    try:
        split_cat = sub_aisles_string.split(',')
        split_cat.reverse()
        ProductCategory = split_cat.pop()
        if (len(split_cat) > 0):
            ProductSubCategory = split_cat.pop()
    except:
        print('Failed to get Sub Aisles')

    try:
        ProductName = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.shelfProductTile-title"))).text
    except:
        print('Failed to get Name')

    try:
        None
    except:
        print('Failed to get Brand')

    try:
        script = """
        function getElementFromShadowRoot(selector) {
            let element = document.querySelector(selector);
            while (element && element.shadowRoot) {
                element = element.shadowRoot.querySelector(selector);
            }
            return element;
        }
        const element = getElementFromShadowRoot('section.ingredients');
        return element ? element.outerHTML : null;
        """
        ingredients_html = driver.execute_script(script)
        soup = BeautifulSoup(ingredients_html, 'html.parser')
        Ingredients = soup.find('div', class_='view-more-content').text
    except:
        print('Failed to get Ingredients')

    try:
        DescriptionContainer = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.bottom-container.margin-ar-fix")))
        description_html = DescriptionContainer.get_attribute('outerHTML')
        soup = BeautifulSoup(description_html, 'html.parser')
        description_text = soup.find('div', class_ ='view-more-content').text
        if (description_text == ''):
            Description = 'None'
        else:
            Description = description_text
    except:
        print('Failed to get Description')

    try:
        if (not ProductName == None):
            ProductBrand = ProductName.split(' ')[0]
        else:
            print('Failed to get Brand')
    except:
        print('Failed to get Brand')

    try:
        images_arr = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.thumbnail-image")))

        images_arr_src = [image.get_attribute('src') for image in images_arr]
        ProductImages = ','.join(images_arr_src)

        for index in range(len(images_arr_src)):
            response = requests.get(images_arr_src[index])
            if response.status_code == 200:
                if not os.path.exists(f'output/images/{str(ind)}/{str(ID)}'):
                    os.makedirs(f'output/images/{str(ind)}/{str(ID)}', exist_ok=True)
                full_path = 'output/images/' + str(ind) + '/' + str(ID) + '/' + str(ID) + '-' + str(index) + '.png'
                with open(full_path, 'wb') as file:
                    file.write(response.content)

    except Exception as e:
        print('Failed to get Product Images')
        print(e)

    try:
        pattern = r'(\d+(?:\.\d+)?)\s*(L|ML|l|ml)'
        match = re.search(pattern, ProductName, re.IGNORECASE)
        if match:
            volume = match.group(1)
            unit = match.group(2).upper()
            Containersize_org = f"{volume}{unit}"
            Containersize_val = volume
            Containersize_unit = unit
    except:
        print('Failed to get Container Size')

    try:
        match = re.search(r'(\d+x\d+(?:\.\d+)?(?:ml|l|g|kg))', ProductName, re.IGNORECASE)
        if match:
            full_quantity = match.group(1)
            pack_size_match = re.search(r'(\d+)x', full_quantity)
            if pack_size_match:
                # pack_size = int(pack_size_match.group(1))
                Packsize_org = f"{full_quantity}"
    except:
        print("Failed to get Packsize")

    try:
        pattern = r'\b(bottles?|cans?|cartons?|boxe?s?|pouche?s?|sachets?|' \
                  r'flasks?|jugs?|pitchers?|tetra\s?paks?|kegs?|barrels?|casks?|' \
                  r'cups?|glass(?:es)?|mugs?|tumblers?|goblets?|steins?|' \
                  r'canisters?|thermos(?:es)?|vacuum\s?flasks?|' \
                  r'six-packs?|twelve-packs?|cases?|packs?|' \
                  r'tins?|containers?|tubs?|packets?|' \
                  r'single-serves?|multi-packs?|variety\s?packs?|' \
                  r'miniatures?|minis?|nips?|shooters?|' \
                  r'pints?|quarts?|gallons?|liters?|ml|fl\s?oz|' \
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

        match = re.search(pattern, ProductName, re.IGNORECASE)
        if match:
            Pack_type = match.group(1).lower()
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
        if (not Packsize_org == None):
            None
        if (not Containersize_val == None):
            None
    except:
        print('Failed to get Net Content')


    new_row = {
                'ID': ID,
                'Country' : 'Australia',
                'Store' : 'Woolworths',
                'Region' : Region,
                'City' : City,
                'ProductName': ProductName,
                'ProductVariety' : ProductVariety,
                'ProductFlavor' : ProductFlavor,
                'ProductBrand': ProductBrand,
                'ProductAisle': aisle,
                'ProductCategory': ProductCategory,
                'ProductSubCategory': ProductSubCategory,
                'ProductImages': ProductImages,
                'Containersize_org': Containersize_org,
                'Containersize_val': Containersize_val,
                'Containersize_unit': Containersize_unit,
                'Cals_org_pp' : Cals_org_pp,
                'Cals_value_pp' : Cals_value_pp,
                'Cals_unit_pp' : Cals_unit_pp,
                'TotalCarb_g_pp' : TotalCarb_g_pp,
                'TotalCarb_pct_pp' : TotalCarb_pct_pp,
                'TotalSugars_g_pp' : TotalSugars_g_pp,
                'TotalSugars_pct_pp' : TotalSugars_pct_pp,
                'AddedSugars_g_pp' : AddedSugars_g_pp,
                'AddedSugars_pct_pp' : AddedSugars_pct_pp,
                'Cals_value_p100g' : Cals_value_p100g,
                'Cals_unit_p100g' : Cals_unit_p100g,
                'TotalCarb_g_p100g' : TotalCarb_g_p100g,
                'TotalCarb_pct_p100g' : TotalCarb_pct_p100g,
                'TotalSugars_g_p100g' : TotalSugars_g_p100g,
                'TotalSugars_pct_p100g' : TotalSugars_pct_p100g,
                'AddedSugars_g_p100g' : AddedSugars_g_p100g,
                'AddedSugars_pct_p100g' : AddedSugars_pct_p100g,
                'Packsize_org' : Packsize_org,
                'Pack_type' : Pack_type,
                'price': price,
                'itemNum': itemNum,
                'Description': Description,
                'Nutr_label': Nutr_label,
                'Ingredients': Ingredients,
                'url': item_url,
                'item_warning': item_warning,
                'timeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
               }
    return (new_row)
