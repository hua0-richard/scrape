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
GEN_TIMEOUT = 3
STORE_NAME = 'walmart_canada'
LOCATION = ''
MAX_RETRY = 10


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
    for _ in range(MAX_RETRY):
        try:
            None
        except Exception as e:
            print(f'Error Setting Location... Trying Again... Attempt {_}')

    for _ in range(MAX_RETRY):
        try:
            time.sleep(1)
            set_loc_btn = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.f6.pointer.b")))
            set_loc_btn.click()
            print('Set Location')
            break
        except:
            print(f'Trying Again... Attempt{_}')

    for _ in range(MAX_RETRY):
        try:
            time.sleep(1)
            icon = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'i.ld.ld-ChevronRight[aria-hidden="true"][style*="font-size: 1.5rem"]'))
            )
            icon.click()
            print('Set Location Button')
            break
        except:
            print(f'Trying Again... Attempt{_}')

    for _ in range(MAX_RETRY):
        try:
            time.sleep(1)
            input_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[data-automation-id="store-zip-code"][type="text"][maxlength="7"]'))
            )
            input_element.clear()
            input_element.send_keys('N2L0C9')
            break
        except:
            print('Postal Code Failed')
            print(f'Trying Again... Attempt{_}')

    for _ in range(MAX_RETRY):
        try:
            time.sleep(1)
            save_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="save-label"]'))
            )
            save_button.click()
            break
        except:
            print('Postal Code Failed')
            print(f'Trying Again... Attempt{_}')
    print('Set Location Complete')


def scrapeSite_target(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    # i in items
    # i[0] is url
    # i[1] is aisle
    items = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')

        if aisle == 'Drinks':
            driver.get('https://www.walmart.ca/en/browse/grocery/drinks/10019_6000194326336')
            time.sleep(GEN_TIMEOUT)
            target_divs = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'div.mb0.ph0-xl.pt0-xl.bb.b--near-white.w-25.pb3-m.ph1')))
            for div in target_divs:
                a_elements = div.find_elements(By.TAG_NAME, 'a')
                div_hrefs = [element.get_attribute('href') for element in a_elements]
                for dh in div_hrefs:
                    items.append(dh)
            max_pages = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR,                                                                                  'div.sans-serif.ph1.pv2.w4.h4.lh-copy.border-box.br-100.b--solid.mh2-m.db.tc.no-underline.gray.bg-white.b--white-90'))).text
            print(f"pages {max_pages}")
            for page in range(2, int(max_pages) + 1):
                time.sleep(EXPLICIT_WAIT_TIME)
                driver.get(f'https://www.walmart.ca/en/browse/grocery/drinks/10019_6000194326336?page={str(page)}')
                target_divs = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div.mb0.ph0-xl.pt0-xl.bb.b--near-white.w-25.pb3-m.ph1')))
                for div in target_divs:
                    a_elements = div.find_elements(By.TAG_NAME, 'a')
                    div_hrefs = [element.get_attribute('href') for element in a_elements]
                    for dh in div_hrefs:
                        items.append(dh)
                print(items)
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
    Notes = 'OK'

    for p_name in range(2):
        try:
            ProductName = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'h1#main-title[data-pcss-show="true"][itemprop="name"][elementtiming="ip-main-title"]'))
            ).text
            break
        except Exception as e:
            print(f'Failed to get Product Name Attempt {p_name} of 2')
            for timer in range(30):
                print(f'Resuming in... {30 - timer}')
                time.sleep(1)
            return None

    try:
        ProductBrand = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.bg-transparent.bn.lh-solid.pa0.sans-serif.tc.underline.inline-button.mid-gray.pointer.f6'))).text
    except:
        print('Failed to get Product Brand')

    try:
        ol_element = driver.find_element(By.CSS_SELECTOR, 'ol.w_3Z__')
        span_elements = ol_element.find_elements(By.CSS_SELECTOR, 'span[itemprop="name"]')
        breadcrumb_text = [span.text for span in span_elements]
        breadcrumb_text.pop(0)
        breadcrumb_text.pop(0)
        if len(breadcrumb_text) > 0:
            ProductCategory = breadcrumb_text.pop(0)
        if len(breadcrumb_text) > 0:
            ProductSubCategory = breadcrumb_text.pop(0)
    except:
        print('Failed to get Product Categories')

    try:
        img_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="vertical-carousel-container"] img')
        image_sources = [img.get_attribute('src') for img in img_elements]
        modified_sources = []
        for src in image_sources:
            # Replace Height=80 and Width=80 with Height=612 and Width=612
            modified_src = re.sub(r'odnHeight=80', 'odnHeight=612', src)
            modified_src = re.sub(r'odnWidth=80', 'odnWidth=612', modified_src)
            modified_sources.append(modified_src)

        for index in range(len(modified_sources)):
            response = requests.get(modified_sources[index])
            if response.status_code == 200:
                if not os.path.exists(f'output/images/{str(ind)}/{str(ID)}'):
                    os.makedirs(f'output/images/{str(ind)}/{str(ID)}', exist_ok=True)
                full_path = 'output/images/' + str(ind) + '/' + str(ID) + '/' + str(ID) + '-' + str(index) + '.png'
                with open(full_path, 'wb') as file:
                    file.write(response.content)

        ProductImages = ','.join(modified_sources)

    except:
        print('Failed to get Product Images')

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
                Unitpp = int(pack_size_match.group(1))
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
            match = re.match(r'([\d.]+x[\d.]+)([a-zA-Z]+)', Packsize_org)
            if match:
                numeric_part, unit = match.groups()
                num1, num2 = map(float, numeric_part.split('x'))
                result = num1 * num2
            Netcontent_org = f"{result:.10g}{unit}"
            Netcontent_val = result
            Netcontent_unit = unit
        elif (not Containersize_org == None):
            Netcontent_org = Containersize_org
            pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)'
            match = re.match(pattern, Containersize_org)
            if match:
                Netcontent_val = float(match.group(1))
                Netcontent_unit = match.group(2)
    except:
        print('Failed to get Net Content')

    try:
        full_path = 'output/images/' + str(ind) + '/' + str(ID) + '/'
        entries = os.listdir(full_path)
        print(entries)
        for f in entries:
            print(f)
            image_path = full_path + f
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            text = remove_empty_lines(text)
            split_text = text.split('\n')
            # check for Label
            for s in split_text:
                tmp_s = s.lower()
                keyword = 'Nutrition Facts'
                keyword = keyword.lower()
                if keyword in tmp_s:
                    Nutr_label = "Present"
                    break
            # check for Ingredients
            for s in split_text:
                tmp_s = s.lower()
                keyword = 'Ingredients'
                keyword = keyword.lower()
                if keyword in tmp_s:
                    Ingredients = f
                    break
    except:
        print('Failed to get Ingredients and/or Nutrition Label')

    new_row = {
        'ID': ID,
        'Country': 'Canada',
        'Store': 'Walmart',
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
    return (new_row)
