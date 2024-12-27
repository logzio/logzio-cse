# Grafana Dashboard Copier

This Python script allows you to copy Grafana dashboards from a main Logz.io account to a sub-account using the Logz.io API. You can list available dashboards, choose one, and automatically copy it to the sub-account.

## Prerequisites

1. Python 3.x installed.
2. Virtual environment (`venv`) set up.
3. `requests` and `python-dotenv` libraries installed. These are listed in the `requirements.txt` file.
4. Logz.io API keys for both the main and sub-accounts.

## Setup

### Step 1: Create a Virtual Environment

1. Create a virtual environment (if not already done):
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:

   On Linux/macOS:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Create `.env` File

Create a `.env` file in the root directory of the project and add your Logz.io API keys:

```env
MAIN_ACCOUNT_API_KEY=your_main_account_api_key
SUB_ACCOUNTS_API_KEYS=your_sub_account_api_key_1,your_sub_account_api_key_2,your_sub_account_api_key_3
```

### Step 3: Run the Script

Run the script to list Grafana dashboards from the main account and copy them to the sub-account:

```bash
python copy_dashboard.py
```

You will be prompted to choose a dashboard to copy after the list is displayed.

### Script Explanation

- **list_grafana_dashboards**: This function lists all available Grafana dashboards from the main account.
- **copy_grafana_dashboard**: This function allows you to copy a selected Grafana dashboard from the main account to the sub-account.
- **make_api_request**: This is a helper function that makes the API requests, handles the responses, and manages potential errors.
