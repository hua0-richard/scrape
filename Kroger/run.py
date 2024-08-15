# Packages for scrapping
#import undetected_chromedriver as uc
import time

import pandas as pd
from selenium import webdriver as uc
import os
import soriana


def main():
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)
    EXPLICIT_WAIT_TIME = 30

    for z in [29, 30, 31, 32]:
        ind = z
        print('\nIndex: ', ind)
        url = site_location_df.loc[ind, 0]
        scrape_location = site_location_df.loc[ind, 1]
        scrape_country = site_location_df.loc[ind, 2]
        scrape_store = site_location_df.loc[ind, 3]
        print(url)
        print(scrape_location)
        print(scrape_country)
        print(scrape_store)
        ind = z + 1
        try:
            os.mkdir('output/images/' + str(ind))
        except:
            None
        driver_options = uc.chrome.options.Options()
        driver_options.add_argument("--disable-notifications")
        driver_options.add_argument("--disable-infobars")
        driver_options.add_argument("--disable-extensions")
        driver = uc.Chrome(driver_options)
        driver.maximize_window()

        driver.get(url)

        # soriana.setup_soriana(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)
        # soriana.scrapeSite_soriana(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisles=['Jugos y bebidas'],
        #                            ind=ind)
        soriana.setup_kroger(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)
        soriana.scrapeSite_kroger(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisles=['Lácteos y huevo'],
                                  ind=ind)
if __name__ == '__main__':
    res = main()
