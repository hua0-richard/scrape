# Packages for scrapping
#import undetected_chromedriver as uc
import time

import pandas as pd
from selenium import webdriver as uc
import os
import sainsbury


def main():
    EXPLICIT_WAIT_TIME = 10
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)

    # for _ in [65, 66, 67, 68]:
    #     ind = _
    #     print('\nIndex: ', ind)
    #     url = site_location_df.loc[ind, 0]
    #     scrape_location = site_location_df.loc[ind, 1]
    #     scrape_country = site_location_df.loc[ind, 2]
    #     scrape_store = site_location_df.loc[ind, 3]
    #     print(url)
    #     print(scrape_location)
    #     print(scrape_country)
    #     print(scrape_store)
    #     ind = _ + 1
    #
    #     driver_options = uc.chrome.options.Options()
    #     driver_options.add_argument("--disable-notifications")
    #     driver_options.add_argument("--disable-infobars")
    #     driver_options.add_argument("--disable-extensions")
    #     driver = uc.Chrome(driver_options)
    #     driver.maximize_window()
    #
    #     driver.get(url)
    #
    #     sainsbury.setup_sainbury(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)
    #     sainsbury.scrapeSite_sainbury(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisle='Drinks',ind=ind)
    #
    #     driver.quit()

    for _ in [65, 66, 67, 68]:
        ind = _
        print('\nIndex: ', ind)
        url = site_location_df.loc[ind, 0]
        scrape_location = site_location_df.loc[ind, 1]
        scrape_country = site_location_df.loc[ind, 2]
        scrape_store = site_location_df.loc[ind, 3]
        print(url)
        print(scrape_location)
        print(scrape_country)
        print(scrape_store)
        ind = _ + 1

        driver_options = uc.chrome.options.Options()
        driver_options.add_argument("--disable-notifications")
        driver_options.add_argument("--disable-infobars")
        driver_options.add_argument("--disable-extensions")
        driver = uc.Chrome(driver_options)
        driver.maximize_window()

        driver.get(url)

        sainsbury.setup_sainbury(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)
        sainsbury.scrapeSite_sainbury(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisle='Dairy, eggs & chilled',ind=ind)

if __name__ == '__main__':
    res = main()
