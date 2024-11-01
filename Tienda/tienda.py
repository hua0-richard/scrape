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

import time
import datetime
import pytz

import random

import re

FAVNUM = 22222
GEN_TIMEOUT = 3
STORE_NAME = 'tienda'
LOCATION = ''
MAX_RETRY = 10


def extract_number_of_units(product_name):
    # Regular expression patterns
    patterns = [
        # Pattern for "NxM unit" format (e.g., 18x330ml, 6 X 2 Litre)
        r'(\d+)\s*(?:x|X)\s*\d+(?:\.\d+)?\s*(?:ml|l|litr?e?|cl|fl\.?\s*oz|oz|gal|pt|kg|g|lb)',

        # Pattern for "N pack" or "pack of N" format
        r'(\d+)(?:\s*-?\s*pack|pack\s+of\s+\d+)',

        # Pattern for "N cans/bottles" format
        r'(\d+)\s+(?:cans?|bottles?)'
    ]

    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # If no multi-pack information is found, assume it's a single unit
    return 1

def extract_serving_size(text):
    # Regular expression pattern to match serving size
    pattern = r'(?:per|each|one|a serving contains)?\s*(?:can|glass)?\s*\(?(\d+(?:\.\d+)?)\s*(ml|g)\)?'

    # Find all matches in the text
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        value = match.group(1)
        unit = match.group(2).lower()
        return {
            'serving_size_value': float(value),
            'serving_size_unit': unit
        }
    else:
        return {
            'serving_size_value': None,
            'serving_size_unit': None
        }

def extract_container_info(product_name):
    # Comprehensive list of possible units
    units = r'ml|l|litr?e?|cl|fl\.?\s*oz|oz|gal|pt|kg|g|lb'

    # Regular expression patterns
    patterns = [
        # Pattern for "NxM unit" format (e.g., 18x330ml)
        rf'(\d+\s*x\s*\d+(?:\.\d+)?)\s*({units})',

        # Pattern for single value with unit (e.g., 2L, 750ml, 1 Litre)
        rf'(\d+(?:\.\d+)?)\s*({units})',

        # Pattern for fractional values (e.g., 1/2 gallon)
        rf'(\d+/\d+)\s*({units})',

        # Pattern for value with unit and pint equivalent (e.g., 1.13L, 2 Pints)
        rf'(\d+(?:\.\d+)?)\s*({units})(?:\s*,\s*(\d+(?:\.\d+)?)\s*pints?)?'
    ]

    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            container_size = match.group(0)
            container_value = match.group(1)
            container_unit = match.group(2)

            # Standardize units
            container_unit = standardize_unit(container_unit)

            return {
                'product_name': product_name,
                'container_size': container_size,
                'container_value': container_value,
                'container_unit': container_unit
            }

    # If no match is found
    return {
        'product_name': product_name,
        'container_size': None,
        'container_value': None,
        'container_unit': None
    }

def standardize_unit(unit):
    unit = unit.lower()
    if unit in ['l', 'litr', 'litre', 'liter']:
        return 'L'
    elif unit in ['ml', 'milliliter', 'millilitre']:
        return 'ml'
    elif unit in ['kg', 'kilogram']:
        return 'kg'
    elif unit in ['g', 'gram']:
        return 'g'
    elif unit in ['oz', 'ounce']:
        return 'oz'
    elif unit in ['fl oz', 'fl. oz', 'fluid ounce']:
        return 'fl oz'
    elif unit in ['gal', 'gallon']:
        return 'gal'
    elif unit in ['pt', 'pint']:
        return 'pt'
    else:
        return unit

def parse_net_content(content):
    # Regular expression to match quantity, unit, and optional multiplier
    pattern = r'^(\d+(?:\.\d+)?)\s*x?\s*(\d+(?:\.\d+)?)?\s*([a-zA-Z]+)?\s*(e|℮)?$'

    match = re.match(pattern, content, re.IGNORECASE)

    if not match:
        return None, None  # Return None if the content doesn't match expected format

    quantity = match.group(1)
    multiplier = match.group(2)
    unit = match.group(3)

    # Calculate total quantity
    if multiplier:
        quantity = float(quantity) * float(multiplier)
    else:
        quantity = float(quantity)

    # Standardize units
    if unit:
        unit = unit.lower()
        if unit in ['l', 'litre', 'liter']:
            unit = 'L'
        elif unit == 'ml':
            quantity /= 1000
            unit = 'L'
        elif unit == 'cl':
            quantity /= 100
            unit = 'L'
        elif unit == 'g':
            unit = 'g'
        elif unit == 'kg':
            quantity *= 1000
            unit = 'g'
        elif unit in ['pint', 'pints']:
            quantity *= 0.568261
            unit = 'L'
    else:
        unit = ''  # If no unit is specified

    return round(quantity, 3), unit

def extract_pack_size(text):
    # Regular expression pattern to match "Pack size:" followed by a number and optional unit
    pattern = r"Pack size:\s*(\d+(?:\.\d+)?(?:\s*[A-Za-z]+)?)"

    # Search for the pattern in the text
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        return None

def extract_city_and_region(address):
    parts = address.split(', ')
    if len(parts) >= 3:
        city = parts[-3]
        region = parts[-2].split()[0]
        return [city, region]
    else:
        return ["Invalid", "Address"]

def format_nutrition(nutritional_info):
    result = []

    # Get the maximum width for each column
    col_widths = [max(len(str(row[i])) for row in [nutritional_info['headers']] + nutritional_info['data'])
                  for i in range(len(nutritional_info['headers']))]

    # Add headers
    header = " | ".join(h.ljust(w) for h, w in zip(nutritional_info['headers'], col_widths))
    result.append(header)

    # Add a separator line
    result.append("-" * len(header))

    # Add data rows
    for row in nutritional_info['data']:
        formatted_row = " | ".join(str(item).ljust(w) for item, w in zip(row, col_widths))
        result.append(formatted_row)

    return "\n".join(result)

def extract_info(heading, content):
    soup = BeautifulSoup(content, 'html.parser')
    h3 = soup.find('h3', string=heading)
    if h3:
        div = h3.find_next('div', class_='styled__Content-mfe-pdp__sc-1od89q4-2')
        if div:
            return div.text.strip()
    return None

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

def scrape_product_page(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index):
    # Initialize data dictionary with default values
    data = {
        'ID': f"{ind}-{aisle}-{item_index}",
        'Country': 'Mexico',
        'Store': 'Chedraui',
        'Region': None,
        'City': None,
        'ProductName': None,
        'ProductVariety': None,
        'ProductFlavor': None,
        'Unitpp': None,
        'ProductBrand': None,
        'ProductAisle': aisle,
        'ProductCategory': None,
        'ProductSubCategory': None,
        'ProductImages': None,
        'Containersize_org': None,
        'Containersize_val': None,
        'Containersize_unit': None,
        'Cals_org_pp': None,
        'Cals_value_pp': None,
        'Cals_unit_pp': None,
        'TotalCarb_g_pp': None,
        'TotalCarb_pct_pp': None,
        'TotalSugars_g_pp': None,
        'TotalSugars_pct_pp': None,
        'AddedSugars_g_pp': None,
        'AddedSugars_pct_pp': None,
        'Cals_value_p100g': None,
        'Cals_unit_p100g': None,
        'TotalCarb_g_p100g': None,
        'TotalCarb_pct_p100g': None,
        'TotalSugars_g_p100g': None,
        'TotalSugars_pct_p100g': None,
        'AddedSugars_g_p100g': None,
        'AddedSugars_pct_p100g': None,
        'Packsize_org': None,
        'Pack_type': None,
        'Netcontent_val': None,
        'Netcontent_org': None,
        'Netcontent_unit': None,
        'Price': None,
        'Description': None,
        'Nutr_label': None,
        'Ingredients': None,
        'NutrInfo_org': None,
        'Servsize_container_type_org': None,
        'Servsize_container_type_val': None,
        'Servsize_container_type_unit': None,
        'Servsize_portion_org': None,
        'Servsize_portion_val': None,
        'Servsize_portion_unit': None,
        'Servings_cont': None,
        'ProdType': 'N/A',
        'StorType': 'N/A',
        'ItemNum': 'N/A',
        'SKU': 'N/A',
        'UPC': 'N/A',
        'url': item_url,
        'DataCaptureTimeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        'Notes': None
    }

    try:
        # Navigate to URL with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(item_url)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)

        wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)

        # Safe element finding function
        def safe_find_element(by, selector, wait_time=EXPLICIT_WAIT_TIME):
            try:
                return wait.until(EC.presence_of_element_located((by, selector)))
            except:
                return None

        def safe_find_elements(by, selector):
            try:
                elements = driver.find_elements(by, selector)
                return elements if elements else []
            except:
                return []

        def safe_get_text(element):
            try:
                return element.text.strip() if element else None
            except:
                return None

        # Product Name
        # Product Name and related information extraction
        try:
            # Try multiple selectors for product name
            selectors = [
                'vtex-store-components-3-x-productBrand--global__product--name',
                'vtex-store-components-3-x-productBrand',
                'vtex-store-components-3-x-productNameContainer',
                'vtex-product-summary-2-x-brandName'
            ]

            product_name = None
            for selector in selectors:
                try:
                    element = safe_find_element(By.CLASS_NAME, selector)
                    if element:
                        product_name = safe_get_text(element)
                        if product_name:
                            # Clean up product name - remove extra spaces and duplicates
                            product_name = ' '.join(product_name.split())
                            # If name is duplicated, take first instance
                            if product_name.count(product_name.split()[0]) > 1:
                                product_name = product_name[:len(product_name) // 2].strip()
                            break
                except:
                    continue

            data['ProductName'] = product_name

            if product_name:
                # Extract flavor/variety
                try:
                    # Look for various flavor indicators
                    flavor_patterns = [
                        r'sabor\s+([^\d]+?)(?:\d|$)',  # "sabor X"
                        r'(?:sabor|gusto)\s+a\s+([^\d]+?)(?:\d|$)',  # "sabor a X"
                        r'(?:de|con)\s+([^\d]+?)(?:\d|$)'  # "de X" or "con X"
                    ]

                    for pattern in flavor_patterns:
                        flavor_match = re.search(pattern, product_name, re.IGNORECASE)
                        if flavor_match:
                            flavor = flavor_match.group(1).strip()
                            if flavor and len(flavor) > 2:  # Ensure meaningful flavor text
                                data['ProductFlavor'] = flavor
                                break
                except Exception as e:
                    print(f"Error extracting flavor: {e}")

                # Extract container size
                try:
                    # Enhanced size pattern matching
                    size_patterns = [
                        r'(\d+(?:\.\d+)?)\s*(ml|g|l|ML|G|L)',  # Standard sizes
                        r'(\d+(?:\.\d+)?)(ml|g|l|ML|G|L)',  # No space between number and unit
                        r'(\d+(?:\.\d+)?)\s*(?:mil[iíl]?litros?|gramos?|litros?)',  # Written out units
                    ]

                    for pattern in size_patterns:
                        size_match = re.search(pattern, product_name, re.IGNORECASE)
                        if size_match:
                            # Standardize the size information
                            value = size_match.group(1)
                            unit = size_match.group(2).lower()

                            # Standardize unit format
                            if unit == 'l':
                                unit = 'ml'
                                value = float(value) * 1000

                            # Store standardized values
                            data['Containersize_org'] = size_match.group(0)
                            data['Containersize_val'] = str(value)
                            data['Containersize_unit'] = unit

                            # Mirror to netcontent fields
                            data['Netcontent_org'] = data['Containersize_org']
                            data['Netcontent_val'] = data['Containersize_val']
                            data['Netcontent_unit'] = data['Containersize_unit']
                            break
                except Exception as e:
                    print(f"Error extracting container size: {e}")

            # Product Name and related information extraction
            try:
                # ... [previous product name extraction code] ...

                if product_name:
                    # Extract units per package (Unitpp)
                    try:
                        # Patterns for common package quantity indicators
                        unitpp_patterns = [
                            r'(\d+)\s*(?:pack|paquete|pza|pzas|unidades|piezas|botella|botellas|lata|latas)',
                            # explicit pack sizes
                            r'(\d+)\s*(?:x|×)\s*\d+\s*(?:ml|g|l)',  # format like "6 x 355ml"
                            r'paquete\s*(?:de|con)\s*(\d+)',  # "paquete de X"
                            r'(\d+)\s*(?:en|por)\s*paquete',  # "X en paquete"
                            r'(\d+)\s*(?:ct|count|cantidad)',  # count indicators
                        ]

                        unitpp = None

                        # First check product name
                        for pattern in unitpp_patterns:
                            match = re.search(pattern, product_name, re.IGNORECASE)
                            if match:
                                unitpp = int(match.group(1))
                                break

                        # If not found in product name, check description
                        if not unitpp and data.get('Description'):
                            for pattern in unitpp_patterns:
                                match = re.search(pattern, data['Description'], re.IGNORECASE)
                                if match:
                                    unitpp = int(match.group(1))
                                    break

                        # If still not found, check if it's a single unit based on container size
                        if not unitpp and data.get('Containersize_org'):
                            # Assume it's a single unit unless proven otherwise
                            unitpp = 1

                        data['Unitpp'] = unitpp

                        # If we found multiple units, update Pack_type
                        if unitpp and unitpp > 1:
                            data['Pack_type'] = f'{unitpp}-pack'

                    except Exception as e:
                        print(f"Error extracting units per package: {e}")

                    # ... [rest of the product name section code] ...

            except Exception as e:
                print(f"Error in product name section: {e}")
                data['Notes'] = f"Error in product name section: {e}"

        except Exception as e:
            print(f"Error in product name section: {e}")
            data['Notes'] = f"Error in product name section: {e}"

        # Brand
        brand_element = safe_find_element(By.CLASS_NAME, 'vtex-store-components-3-x-productBrandName')
        data['ProductBrand'] = safe_get_text(brand_element)

        # Price
        try:
            price_element = safe_find_element(By.CLASS_NAME,
                                              'chedrauimx-frontend-applications-4-x-productPriceSellingContainerQS')
            if price_element:
                price_text = safe_get_text(price_element)
                if price_text:
                    data['Price'] = float(price_text.replace('$', '').strip().replace(',', ''))
        except:
            pass

        # Breadcrumbs
        breadcrumbs = safe_find_elements(By.CLASS_NAME, 'vtex-breadcrumb-1-x-link')
        if breadcrumbs:
            try:
                data['ProductCategory'] = safe_get_text(breadcrumbs[2]) if len(breadcrumbs) > 2 else None
                data['ProductSubCategory'] = safe_get_text(breadcrumbs[3]) if len(breadcrumbs) > 3 else None
            except:
                pass

        # Images
        images = safe_find_elements(By.CLASS_NAME, 'vtex-store-components-3-x-productImageTag')
        if images:
            try:
                data['ProductImages'] = [img.get_attribute('src') for img in images
                                         if img.get_attribute('src')]
            except:
                pass

        # Description
        description_element = safe_find_element(By.CLASS_NAME,
                                                'vtex-store-components-3-x-productDescriptionText')
        data['Description'] = safe_get_text(description_element)

        # Specifications and Nutrition Info
        specs = safe_find_elements(By.CLASS_NAME, 'vtex-product-specifications-1-x-specificationValue')
        nutr_info = []

        for spec in specs:
            try:
                spec_name = spec.get_attribute('data-specification-name')
                spec_text = safe_get_text(spec)

                if spec_text:
                    nutr_info.append(f"{spec_name}: {spec_text}")

                    if spec_name == 'Ingredientes':
                        data['Ingredients'] = spec_text
                    elif spec_name == 'Contenido energético por envase':
                        data['Cals_org_pp'] = spec_text
                        try:
                            data['Cals_value_pp'] = float(re.search(r'\d+', spec_text).group())
                            data['Cals_unit_pp'] = 'kcal'
                        except:
                            pass
                    elif spec_name == 'Carbohidratos / Hidratos de Carbono':
                        try:
                            data['TotalCarb_g_pp'] = float(re.search(r'\d+', spec_text).group())
                        except:
                            pass
                    elif spec_name == 'Azúcares Totales':
                        try:
                            data['TotalSugars_g_pp'] = float(re.search(r'\d+', spec_text).group())
                        except:
                            pass
            except:
                continue

        if nutr_info:
            data['NutrInfo_org'] = ' | '.join(nutr_info)

    except Exception as e:
        error_msg = f"Error scraping page {item_index}: {str(e)}"
        print(error_msg)
        data['Notes'] = error_msg

    # Extract serving size information
    try:
        specs = safe_find_elements(By.CLASS_NAME, 'vtex-product-specifications-1-x-specificationValue')
        for spec in specs:
            try:
                spec_name = spec.get_attribute('data-specification-name')
                spec_text = safe_get_text(spec)

                if not spec_name or not spec_text:
                    continue

                # Patterns for serving size information
                serving_patterns = {
                    'portion': [
                        r'porción(?:\s+de)?\s+(\d+(?:\.\d+)?)\s*(ml|g|oz|mL|G)',
                        r'(\d+(?:\.\d+)?)\s*(ml|g|oz|mL|G)(?:\s+por)?\s+porción',
                        r'tamaño\s+de\s+porción\s+(\d+(?:\.\d+)?)\s*(ml|g|oz|mL|G)'
                    ],
                    'container': [
                        r'(\d+(?:\.\d+)?)\s*(ml|g|oz|mL|G)\s+por\s+envase',
                        r'contenido\s+(?:total|neto)\s+(\d+(?:\.\d+)?)\s*(ml|g|oz|mL|G)'
                    ]
                }

                # Check for portion/serving size
                if 'porción' in spec_name.lower() or 'tamaño' in spec_name.lower():
                    data['Servsize_portion_org'] = spec_text

                    # Try each pattern for portion size
                    for pattern in serving_patterns['portion']:
                        match = re.search(pattern, spec_text, re.IGNORECASE)
                        if match:
                            data['Servsize_portion_val'] = match.group(1)
                            data['Servsize_portion_unit'] = match.group(2).lower()
                            break

                # Check for container type serving info
                if 'contenido' in spec_name.lower() or 'envase' in spec_name.lower():
                    None
                    # data['Servsize_container_type_org'] = spec_text

                    # Try each pattern for container size
                    for pattern in serving_patterns['container']:
                        match = re.search(pattern, spec_text, re.IGNORECASE)
                        if match:
                            data['Servsize_container_type_val'] = match.group(1)
                            data['Servsize_container_type_unit'] = match.group(2).lower()
                            break

                # Look for number of servings per container
                if 'porciones' in spec_name.lower() or 'servidas' in spec_name.lower():
                    servings_patterns = [
                        r'(\d+(?:\.\d+)?)\s*porciones',
                        r'(\d+(?:\.\d+)?)\s*servidas',
                        r'rinde\s+(\d+(?:\.\d+)?)',
                        r'aproximadamente\s+(\d+(?:\.\d+)?)'
                    ]

                    for pattern in servings_patterns:
                        match = re.search(pattern, spec_text, re.IGNORECASE)
                        if match:
                            data['Servings_cont'] = float(match.group(1))
                            break

                # If we have container and portion size but no servings count,
                # try to calculate it
                if (data['Servsize_container_type_val'] and data['Servsize_portion_val'] and
                        not data['Servings_cont'] and
                        data['Servsize_container_type_unit'] == data['Servsize_portion_unit']):
                    try:
                        container_val = float(data['Servsize_container_type_val'])
                        portion_val = float(data['Servsize_portion_val'])
                        if portion_val > 0:
                            data['Servings_cont'] = round(container_val / portion_val, 1)
                    except:
                        pass

            except Exception as e:
                print(f"Error processing serving size specification: {e}")
                continue

    except Exception as e:
        print(f"Error extracting serving size information: {e}")
        data['Notes'] = f"Error extracting serving size information: {e}"

    # Nutritional Information Extraction with safer handling
    try:
        specs = safe_find_elements(By.CLASS_NAME, 'vtex-product-specifications-1-x-specificationValue')
        nutr_info = []

        # Helper functions with better error handling
        def safe_extract_value(text):
            try:
                if not text:
                    return None
                matches = re.findall(r'(\d+(?:\.\d+)?)', text)
                if matches:
                    return float(matches[0])
                return None
            except:
                return None

        def safe_extract_percentage(text):
            try:
                if not text:
                    return None
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                return float(match.group(1)) if match else None
            except:
                return None

        # Store raw nutrition values with safety checks
        def safe_store_nutrition(text, value_field, percentage_field=None):
            if text:
                value = safe_extract_value(text)
                if value is not None:
                    data[value_field] = value
                if percentage_field:
                    pct = safe_extract_percentage(text)
                    if pct is not None:
                        data[percentage_field] = pct

        for spec in specs:
            try:
                spec_name = spec.get_attribute('data-specification-name')
                spec_text = safe_get_text(spec)

                if not spec_name or not spec_text:
                    continue

                # Keep track of all nutrition info
                nutr_info.append(f"{spec_name}: {spec_text}")

                # Standardize spec name for comparison
                spec_name_lower = spec_name.lower().strip()

                # Dictionary mapping spec names to their corresponding data fields
                nutrition_mappings = {
                    'contenido energético': {
                        'value_field': 'Cals_value_pp',
                        'org_field': 'Cals_org_pp',
                        'unit_field': 'Cals_unit_pp',
                        'unit_value': 'kcal'
                    },
                    'carbohidratos': {
                        'value_field': 'TotalCarb_g_pp',
                        'pct_field': 'TotalCarb_pct_pp'
                    },
                    'hidratos de carbono': {
                        'value_field': 'TotalCarb_g_pp',
                        'pct_field': 'TotalCarb_pct_pp'
                    },
                    'azúcares totales': {
                        'value_field': 'TotalSugars_g_pp',
                        'pct_field': 'TotalSugars_pct_pp'
                    },
                    'azúcares añadidos': {
                        'value_field': 'AddedSugars_g_pp',
                        'pct_field': 'AddedSugars_pct_pp'
                    }
                }

                # Check each mapping
                for key, fields in nutrition_mappings.items():
                    if key in spec_name_lower:
                        if 'org_field' in fields:
                            data[fields['org_field']] = spec_text
                        if 'unit_field' in fields and 'unit_value' in fields:
                            data[fields['unit_field']] = fields['unit_value']
                        safe_store_nutrition(
                            spec_text,
                            fields['value_field'],
                            fields.get('pct_field')
                        )

                # Store ingredients if found
                if 'ingredientes' in spec_name_lower:
                    data['Ingredients'] = spec_text

                # Store complete nutrition label if found
                if any(term in spec_name_lower for term in ['información nutrimental', 'nutricional', 'nutrición']):
                    data['Nutr_label'] = spec_text

            except Exception as e:
                print(f"Error processing individual nutrition spec: {e}")
                continue

        # Store all collected nutrition info
        if nutr_info:
            data['NutrInfo_org'] = ' | '.join(filter(None, nutr_info))

        # Calculate per 100g values only if we have valid serving size
        if data.get('Servsize_portion_val'):
            try:
                portion_size = float(data['Servsize_portion_val'])
                if portion_size > 0:
                    # Helper function for safe calculation
                    def safe_calculate_per_100(value_field, result_field):
                        try:
                            if data.get(value_field) is not None:
                                data[result_field] = round((data[value_field] * 100) / portion_size, 1)
                        except:
                            pass

                    # Calculate all per 100g values
                    calculations = [
                        ('Cals_value_pp', 'Cals_value_p100g'),
                        ('TotalCarb_g_pp', 'TotalCarb_g_p100g'),
                        ('TotalSugars_g_pp', 'TotalSugars_g_p100g'),
                        ('AddedSugars_g_pp', 'AddedSugars_g_p100g')
                    ]

                    for value_field, result_field in calculations:
                        if not data.get(result_field):  # Only calculate if not already present
                            safe_calculate_per_100(value_field, result_field)

                    # Copy unit if calculated calories
                    if data.get('Cals_value_p100g') and data.get('Cals_unit_pp'):
                        data['Cals_unit_p100g'] = data['Cals_unit_pp']

            except Exception as e:
                print(f"Error calculating per 100g values: {e}")

    except Exception as e:
        print(f"Error in nutrition extraction: {e}")
        if 'Notes' in data:
            data['Notes'] = f"{data['Notes']} | Error in nutrition extraction: {e}"
        else:
            data['Notes'] = f"Error in nutrition extraction: {e}"

    # Extract Referencia number
    try:
        # Try multiple selector patterns for Referencia
        reference_selectors = [
            (By.CLASS_NAME, 'vtex-product-identifier-0-x-product-identifier__value'),  # Primary selector
            (By.CLASS_NAME, 'vtex-product-identifier-0-x-value'),  # Alternative selector
        ]

        item_num = None

        for selector_type, selector in reference_selectors:
            try:
                reference_element = safe_find_element(selector_type, selector)
                if reference_element:
                    item_num = safe_get_text(reference_element)
                    if item_num:
                        # Clean up the number - remove any non-numeric characters
                        item_num = ''.join(filter(str.isdigit, item_num))
                        if item_num:  # Make sure we still have a value after cleaning
                            break
            except:
                continue

        # If we found a valid reference number, store it
        if item_num:
            data['ItemNum'] = item_num
            data['SKU'] = item_num  # Optionally also store in SKU if needed

    except Exception as e:
        print(f"Error extracting reference number: {e}")
        # Don't override the default 'N/A' value in case of error

    finally:
        # Always return data, even if incomplete
        return data
def scrapeSite_tienda(driver, EXPLICIT_WAIT_TIME, idx=None, aisle='', ind=None):
    items = []
    # check for previous items
    try:
        items = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_item_urls.csv")
        items = items.iloc[:, 0].tolist()
        print('Found Prior Items')
    except Exception as e:
        print('No Prior Items')
        driver.get('https://www.chedraui.com.mx/supermercado/bebidas')
        categories_drinks = ['https://www.chedraui.com.mx/supermercado/bebidas/jugos', 'https://www.chedraui.com.mx/supermercado/bebidas/refrescos', 'https://www.chedraui.com.mx/supermercado/bebidas/agua', 'https://www.chedraui.com.mx/supermercado/bebidas/rehidratantes-y-energizantes', 'https://www.chedraui.com.mx/supermercado/bebidas/te-y-cafe-bebibles']

        for cat in categories_drinks:
            driver.get(cat)
            try:
                for i in range(50):
                    gallery_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "gallery-layout-container"))
                    )
                    links = gallery_container.find_elements(By.TAG_NAME, "a")

                    for link in links:
                        href = link.get_attribute("href")
                        if href:
                            items.append(href)  # Append href instead of link object

                    scroll_amount = 500
                    scroll_script = f"window.scrollBy(0, {scroll_amount});"
                    driver.execute_script(scroll_script)
                    time.sleep(2)

                items = list(set(items))  # Remove duplicates after all scrolling
                print(f'items so far... {len(items)}')

            except Exception as e:
                print(f'error: {str(e)}')
            pd.DataFrame(items).to_csv(f'output/tmp/index_{str(ind)}_{aisle}_item_urls.csv', index=False, header=None, encoding='utf-8-sig')

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
                new_row = scrape_product_page(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, item_index)
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
    result = extract_city_and_region(LOCATION)
    City = result[0]
    Region = result[1]



    new_row = {
        'ID': ID,
        'Country': 'United Kingdom',
        'Store': 'Tienda',
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
    return new_row
