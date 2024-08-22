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
GEN_TIMEOUT = 3
STORE_NAME = 'woolworths'
LOCATION = ''
MAX_RETRY = 10


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


def setup_walmart(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_walmart(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)


def setLocation_walmart(driver, address, EXPLICIT_WAIT_TIME):
    global LOCATION
    LOCATION = address
    for _ in range(MAX_RETRY):
        try:
            time.sleep(1)
            signin_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.mw3.mw4-hdkp.truncate.lh-title.f7")))
            signin_button.click()
            print('Button')
            button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Sign in or create account']")))
            button.click()
            print('Sign In')

            try:
                email_input = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@type="email" and @id="react-aria-1"]')))
                email_input.send_keys('u2894478@gmail.com')
                print('Email')
            except Exception as e:
                print('Email Error')
                print(e)

            try:
                WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.w_hhLG.w_8nsR.w_lgOn.w_jDfj.mv3"))).click()
                password_input = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@type="password" and @id="react-aria-1"]')))
                password_input.send_keys('Notme123!')
                print('Password')
            except Exception as e:
                print('Password Error')
                print(e)

            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.w_hhLG.w_8nsR.w_jDfj.w-100"))).click()

            try:
                no_number = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[link-identifier="notNow"][aria-label="Not now"]'))
                )
                no_number.click()
            except Exception as e:
                print('Number Message Not Present')
            break
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


def scrapeSite_walmart(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
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

    except:
        print('Failed to get Product Images')

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
