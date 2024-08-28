# Packages for scrapping
import json
import random
import time
from telnetlib import EC
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.options import Options
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asda


def connect_to_existing_chrome():
    print('Start')
    # Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # Connect to the existing Chrome instance
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Get the current URL
        current_url = driver.current_url
        print(f"Connected to Chrome. Current URL: {current_url}")

        # You can now interact with the browser as usual
        # For example, let's print the page title
        print(f"Page title: {driver.title}")

        # Add more actions as needed...
        groceries_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "Groceries"))
        )
        groceries_link.click()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Don't quit the driver if you want to keep the browser open
        # driver.quit()
        pass


# Usage

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
        # driver = uc.Chrome()
        # driver.get('https://www.asda.com/account?request_origin=asda&redirect_uri=https%3A%2F%2Fwww.asda.com%2F')
        # # Split the cookie string into individual cookies
        #
        #
        # cookie = {'name': 'ADB2C.AUTH_TOKEN', 'value': 'eyJhbGciOiJSUzI1NiIsImtpZCI6Ik5ucW15VUZvMmF3M0tTRlVqdWJOYTdnVmUwSlFmaHlXbWRGN2JzTjhqZ3ciLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI4MTIxYTNkNi0zZTFjLTQ5OTItOWI0My1jMGJmNTU1MTU5ZjUiLCJpc3MiOiJodHRwczovL2ZkLWxvZ2luLXByb2QuYXNkYS51ay81MGE1NGQ1OS1mZWZmLTQ3NDYtYjE3Mi05M2NlOGI1ZTRkYmIvdjIuMC8iLCJleHAiOjE3MjQ4MTM5OTUsIm5iZiI6MTcyNDgxMjE5NSwiV01fU0VDLkFVVEhfVE9LRU4iOiJNVEF5T1RZeU1ERTR0cTZvekxwUG4zd1cwOG1hNnJ1cFVIQTREV29XcDMwTkJxUkZyQ2xHeXpuNlY2ZVlSanRzNXphcE93TmVhUk9nbDBqWSs1MGovU1lLYWUvUm1XNldFbHgxdW5nUk50cmFpQlU5NDNNVFNoREFXUUJmbUtTL3NZd1UxanJBOGdaenk5dTR2ait4bS8rWjRSL2UrRFFPT1c3N0s0cVNoUG1EQVRvcGV6M0hiMU1DZ3hGczhnMjJSS1psUFFSQTdDQXpoQ1hPNk9vS255bG15ZlJNbisyR1o5c2FzcWZxUThYTTBsd3IybXcyRmtkR2xhN2RGejNlbHhFUjdDOG8xWlU3UW9Id2lvZnJ0MjgyM2c4UzgxZDZrVUdJZmJQcFpMN25BMlJMdmx5bVpUbFlWZm5VNEMzSEdxZTZocjAxL2FtNUlZd2IrSjBrczRqdkhWbnJPWFlDd2NabW13cTd3UEZ4R2V6UmZCeFNsZmZKVFZsSUlyTG5zM2NHSmwxbHoxNTYvTVlOMHJwNElVcW9oQ0ZXT25TWTVRPT0iLCJMVCI6IjE3MjQ4MTIxOTMxNDkiLCJMQVQiOiIxNzI0ODEyMTkzMTQ5IiwidGZwIjoiYjJjXzFhX2FzZGFfcHdhX3NpZ251cF9zaWduaW4iLCJzdWIiOiJlMGQxNzM2OS05ZDQ2LTRiNGItYWRiZC01ODExZTM0ZjcyODYiLCJuZXdDdXN0b21lcklEIjoiMDAzSjcwMDAwMDdTMVh1SUFLIiwib2xkQ3VzdG9tZXJJRCI6IjhkOGU0ZDFiLTRjNjUtNDA1Ny1iYzM5LTVhZTljYmNmMzgwYyIsImVtYWlsIjoidTI4OTQ0NzhAZ21haWwuY29tIiwiZ2l2ZW5fbmFtZSI6IkJsdWUiLCJuZXdVc2VyIjpmYWxzZSwiYXpwIjoiODEyMWEzZDYtM2UxYy00OTkyLTliNDMtYzBiZjU1NTE1OWY1IiwidmVyIjoiMS4wIiwiaWF0IjoxNzI0ODEyMTk1fQ.PdM9SuluRMYLxwN_IPO4j5Pz8EaaPbvnLrBiWisT-p19KgWQ_7ExbQkf3NpaG7mDhCqmXWFRIYdkDmoYfDkoceO3HsRl7PKbgRpTENcQljPDvJkwjXTglP0zd1UfJ9DTk5QjHLD2MZxw_MMvtzVbN413TAAcYDEk5UJ4_SdDsHEy6cKXOQ7KnLMo3EDhff_vsZwiKzUDDbxzE1n4t8YdA1ZmsfAu2NzdvpJu8JESWNEP6wYi4zqnhwsHz0g0SdUeR64L_trboxt5UD07D6Co6KtzsBEgdb6BO5tBMT4JHTBHuNsqUrsw4UA7AyGL8gTs4cQ5cTN4_AcPIBN5NT-GdA'}
        # driver.add_cookie(cookie)
        # cookie = {'name': 'ADB2C.REFRESH_TOKEN', 'value': 'eyJraWQiOiJyd2xtX1hIS3c2d0ZPMWlTTjZJbjNFWXp0MXlZaEZIY1Y1cnY1NFBwWDVjIiwidmVyIjoiMS4wIiwiemlwIjoiRGVmbGF0ZSIsInNlciI6IjEuMCJ9.E_-hnqcpzwg6eOreiE9zKxFFDfbe2GY1hsAq-gD1g0FpfFM4bjuKnVTidkoRTbBN1ShZac4OPGho9USLFvAhFlRfR6qDryO4kDaw3rbNFF5eNdBUbVkqP3Fwx9qgphJDeF1ov-8xc11mkmDpx0ct3J8N8mP92bH0bxhr0-Q5uPgCYVwO5uoC7X9dnyV89wCvNGRi_hGwlZ88kvi8AZqcLhsIbu9jW_wH7tFzvm_S2SxU4bNSdtAfrkxzCgbTQuH9G3dERWaIaZkb6rkzz8nMFDL2xG_jkpQd-J4RMz_NKQxQa2VQcE21BjLk9tdljyw092TNS-8yhrqmvPMNQsdQAQ.ecq9xAZknWFJBVOM.99-0KoqjuRJDIA287dUkdJ5fxutTvqL1KjJOidr7dCkgzEVeRFHWDK3JGzU3fHRW4j6QboDi2EqSNN1w2DNOETDX3PZZ84RPiCs2IXHLrSEHQ40_JEwRmYuCehmMhyrfKKNRrDrApn-Og1S_paA1IoEYnfnI-ym8Zg7yLpIbhF-CSL8OUm0_5wbmgak_MrwDFfoyjQF1eEGukNBnZ4J1TtijqmGAspYwaGY5qhlaXvN14_JmDiSzcfD9ql50yKG4LjQCZW4hVHHKd-zj3r1MgcHchBiyja1tXZw8TEhs0CVk4tAhQf92LqQoZ1_1HLNxPBsW6bw6A-y93lQ9avCFOowRbHAsTwA64dclw-PEnthE-3G1_5rGxwqN9zGq2JTQxdGj7oPO4pT33vNKcGr8MhECiAfhmh99t96C1EfFyBOkdgeZKxgy_DyMlqOQq5rIQ5ifGhDb86iIDtt2346UkGDaWldYtqWQv-dXzPXe157f0o1hhGrfOgLJEqYYGAE0MhXT_nYaNGzapIsHHZ9vuewtzZWpmnXIMcuc84tVNjO1FT2rm1luzHN8a0uyKz6A0ac8BdgJGaIPmC9LQHVBq_jUmRR119qG_f7beLsf6EckTHy1Vnw2xKjTXkI6SCIipwkvlSXwo34MyMEZ0z4OV8TlyucbWx26KCrGx_u5uBbOrvsLKcvJdIHTM-eXs9tMsIb8TuDGe2rXenVS1yZWrOpze-6YxbvDDxetdiDghuJYy6LMvl8C5T0Br5ny10pHVhkUbd0nlzA-DJkIOwE-enkcxRh1IkyOBVmH9pmwdFEd6HR-TqCy2H0vV6c2bXWhdFlkxXv8ojxurYuJjnX0kXIasEXHADXSoMBNQxI2Y0vDfpIotFzo8UYyPYTp3FChKpaOFOh_znTWAShmZUfNzwWbA5Q_ASsyZYjB2QRqdvDcdZ_qtugRYOEeNkHLV2SpG58RoJuQdH61oN66tttqp5i5cV17_F4X9hqF1Q95Sps-l4Yb6QnN6Nfvhkc8nGO0WD4K_zkqs-43dKASS4X9vHey0fo5Vt5vRfTfQZDq1JXJn9tLRufLgq1ve1U7PTOYwiYYhMgSItoD-MB4fXgQHspMwv5CA9YxJdm0y9Xa1j57x18c0xbqEhQYrivz6PuCCEOhmZy67xbVusmRrIStzlqpxK-Nlyq4hlAauF3xPL3ONt3-rQPHI00C59eTx5c9ezxg8AvRkr0RiN7nHQGf3rL3l6w9-9QlJ8vFygfP0Pa_4sjI37-caKgEoQ6LxapNmBvjzDVKfWXgCHLoaOIZ8fmxRKqdcZHUvRF2WOedAgK-oEwrRSuETKo6BV9tgSoY3_zKLgFjlFIzQlOVmvjGyeEqtVYN_p65ZzYWQI-fK0SXkTA90rzOiz_sCNMSmqWumveSgZEH7e-ysKjm0bISo_WSJCElHGghmEzcALkQqkyhVOm4wxuLKQ.fym99A4Un5Xm-fSgbHf9PA'}
        # driver.add_cookie(cookie)
        # cookie = {'name': 'WM_SEC.AUTH_TOKEN', 'value': 'MTAyOTYyMDE4tq6ozLpPn3wW08ma6rupUHA4DWoWp30NBqRFrClGyzn6V6eYRjts5zapOwNeaROgl0jY+50j/SYKae/RmW6WElx1ungRNtraiBU943MTShDAWQBfmKS/sYwU1jrA8gZzy9u4vj+xm/+Z4R/e+DQOOU66ohoyO24GPgj6uWWdaXt+NeO85KYwvyDQ5obzddr1xI3pWIuJ9d98J9Slgk0I0tsasqfqQ8XM0lwr2mw2Fkc/KfKLJcuKSvbWX/0aD3PpJ0tmvH1FCaN9tZDh4SCrHVf/Quz/bn1sx96L61t3iNm0qfeilaVpblqz3vc/DAgfFoWIKTxZTLUSxnZVDqvh8mAPA5i6KUywPRsoYXBxb0dCgfCKh+u3bzbeDxLzV3qRBz/Rz/inSLNgkC+GfbUv6Ur1eX9YGQ0laieVMoEr348='}
        # driver.add_cookie(cookie)
        # nrba_session_value = {
        #     "custom" : {},
        #     "value": "aa4cc04b55136159",
        #     "inactiveAt": 1724815319254,
        #     "expiresAt": 1724827862649,
        #     "updatedAt": 1724813519254,
        #     "sessionReplayMode": 0,
        #     "sessionReplaySentFirstChunk": False,
        #     "sessionTraceMode": 0,
        #     "traceHarvestStarted": False
        # }
        #
        # # Convert the value to a JSON string
        # nrba_session_json = json.dumps(nrba_session_value)
        #
        # # Add the NRBA_SESSION to local storage
        # script = f"""
        # localStorage.setItem('NRBA_SESSION', '{nrba_session_json}');
        # return localStorage.getItem('NRBA_SESSION');
        # """
        #
        # # Verify cookies were added
        # all_cookies = driver.get_cookies()
        # print(f"Number of cookies added: {len(all_cookies)}")
        # driver.refresh()
        # time.sleep(9999)
        # driver.quit()

        connect_to_existing_chrome()


if __name__ == '__main__':
    res = main()
