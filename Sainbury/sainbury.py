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
GEN_TIMEOUT = 5

def setup_sainbury(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url):
    setLocation_sainbury(driver, site_location_df.loc[ind, 1], EXPLICIT_WAIT_TIME)


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
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.top-right-links--login[data-test-id='login-register-link']"))
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

    input('Continue? [Y] / [N]')

    time.sleep(FAVNUM)



def scrapeSite_sainbury(driver, EXPLICIT_WAIT_TIME=10, idx=None, aisles=[], ind=None,
                        site_location_df=None):
    #  Setup Data
    site_items_df = pd.DataFrame(columns=['idx', 'name', 'brand', 'aisle', 'subaisle', 'subsubaisle',
                                          'size', 'price', 'multi_price',
                                          'old_price', 'pricePerUnit', 'itemNum',
                                          'description', 'serving', 'img_urls',
                                          'item_label', 'item_ingredients',
                                          'pack',
                                          'url', 'timeStamp'])


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
