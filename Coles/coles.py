# Packages for scrapping
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request

# Special Package to scrap and aids in avoiding more stringent sites
#import undetected_chromedriver as uc

import time
import datetime
import pytz
import math

import random

import re


## This setups coles by removing notices and setting location
def setup_coles(driver, EXPLICIT_WAIT_TIME, site_location_df, ind):
    address = site_location_df.loc[ind, 1]
    tmp = address.split(',')
    address = ''.join(tmp[0:(len(tmp) - 1)])
    # Remove cookies notice if exists
    #checkRemoveCookiesNotice_coles(driver, EXPLICIT_WAIT_TIME)
    # Set Location
    try:
        setLocation_coles(driver, address, 5 * EXPLICIT_WAIT_TIME)
    except:
        raise Exception("setLocation Error")

    # Remove cookies notice if exists (sometimes pops up late)
    #checkRemoveCookiesNotice_coles(driver, EXPLICIT_WAIT_TIME/2)


## This removes cookies popup for coles
def checkRemoveCookiesNotice_coles(driver, EXPLICIT_WAIT_TIME):
    try:
        # Wait a bit as it pops up late and explicit wait doesn't quite work..
        time.sleep(2)
        ## Find cookies
    except:
        None


## This sets location for Lablaws
def setLocation_coles(driver, address, EXPLICIT_WAIT_TIME):
    # Set Location
    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, 'delivery-selector-button'))
    ).click()

    text_enter = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@data-testid="autocomplete-input"]'))
    )
    text_enter.send_keys(address)

    results = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'MuiAutocomplete-listbox'))
    )
    results_list = results.find_elements(By.XPATH, './li')
    results_list[0].click()

    WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.XPATH, '//button[@data-testid="cta-secondary"]'))
    ).click()


## This scraps the data for Lablaws
def scrapSite_coles(driver, EXPLICIT_WAIT_TIME=10, idx=None, aisles=[], ind=None,
                    url=None, site_location_df=None):
    col = ['idx', 'name', 'brand', 'aisle', 'subaisle', 'subsubaisle',
           'size', 'price', 'multi_price',
           'old_price', 'pricePerUnit', 'itemNum',
           'description', 'serving', 'img_urls',
           'item_label', 'item_ingredients',
           'url', 'SKU', 'UPC', 'timeStamp']
    #  Setup Data
    site_items_df = pd.DataFrame(columns=col)

    for aisle in aisles:
        print(aisle)
        time_aisle = time.time()

        # Get aisle URL
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@data-testid="header-link-shop-categories"]'))
        ).click()

        poss_aisles = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'coles-targeting-NavigationListNavigationWrapper'))
        ).find_elements(By.XPATH, './li/a')
        for pa in poss_aisles:
            if pa.text == aisle:
                pa.click()
                break
            if pa == poss_aisles[len(poss_aisles) - 1]:
                raise Exception('Aisle not found')

        poss_subaisles = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.ID, 'sub-categories-navlist'))
        ).find_elements(By.XPATH, './nav/ul/li/a')
        subaisle_urls = []
        for psa in poss_subaisles:
            try:
                psa.text.index('All')
            except:
                subaisle_urls.append(psa.get_attribute('href'))

        for subaisle in subaisle_urls:
            print(subaisle)

        for subaisle_url_idx in range(len(subaisle_urls)):
            # reset site items
            site_items_df = pd.DataFrame(columns=col)

            subaisle_url = subaisle_urls[subaisle_url_idx]

            driver.get(subaisle_url)

            # Get where items are
            try:
                item_urls = getItem_urls(driver, EXPLICIT_WAIT_TIME)
            except:
                time.sleep(15)
                item_urls = getItem_urls(driver, EXPLICIT_WAIT_TIME)

            # Save URLS in case of issue
            pd.DataFrame(item_urls).to_csv(
                'output/tmp/ind' + str(ind) + 'Idx' + str(idx) + 'A' + aisle + '_item_urls.csv', index=False)
            print('(Number of Items: ' + str(len(item_urls)) + ')')

            start = 0
            file_path = 'output/tmp/ind' + str(ind) + 'aisle-sub_' + str(aisle) + ' ' + str(subaisle_url_idx) + '.csv'
            try:
                site_items_df = pd.read_csv(file_path)
                print(site_items_df)
                start = len(site_items_df) - 1
                if start < 0:
                    start = 0
                print(f"recovering from index {start}")
            except Exception as e:
                print("No prior file found")
                None

            # Loop through items to scrape information
            for item_url_idx in range(start, len(item_urls)):
                print(item_url_idx)
                item_url = item_urls[item_url_idx]
                # Go to product url
                driver.get(item_url)

                try:
                    time.sleep(0.5)
                    new_row = scrap_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx)
                except:
                    time.sleep(15)
                    try:
                        driver.get(item_url)
                        new_row = scrap_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx)
                    except:
                        time.sleep(60 * 25)
                        try:
                            driver.get(item_url)
                            new_row = scrap_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx)
                        except:
                            print(f"{item_url_idx} Error")
                            time.sleep(15)
                            break

                if (math.isnan(site_items_df.index.max())):
                    site_items_df.loc[0] = new_row
                else:
                    site_items_df.loc[site_items_df.index.max() + 1] = new_row
                print(site_items_df)
                if (item_url_idx % 10 == 0):
                    site_items_df.to_csv(
                        'output/tmp/ind' + str(ind) + 'aisle-sub_' + str(aisle) + ' ' + str(subaisle_url_idx) + '.csv',
                        index=False)
                    print(len(item_urls))

        site_items_df.to_csv(
            'output/tmp/ind' + str(ind) + 'aisle-sub_' + str(aisle) + ' ' + str(subaisle_url_idx) + '.csv', index=False)
        print_time = time.time() - time_aisle
        try:
            print('Time for aisle: ' + str(round(print_time, 1)) + 's (' + str(
                round(print_time / len(item_urls), 2)) + 's est. per item)')
        except:
            print("Finished")
    return (site_items_df)


def getItem_urls(driver, EXPLICIT_WAIT_TIME):
    urls = []
    while True:
        # Find items
        items = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME, 'coles-targeting-ProductTileProductTileWrapper'))
        )
        for item in items:
            urls.append(item.find_element(By.CLASS_NAME, 'product__link').get_attribute('href'))

        try:
            nextPage = driver.find_element(By.ID, 'pagination-button-next')
            if nextPage.is_enabled():
                nextPage.click()
                time.sleep(4)
            else:
                break
        except:
            break

    return (list(set(urls)))


# def reset_site(driver,url,EXPLICIT_WAIT_TIME, site_location_df,ind,item_url):
#     try:
#         driver.close()
#     except:
#         None
#     time.sleep(10)
#     driver = uc.Chrome()#use_subprocess=False)
#     driver.maximize_window()
#     driver.get(url)
#     try:
#         captcha_coles2(driver,EXPLICIT_WAIT_TIME)
#         checkRemoveCookiesNotice_coles(driver, EXPLICIT_WAIT_TIME)
#         captcha_coles1(driver,EXPLICIT_WAIT_TIME)
#         time.sleep(5)
#         setup_coles(driver, site_location_df.loc[ind,1], EXPLICIT_WAIT_TIME)
#         # Go to product url
#         driver.get(item_url)
#     except:
#         None

#     return(driver)


def scrap_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, idx):
    # Scrap aisles
    breadcrumbs = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'coles-targeting-BreadcrumbsList'))
    ).find_elements(By.XPATH, './/span[@itemprop="name"]')
    try:
        subaisle = breadcrumbs[3].text
    except:
        subaisle = ''
    try:
        subsubaisle = breadcrumbs[4].text
    except:
        subsubaisle = ''

    time.sleep(1)

    rightSide = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'coles-targeting-StylesProductDetailStylesProductCTAWrapper'))
    )

    # Scrap name
    try:
        name = rightSide.find_element(By.CLASS_NAME, 'product__title').text
    except:
        name = ''

    size = ''

    # Item Index for matching
    itemIdx = 'Ind' + str(ind) + 'S' + str(idx) + '_A' + aisle + '_SA' + subaisle + '_I' + name

    # Scrap brand
    try:
        brand = rightSide.find_element(By.CLASS_NAME, 'product__top_messaging__item').text
    except:
        brand = None

    # Scrap price
    try:
        price = rightSide.find_element(By.CLASS_NAME, 'price__value').text
    except:
        price = None

    pricePerUnit = None
    old_price = None
    try:
        partial = rightSide.find_element(By.CLASS_NAME, 'price__calculation_method').text.split('|')
        pricePerUnit = partial[0].strip()
        old_price = partial[1].strip().replace('Was ', '')
    except:
        None

    # Multiprice
    try:
        multi_price = rightSide.find_element(By.CLASS_NAME, 'product_promotion').text
    except:
        multi_price = None

    # TODO:: Scrap pictures
    try:
        imgs = None
        img_urls = []
        for img_idx in range(len(imgs)):
            raise Exception('Found item')
            #time.sleep(4*random.random())
            src = imgs[img_idx].get_attribute('src')
            img_urls.append(src)
            try:
                # Save by source
                urllib.request.urlretrieve(src,
                                           'output/images/' + str(ind) + '/' + itemIdx + '_Img' + str(img_idx) + '.png')
            except:
                None
    except:
        img_urls = ['']

    leftSide = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located(
            (By.CLASS_NAME, 'coles-targeting-StylesProductDetailStylesProductDetailsWrapper'))
    )
    # certifications
    try:
        certifications_list = leftSide.find_element(By.CLASS_NAME, 'dietary-allergen-list').find_elements(By.XPATH,
                                                                                                          './/button/span')
        certifications = []
        for certs in certifications_list:
            certifications.append(certs.get_attribute('innerHTML').split('<svg')[0])
        certifications = ', '.join(certifications)
    except:
        certifications = None

    # Scrape Description
    try:
        description = leftSide.find_element(By.CLASS_NAME, 'coles-targeting-SectionHeaderDescription').text
    except:
        description = None

    # Scrap Nutrition
    try:
        time.sleep(3)
        leftSide.find_element(By.ID, 'nutritional-information-label').click()
        time.sleep(2)
        try:
            item_label = leftSide.find_element(By.ID, 'nutritional-information-control').text
        except:
            print("Erorr")
    except:
        print("no label")
        item_label = None

    # Ingredients
    try:
        leftSide.find_element(By.ID, 'ingredients').click()
        item_ingredients = leftSide.find_element(By.ID, 'ingredients-control').text
    except:
        item_ingredients = None

        # Allergen Info
    try:
        leftSide.find_element(By.ID, 'allergen').click()
        allergen_info = leftSide.find_element(By.ID, 'allergen-control').text
    except:
        allergen_info = None

    # Serving Size
    serving = None

    # itemNum
    try:
        leftSide.find_element(By.ID, 'warnings').click()
        warnings = leftSide.find_element(By.ID, 'warnings-control').text
    except:
        warnings = None

    # itemNum
    try:
        itemNum = leftSide.find_element(By.XPATH, './/*[@data-testid="product-code"]').text.replace('Code: ', '')
    except:
        itemNum = None

        # UPC
    UPC = None
    SKU = None

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
               'warnings': warnings, 'certifications': certifications,
               'SKU': SKU, 'UPC': UPC, 'allergen_info': allergen_info,
               'timeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()}

    time.sleep(3)

    return (new_row)


def captcha_coles1(driver, EXPLICIT_WAIT_TIME):
    # As needed
    try:
        None
    except:
        None


def captcha_coles2(driver, EXPLICIT_WAIT_TIME):
    try:
        None
    except:
        None
