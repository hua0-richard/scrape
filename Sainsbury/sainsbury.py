import requests
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
from bs4 import BeautifulSoup
import os
import glob

# Special Package to scrap and aids in avoiding more stringent sites
import undetected_chromedriver as uc

import time
import datetime
import pytz

import random

import re

FAVNUM = 22222
GEN_TIMEOUT = 5
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

def setup_sainbury(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_sainbury(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)

def setLocation_sainbury(driver, address, EXPLICIT_WAIT_TIME):
    # Reject Cookies Button
    try:
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
        ).click()
        print('Reject Cookies Button')
    except Exception as e:
        print('No Cookies Button')

    # Login
    for _ in range(5):
        try:
            time.sleep(GEN_TIMEOUT)
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.top-right-links--login"))
            ).click()
            print('Login Button')
            break
        except Exception as e:
            print(f'Error Clicking Login Button. Trying Again. Attempt {_}')

    # Reject Cookies Button Login
    try:
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
        ).click()
        print('Reject Cookies Button')
    except Exception as e:
        print('No Cookies Button')

    # Login Data
    text_enter = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, 'username'))
    )
    text_enter.send_keys('u2894478@gmail.com')

    text_enter = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, 'password'))
    )
    text_enter.send_keys('Notme123!')

    try:
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='log-in']"))).click()
        print('Set Location Complete')
        print('Found Login Button')
    except Exception as e:
        print('Did not find Login Button')

    # input('Continue? [Y] / [N]')
    time.sleep(GEN_TIMEOUT)

    # Set Location
    for _ in range(5):
        try:
            time.sleep(GEN_TIMEOUT)
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.book-delivery__icon.ln-c-icon"))).click()
            print('Found Delivery Options')
            css_selector = (
                'input#store-search'
                '[aria-describedby="store-searchInfo store-searchValidation"]'
                '[style="text-transform: uppercase;"]'
                '[name="store-search"]'
                '[type="text"]'
                '.ln-c-text-input.ln-c-input-group__control'
                '[required]'
                '[maxlength="8"]'
            )
            print('Found Address Input')
            # Postal Code
            input_field = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
            print(address)
            uk_postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}\b'
            match = re.search(uk_postcode_pattern, address)
            postal_code = ''
            if match:
                postal_code = match.group()
            input_field.send_keys(postal_code)
            time.sleep(GEN_TIMEOUT)
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ln-c-button.ln-c-button--filled.ln-c-input-group__button"))).click()
            print('Location Done')
            store_list = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "store-card__list")))
            store = store_list.find_element(By.CSS_SELECTOR, "li.store-card__list--item")
            store.find_element(By.CSS_SELECTOR, "div.store-card").click()
            print('Store Done')
            break
        except Exception as e:
            print('Failed to find Delivery Options')

    # Reserve Delivery Slot
    for _ in range(5):
        try:
            print('Finding Delivery Slot')
            table = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CLASS_NAME, "slot-table"))
            )
            print('Found Table')
            time.sleep(GEN_TIMEOUT)
            button = WebDriverWait(table, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, ".//button[not(@disabled)]"))
            )
            if (button):
                print('Found Button')
                button.click()
            print('Obtained Delivery Slot')
            break
        except Exception as e:
            print(f'Failed to get Delivery Slot. Trying again... Attempt {_}')

    for _ in range(5):
        try:
            time.sleep(GEN_TIMEOUT)
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ln-c-button.ln-c-button--filled.ln-c-button--full.cnc-reserve-modal__primary-button.ln-u-display-inline-flex.ln-u-justify-content-center.ln-u-align-items-center"))
            ).click()
            break
        except Exception as e:
            print(f'Trying again... Attempt {_}')

    for _ in range(5):
        try:
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ln-c-button.ln-c-button--filled.cnc-booking-confirmation__button'))).click()
            print('Booking Confirmed')
            break
        except:
            print(f'Trying again. Attempt {_}')

    print('Set Location Complete')
def scrapeSite_sainbury(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    site_items_df = pd.DataFrame(columns=['idx', 'name', 'brand', 'aisle', 'subaisle', 'subsubaisle',
                                          'size', 'price', 'multi_price',
                                          'old_price', 'pricePerUnit', 'itemNum',
                                          'description', 'serving', 'img_urls',
                                          'item_label', 'item_ingredients',
                                          'pack',
                                          'url', 'timeStamp'])
    subaisles = []
    items = []

    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print(e)
        print('No Prior Data URLs Found... ')
        # Get Aisle
        for _ in range(5):
            try:
                # Get Grocery Aisles Menu
                time.sleep(GEN_TIMEOUT)
                grocery_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/shop/gb/groceries'].nav__menu-link")))
                actions = ActionChains(driver)
                actions.move_to_element(grocery_element)
                actions.perform()
                print('Found Grocery Menu')
                time.sleep(GEN_TIMEOUT)
                # Get Specific Aisle
                nav_list = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ln-o-bare-list")))
                nav_items = nav_list.find_elements(By.CSS_SELECTOR, "li.ln-o-bare-list__item a.desktop-nav__item")
                aisle_element = next((item for item in nav_items if item.find_element(By.CSS_SELECTOR,"div.desktop-nav__item-wrapper").text.strip() == aisle),None)
                print('Found Aisle')
                if aisle_element:
                    href = aisle_element.get_attribute('href')
                    print(href)
                    driver.get(href)
                    print(f'At Aisle {aisle}')
                break
            except Exception as e:
                print(f'Trying again... Attempt {_}')

        # Get subaisles
        if aisle == 'Drinks':
            for _ in range(5):
                try:
                    divs = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.M052styles__Container-sc-1cubg5c-2.bEpIHz'))
                    )
                    for div in divs:
                        anchors = div.find_elements(By.TAG_NAME, 'a')
                        for anchor in anchors:
                            href = anchor.get_attribute('href')
                            if href:
                                subaisles.append(href)
                    print(subaisles)
                    # Don't Scrape Special Offers
                    subaisles.pop(0)
                    print('Found Subaisles')
                    break
                except Exception as e:
                    print(f'Trying again... Attempt {_}')

        if aisle == 'Dairy, eggs & chilled':
            for _ in range(5):
                try:
                    ul_element_links = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "ul.browse-pill-list.browse-pill-list__disable-scrollbars"))
                    )
                    li_elements = ul_element_links.find_elements(By.TAG_NAME, "li")
                    for index, li in enumerate(li_elements, start=1):
                        a_tag = li.find_element(By.TAG_NAME, "a")
                        href = a_tag.get_attribute("href")
                        subaisles.append(href)
                    print(subaisles)
                    break
                except:
                    print(f'Trying again... Attempt {_}')


        for s in subaisles:
            driver.get(s)
            time.sleep(GEN_TIMEOUT)
            while True:
                time.sleep(GEN_TIMEOUT)
                ul = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ln-o-grid.ln-o-grid--matrix.ln-o-grid--equal-height'))
                )
                pt_links = ul.find_elements(By.CLASS_NAME, 'pt__link')
                for link in pt_links:
                    href = link.get_attribute('href')
                    if href:
                        items.append(href)
                try:
                    WebDriverWait(driver, GEN_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a.ln-c-pagination__link[rel="next"][aria-label="Next page"]'))
                    ).click()
                except Exception as e:
                    print('No Next Page')
                    break

        items = list(dict.fromkeys(items))
        pd.DataFrame(items).to_csv(f'output/tmp/index_{str(ind)}_{aisle}_item_urls.csv', index=False, header=None,encoding='utf-8-sig')
        print(f'items so far... {len(items)}')

    # check for previous items
    df_data = pd.DataFrame()
    site_items_df = pd.DataFrame()
    try:
        df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_sainsbury_data.csv")
        site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
    except:
        print('No Prior Data Found... ')

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
                    full_path = 'output/images/' + str(ind) + '/' + str(index_for_here)+ '-' + str(0) + '.png'
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
            site_items_df = site_items_df.sort_values(by='idx', key=lambda x: x.map(custom_sort_key))
            site_items_df = site_items_df.reset_index(drop=True)
            site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_sainsbury_data.csv', index=False)

    site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_sainsbury_data.csv', index=False)
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

    try:
        name = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.pd__header'))
        ).text
    except:
        print('No Name')

    try:
        brand = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.pd__header'))
        ).text.split()[0]
    except:
        print('No Brand')

    try:
        price = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.pd__cost__retail-price'))
        ).text
    except:
        print('No Price')

    try:
        description = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.pd__description'))
        ).text
    except:
        print('No Description')

    try:
        table = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "nutritionTable"))
        )

        # Extract headers
        headers = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.XPATH, "//th[@scope='col']"))
        )
        headers = [header.text for header in headers]

        # Extract rows
        rows = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@class='nutritionTable']/tbody/tr"))
        )

        output = "Nutrient\t" + "\t".join(headers[1:]) + "\n"

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                nutrient = row.find_element(By.TAG_NAME, "th").text
                values = [cell.text.replace('\n', ' ') for cell in cells]
                output += f"{nutrient}\t" + "\t".join(values) + "\n"

        item_label = output.strip()

    except:
        print('No Nutrition Label')

    try:
        item_ingredients = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "productIngredients"))
        ).text
    except:
        print('Trying Secondary Ingredient Parse')
        try:
            ingredients_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//strong[contains(text(), 'INGREDIENTS:')]/following-sibling::p"))
            )
            item_ingredients = ingredients_element.text
        except:
            print('No Ingredients')

    try:
        itemNum = WebDriverWait(driver, GEN_TIMEOUT).until(EC.presence_of_element_located((By.ID, "productSKU"))).text
    except:
        print("No SKU")

    try:
        size_patterns = [
            r'(\d+(\.\d+)?)\s*(ml|g|kg|oz|fl\s*oz)\s*(?:serving|per\s*serving)',
            r'Serving\s*size:?\s*(\d+(\.\d+)?)\s*(ml|g|kg|oz|fl\s*oz)',
            r'1\s*serving\s*=\s*(\d+(\.\d+)?)\s*(ml|g|kg|oz|fl\s*oz)',
        ]

        for pattern in size_patterns:
            size_match = re.search(pattern, item_label, re.IGNORECASE)
            if size_match:
                serving = f"{size_match.group(1)} {size_match.group(3)}"
                break
    except:
        print("No Serving Size")

    try:
        aisle_texts = []
        aisle_label_container = WebDriverWait(driver, GEN_TIMEOUT).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.ln-c-breadcrumbs__item')))
        for t in aisle_label_container:
            link = t.find_element(By.TAG_NAME, 'a')
            aisle_texts.append(link.text)
        aisle_texts = aisle_texts[1:]
        aisle_texts = list(reversed(aisle_texts))
        if (len(aisle_texts) > 0):
            subaisle = aisle_texts.pop()
        if (len(aisle_texts) > 0):
            subsubaisle = aisle_texts.pop()
    except:
        print("Aisle Error")

    try:
        pattern = r'(\d+(?:\.\d+)?)\s*(L|ML|l|ml)'
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            volume = match.group(1)
            unit = match.group(2).upper()
            size = f"{volume}{unit}"
    except:
        print("Size Error")

    try:
        pricePerUnit = WebDriverWait(driver, GEN_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.pd__cost__unit-price-per-measure'))).text
    except:
        print('Price per Unit Error')

    try:
        match = re.search(r'(\d+)x', name)
        if match:
            no_units = int(match.group(1))
            multi_price = f"{no_units} for {price}"
    except:
        print('Multi Price Error / No Multi Price')

    try:
        match = re.search(r'(\d+x\d+(?:\.\d+)?(?:ml|l|g|kg))', name, re.IGNORECASE)
        if match:
            full_quantity = match.group(1)
            pack_size_match = re.search(r'(\d+)x', full_quantity)
            if pack_size_match:
                # pack_size = int(pack_size_match.group(1))
                pack = f"{full_quantity}"
    except:
        print("No Pack")

    try:
        old_price = WebDriverWait(driver, GEN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.pd__cost--price"))
        ).text
    except:
        print('No Nectar (Discount) Price')

    try:
        images = WebDriverWait(driver, GEN_TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.pd__image.pd__image__nocursor")))
        src = images.get_attribute("src")
        img_urls.append(src)
        print(src)
        response = requests.get(src)
        if response.status_code == 200:
            full_path = 'output/images/' + str(ind) + '/' + str(itemIdx) + '-' + str(0) + '.png'
            with open(full_path, 'wb') as file:
                file.write(response.content)
    except:
        print('Images Error')

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
    None
