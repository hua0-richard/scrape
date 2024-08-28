# Packages for scrapping
from selenium import webdriver as uc
import undetected_chromedriver as uc
import pandas as pd
import asda

def main():
    EXPLICIT_WAIT_TIME = 10
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)

    for _ in [69, 70, 71, 72]:
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
        driver = uc.Chrome()
        driver.maximize_window()

        driver.get(url)

        asda.setup_asda(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)
        # asda.scrapeSite_target(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisle='Beverages', ind=ind)

        driver.quit()

if __name__ == '__main__':
    res = main()
