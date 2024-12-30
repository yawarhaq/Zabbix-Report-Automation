import requests
import json

url = "http://172.16.200.110/zabbix/api_jsonrpc.php"
username = "Admin"
password = "zabbix"

def get_auth_token():
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": username,
            "password": password
        },
        "id": 1
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    print(result)
    if "error" in result:
        raise Exception(f"Login failed: {result['error']}")
    return result["result"]


def list_item_fields(host_id):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": "extend",  # 'extend' retrieves all available fields
            "hostids": host_id,
        },
        "auth": auth_token,
        "id": 2
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    items = response.json().get('result', [])

    # Print field names for each item
    if items:
        print("Available fields in latest data for each item:")
        for field in items[0]:
            print(field)
    else:
        print("No items found for this host.")


auth_token = get_auth_token()
host_id = ["10620, 10619, 10621, 10627, 10623, 10622, 10624, 10628, 10626, 10625"]
list_item_fields(host_id)