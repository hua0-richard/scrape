import pandas as pd
import logging
import os
import math
from util import headings
from specific.unimarc import unimarc as m
import sys

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)] %(message)s')


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def process_data(dat):
    clean_dat = headings.clean_dat
    if not m.preprocess(clean_dat).columns.empty:
        print("REMOVED CITY REGION STORE")
        clean_dat = m.preprocess(clean_dat)

    # set all columns to None
    for col in clean_dat:
        clean_dat[col] = None

    for item_idx in range(len(dat)):

        # progress of script
        if (item_idx % 50 == 0 or item_idx == len(dat) - 1):
            # clear_console()
            print("Progress: " + str(math.ceil(item_idx / len(dat) * 100)) + "%")

        # extract indices
        try:
            m.indices(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract country, region, city, store
        try:
            m.country(item_idx, clean_dat)
            m.region(item_idx, clean_dat)
            m.city(item_idx, clean_dat)
            m.store(item_idx, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract names
        try:
            m.name(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract brand names
        try:
            m.brand(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract aisle 
        try:
            m.aisle(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract subasile
        try:
            m.subaisle(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract subsubaisle
        try:
            m.subsubaisle(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract item num
        try:
            m.itemNum(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        # extract description
        try:
            m.description(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Description Error")
            logging.error(e)

        # extract item_label
        try:
            m.item_label(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Item Error")
            logging.error(e)

        # extract item_serving
        try:
            m.servsize_portion_org(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Item Error")
            logging.error(e)

        # extract item_ingredients
        try:
            m.item_ingredients(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Ingredients Error")
            logging.error(e)

        # extract url
        try:
            m.url(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Description Error")
            logging.error(e)

        # extract images
        try:
            m.img_urls(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Image Error")
            logging.error(e)

        # extract size
        try:
            m.size(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error("Size (container) error")
            logging.error(e)

        # extract SKU
        try:
            m.sku(item_idx, dat, clean_dat)
        except:
            logging.error("Description Error")
            logging.error(e)
        # extract UPC

        # extract time stamp
        try:
            m.time_stamp(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

        try:
            m.containersize_org(item_idx, dat, clean_dat)
        except Exception as e:
            logging.error(e)

    return clean_dat


# Read from Template
input_file_path = sys.argv[1]
output_file_name = f"{input_file_path[:-4]}_clean.csv"

try:
    site_location_df = pd.read_csv(input_file_path, encoding='utf-8')
except Exception as e:
    logging.error(e)

final_product = process_data(site_location_df)
final_product.to_csv(output_file_name, index=False, encoding='utf-8')
