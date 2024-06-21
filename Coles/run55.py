# Packages for scrapping
from selenium import webdriver
import undetected_chromedriver as uc
import pandas as pd

import time
import os 

# Load store file
import coles


def main():
    # Import file of locations
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)
    
    # General Vars
    EXPLICIT_WAIT_TIME = 30

    for ind in [55]:
        print('\nIndex: ',ind)
        try:
            os.mkdir('output/images/'+str(ind)) 
        except:
            None
        driver = uc.Chrome()
        driver.maximize_window()
        
        url = site_location_df.loc[ind,0]
        driver.get(url)
        
        try:
            coles.setup_coles(driver, EXPLICIT_WAIT_TIME, site_location_df, ind)
        except:
            driver.close()
            driver = uc.Chrome()
            driver.maximize_window()
            
            url = site_location_df.loc[ind,0]
            driver.get(url)
            try:
                coles.setup_coles(driver, EXPLICIT_WAIT_TIME, site_location_df, ind)
            except:
                time.sleep(5)
                coles.setup_coles(driver, EXPLICIT_WAIT_TIME, site_location_df, ind)
            
        
        new_data = coles.scrapSite_coles(driver, EXPLICIT_WAIT_TIME,idx='Coles',
                                            aisles=['Dairy, Eggs & Fridge'], ind=ind)
                                            
        new_data['store'] = '3'
        
        
        new_data.to_csv('output/ind'+str(ind)+'aisle-Dairy.csv', index = False)
        
if __name__ == '__main__':
    res = main()