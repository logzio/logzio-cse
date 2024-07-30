import os
import sys
import json
import subprocess
import re
import shlex
from dotenv import load_dotenv, set_key

# Add the root directory to the system path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from api.api import make_api_request
from commands.commands import get_dashboard_by_uid

# Define the base directory and config paths
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
PAYLOADS_PATH = os.path.join(CONFIG_DIR, 'payloads.json')
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load environment variables from .env file
load_dotenv()

# Load payloads
try:
    with open(PAYLOADS_PATH, 'r') as payloads_file:
        PAYLOADS = json.load(payloads_file)
except json.JSONDecodeError as e:
    print(f"Error loading payloads.json: {e}")
    sys.exit(1)

def run_command(command):
    """Run a command and return the output"""
    args = shlex.split(command)
    result = subprocess.run(args, capture_output=True, text=True, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
        return None
    try:
        # Find the JSON part in the output
        json_start = result.stdout.find('{')
        json_end = result.stdout.rfind('}') + 1
        json_output = result.stdout[json_start:json_end]
        return json.loads(json_output)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from command: {e}")
        print(result.stdout)
        return None

def create_sub_account():
    """Create a sub-account"""
    command = "python3 main.py create-sub-account --json-file config/payloads.json"
    output = run_command(command)
    print(output)
    if output:
        return output['accountId']
    return None

def update_payloads(account_id):
    """Update the payloads with the new account ID"""
    PAYLOADS['create_api_key']['accountId'] = account_id
    PAYLOADS['create_metric_account']['authorizedAccountsIds'].append(int(account_id))

    with open(PAYLOADS_PATH, 'w') as f:
        json.dump(PAYLOADS, f, indent=2)

def create_api_key(account_id):
    """Create an API key for the new sub-account"""
    update_payloads(account_id)

    command = f"python3 main.py create-api-key --json-file config/payloads.json"
    output = run_command(command)
    if output:
        return output['token']
    return None

def get_dashboard_by_uid(uid):
    """Retrieve dashboard by UUID using run_command"""
    command = f"python3 main.py get-dashboard-by-uid {uid}"
    return run_command(command)

def update_env_file(new_api_key):
    """Update the .env file with the new API key"""
    set_key(ENV_PATH, 'LOGZIO_API_KEY', new_api_key)

def create_metric_account():
    """Create a new metric account using the new API key"""
    command = "python3 main.py create-metric-account --json-file config/payloads.json"
    return run_command(command)

def create_grafana_folder():
    """Create a new Grafana folder using the new API key"""
    command = "python3 main.py create-grafana-folder --json-file config/payloads.json"
    output = run_command(command)
    if output:
        return output.get('id'), output.get('uid')
    return None, None

def search_dashboards():
    """Search for all dashboards"""
    endpoint = "/grafana/api/search?type=dash-db"
    response = make_api_request(endpoint)
    return response

def create_dashboard(dashboard_data, account_name, folder_id, folder_uid):
    """Create a new dashboard on the new sub-account"""

    dashboard_content = json.dumps(dashboard_data)
    dashboard_content = re.sub(r"acadian", account_name, dashboard_content)

    # Load updated dashboard content
    updated_dashboard_data = json.loads(dashboard_content)

    # Prepare payload
    payload = {
        "create_dashboard": {
            "dashboard": updated_dashboard_data["dashboard"],
            "folderId": folder_id,
            "folderUid": folder_uid,
            "overwrite": True
        }
    }
    # Ensure the dashboard ID is None to avoid conflicts
    payload["create_dashboard"]["dashboard"]["id"] = None

    # Update the title to differentiate the copied dashboard
    payload["create_dashboard"]["dashboard"]["title"] = f"{payload['create_dashboard']['dashboard']['title']}"

    # Save to temporary JSON file
    payload_path = os.path.join(CONFIG_DIR, 'temp_create_dashboard.json')
    with open(payload_path, 'w') as f:
        json.dump(payload, f, indent=2)

    # Run the create_dashboard command
    command = f"python3 main.py create-dashboard --json-file {payload_path}"
    response = run_command(command)

    # Remove the temporary file
    if os.path.exists(payload_path):
        os.remove(payload_path)

    return response

def main():
    # Step 1: Create a sub-account
    print("Creating sub-account...")
    account_id = create_sub_account()
    account_name = PAYLOADS['create_sub_account']['accountName']
    if not account_id:
        print("Failed to create sub-account")
        return

    print(f"Sub-account created with account ID: {account_id}")

    # Step 2: Create an API key for the new sub-account
    print("Creating API key...")
    new_api_key = create_api_key(account_id)
    if not new_api_key:
        print("Failed to create API key")
        return

    print(f"API key created: {new_api_key}")

    # Step 3: Search for dashboards
    print("Searching for dashboards...")
    dashboards = search_dashboards()
    if not dashboards:
        print("Failed to retrieve dashboards")
        return
    print(dashboards)
    # Find the dashboard with the specified title
    dashboard_title = PAYLOADS['create_dashboard']['dashboard']['title']
    matching_dashboard = next((d for d in dashboards if d['title'] == dashboard_title), None)
    if not matching_dashboard:
        print(f"No dashboard found with title: {dashboard_title}")
        return
    print(f'Matching {matching_dashboard}')
    
    # Retrieve the dashboard from the main account
    dashboard_uid = matching_dashboard['uid']
    print(f"Retrieving dashboard with UID: {dashboard_uid}")
    dashboard_data = get_dashboard_by_uid(dashboard_uid)
    if not dashboard_data:
        print("Failed to retrieve dashboard")
        return

    # Update the environment variable with the new API key
    update_env_file(new_api_key)
    load_dotenv(override=True)

    # # Step 4: Create a new metric account
    print("Creating metric account...")
    create_metric_account()

    # Step 5: Create a new Grafana folder
    print("Creating Grafana folder...")
    folder_id, folder_uid = create_grafana_folder()
    if not folder_id or not folder_uid:
        print("Failed to create Grafana folder")
        return

    # Step 6: Create a new dashboard on the new sub-account
    print("Creating dashboard on the new sub-account...")
    response = create_dashboard(dashboard_data, account_name, folder_id, folder_uid)
    print(response)

if __name__ == "__main__":
    main()
