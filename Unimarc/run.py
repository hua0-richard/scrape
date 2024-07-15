from selenium import webdriver as uc
import pandas as pd
import time
import unimarc as bot
#import undetected_chromedriver as uc


def main():
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)
    EXPLICIT_WAIT_TIME = 45

    for ind in [41,42,43,44]:
        print('\nIndex: ',ind)
        driver = uc.Chrome()
        driver.maximize_window()
        url = site_location_df.loc[ind,0]
        driver.get(url)

        try:
            bot.setup_unimarc(driver, EXPLICIT_WAIT_TIME, site_location_df, ind)
        except Exception as e:
            print("Error")
            print(e)
            return

        new_data = bot.scrapSite_unimarc(driver, EXPLICIT_WAIT_TIME,idx='Unimarc',
                                            aisles=['Bebidas y Licores'], ind=ind)

        new_data['store'] = 'unimarc'

if __name__ == '__main__':
    res = main()
