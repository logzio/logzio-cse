import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
MAIN_ACCOUNT_API_KEY = os.getenv('MAIN_ACCOUNT_API_KEY')
SUB_ACCOUNT_API_KEYS = os.getenv('SUB_ACCOUNT_API_KEYS').split(',')
BASE_URL = "https://api.logz.io/v1"

# Helper function to make API requests
def make_api_request(endpoint, api_key, method='GET', data=None, params=None):
    headers = {
        'X-API-TOKEN': api_key,
        'Content-Type': 'application/json'
    }
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, headers=headers, json=data, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)
        return None

def list_grafana_dashboards():
    """List all Grafana dashboards in the main account"""
    endpoint = "/grafana/api/search"
    dashboards = make_api_request(endpoint, MAIN_ACCOUNT_API_KEY)

    if not dashboards:
        print("No dashboards found or error fetching dashboards.")
        return

    print("Available Dashboards:")
    for i, dashboard in enumerate(dashboards, start=1):
        print(f"{i}. {dashboard['title']} (UID: {dashboard['uid']})")

    return dashboards

def copy_grafana_dashboard(dashboard_uid):
    """Copy a Grafana dashboard from the main account to all sub-accounts"""
    # Fetch the dashboard from the main account
    endpoint = f"/grafana/api/dashboards/uid/{dashboard_uid}"
    dashboard_data = make_api_request(endpoint, MAIN_ACCOUNT_API_KEY)

    if not dashboard_data:
        print("Error fetching dashboard.")
        return

    # Prepare the dashboard data for the sub-account
    dashboard = dashboard_data['dashboard']
    dashboard['id'] = None  # Ensure the dashboard ID is None to avoid conflicts

    # Set the folder ID to the appropriate one in the sub-account (or 0 for the General folder)
    folder_id = 0

    # Iterate over each sub-account API key and copy the dashboard
    for api_key in SUB_ACCOUNT_API_KEYS:
        endpoint = "/grafana/api/dashboards/db"
        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": False
        }
        response = make_api_request(endpoint, api_key, method='POST', data=payload)

        if response:
            print(f"Dashboard '{dashboard['title']}' copied successfully to sub-account with API key ending in '{api_key[-4:]}'.")
        else:
            print(f"Failed to copy dashboard '{dashboard['title']}' to sub-account with API key ending in '{api_key[-4:]}'.")
    
def main():
    # List all Grafana dashboards
    dashboards = list_grafana_dashboards()

    if not dashboards:
        return

    # Prompt the user to select a dashboard UID to copy
    try:
        selection = int(input("Enter the number of the dashboard to copy: ")) - 1
        if selection < 0 or selection >= len(dashboards):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    dashboard_uid = dashboards[selection]['uid']
    print(f"Copying Grafana dashboard with UID '{dashboard_uid}'...")
    copy_grafana_dashboard(dashboard_uid)

if __name__ == "__main__":
    main()
