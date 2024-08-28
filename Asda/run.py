from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import asda


def connect_to_existing_chrome(address, ind):
    print('Start')
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        current_url = driver.current_url
        print(f"Connected to Chrome. Current URL: {current_url}")
        print(f"Page title: {driver.title}")
        # asda.setLocation_asda(driver, address, 10)
        asda.scrapeSite_asda(driver, EXPLICIT_WAIT_TIME = 10, aisle='Drinks', ind = ind)
    except Exception as e:
        print(f"An error occurred: {e}")


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
        connect_to_existing_chrome(scrape_location, ind)


if __name__ == '__main__':
    res = main()
