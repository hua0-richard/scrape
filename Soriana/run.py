# Packages for scrapping
#import undetected_chromedriver as uc
import pandas as pd
from selenium import webdriver as uc
import os
import soriana


def main():
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)
    EXPLICIT_WAIT_TIME = 30

    for ind in [30,31,32,33]:
        print('\nIndex: ',ind)
        try:
            os.mkdir('output/images/'+str(ind)) 
        except:
            None
        driver_options = uc.chrome.options.Options()
        driver_options.add_argument("--disable-notifications")
        driver_options.add_argument("--disable-infobars")
        driver_options.add_argument("--disable-extensions")
        driver = uc.Chrome(driver_options)
        driver.maximize_window()
        
        url = site_location_df.loc[ind,0]
        driver.get(url)
        
        soriana.setup_soriana(driver, EXPLICIT_WAIT_TIME, site_location_df, ind, url)

        soriana.scrapeSite_soriana(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisles=['Jugos y bebidas'], ind=ind)
        print('Done!')
        soriana.scrapeSite_soriana(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisles=['Lácteos y huevo'], ind=ind)
        print('Done!')
        soriana.scrapeSite_soriana(driver, EXPLICIT_WAIT_TIME, idx=str(ind), aisles=['Vinos, licores y cervezas'])
        print('Done!')

if __name__ == '__main__':
    res = main()