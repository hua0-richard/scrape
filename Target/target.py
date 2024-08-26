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
from PIL import Image
import pytesseract

# Special Package to scrap and aids in avoiding more stringent sites
import undetected_chromedriver as uc

import time
import datetime
import pytz

import random

import re

FAVNUM = 22222
GEN_TIMEOUT = 6
STORE_NAME = 'target'
LOCATION = ''
MAX_RETRY = 10


def format_nutrition_label(nutrition_data):
    # Find all unique columns
    columns = set()
    for values in nutrition_data.values():
        columns.update(values.keys())
    columns = sorted(list(columns))

    # Create the header
    label = "Nutrition Information\n"
    label += "=" * (25 + 25 * len(columns)) + "\n"
    header = "Nutrient".ljust(25)
    for col in columns:
        header += col.ljust(25)
    label += header + "\n"
    label += "-" * (25 + 25 * len(columns)) + "\n"

    # Add each nutrient row
    for nutrient, values in nutrition_data.items():
        row = nutrient.ljust(25)
        if nutrient.startswith('–'):
            row = "  " + nutrient.ljust(23)
        for col in columns:
            row += values.get(col, "N/A").ljust(25)
        label += row + "\n"

    return label


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


def setup_target(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_target(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)


def setLocation_target(driver, address, EXPLICIT_WAIT_TIME):
    global LOCATION
    LOCATION = address
    time.sleep(GEN_TIMEOUT)
    try:
        signin_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.sc-58ad44c0-3.kwbrXj.h-margin-r-x3"))
        )
        signin_button.click()
        signin_button_v2 = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.sc-859e7637-0.hHZPQy"))
        )
        signin_button_v2.click()
        input_username = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "username"))
        )
        input_username.send_keys('u2894478@gmail.com')
        password_input = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "password"))
        )
        password_input.send_keys('notme123!')
        submit_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        submit_button.click()
        try:
            print('Skip Link')
            skip_link = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.sc-9306beff-0.sc-e6042511-0.dfqbQr.ibmrHV")))
            skip_link.click()
        except:
            print('None')
    except:
        print('Failed to sign in')

    try:
        zip_code_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-test="@web/ZipCodeButton/ZipCodeNumber"]'))
        )
        zip_code_element.click()
        print('Zip Code Button')
    except:
        print('Failed to get Zip Code Button')

    try:
        zip_code_input = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "zip-code"))
        )
        zip_code_input.send_keys(Keys.BACKSPACE * 10)
        time.sleep(GEN_TIMEOUT)
        zip_code_input.send_keys('19131')
        time.sleep(GEN_TIMEOUT)
    except:
        print('Failed to input Zip Code')

    try:
        update_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-test='@web/LocationFlyout/UpdateLocationButton']"))
        )
        update_button.click()
    except:
        print('Failed to Update Zip Code')

    print('Set Location Complete')


def scrapeSite_target(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    # i in items
    # i[0] is url
    # i[1] is aisle
    items = []
    subaisles = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')

        try:
            time.sleep(GEN_TIMEOUT)
            categories_link = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[data-test='@web/Header/MainMenuLink'][aria-label='Categories']"))
            )
            categories_link.click()
        except:
            print('Failed to get Categories')

        try:
            time.sleep(GEN_TIMEOUT)
            grocery_span = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//span[contains(@class, 'styles_wrapper__YYaWP') and text()='Grocery']"))
            )
            grocery_span.click()
        except:
            print('Failed to get Grocery')

        try:
            time.sleep(GEN_TIMEOUT)
            aisle_span = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//span[contains(@class, 'styles_wrapper__YYaWP') and text()='{aisle}']"))
            )
            aisle_span.click()
        except:
            print('Failed to get Aisle')

        try:
            time.sleep(GEN_TIMEOUT)
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-test='@web/component-header/CategoryLink']"))
            )
            category_links = driver.find_elements(By.CSS_SELECTOR, "a[data-test='@web/component-header/CategoryLink']")
            print(len(category_links))
            for link in category_links:
                href = link.get_attribute("href")
                if (href != 'https://www.target.com/c/coffee-beverages-grocery/-/N-4yi5p'):
                    subaisles.append(href)
        except:
            print('Failed to get Aisle SubCategories')

        try:
            subaisles.pop(0)
            for s in subaisles:
                items = list(dict.fromkeys(items))
                print(f'Items so far... {len(items)}')
                driver.get(s)
                print('start')
                while True:

                    # REMOVE LATER
                    if (len(items) > 100):
                        break
                    # REMOVE LATER

                    time.sleep(GEN_TIMEOUT * 4)
                    # Wait for the product cards to be present
                    products = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                        EC.presence_of_all_elements_located(
                            (By.CLASS_NAME, "rLjwS"))
                    )
                    # Extract Links from Products
                    for p in products:
                        prod_html = p.get_attribute("outerHTML")
                        soup = BeautifulSoup(prod_html, 'html.parser')
                        a_tag = soup.find('a')
                        if a_tag:
                            href = a_tag['href']
                            print(f"The href attribute is: https://www.target.com{href}")
                            items.append(f"https://www.target.com{href}")
                        else:
                            print("The specific <a> tag was not found.")
                    try:
                        outer_container = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test="pagination"]')))
                        next_button = outer_container.find_element(By.CSS_SELECTOR, 'button[data-test="next"]')
                        is_disabled = next_button.get_attribute("disabled") is not None
                        if is_disabled:
                            print('No Next')
                            break
                        next_button.click()
                        print('Next Button Found')
                    except Exception as e:
                        print('Next Button Not Found')
                        print(e)
                        break

        except Exception as e:
            print('Failed to get Subaisles')
            print(e)

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

    for p_name in range(2):
        try:
            ProductName = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located((By.ID, "pdp-product-title-id"))
            ).text
            break
        except Exception as e:
            print(f'Failed to get Product Name Attempt {p_name} of 2')
            for timer in range(30):
                print(f'Resuming in... {30 - timer}')
                time.sleep(1)
            return None

    try:
        ProductBrand = ProductName.split()[0]
    except:
        print('Failed to get Product Brand')

    try:
        breadcrumbs_container = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-module-type='ProductDetailBreadcrumbs']"))
        )
        breadcrumb_links = breadcrumbs_container.find_elements(By.CSS_SELECTOR,
                                                               "a[data-test='@web/Breadcrumbs/BreadcrumbLink']")
        breadcrumb_texts = [link.text for link in breadcrumb_links]
        breadcrumb_texts.pop(0)
        breadcrumb_texts.pop(0)
        if len(breadcrumb_texts) > 0:
            ProductCategory = breadcrumb_texts.pop(0)
        if len(breadcrumb_texts) > 0:
            ProductSubCategory = breadcrumb_texts.pop(0)
    except:
        print('Failed to get Product Categories')

    try:
        gallery_section = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "PdpImageGallerySection"))
        )
        img_elements = gallery_section.find_elements(By.TAG_NAME, "img")
        image_urls = [img.get_attribute("src") for img in img_elements]
        if len(image_urls) > 0:
            response = requests.get(image_urls[0])
            if response.status_code == 200:
                if not os.path.exists(f'output/images/{str(ind)}/'):
                    os.makedirs(f'output/images/{str(ind)}/', exist_ok=True)
                full_path = 'output/images/' + str(ind) + '/' + str(ID) + '-' + str(index) + '.png'
                with open(full_path, 'wb') as file:
                    file.write(response.content)
            None
    except:
        print('Failed to get Product Images')

    try:
        size_pattern = r'(\d+(?:\.\d+)?)\s*(fl\s*oz|oz|ml|l|pk|pack)\b'
        focus_string = ProductName.split('-')[1].strip()
        match = re.search(size_pattern, focus_string, re.IGNORECASE)
        if match:
            volume = match.group(1)
            unit = match.group(2).lower()
            Containersize_org = f"{volume}{unit}"
            Containersize_val = volume
            Containersize_unit = unit
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
        elements = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.h-margin-t-tight")))
        nutrition_dict = {}
        for element in elements:
            spans = element.find_elements(By.TAG_NAME, "span")
            if len(spans) >= 2:
                nutrient_name = spans[0].find_element(By.TAG_NAME, "b").text.strip()
                nutrient = spans[0].text.strip().replace(nutrient_name, '')
                value = spans[1].text.strip()

                nutrition_dict[nutrient_name] = {
                    'amount': nutrient,
                    'daily_value': value
                }
        print(nutrition_dict)

        for key, value in nutrition_dict.items():
            if key == 'Total Carbohydrate':
                TotalCarb_g_pp = value['amount']
                TotalCarb_pct_pp = value['daily_value']
            elif key == 'Sugars':
                TotalSugars_g_pp = value['amount']
                TotalSugars_pct_pp = value['daily_value']
            elif key == 'Added Sugars':
                TotalCarb_g_pp = value['amount']
                TotalCarb_pct_pp = value['daily_value']

        Nutr_label = format_nutrition_label(nutrition_dict)


    except:
        print('Failed to get Ingredients and/or Nutrition Label')

    try:
        containers_html = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sc-cf555beb-2.sFaVI')))
        ptags = containers_html.find_elements(By.TAG_NAME, "p")
        for p in ptags:
            btag = p.find_element(By.TAG_NAME, "b")
            ptag_text = p.text.replace(btag.text, '')
            print(btag.text.strip())
            print(ptag_text.strip())
    except:
        print('Failed to get Servings')

    try:
        containers_html = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.h-padding-l-default')))
        spans = containers_html.find_elements(By.TAG_NAME, "span")
        Cals_org_pp = f'{spans[0].text.strip()} {spans[1].text.strip()}'
        Cals_unit_pp = 'Calories'
        Cals_value_pp = spans[1].text.strip()
        for s in spans:
            print(s.text)

    except:
        print('Calories Error')

    try:
        h4_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located(
            (By.XPATH, "//h4[contains(@class, 'sc-fe064f5c-0') and text()='Ingredients:']")))
        parent_div = h4_element.find_element(By.XPATH, "..")
        Ingredients = parent_div.find_element(By.TAG_NAME, "div").text.strip()
    except:
        print('Ingredients Error')

    try:
        time.sleep(GEN_TIMEOUT)
        for _ in range(5):
            try:
                details_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable(
                    (By.XPATH, "//h3[contains(@class, 'sc-fe064f5c-0') and contains(@class, 'cJJgsH') and contains(@class, 'h-margin-b-none') and text()='Details']")
                ))
                driver.execute_script("arguments[0].scrollIntoView(true);", details_element)
                driver.execute_script("window.scrollBy(0, arguments[0]);", -200)
                time.sleep(1)
                details_element.click()
                break
            except Exception as e:
                print(f'Trying Again Description... Attempt {_}')
                print(e)
                time.sleep(1)
        time.sleep(GEN_TIMEOUT)
        description_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "div.h-margin-t-x2[data-test='item-details-description']"
        )))
        Description = description_element.text
        print(Description)
    except Exception as e:
        Notes = 'ERR'
        print('Description Error')

    try:
        for _ in range(5):
            try:
                button_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@class, 'styles_button__D8Xvn') and .//h3[contains(text(), 'Specifications')]]"
                )))
                driver.execute_script("arguments[0].scrollIntoView(true);", button_element)
                driver.execute_script("window.scrollBy(0, arguments[0]);", -200)
                time.sleep(1)
                button_element.click()
                break
            except Exception as e:
                print(f'Trying Again Description... Attempt {_}')
                time.sleep(1)
                print(e)
        time.sleep(GEN_TIMEOUT)
        container = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='item-details-specifications']"))
        )
        divs = container.find_elements(By.TAG_NAME, "div")
        # More Specifications
        net_weight_div = None
        pack_quant_div = None
        upc_div = None
        for div in divs:
            bold_element = div.find_elements(By.TAG_NAME, "b")
            for i in bold_element:
                if "Net weight:" in i.text:
                    net_weight_div = div
                elif bold_element and "Package Quantity:" in i.text:
                    pack_quant_div = div
                elif bold_element and "UPC" in i.text:
                    upc_div = div
        Netcontent_org = net_weight_div.text.strip()
        Netcontent_unit = net_weight_div.text.strip()
        Netcontent_val = net_weight_div.text.strip()

        Unitpp = pack_quant_div.text.strip()
        UPC = upc_div.text.strip()
    except:
        Notes = 'ERR'
        print('More Details Error')

    new_row = {
        'ID': ID,
        'Country': 'United States',
        'Store': 'Target',
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
        'UPC': UPC,
        'url': item_url,
        'DataCaptureTimeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        'Notes': Notes
    }
    return (new_row)
