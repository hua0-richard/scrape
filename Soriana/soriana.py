# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 00:52:39 2023

@author: j53vande
"""

# Packages for scrapping
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

def setup_soriana(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_soriana(driver, site_location_df.loc[ind, 1], EXPLICIT_WAIT_TIME)


## This removes cookies popup for Loblaws
def checkRemoveCookiesNotice_soriana(driver, EXPLICIT_WAIT_TIME):
    try:
        # Wait a bit as it pops up late and explicit wait doesn't quite work..
        time.sleep(2)
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'lds__privacy-policy__btnClose')) and
            EC.element_to_be_clickable((By.CLASS_NAME, 'lds__privacy-policy__btnClose'))
        ).click()
    except:
        None


def setLocation_soriana(driver, address, EXPLICIT_WAIT_TIME):
    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'common-header__postal-code-title'))
    ).click()
    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".modal-dialog.modal-dialog-centered.store-select-modal.mb-5.mt-1 .modal-content"))
    )
    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.change-postal-code-btn.js-change-postal-code-btn"))
    ).click()

    postal_input = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "new-postalcode-field"))
    )
    nums = re.findall(r'\d+', address)
    postal_input.send_keys(nums[len(nums) - 1])
    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
                                    ".btn.btn-primary.postalcode-search.js-postalcode-search.position-absolute.d-flex.align-items-center.justify-content-center.p-0")
                                   )).click()

    for i in range(5):
        try:
            postal_input = None
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "js-select-store-modal"))
            ).click()
            break
        except:
            print(f'Attempt {i + 1}. Stale. Trying Again...')
            continue

    print('Set Location Complete')


def scrapSite_soriana(driver, EXPLICIT_WAIT_TIME=10, idx=None, aisles=[], ind=None,
                      site_location_df=None):
    #  Setup Data
    site_items_df = pd.DataFrame(columns=['idx', 'name', 'brand', 'aisle', 'subaisle', 'subsubaisle',
                                          'size', 'price', 'multi_price',
                                          'old_price', 'pricePerUnit', 'itemNum',
                                          'description', 'serving', 'img_urls',
                                          'item_label', 'item_ingredients',
                                          'pack',
                                          'url', 'timeStamp'])

    for aisle in aisles:
        print('\n', aisle)
        time_aisle = time.time()
        # Open Grocery
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Departamentos"]'))
        ).click()
        time.sleep(1)

        # Search for Aisle
        poss_aisles = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "menu-web"))
        )
        time.sleep(1)
        poss_aisles = poss_aisles.find_elements(By.XPATH, './li')
        for pa in poss_aisles:
            if pa.text == aisle:
                success = pa
                break
            elif pa == poss_aisles[len(poss_aisles) - 1]:
                raise Exception('Aisle not found')

        success.click()
        time.sleep(1)
        poss_subaisles = success.find_elements(By.XPATH, './/a[@class="nav__cat-item-megamenu"]')

        subaisles_urls = []
        for psa in poss_subaisles:
            subaisles_urls.append(psa.get_attribute('href'))

        all_urls = []
        for subaisles_url_idx in range(len(subaisles_urls)):
            print(subaisles_urls[subaisles_url_idx])

            subaisles_url = subaisles_urls[subaisles_url_idx]

            driver.get(subaisles_url)
            item_urls = getItem_urls(driver, EXPLICIT_WAIT_TIME)
            for u in item_urls:
                all_urls.append(u)

            # Save URLS in case of issue
            pd.DataFrame(all_urls).to_csv('output/tmp/ind' + str(ind) + '_item_urls.csv', index=False,
                                          encoding='utf-8-sig')
            print(f'items so far... {len(all_urls)}')

        # check for previous items
        df_data = pd.DataFrame()
        site_items_df = pd.DataFrame()
        try:
            df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_soriana_data.csv")
            site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
        except:
            print('No Prior Data Found... ')

        for item_url_idx in range(len(all_urls)):
            item_url = item_urls[item_url_idx]
            new_row = None
            if not df_data.empty and all_urls[i] in df_data['url'].values:
                print(f'{ind}-{i} Item Already Exists!')
                continue

            for i in range(5):
                try:
                    driver.get(item_url)
                    new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx)
                    site_items_df = pd.concat([site_items_df, pd.DataFrame([new_row])], ignore_index=True)
                    site_items_df = site_items_df.drop_duplicates(subset=['url'], keep='last')
                    break
                except Exception as e:
                    print(f'Failed to scrape item. Attempt {i}. Trying Again... ')
                    None

            if (item_url_idx % 10 == 0):
                site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_soriana_data.csv', index=False)

        site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_soriana_data.csv', index=False)


def scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx):
    # Scrap main
    breadcrumbs = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'breadcrumb'))
    ).text.split('\n')
    subaisle = ''
    subsubaisle = ''
    try:
        subaisle = breadcrumbs[2]
        subsubaisle = breadcrumbs[3]
    except:
        None

    try:
        name = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'product-name'))
        ).text
    except:
        name = ''

    # Item Index for matching
    itemIdx = 'S' + str(idx) + '_A' + aisle + '_SA' + subaisle + '_I' + name

    try:
        brand = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'brand-content'))
        )
        brand = brand.find_element(By.XPATH, './div/a/p').text
    except:
        brand = None

    ## Prices
    price = None
    old_price = None
    multi_price = None
    try:
        price_data = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'product-detail__details-container'))
        )
        try:
            price = price_data.find_element(By.CLASS_NAME, 'oldDiscountPrice ').text
        except:
            None
        try:
            old_price = price_data.find_element(By.XPATH, './/*[@class="value "]').text
        except:
            None
    except:
        None

    # Scrap pictures
    imgs = driver.find_element(By.CLASS_NAME, 'primary-images')
    imgs = imgs.find_elements(By.XPATH, './/img')
    img_urls = []
    img_idx = 1
    for img_idx in range(len(imgs)):
        src = imgs[img_idx].get_attribute('src')
        img_urls.append(src)
        try:
            # ActionChains(driver).move_to_element(imgs[img_idx]).click().perform()
            # urllib.request.urlretrieve(src, 'output/images/'+str(ind)+'/'+itemIdx+'_Img'+str(img_idx)+'.png')
            imgs[img_idx].screenshot('output/images/' + str(ind) + '/' + itemIdx + '_Img' + str(img_idx) + '.png')
        except:
            None

    try:
        description = driver.find_element(By.ID, 'videosMobile').text
    except:
        description = None

    driver.find_elements(By.CLASS_NAME, 'tab-link')[1].click()
    item_label = driver.find_element(By.CLASS_NAME, "table-striped").text
    table = item_label.split('\n')

    size = None
    serving = None
    pack = None
    pricePerUnit = None
    item_ingredients = None
    for val in table:
        try:
            val.index('Contenido del Empaque')
            size = val.replace('Contenido del Empaque', '')
        except:
            None

        try:
            val.index('Contenido Neto')
            serving = val.replace('Contenido Neto', '')
        except:
            None

        try:
            val.index('Presentación')
            pack = val.replace('Presentación', '')
        except:
            None

        try:
            val.index('Ingredientes')
            item_ingredients = val.replace('Ingredientes', '')
        except:
            None

        try:
            val.index('Número de Piezas')
            pricePerUnit = str(re.findall(r'd+', val)) + ' / ' + price
        except:
            None

    itemNum = None

    # Save results (processing in later step)
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


def getItem_urls(driver, EXPLICIT_WAIT_TIME):
    urls = []
    items = []
    while True:
        time.sleep(5)
        for i in range(5):
            try:
                items = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.visibility_of_all_elements_located((By.CLASS_NAME, 'product'))
                )
                items_html = [item.get_attribute('outerHTML') for item in items]
                break
            except Exception as e:
                print("Failed to get Item URL. Trying Again... ")
                time.sleep(5)
        for html in items_html:
            # Create a new element to parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            try:
                urls.append(f'https://www.soriana.com{soup.find('a')['href']}')
            except Exception as e:
                print('Failed to get item URL')
        urls = list(set(urls))
        for i in range(5):
            if (i == 4):
                return urls
            try:
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Next"]'))
                ).click()
                break
            except:
                print("Trying to find next button... ")
