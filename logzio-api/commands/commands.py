import click
import os
import json
from api.api import make_api_request

# Load configuration
with open('config/config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

@click.group()
def cli():
    """Logz.io CLI"""
    pass

def load_json(file_path):
    """Load JSON data from a file"""
    # Validate the file path
    if not os.path.isabs(file_path):
        raise ValueError("The file path must be absolute")
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist")

    with open(file_path, 'r') as file:
        return json.load(file)

def validate_required_fields(data, required_fields):
    """Validate that required fields are present"""
    missing_fields = [field for field in required_fields if data.get(field) is None]
    if missing_fields:
        raise click.BadParameter(f"Missing required fields: {', '.join(missing_fields)}")

@click.command()
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file containing sub-account data.')
@click.option('--account-name', help='The name of the sub-account.')
@click.option('--email', help='The email associated with the sub-account.')
@click.option('--retention-days', type=int, help='The retention period for the sub-account.')
@click.option('--sharing-objects-accounts', help='The accounts with which the sub-account can share objects.')
@click.option('--is-flexible', type=bool, help='Whether the account is flexible.')
@click.option('--reserved-daily-gb', type=int, help='The reserved daily volume in GB for the sub-account.')
@click.option('--maxdaily-gb', type=int, help='The maximum daily volume in GB for the sub-account.')
@click.option('--searchable', type=bool, help='Whether the sub-account is searchable.')
@click.option('--accessible', type=bool, help='Whether the sub-account is accessible.')
@click.option('--doc-size-setting', type=bool, help='The doc size setting for the sub-account.')
@click.option('--utilization-settings', help='The utilization settings for the sub-account.')
def create_sub_account(json_file, account_name, email, retention_days, sharing_objects_accounts, is_flexible, reserved_daily_gb, maxdaily_gb, searchable, accessible, doc_size_setting, utilization_settings):
    """Create a sub-account"""
    required_fields = ["accountName", "email", "retentionDays", "sharingObjectsAccounts"]
    if json_file:
        data = load_json(json_file)['create_sub_account']
        validate_required_fields(data, required_fields)
    else:
        data = {
            "accountName": account_name,
            "email": email,
            "retentionDays": retention_days,
            "sharingObjectsAccounts": sharing_objects_accounts,
            "isFlexible": is_flexible,
            "reservedDailyGB": reserved_daily_gb,
            "maxDailyGB": maxdaily_gb,
            "searchable": searchable,
            "accessible": accessible,
            "docSizeSetting": doc_size_setting,
            "utilizationSettings": utilization_settings
        }
        validate_required_fields(data, required_fields)
    
    endpoint = CONFIG["endpoints"]["create_sub_account"]
    response = make_api_request(endpoint, method='POST', data=data)
    print(json.dumps(response, indent=2))

@click.command()
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file containing API token data.')
@click.option('--name', help='The name of the API token.')
@click.option('--account-id', type=int, help='The ID of the account for which the API token is created.')
def create_api_key(json_file, name, account_id):
    """Create an API key"""
    required_fields = ["name", "accountId"]
    if json_file:
        data = load_json(json_file)['create_api_key']
        validate_required_fields(data, required_fields)
    else:
        data = {
            "name": name,
            "accountId": account_id
        }
        validate_required_fields(data, required_fields)

    endpoint = CONFIG["endpoints"]["create_api_key"]
    response = make_api_request(endpoint, method='POST', data=data)
    print(json.dumps(response, indent=2))

@click.command()
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file containing metric account data.')
@click.option('--email', help='The email of the account owner.')
@click.option('--account-name', help='The name of the metrics account.')
@click.option('--plan-uts', type=int, help='The plan UTS for the metrics account.')
@click.option('--authorized-accounts-ids', help='Comma-separated list of authorized account IDs.')
def create_metric_account(json_file, email, account_name, plan_uts, authorized_accounts_ids):
    """Create a new metrics account"""
    required_fields = ["email", "accountName", "planUts"]
    if json_file:
        data = load_json(json_file)['create_metric_account']
        validate_required_fields(data, required_fields)
    else:
        authorized_accounts_ids_list = [int(id) for id in authorized_accounts_ids.split(',')] if authorized_accounts_ids else []
        data = {
            "email": email,
            "accountName": account_name,
            "planUts": plan_uts,
            "authorizedAccountsIds": authorized_accounts_ids_list
        }
        validate_required_fields(data, required_fields)

    endpoint = CONFIG["endpoints"]["create_metric_account"]
    response = make_api_request(endpoint, method='POST', data=data)
    print(json.dumps(response, indent=2))

@click.command()
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file containing Grafana folder data.')
@click.option('--title', help='The title of the Grafana folder.')
def create_grafana_folder(json_file, title):
    """Create a Grafana folder"""
    required_fields = ["title"]
    if json_file:
        data = load_json(json_file)['create_grafana_folder']
        
        validate_required_fields(data, required_fields)
    else:
        data = {
            "title": title
        }
        validate_required_fields(data, required_fields)

    endpoint = CONFIG["endpoints"]["create_grafana_folder"]
    response = make_api_request(endpoint, method='POST', data=data)
    print(json.dumps(response, indent=2))

@click.command()
def get_all_grafana_data_sources():
    """Get all Grafana data sources"""
    endpoint = CONFIG["endpoints"]["get_all_grafana_data_sources"]
    response = make_api_request(endpoint)
    print(json.dumps(response, indent=2))

@click.command()
@click.argument('uid')
def get_dashboard_by_uid(uid):
    """Get a dashboard with a specific UID"""
    endpoint = CONFIG["endpoints"]["get_dashboard_by_uid"].format(uid=uid)
    response = make_api_request(endpoint)
    print(json.dumps(response, indent=2))

@click.command()
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file containing dashboard data.')
@click.option('--dashboard-title', help='The title of the dashboard.')
def create_dashboard(json_file, dashboard_title):
    """Create a new dashboard"""
    if json_file:
        data = load_json(json_file)['create_dashboard']
        required_fields = ["dashboard"]
        validate_required_fields(data, required_fields)

        endpoint = CONFIG["endpoints"]["create_dashboard"]
        response = make_api_request(endpoint, method='POST', data=data)
    else:
        data = {
            "dashboard": {
                "title": dashboard_title,
                "panels": []
            },
            "folderId": 0,
            "overwrite": False
        }

        endpoint = CONFIG["endpoints"]["create_dashboard"]
        response = make_api_request(endpoint, method='POST', data=data)
    
    print(json.dumps(response, indent=2))

# Add commands to the CLI group
cli.add_command(create_sub_account)
cli.add_command(create_api_key)
cli.add_command(create_metric_account)
cli.add_command(create_grafana_folder)
cli.add_command(get_all_grafana_data_sources)
cli.add_command(get_dashboard_by_uid)
cli.add_command(create_dashboard)
