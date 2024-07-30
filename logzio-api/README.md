### README.md

## Overview
This project contains a set of scripts to manage and automate tasks within Logz.io. The primary script is `main.py`, which supports various commands for managing Logz.io accounts, API keys, Grafana folders, and dashboards.

### Prerequisites
- Python 3.x
- `pip` for installing required packages
- Logz.io API access
- `.env` file with necessary environment variables

### Installation
1. Clone the repository:
   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up your `.env` file with the required environment variables:
   ```sh
   LOGZIO_API_KEY='XXXXXXXXX'
   ```

### Usage

#### Command Line Options

##### Create a Sub-Account
Create a new sub-account using a JSON payload.
```sh
python3 main.py create-sub-account --json-file config/payloads.json
```

##### Create an API Key
Create an API key for a sub-account.
```sh
python3 main.py create-api-key --json-file config/payloads.json
```

##### Create a Metric Account
Create a new metric account using the new API key.
```sh
python3 main.py create-metric-account --json-file config/payloads.json
```

##### Create a Grafana Folder
Create a new Grafana folder using the new API key.
```sh
python3 main.py create-grafana-folder --json-file config/payloads.json
```

##### Get a Dashboard by UID
Retrieve a specific Grafana dashboard by its UID.
```sh
python3 main.py get-dashboard-by-uid <UID>
```

##### List All Grafana Data Sources
Retrieve all data sources configured in Grafana.
```sh
python3 main.py get-all-grafana-data-sources
```

#### Help Command

Use the `--help` option with any command to get more information about the available options and usage.
```sh
python3 main.py <command> --help
```

### Sample `payloads.json` 
The sample payloads.json can be found under the config directory.

### License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

### Contact
For any questions or support, please contact Sovanmony Lim at sovanmony.lim@logz.io.

---

This README provides an overview and usage instructions for the main functionalities of the project. For more detailed information or troubleshooting, refer to the comments within the code files or contact the project maintainer.