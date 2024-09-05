import glob
import os

import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import Select
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
GEN_TIMEOUT = 6
STORE_NAME = 'asda'
LOCATION = ''
MAX_RETRY = 10


def extract_city_and_region(address):
    parts = address.split(', ')
    if len(parts) >= 3:
        city = parts[-3]
        region = parts[-2].split()[0]
        return [city, region]
    else:
        return ["Invalid", "Address"]


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


def setup_asda(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_asda(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)


def setLocation_asda(driver, address, EXPLICIT_WAIT_TIME):
    input('Manually Set Location')
    print('Set Location Complete')


def scrapeSite_asda(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    # i in items
    # i[0] is url
    # i[1] is aisle
    items = []
    subaisles = []
    subsubaisles = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')

        try:
            time.sleep(GEN_TIMEOUT)
            wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
            groceries_link = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(@class, 'navigation-menu__text') and contains(text(), 'Groceries')]")))
            groceries_link.click()
            time.sleep(GEN_TIMEOUT)
            aisle_button = wait.until(EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//button[contains(@class, 'h-nav__item-button') and ./span[contains(text(), '{aisle}')]]")))
            aisle_button.click()
        except Exception as e:
            print('Failed to get Categories')
            print(e)

        try:
            time.sleep(GEN_TIMEOUT)
            wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
            taxonomy_explore = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-auto-id="taxonomyExplore"]')))
            links = taxonomy_explore.find_elements(By.CSS_SELECTOR, 'a.asda-btn.asda-btn--light.taxonomy-explore__item')
            for link in links:
                href = link.get_attribute('href')
                subaisles.append(href)
            print(subaisles)
        except:
            print('Failed to get sub aisles Page')

        try:
            for s in subaisles:
                driver.get(s)
                links = []
                for q in range(5):
                    try:
                        time.sleep(GEN_TIMEOUT * 4)
                        wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
                        taxonomy_explore = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-auto-id="taxonomyExplore"]')))
                        links = taxonomy_explore.find_elements(By.CSS_SELECTOR,
                                                               'a.asda-btn.asda-btn--light.taxonomy-explore__item')
                        break
                    except Exception as e:
                        print('Trying again subaisle... ')
                for next_page in links:
                    href = next_page.get_attribute("href")
                    subsubaisles.append(href)
                print(subsubaisles)

        except Exception as e:
            print('Failed to get sub sub aisles')
            print(e)

        try:
            print('sub sub aisles')
            for s in subsubaisles:
                time.sleep(GEN_TIMEOUT * 2)
                driver.get(s)
                while True:
                    time.sleep(GEN_TIMEOUT * 2)
                    parent_element = driver.find_element(By.CSS_SELECTOR,
                                                         'div.co-product-list[data-module-id="89f48dab-0e3f-4e2e-944e-add8f133a1f7"]')
                    li_elements = parent_element.find_elements(By.CSS_SELECTOR, 'li.co-item')
                    for li in li_elements:
                        try:
                            anchor = li.find_element(By.CSS_SELECTOR, 'a.co-product__anchor')
                            href = anchor.get_attribute('href')
                            items.append(href)
                        except Exception as e:
                            print(f"An error occurred:")
                            print(e)
                    print(items)
                    print(f'items so far... {len(items)}')

                    try:
                        total_height = driver.execute_script("return document.body.scrollHeight")
                        half_height = total_height // 2
                        driver.execute_script(f"window.scrollTo(0, {half_height});")
                        time.sleep(2)
                        wait = WebDriverWait(driver, 5)
                        next_page = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-auto-id="btnright"]')))
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                        driver.execute_script("window.scrollBy(0, -200);")
                        next_page.click()
                        print('Found Next Page')
                    except:
                        print('No Next Page')
                        break

        except Exception as e:
            print('Failed to get items')
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
    ItemNum = None
    Notes = 'OK'

    global LOCATION
    print(LOCATION)
    result = extract_city_and_region(LOCATION)
    City = result[0]
    Region = result[1]

    for p_name in range(2):
        try:
            ProductName = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.pdp-main-details__title"))
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
        print('Brand Error')

    try:
        ItemNum = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "span.pdp-main-details__product-code"))).text
    except:
        print('ItemNum Error')

    try:
        net_content_title = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH,
                                            "//div[contains(@class, 'pdp-description-reviews__product-details-title') and text()='Net Content']")))

        net_content_value = net_content_title.find_element(By.XPATH,
                                                           "following-sibling::div[contains(@class, 'pdp-description-reviews__product-details-content')]")

        Netcontent_org = net_content_value.text
        Netcontent_val = net_content_value.text
        Netcontent_unit = net_content_value.text

    except:
        print('Net Content Error')

    try:
        product_info_title = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(EC.presence_of_element_located((By.XPATH,"//div[contains(@class, 'pdp-description-reviews__product-details-title') and text()='Product Information']")))
        product_info_content = product_info_title.find_element(By.XPATH,"following-sibling::div[contains(@class, 'pdp-description-reviews__product-details-content')]")
        Description = product_info_content.text
    except:
        print('Description Error')

    try:
        ingredients_title = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'pdp-description-reviews__product-details-title') and text()='Ingredients']"))
        )
        ingredients_content = ingredients_title.find_element(By.XPATH, "following-sibling::div[contains(@class, 'pdp-description-reviews__product-details-content')]")
        Ingredients = ingredients_content.text
    except:
        print('Description Error')

    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pdp-description-reviews__nutrition-table-cntr"))
        )
        rows = table.find_elements(By.CLASS_NAME, "pdp-description-reviews__nutrition-row")
        header_cells = rows[0].find_elements(By.CLASS_NAME, "pdp-description-reviews__nutrition-cell")
        serving_sizes = [cell.text.strip() for cell in header_cells[1:] if cell.text.strip()]
        nutrition_info = {size: {} for size in serving_sizes}
        nutrition_string = f"Serving sizes: {', '.join(serving_sizes)}\n\n"
        current_main_nutrient = ""
        for row in rows[1:]:
            cells = row.find_elements(By.CLASS_NAME, "pdp-description-reviews__nutrition-cell")
            if len(cells) >= len(serving_sizes) + 1:
                key = cells[0].text.strip()
                values = [cell.text.strip() for cell in cells[1:len(serving_sizes)+1]]

                if "of which" in key.lower():
                    key = f"{current_main_nutrient} - {key}"
                else:
                    current_main_nutrient = key

                nutrition_string += f"{key}:\n"
                for size, value in zip(serving_sizes, values):
                    nutrition_info[size][key] = value
                    nutrition_string += f"  {size} - {value}\n"
                nutrition_string += "\n"
        Nutr_label = nutrition_string
    except:
        print('Nutrition Error')

    try:
        element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pdp-main-details__weight"))
        )
        Unitpp = element.text.strip()
    except:
        print('Unitpp Error')

    try:
        image_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.asda-img.asda-image.product-detail-page__swatch-img"))
        )
        image_url = image_element.get_attribute('src')
        ProductImages = image_url
        response = requests.get(image_url)
        if response.status_code == 200:
            if not os.path.exists(f'output/images/{str(ind)}/'):
                os.makedirs(f'output/images/{str(ind)}/', exist_ok=True)
            full_path = 'output/images/' + str(ind) + '/' + str(ID) + '-' + str(index) + '.png'
            with open(full_path, 'wb') as file:
                file.write(response.content)
    except:
        print('Image Error')

    new_row = {
        'ID': ID,
        'Country': 'United Kingdom',
        'Store': 'ASDA',
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
        'ItemNum': ItemNum,
        'SKU': 'N/A',
        'UPC': UPC,
        'url': item_url,
        'DataCaptureTimeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        'Notes': Notes
    }
    return new_row
