import pandas as pd
import requests
import zipfile
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import os
import shutil

# Define data URLs
WORLD_BANK_URL = 'https://api.worldbank.org/v2/en/indicator/EN.ATM.CO2E.KT?downloadformat=csv'
GLOBAL_CARBON_ATLAS_URL = 'https://carbon-atlas-emissions.wedodata.dev/index.php?lang=en#'

# Determine script and base folders
SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
BASE_FOLDER = os.path.dirname(os.path.dirname(SCRIPT_FOLDER))

# Define download directories
DOWNLOAD_DIR = os.path.join(BASE_FOLDER, "made/data")
DEFAULT_DOWNLOAD_DIR = os.path.join(BASE_FOLDER, "made/data")

# Ensure download directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

# Function to download and read CSV data from a URL
def download_csv_data(url, encoding='latin1'):
    response = requests.get(url)
    if response.status_code == 200:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        csv_filename = "API_EN.ATM.CO2E.KT_DS2_en_csv_v2_145183.csv"
        with zip_file.open(csv_filename) as csvfile:
            data = pd.read_csv(csvfile, skiprows=4, encoding=encoding)
            return data
    else:
        print(f"Failed to download data from {url}")
        return None

# Function to download Global Carbon Atlas data using Selenium
def download_global_carbon_data(url, download_dir, default_download_dir):
    print(f"DEFAULT_DOWNLOAD_DIR {DEFAULT_DOWNLOAD_DIR}")
    options = Options()
    options.headless = False  # Run in headless mode
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", default_download_dir)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    geckodriver_path = GeckoDriverManager().install()
    driver = webdriver.Firefox(executable_path=geckodriver_path, options=options, firefox_profile=profile)
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 30)
        download_button = wait.until(EC.element_to_be_clickable((By.ID, 'misc_download')))
        time.sleep(10)
        print("Download button located, clicking it now.")
        driver.execute_script("arguments[0].click();", download_button)  # Use JavaScript to click the button

        # Wait for the loading spinner to disappear
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.spinner')))

        time.sleep(10)
        # Wait for the "Download Dataset" button to be clickable
        dataset_download_button = wait.until(EC.element_to_be_clickable((By.ID, 'download_dataset')))
        print("Download Dataset button located, clicking it now.")
        driver.execute_script("arguments[0].click();", dataset_download_button)  # Use JavaScript to click the button

        # Wait for the download to complete
        time.sleep(20)
    except Exception as e:
        print(f"Error locating or clicking the download link: {e}")
    finally:
        driver.quit()

    # Find the downloaded file in the default download directory
    for file_name in os.listdir(default_download_dir):
        if file_name.endswith('export_emissions.csv'):
            source_path = os.path.join(default_download_dir, file_name)
            destination_path = os.path.join(download_dir, file_name)
            shutil.move(source_path, destination_path)
            return destination_path

    return None

# Function to read the local CSV file
def read_local_csv(file_path, encoding='latin1'):
    data = pd.read_csv(file_path, skiprows=4, encoding=encoding)
    return data

# Function to delete existing files in the download directory
def clear_download_directory(download_dir):
    for file_name in os.listdir(download_dir):
        file_path = os.path.join(download_dir, file_name)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

# Function to process World Bank data
def process_world_bank_data(url):
    data = download_csv_data(url)
    if data is not None:
        data = data.drop(columns=['Indicator Name', 'Indicator Code', 'Unnamed: 68'], errors='ignore')
        data = data.melt(id_vars=["Country Name", "Country Code"], var_name="Year", value_name="CO2 Emissions")
        data['Year'] = data['Year'].astype(int)
        data = data.dropna(subset=['CO2 Emissions'])
        data.to_csv(os.path.join(DOWNLOAD_DIR, 'cleaned_world_bank_data.csv'), index=False)
        print("World Bank data processed and saved.")
    else:
        print("World Bank data could not be processed.")

# Function to process Global Carbon Atlas data
def process_global_carbon_data(url, download_dir, default_download_dir):
    file_path = download_global_carbon_data(url, download_dir, default_download_dir)
    print(f"file_path 2{file_path}")
    if file_path is not None:
        data = pd.read_csv(file_path, encoding='latin1')
        column_names = data.iloc[0].values
        data = data[1:]  # Remove the first row
        data.columns = column_names

        data.rename(columns={column_names[0]: 'Year'}, inplace=True)
        data = data.melt(id_vars=["Year"], var_name="Country", value_name="CO2 Emissions")

        data = data.dropna(subset=['Year'])
        data = data[pd.to_numeric(data['Year'], errors='coerce').notnull()]
        data['Year'] = data['Year'].astype(int)
        data['CO2 Emissions'] = pd.to_numeric(data['CO2 Emissions'], errors='coerce')
        data = data.dropna(subset=['CO2 Emissions'])

        data.to_csv(os.path.join(download_dir, 'cleaned_global_carbon_data.csv'), index=False)
        print("Global Carbon Atlas data processed and saved.")
        
        # Delete the file from the default download directory
        os.remove(file_path)
    else:
        print("Global Carbon Atlas data could not be processed.")

def main():
    # Clear the download directory
    clear_download_directory(DOWNLOAD_DIR)
    clear_download_directory(DEFAULT_DOWNLOAD_DIR)

    # Process World Bank data
    process_world_bank_data(WORLD_BANK_URL)

    # Process Global Carbon Atlas data
    process_global_carbon_data(GLOBAL_CARBON_ATLAS_URL, DOWNLOAD_DIR, DEFAULT_DOWNLOAD_DIR)

if __name__ == "__main__":
    main()

