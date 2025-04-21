import requests
import json
import math
import logging,time
from staging_table_creation import checked_staging_table, create_staging_table, dump_device_data_to_staging
from Database_connection_Utils import connect_and_create_schemas

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

db_connection = connect_and_create_schemas()
cur = db_connection.cursor()

BASE_URL = "http://127.0.0.1:8000"
DEVICES_ENDPOINT = "/devices"
DEFAULT_PAGE_SIZE = 501 # Use the default page size from your API


def read_paginated_devices(page=1, page_size=DEFAULT_PAGE_SIZE):
    """
    Reads paginated data from the /devices endpoint for a specific page.
    """
    url = f"{BASE_URL}{DEVICES_ENDPOINT}"
    params = {'page': page, 'page_size': page_size}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error reading page {page}: {e}")
        return None


if __name__ == "__main__":
    print("Automatically reading all pages:")

    first_page_data = read_paginated_devices(page=1)
    print(first_page_data)
    if first_page_data:
        total_devices = first_page_data.get('total', 0)
        page_size = first_page_data.get('page_size', DEFAULT_PAGE_SIZE)
        total_pages = math.ceil(total_devices / page_size) if page_size > 0 else 1

        print(f"Total devices: {total_devices}, Page size: {page_size}, Total pages: {total_pages}")

        for page_num in range(1, total_pages + 1):
            print(f"\n--- Page {page_num} ---")
            page_data = read_paginated_devices(page=page_num, page_size=page_size)
            if page_data and 'response' in page_data:
                time.sleep(20)
                dump_device_data_to_staging(page_data['response'])  # Call the dumping function
            elif page_data:
                print("No 'response' key found on this page.")
            else:
                print(f"Failed to read page {page_num}.")
    else:
        print("Failed to read the first page to determine the total number of pages.")
