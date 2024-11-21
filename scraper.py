# ------------------ Imports
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from seleniumbase import Driver

# ------------------ Events Data
hyrox_events = pd.read_csv("data/hyrox_events.csv")

# ------------------ Helper Functions
def select_helper(select_name, option, driver):
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.NAME, select_name)))
    select = Select(element)
    select.select_by_visible_text(option)


def get_athlete_table(driver):
    # Create an empty DataFrame
    df = pd.DataFrame(columns=["desc", "time_day", "time", "diff", "fullname", "age_class", "start_no"])

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the table
    table = soup.select_one('table.table-condensed.table-striped')

    # Extract the rows from the table body
    rows = table.tbody.find_all('tr')

    # Find additional information
    fullname = soup.find("td", class_="f-__fullname last").get_text(strip=True)
    try:
        age_class = soup.find("td", class_="f-_type_age_class last").get_text(strip=True)
    except:
        age_class = "_NONE_"
    try:
        start_no = soup.find("td", class_="f-start_no_text last").get_text(strip=True)
    except:
        start_no = "_NONE_"

    # Loop through each row
    all_rows = []
    for row in rows:
        # Extract the cells from the row
        cells = row.find_all('td')

        # Extract the description from the row header
        desc = row.find('th').get_text(strip=True)

        # Extract the time of day, time, and diff from the cells
        if len(cells) == 3:
            time_day = cells[0].get_text(strip=True)
            time = cells[1].get_text(strip=True)
            diff = cells[2].get_text(strip=True)
        if len(cells) == 2:
            time_day = "_NONE_"
            time = cells[0].get_text(strip=True)
            diff = cells[1].get_text(strip=True)

        # Create a dictionary with the row data
        row_data = pd.DataFrame({
            "desc": [desc], 
            "time_day": [time_day], 
            "time": [time], 
            "diff": [diff], 
            "fullname": [fullname], 
            "age_class": [age_class], 
            "start_no": [start_no]
        })
        all_rows.append(row_data)

    # Create final df
    df = pd.concat(all_rows, axis=0,ignore_index=True)
    return df


def scrape_page(all_athlete_list, driver):
    # Scrape name pages
    count = len(driver.find_elements(By.CSS_SELECTOR, "h4.list-field.type-fullname"))
    print(f"Athletes found: {count}")
    index = 0
    while index < count:
        # Fetch the list of h4 elements on each iteration
        h4_elements = driver.find_elements(By.CSS_SELECTOR, "h4.list-field.type-fullname")
        
        # Click on the h4 element at the current index
        link = h4_elements[index].find_element(By.TAG_NAME, 'a')
        link.click()
        time.sleep(.5)
        athlete_df = get_athlete_table(driver)
        all_athlete_list.append(athlete_df)
        # Go back to the previous page
        driver.back()
        # Increment the index
        index += 1
    return all_athlete_list


def main(config, write=True):
    # Start driver
    driver = Driver(uc=True)
    driver.get(config["hyrox_path"])
    time.sleep(2)
    # Get config selections
    select_helper("event_main_group", config["city"], driver)
    time.sleep(2)
    select_helper("event", config["event"], driver)
    time.sleep(.5)
    select_helper("search[sex]", config["gender"], driver)
    time.sleep(.5)
    select_helper("num_results", config["results"], driver)
    time.sleep(.5)
    submit_button = driver.find_element(By.ID, "default-submit")
    time.sleep(2)
    submit_button.click()
    time.sleep(2)

    all_athlete_list = []
    page = 1
    cont = True
    # Scrape all pages with selection
    while page < 30:
        print(f"page: {page}")
        if page == 1:
            all_athlete_list = scrape_page(all_athlete_list, driver)
            page += 1
        elif page == 2:
            try:
                next_page_button = driver.find_element(By.CSS_SELECTOR, "li.pages-nav-button a:not([disabled])")
                next_page_button.click()
                time.sleep(1.25)
                all_athlete_list = scrape_page(all_athlete_list, driver)
                page+=1
            except:
                page+=1
        else:
            try:
                # Get the current URL
                current_url = driver.current_url
                print(current_url)
                # Regex to find the 'page=x' part of the URL and replace it with the new page number
                new_page_number = f"page={page}"
                if "page=" in current_url:
                    # If 'page=' is already in the URL, replace it with the new page number
                    new_url = re.sub(r"page=\d+", new_page_number, current_url)
                    print(new_url)
                else:
                    # If 'page=' is not in the URL, add it
                    new_url = current_url + f"&{new_page_number}"
                # Navigate to the new URL
                driver.get(new_url)
                time.sleep(1.25)  # Adjust delay as needed
                # Scrape the new page
                all_athlete_list = scrape_page(all_athlete_list, driver)
                # Increment page number
                page += 1
            except Exception as e:
                print(f"Stopped on page {page} due to error: {e}")
                page = 30
            
    # Create and export csv
    all_athlete_df = pd.concat(all_athlete_list, axis=0, ignore_index=True)
    all_athlete_df["event_id"] = config["city"] + "_" + config["event"] + "_" + config["gender"]
    all_athlete_df["season"] = config["season"]
    if write:
        all_athlete_df.to_csv(config["export_path"], mode=config["mode"], index=False, header=False)
    else:
        return all_athlete_df
    driver.close()


# ------------------ Scraping Functions
def scrape_multiple_events(
    df,
    division,
    gender,
    season="2023-2024",
    mode="a",
    results_url="https://results.hyrox.com/season-6/&lang=EN_CAP"
):

    if division == "pro":
        event = "HYROX PRO"
        export_path = f"data/hyrox_results_pro.csv"
    if division == "pro-all":
        event = "HYROX PRO - Overall"
        export_path = f"data/hyrox_results_pro.csv"
    if "ELITE" in division:
        event = division
        export_path = f"data/hyrox_results_pro.csv"
    if division == "open":
        event = "HYROX"
        export_path = f"data/hyrox_results_{division}_{gender}.csv"
    if division == "doubles":
        event = "HYROX DOUBLES"
        export_path = f"data/hyrox_results_{division}_{gender}.csv"
    if division == "pro doubles":
        event = "HYROX PRO DOUBLES"
        export_path = f"data/hyrox_results_{division}_{gender}.csv"

    for i in df.index:
        event_name = df.iat[i,0]
        config = {
            "city": event_name,
            "event": event,
            "gender": gender,
            "results": "100",
            "season": season,
            "hyrox_path": results_url,
            "mode": mode, # 'a' or 'w'
            "export_path": export_path
        }
        print(f"Scraping: {config}")
        main(config)


def scrape_single_event_all_divisions(
    city,
    season="2023-2024",
    mode="a",
    results_url="https://results.hyrox.com/season-6/&lang=EN_CAP",
    write_results=True
):

    divisions = {
        "Pro Men": {"name": "HYROX PRO", "gender": "Men", "file": "data/hyrox_results_pro.csv"},
        "Pro Women": {"name": "HYROX PRO", "gender": "Women", "file": "data/hyrox_results_pro.csv"},
        "Elite Men": {"name": "HYROX ELITE", "gender": "Men", "file": "data/hyrox_results_pro.csv"},
        "Elite Women": {"name": "HYROX ELITE", "gender": "Women", "file": "data/hyrox_results_pro.csv"},
        "Open Men": {"name": "HYROX", "gender": "Men", "file": "data/hyrox_results_open_Men.csv"},
        "Open Women": {"name": "HYROX", "gender": "Women", "file": "data/hyrox_results_open_Women.csv"},
    }

    for key, value in divisions.items():
        config = {
            "city": city,
            "event": value["name"],
            "gender": value["gender"],
            "results": "100",
            "season": season,
            "hyrox_path": results_url,
            "mode": mode, # 'a' or 'w'
            "export_path": value["file"]
        }
        print(f"Scraping: {config}")
        #main(config, write=write_results)

# ------------------ Process

event_list = [
    "2024 Amsterdam"
]
scrape_events = hyrox_events[hyrox_events["Event Name"].isin(event_list)].reset_index(drop=True)

scrape_multiple_events(
    scrape_events,
    "HYROX ELITE - Thursday",
    "Men",
    season="2024-2025",
    mode="a",
    results_url="https://results.hyrox.com/season-7/&lang=EN_CAP"
)

#scrape_multiple_events(
#    scrape_events,
#    "pro",
#    "Women",
#    season="2023-2024",
#    mode="a",
#    results_url="https://results.hyrox.com/season-6/&lang=EN_CAP"
#)