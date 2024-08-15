from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import datetime
import pytz
import re

FAVNUM = 22222

def setup_kroger(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_kroger(driver, site_location_df.loc[ind, 1], EXPLICIT_WAIT_TIME)


def setLocation_kroger(driver, address, EXPLICIT_WAIT_TIME):
    None
    print('Set Location Complete')


def scrapeSite_kroger(driver, EXPLICIT_WAIT_TIME=10, idx=None, aisles=[], ind=None,
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
        None
        # site_items_df.to_csv(f'output/tmp/index_{str(ind)}_{aisle}_soriana_data.csv', index=False)


def scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind, index):
    itemIdx = None
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
    img_urls = None
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


def getItem_urls(driver, EXPLICIT_WAIT_TIME):
    None

