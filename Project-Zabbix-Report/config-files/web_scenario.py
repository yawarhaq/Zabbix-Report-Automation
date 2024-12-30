import requests
import json

# Zabbix API details
ZABBIX_URL = "http://172.16.200.110/zabbix/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

# Host ID to associate the web scenario with
HOST_ID = "10084"

def zabbix_api_call(method, params):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": None,
        "id": 1,
    }

    response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()

def get_auth_token():
    params = {
        "username": ZABBIX_USER,
        "password": ZABBIX_PASSWORD,
    }
    result = zabbix_api_call("user.login", params)
    return result["result"]

def create_web_scenario(auth_token):
    params = {
        "name": "Example Web Scenario",
        "hostid": HOST_ID,
        "steps": [
            {
                "name": "Step 1 - Check Home Page",
                "url": "https://google.com",
                "status_codes": "200",
                "no": 1,
            },
            {
                "name": "Step 2 - Check Login Page",
                "url": "https://google.com/login",
                "status_codes": "200",
                "no": 2,
            },
        ],
        "delay": 60,  # Interval in seconds
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "httptest.create",
        "params": params,
        "auth": auth_token,
        "id": 1,
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()
    if "result" in result:
        print("Web scenario created successfully:", result["result"])
    else:
        print("Error creating web scenario:", result)

def main():
    try:
        auth_token = get_auth_token()
        create_web_scenario(auth_token)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
