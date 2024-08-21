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
    for _ in range(5):
        try:
            None
            break
        except:
            print(f'Error Setting Location... Trying Again... Attempt {_}')
    print('Set Location Complete')
    time.sleep(FAVNUM)

def scrapeSite_walmart(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
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
                WebDriverWait(driver, EXPLICIT_WAIT_TIME * 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-grid-v2")))
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
            item_url = items[cache_index][0]
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
                new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index,
                                      items[item_index][1])
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
    Cals_value_p100g = None
    Cals_unit_p100g = None
    TotalCarb_g_p100g = None
    TotalCarb_pct_p100g = 'N/A'
    TotalSugars_g_p100g = None
    TotalSugars_pct_p100g = 'N/A'
    AddedSugars_g_p100g = 'N/A'
    AddedSugars_pct_p100g = 'N/A'
    Notes = 'OK'


    new_row = {
        'ID': ID,
        'Country': 'Australia',
        'Store': 'Woolworths',
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
