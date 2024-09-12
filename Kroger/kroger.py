import glob
import os
import re

import requests
import pandas as pd
import time
import datetime
import pytz
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import bs4

FAVNUM = 22222
GEN_TIMEOUT = 6
STORE_NAME = 'target'
LOCATION = ''
MAX_RETRY = 10
def nutrient_dict_to_string(nutrient_dict):
    result = []
    result.append("Nutrition Facts")
    result.append(f"Servings per container: {nutrient_dict['Servings per container']}")
    result.append(f"Serving size: {nutrient_dict['Serving size']}")
    result.append(f"Calories: {nutrient_dict['Calories']}")
    result.append("\nNutrient Information:")

    for nutrient, info in nutrient_dict.items():
        if nutrient not in ['Servings per container', 'Serving size', 'Calories']:
            result.append(f"{nutrient}:")
            result.append(f"  Amount: {info['Amount']}")
            result.append(f"  Daily Value: {info['Daily Value']}")

    return "\n".join(result)

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


def setup_kroger(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_kroger(driver, site_location_df.loc[ind - 1, 1], EXPLICIT_WAIT_TIME)


def setLocation_kroger(driver, address, EXPLICIT_WAIT_TIME):
    input('Manually set location?')
    print('Set Location Complete')


def scrapeSite_kroger(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None, base_url=None):
    items = []
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print(items)
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')

        if aisle == 'Beverages':
            driver.get(f'{base_url}d/beverages')
        elif aisle == 'Beer, Wine & Liquor':
            driver.get(f'{base_url}d/beer-wine-liquor')
        elif aisle == 'Dairy & Eggs':
            driver.get(f'{base_url}d/dairy')
        elif aisle == 'Coffee':
            driver.get(f'{base_url}d/coffee')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ImageNav a.kds-Link"))
        )
        link_elements = driver.find_elements(By.CSS_SELECTOR, "div.ImageNav a.kds-Link")
        store_aisles = []
        for element in link_elements:
            href = element.get_attribute('href')
            if href and href not in store_aisles:
                store_aisles.append(href)

        # aisle links fix
        if aisle == 'Beverages':
            store_aisles.append(f'{base_url}/pl/energy-drinks/04011')
            store_aisles.append(f'{base_url}/pl/sports-drinks/04005')

        for s in store_aisles:
            driver.get(s)
            flag = True
            while flag:
                for ty in range(3):
                    try:
                        time.sleep(5)
                        wait = WebDriverWait(driver, 10)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)  # Give time for new content to load
                        break
                    except:
                        print('error... trying again')

                for x in range(2):
                    try:
                        time.sleep(2)
                        load_more_button = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "button.LoadMore__load-more-button"))
                        )
                        actions = ActionChains(driver)
                        actions.move_to_element(load_more_button).perform()
                        load_more_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.LoadMore__load-more-button"))
                        )
                        load_more_button.click()
                        print('More Items To Scroll')
                        break
                    except:
                        print(f'Failed. Trying Again... Attempt {x}')
                        if (x == 1):
                            flag = False
                            break
            print('No More items to scroll... ')
            try:
                product_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductGridContainer"))
                )
                link_elements = driver.find_elements(By.CSS_SELECTOR, "a.ProductDescription-truncated")
                links = [elem.get_attribute('href') for elem in link_elements if elem.get_attribute('href')]

                # Add base_url if necessary and extend items list
                full_links = [base_url + link if not link.startswith('http') else link for link in links]
                items.extend(full_links)
                print(len(items))
                print(items)
            except Exception as e:
                print('Failed!')

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

    global LOCATION
    print(LOCATION)

    # Product Name
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1.ProductDetails-header[data-testid='product-details-name']"))
        )
        ProductName = element.text
        print(f"Product name: {ProductName}")
    except Exception as e:
        print('Name Error')

    # Product Brand
    try:
        ProductBrand = ProductName.split()[0]
    except Exception as e:
        print('Brand Error')

    # Product Description
    try:
        details_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='product-details']"))
        )
        description_p = details_div.find_element(By.CSS_SELECTOR, ".RomanceDescription p")
        Description = description_p.text
        try:
            bullet_points = details_div.find_elements(By.CSS_SELECTOR, ".RomanceDescription ul li")
            for point in bullet_points:
                Description = f'{Description}\n{point.text}'
        except:
            print('No Bullet Points')
        print(Description)
    except Exception as e:
        print('Description Error')

    # Product Ingredients
    try:
        ingredients_p = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.NutritionIngredients-Ingredients"))
        )
        full_text = ingredients_p.text
        ingredients_match = re.search(r'Ingredients\s*(.+)', full_text, re.DOTALL)
        if ingredients_match:
            ingredients = ingredients_match.group(1).strip()
            ingredients = ' '.join(ingredients.split())
            print("Ingredients:")
            print(ingredients)
            Ingredients = ingredients
        else:
            print("Ingredients not found in the expected format.")
    except Exception as e:
        print("Ingredients Error")

    # UPC
    try:
        upc_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.ProductDetails-upc[data-testid='product-details-upc']"))
        )
        full_text = upc_span.text
        upc_match = re.search(r'UPC:\s*(\d+)', full_text)
        if upc_match:
            upc = upc_match.group(1)
            print(f"UPC: {upc}")
            UPC = upc
        else:
            print("UPC not found in the expected format.")
    except Exception as e:
        print('UPC Error')

    try:
        size_label = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "label.kds-Label.kds-VariantSelectorText-groupLabel.kds-Text--m"))
        )
        full_text = size_label.text
        size_match = re.search(r'Size:\s*(\d+)\s*(\w+)', full_text)

        if size_match:
            size = size_match.group(1)
            unit = size_match.group(2)
            Netcontent_org = full_text
            Netcontent_val = size
            Netcontent_org = unit
        else:
            print("Size and unit not found in the expected format.")
    except Exception as e:
        print('Net Content Error')

    nutrition_facts = {}

    # Nutrition Label
    try:
        # Wait for the nutrition facts container to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "NutritionInfo-LabelContainer"))
        )

        # Extract nutrition information
        nutrition_dict = {}

        # Servings per container
        servings = driver.find_element(By.CLASS_NAME, 'NutritionLabel-ServingsPerContainer').text.strip()
        nutrition_dict['Servings per container'] = servings.split(' ')[0]

        # Serving size
        serving_size = driver.find_element(By.CLASS_NAME, 'NutritionLabel-ServingSize').text.strip()
        nutrition_dict['Serving size'] = serving_size.split('Serving size')[-1].strip()

        # Calories
        calories = driver.find_element(By.CLASS_NAME, 'NutritionLabel-Calories').find_elements(By.TAG_NAME, 'span')[
            -1].text
        nutrition_dict['Calories'] = calories

        # Nutrients
        nutrients = driver.find_elements(By.CLASS_NAME, 'NutrientDetail')
        for nutrient in nutrients:
            title = nutrient.find_element(By.CLASS_NAME, 'NutrientDetail-Title').text.strip()
            amount = nutrient.find_element(By.CLASS_NAME, 'NutrientDetail-TitleAndAmount').text.split(title)[-1].strip()
            try:
                daily_value = nutrient.find_element(By.CLASS_NAME, 'NutrientDetail-DailyValue').text
            except:
                daily_value = 'N/A'

            nutrition_dict[title] = {
                'Amount': amount,
                'Daily Value': daily_value
            }
        print(nutrition_dict)
        Nutr_label = nutrient_dict_to_string(nutrition_dict)

        try:
            Servsize_portion_org = nutrition_dict['Serving size']
            pattern = r'\b\d+(?:\.\d+)?\b|\b[a-zA-Z]+\b'
            matches = re.findall(pattern, Servsize_portion_org)
            numbers = [float(match) for match in matches if match[0].isdigit()]
            words = [match for match in matches if match[0].isalpha()]
            Servsize_portion_val = ', '.join(str(x) for x in numbers)
            Servsize_portion_unit = ', '.join(str(x) for x in words)
        except:
            print('No Serving Size')

        try:
            Cals_org_pp = nutrition_dict['Calories']
            Cals_unit_pp = 'Calories'
            Cals_value_pp = Cals_org_pp
        except:
            print('No Calories')

        try:
            try:
                TotalSugars_g_pp = nutrition_dict['Sugar']['Amount']
            except:
                print('Total Sugar Error')
            try:
                TotalSugars_pct_pp = nutrition_dict['Sugar']['Daily Value']
            except:
                print('Total Sugar Daily Error')
            try:
                AddedSugars_g_pp = nutrition_dict['Added Sugar']['Amount']
            except:
                print('Added Sugar Error')
            try:
                AddedSugars_pct_pp = nutrition_dict['Added Sugar']['Daily Value']
            except:
                print('Added Sugar Daily Error')
        except:
            print('No Sugar')

        try:
            try:
                TotalCarb_g_pp = nutrition_dict['Total Carbohydrate']['Amount']
            except:
                print('No Total Carb')
            try:
                TotalCarb_pct_pp = nutrition_dict['Total Carbohydrate']['Daily Value']
            except:
                print('No Daily Total Carb')
        except:
            print('No Carb')

        try:
            Servings_cont = nutrition_dict['Servings per container']
        except:
            print('No Serving Sizes Per Container')

    except:
        print('Nutrition Label Error')

    try:
        nav_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "kds-Breadcrumb"))
        )
        elements = nav_element.find_elements(By.CSS_SELECTOR, "a, span.kds-Text--l")
        breadcrumb_text = [element.text.strip() for element in elements if element.text.strip()]
        breadcrumb_text.pop()
        if (len(breadcrumb_text) > 0):
            ProductSubCategory = breadcrumb_text.pop()
        if (len(breadcrumb_text) > 0):
            ProductCategory = breadcrumb_text.pop()
    except:
        print('Category Error')

    try:
        wait = WebDriverWait(driver, 10)
        image = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.ProductImages-image")))
        ProductImages = image.get_attribute("src")
    except:
        print('Image Error')

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"span#ProductDetails-sellBy-unit.kds-Text--l.mr-8.text-primary.ProductDetails-sellBy"))
        )
        Unitpp = element.text
    except Exception as e:
        print('Unit Error')

    new_row = {
        'ID': ID,
        'Country': 'United States',
        'Store': 'Kroger',
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
    return new_row
