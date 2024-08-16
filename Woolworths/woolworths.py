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


def setup_woolworths(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_woolworths(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)


def setLocation_woolworths(driver, address, EXPLICIT_WAIT_TIME):
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
    subaisles = []
    items = []

    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.hamburger[fetchpriority='high']"))
        ).click()
        aisle_text = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//div[contains(@class, 'description') and contains(text(), '{aisle}')]"))
        )
        aisle_link = aisle_text.find_element(By.XPATH, "..")
        driver.get(aisle_link.get_attribute('href'))

        # Wait for the elements to be present
        elements = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "wow-category-chip a")))
        sub_aisle_links = [element.get_attribute("href") for element in elements[1:]]
        print(sub_aisle_links)
        sub_sub_aisle_links = []
        for s in sub_aisle_links:
            driver.get(s)
            sub_sub_aisle_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "wow-category-chip a")))
            tmp = [element.get_attribute("href") for element in sub_sub_aisle_element[1:]]
            for t in tmp:
                sub_sub_aisle_links.append(t)

        for s in sub_sub_aisle_links:
            driver.get(s)
            bread_crumb = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".breadcrumbs-link")))
            breadcrumb_texts = ", ".join([element.text.strip() for element in bread_crumb[2:]])
            time.sleep(GEN_TIMEOUT)
            while True:
                WebDriverWait(driver, EXPLICIT_WAIT_TIME * 2).until(EC.presence_of_element_located((By.CLASS_NAME, "product-grid-v2")))
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
                    items.append({product['url'], breadcrumb_texts})

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
        time.sleep(FAVNUM)

    # check for previous scrape
    df_data = pd.DataFrame()
    site_items_df = pd.DataFrame()
    try:
        df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_{STORE_NAME}_data.csv")
        site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
    except:
        print('No Prior Data Found... ')

    # scrape items and check for already scraped
    for item_index in range(len(items)):
        item_url = items[item_index]
        if not df_data.empty and items[item_index] in df_data['url'].values:
            print(f'{ind}-{item_index} Item Already Exists!')
            continue

        for v in range(5):
            try:
                time.sleep(GEN_TIMEOUT)
                driver.get(item_url)
                new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index)
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
    itemIdx = f'{ind}-{index}-{aisle.upper()[:3]}'
    name = None
    brand = None
    subaisle = None
    subsubaisle = None
    size = None
    price = None
    multi_price = None
    old_price = None
    pricePerUnit = None
    itemNum = None
    description = None
    serving = None
    img_urls = []
    item_label = None
    item_ingredients = None
    pack = None

    new_row = {'idx': itemIdx,
               'name': name, 'brand': brand,
               'aisle': aisle, 'subaisle': subaisle,
               'subsubaisle': subsubaisle,
               'size': size, 'price': price, 'multi_price': multi_price,
               'old_price': old_price, 'pricePerUnit': pricePerUnit,
               'itemNum': itemNum, 'description': description, 'serving': serving,
               'img_urls': ', '.join(img_urls), 'item_label': item_label,
               'item_ingredients': item_ingredients, 'url': item_url,
               'pack': pack,
               'timeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()}
    return (new_row)
