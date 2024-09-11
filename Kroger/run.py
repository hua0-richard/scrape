import os
import kroger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

def connect_to_existing_chrome(address, ind):
    print('Start')
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        print('Attempting to connect to existing chrome... ')
        current_url = driver.current_url
        print(f"Connected to Chrome. Current URL: {current_url}")
        print(f"Page title: {driver.title}")
        kroger.setLocation_kroger(driver, address, 10)
        aisles_todo = ['Beverages', 'Beer, Wine & Liquor', 'Dairy & Eggs', 'Coffee']
        for a in aisles_todo:
            kroger.scrapeSite_kroger(driver, EXPLICIT_WAIT_TIME = 10, aisle=a, ind = ind)
    except Exception as e:
        print(f"An error occurred: {e}")
def main():
    site_location_df = pd.read_excel('urlLocations.xlsx', header=None)
    EXPLICIT_WAIT_TIME = 30

    for z in [14, 15]:
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
        connect_to_existing_chrome(scrape_location, ind)
if __name__ == '__main__':
    res = main()
