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
GEN_TIMEOUT = 7
STORE_NAME = 'Kroger'
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
    time.sleep(GEN_TIMEOUT)
    items = []
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        items = list(set(items))
        print(items)
        print(len(items))
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

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ImageNav a.kds-Link"))
            )
            link_elements = driver.find_elements(By.CSS_SELECTOR, "div.ImageNav a.kds-Link")
            store_aisles = []
            for element in link_elements:
                href = element.get_attribute('href')
                if href and href not in store_aisles:
                    store_aisles.append(href)
        except Exception as e:
            print('failed getting links')
            print(e)

        # aisle links fix
        if aisle == 'Beverages':
            store_aisles.append(f'{base_url}pl/energy-drinks/04011')
            store_aisles.append(f'{base_url}pl/sports-drinks/04005')

        for s in store_aisles:
            driver.get(s)
            flag = True
            counter = 0
            while flag:
                for ty in range(3):
                    try:
                        time.sleep(2)
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
                        counter = counter + 1
                        break
                    except:
                        print(f'Failed. Trying Again... Attempt {x}')
                        if (x == 1):
                            flag = False
                            break
            print('No More items to scroll... ')
            try:
                product_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.AutoGrid"))
                )
                link_elements = driver.find_elements(By.CSS_SELECTOR, "a.ProductDescription-truncated")
                links = [elem.get_attribute('href') for elem in link_elements if elem.get_attribute('href')]

                # Add base_url if necessary and extend items list
                full_links = [base_url + link if not link.startswith('http') else link for link in links]
                items.extend(full_links)
                items = list(set(items))
                print(items)
                print(len(items))
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
        print(df_data)
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
        element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
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
        ingredients_p = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
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
        upc_span = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
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

    # Nutrition Label
    try:
        # Wait for the nutrition facts container to be present
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
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
        nav_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "kds-Breadcrumb"))
        )
        elements = nav_element.find_elements(By.CSS_SELECTOR, "a, span.kds-Text--l")
        breadcrumb_text = [element.text.strip() for element in elements if element.text.strip()]
        if (len(breadcrumb_text) > 0):
            ProductSubCategory = breadcrumb_text.pop()
        if (len(breadcrumb_text) > 0):
            ProductCategory = breadcrumb_text.pop()
    except:
        print('Category Error')

    try:
        wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
        image = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.ProductImages-image")))
        ProductImages = image.get_attribute("src")
    except:
        print('Image Error')

    try:
        flag_unitpp = False
        span_element = wait.until(EC.presence_of_element_located((By.ID, "ProductDetails-sellBy-unit")))
        unit_text = span_element.text

        unit_text = unit_text.split('/')

        for i in range(len(unit_text)):
            unit_text[i] = unit_text[i].strip()
        if (len(unit_text) > 1):
            Unitpp = unit_text[0]
            unit_text.pop(0)
            flag_unitpp = True
            Packsize_org = Unitpp
        else:
            Unitpp = 1
        Containersize_org = unit_text[0]
        Containersize_val = Containersize_org
        tmp = Containersize_org
        pattern = r'\b\d+(?:\.\d+)?\b|\b[a-zA-Z]+\b'
        matches = re.findall(pattern, tmp)
        numbers = [match for match in matches if re.match(r'\d', match)]
        words = [match for match in matches if re.match(r'[a-zA-Z]', match)]
        Containersize_unit =  ', '.join(str(x) for x in words)
        Containersize_val =  ', '.join(str(x) for x in numbers)

        if flag_unitpp:
            matches = re.findall(pattern, Unitpp)
            numbers = [match for match in matches if re.match(r'\d', match)]

            Netcontent_org = int(round(float(numbers) * round(float(Containersize_val))))
        else:
            Netcontent_org = Containersize_val
        Netcontent_val = Netcontent_org
        Netcontent_unit = Containersize_unit
    except Exception as e:
        print('Unit Error')

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
