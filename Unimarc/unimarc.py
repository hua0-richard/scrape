# Packages for scrapping
from selenium.webdriver.common.by import By
from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
# import undetected_chromedriver as uc

import time
import datetime
import pytz


def setup_unimarc(driver, EXPLICIT_WAIT_TIME, site_location_df, ind):
    address = site_location_df.loc[ind, 1]
    setLocation_unimarc(driver, address, EXPLICIT_WAIT_TIME)
    time.sleep(3)


def setLocation_unimarc(driver, address, EXPLICIT_WAIT_TIME):
    # Login
    tmp = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_all_elements_located((By.ID, 'Location'))
    )
    tmp[0].click()
    text_enter = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@name="rut"]'))
    )
    text_enter.send_keys('70674459')
    pass_enter = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='password']"))
    )
    pass_enter.send_keys('Unimarc1!')
    continue_button = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "login-step__submit-button"))
    )
    continue_button.click()
    time.sleep(5)
    # Set Location
    shop = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_element_located((By.XPATH, "//p[text()='Retiro en tienda']")))
    shop.click()

    address_split = address.split(',')
    region = address_split[len(address_split) - 1].strip()
    comuna = address_split[len(address_split) - 2].strip()

    selectors = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
        EC.visibility_of_all_elements_located((By.XPATH, '//select'))
    )

    opts1 = selectors[0].find_elements(By.XPATH, './option')
    for o in opts1:
        if o.text == region:
            o.click()
            break
        if o == opts1[len(opts1) - 1]:
            raise Exception('Region not found')

    opts2 = selectors[1].find_elements(By.XPATH, './option')
    for o in opts2:
        if o.text == comuna:
            o.click()
            break
        if o == opts2[len(opts2) - 1]:
            raise Exception('Comuna not found')
    time.sleep(1)
    opts = driver.find_elements(By.XPATH, '//input[@role="radio"]')
    opts[0].find_element(By.XPATH, './..').click()

    driver.find_element(By.XPATH, '//*[@aria-label="Confirmar tienda"]').click()
    print("Login and Location Complete")


def scrapSite_unimarc(driver, EXPLICIT_WAIT_TIME=10, idx=None, aisles=[], ind=None,
                      site_location_df=None):
    #  Setup Data
    site_items_df = pd.DataFrame(columns=['idx', 'name', 'brand', 'aisle', 'subaisle', 'subsubaisle',
                                          'size', 'price', 'multi_price',
                                          'old_price', 'pricePerUnit', 'old_pricePerUnit',
                                          'itemNum', 'description', 'serving', 'img_urls',
                                          'item_label', 'item_ingredients',
                                          'url', 'SKU', 'UPC', 'timeStamp'])

    for aisle in aisles:
        print(aisle)
        time_aisle = time.time()

        # Get aisle URL
        categories_container = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "p.Text_text__cB7NM.Categories_categories-text__Ypipt"))
        )
        categories_container.click()

        aisle_menu = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//p[contains(@class, 'Text_text__cB7NM') and text()='{aisle}']"))
        )
        actions = ActionChains(driver)
        actions.move_to_element(aisle_menu).perform()
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Link_link___5dmQ"))
        )
        category_links = driver.find_elements(By.XPATH,
                                              "//a[contains(@class, 'Link_link___5dmQ') and .//p[contains(@class, 'Categories_sublist-text__Nw0T4')]]")

        aisle_urls = []
        item_urls = []
        try:
            df = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_unimarc_urls.csv", header=None, names=['value'])
            item_urls = df['value'].tolist()
            print(item_urls)
        except Exception as e:
            print(e)
            for c in category_links:
                print(c.get_attribute('href'))
                aisle_urls.append(c.get_attribute('href'))

            for a in aisle_urls:
                driver.get(a)
                count = 2

                while (True):
                    time.sleep(10)
                    try:
                        error_message = driver.find_element(By.XPATH,
                                                            "//p[text()='Intenta seleccionando una menor cantidad de filtros para un']")
                        break
                    except:
                        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                            EC.presence_of_element_located((By.TAG_NAME, "section"))
                        )
                        containers = driver.find_element(By.TAG_NAME, "section")
                        product_pages = containers.find_elements(By.TAG_NAME, "section")
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.TAG_NAME, "a"))
                        )
                        for p in product_pages:
                            product_links = p.find_elements(By.CSS_SELECTOR,
                                                            "a.Link_link___5dmQ.Link_link--none__BjwPj")
                            for pl in product_links:
                                print(pl.get_attribute('href'))
                                print(pl.get_attribute('text'))
                                item_urls.append(pl.get_attribute('href'))
                        driver.get(f"{a}?page={count}")
                        count += 1
            pd.DataFrame(item_urls).to_csv(f"output/tmp/'index_{str(ind)}_{aisle}_unimarc_urls.csv", index=False)

        print('(Number of Items: ' + str(len(item_urls)) + ')')
        time.sleep(10)

        df_data = pd.DataFrame()
        site_items_df = pd.DataFrame()
        try:
            df_data = pd.read_csv(f"output/tmp/index_{str(ind)}_{aisle}_unimarc_data.csv")
            site_items_df = pd.concat([site_items_df, df_data], ignore_index=True).drop_duplicates()
        except:
            None

        for i in range(len(item_urls)):
            if not df_data.empty and item_urls[i] in df_data['url'].values:
                print('Item Already Exists!')
                continue
            item_url = item_urls[i]
            driver.get(item_url)

            try:
                driver.find_element(By.XPATH, '//*[@title="Error 404"]')
                continue
            except:
                None

            try:
                new_row = scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind)
            except:
                None
            site_items_df = pd.concat([site_items_df, pd.DataFrame([new_row])], ignore_index=True)
            site_items_df = site_items_df.drop_duplicates(subset=['url'], keep='last')

            if i % 10 == 0:
                site_items_df.to_csv(f"output/tmp/index_{str(ind)}_{aisle}_unimarc_data.csv", index=False)

        site_items_df.to_csv(f"output/tmp/index_{str(ind)}_{aisle}_unimarc_data.csv", index=False)

    return site_items_df


def scrape_item(driver, aisle, item_url, EXPLICIT_WAIT_TIME, ind):
    time.sleep(5)
    subaisle = ''
    subsubaisle = ''
    try:
        categories = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@data-divider='/']"))
        )
        print(categories)
        tmp_subaisle_text = categories[2].find_element(By.XPATH, './/a | .//p').get_attribute('textContent')
        tmp_subsubaisle_text = categories[3].find_element(By.XPATH, './/a | .//p').get_attribute('textContent')
        subaisle = tmp_subaisle_text
        subsubaisle = tmp_subsubaisle_text

    except Exception as e:
        print(e)

    # Top Right data
    topRight = driver.find_element(By.CLASS_NAME, 'title_title__h1__PgNtb ')
    topRight = topRight.find_element(By.XPATH, './../..')

    try:
        name = topRight.find_element(By.XPATH, './/h1[contains(@class,"title_title__h1__PgNtb ")]').text
    except:
        name = ''

    try:
        brand = topRight.find_element(By.XPATH, './/p[contains(@class,"ProductDetail_textBrand__IRQMn")]').text
    except:
        brand = None

    try:
        size = topRight.find_element(By.XPATH, './div/p[contains(@class,"Text_text--lg__GZWsa")]').text
    except:
        size = None

    try:
        SKU = topRight.find_element(By.XPATH, './div/p[contains(@class,"Text_text--xs__Snd0F")]').text.replace('Sku: ',
                                                                                                               '')
    except:
        SKU = None

    price = None
    old_price = None
    multi_price = None
    old_pricePerUnit = None
    pricePerUnit = None
    try:
        tmp = topRight.find_elements(By.XPATH, './div/div/div//*[contains(@class,"Text_text--semibold__MukSj")]')
        tmp_text = []
        for t in tmp:
            tmp_text.append(t.text)

        if len(tmp_text) > 1:
            multi_price = ' '.join(tmp_text)
        else:
            price = tmp_text[0]
    except:
        None

    try:
        tmp = topRight.find_elements(By.XPATH, './/*[contains(@class,"ListPrice_listPrice__mdFUB")]')
        pricePerUnit = tmp[0].text
        old_price = tmp[1].text
        old_pricePerUnit = tmp[2].text
    except:
        None

    itemIdx = f"{ind}_{name}"

    try:
        imgs = driver.find_element(By.CLASS_NAME, 'react-multi-carousel-track ')
        imgs = imgs.find_elements(By.XPATH, './li/picture/img')
    except:
        try:
            imgs = driver.find_element(By.XPATH, '//picture/img')
            imgs = [imgs]
        except:
            imgs = []

    img_urls = []
    for img_idx in range(len(imgs)):
        src = imgs[img_idx].get_attribute('src')
        img_urls.append(src)
        try:
            urllib.request.urlretrieve(src,
                                       'output/images/' + str(ind) + '/' + itemIdx + '_Img' + str(img_idx) + '.png')
        except:
            None

    try:
        find_tmp = driver.find_element(By.ID, 'Description')
        description = find_tmp.find_elements(By.XPATH, './../../../section')[1].text
    except:
        description = None

    try:
        find_tmp = driver.find_element(By.ID, 'Ingredients')
        item_ingredients = find_tmp.find_elements(By.XPATH, './../../../section')[1].text
    except:
        item_ingredients = None

    try:
        itemNum = None
    except:
        itemNum = None

    try:
        UPC = None
    except:
        UPC = None

    item_label = None
    serving = None
    try:
        item_label = driver.find_element(By.CLASS_NAME, 'NutritionalFactTable_expanded__F__Ww').text
        find_tmp = item_label.split('\n')

        for elem in find_tmp:
            if elem.index('Porción por envase') and size is None:
                portion = elem
            elif elem.index('Porción individual'):
                serving = elem
                if size is None:
                    size = ' x '.join([portion, elem])
    except:
        None

    print(item_label)
    new_row = {'idx': itemIdx,
               'name': name, 'brand': brand,
               'aisle': aisle, 'subaisle': subaisle,
               'subsubaisle': subsubaisle,
               'size': size, 'price': price, 'multi_price': multi_price,
               'old_price': old_price, 'pricePerUnit': pricePerUnit,
               'old_pricePerUnit': old_pricePerUnit,
               'itemNum': itemNum, 'description': description, 'serving': serving,
               'img_urls': ', '.join(img_urls), 'item_label': item_label,
               'item_ingredients': item_ingredients, 'url': item_url,
               'SKU': SKU, 'UPC': UPC,
               'timeStamp': datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()}
    print(new_row)
    return new_row
