import requests
import json
import pandas as pd
from datetime import datetime

# Zabbix API details
ZABBIX_URL = "http://<url>/api_jsonrpc.php"
USERNAME = "username"
PASSWORD = "password"

# Step 1: Authenticate
def authenticate():
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"username": USERNAME, "password": PASSWORD},
        "id": 1
    }
    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()["result"]

def get_host_details(auth_token, host_identifier):
    # Check if input is numeric (host ID) or name (host Name)
    filter_field = "hostid" if host_identifier.isdigit() else "host"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name"],
            "selectInterfaces": ["ip"],
            "filter": {filter_field: host_identifier}
        },
        "auth": auth_token,
        "id": 2
    }
    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()["result"]


# Step 3: Get Item IDs
def get_item_ids(auth_token, host_id, search_keys):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "key_"],
            "hostids": host_id,
            "filter": {"key_": search_keys},
            "sortfield": "name"
        },
        "auth": auth_token,
        "id": 3
    }
    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()["result"]

# Step 4: Fetch Trends
def get_trends(auth_token, item_ids, time_from, time_till):
    payload = {
        "jsonrpc": "2.0",
        "method": "trend.get",
        "params": {
            "output": ["itemid", "clock", "num", "value_min", "value_avg", "value_max"],
            "itemids": item_ids,
            "time_from": time_from,
            "time_till": time_till
        },
        "auth": auth_token,
        "id": 4
    }
    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()["result"]

# Step 5: Process and Aggregate
def process_data(trend_data):
    if not trend_data:
        return {"min": None, "avg": None, "max": None}
    df = pd.DataFrame(trend_data)
    # Ensure 'clock' is numeric before converting to datetime
    df["clock"] = pd.to_datetime(pd.to_numeric(df["clock"]), unit="s")
    df[["value_min", "value_avg", "value_max"]] = df[["value_min", "value_avg", "value_max"]].apply(pd.to_numeric)
    return {
        "min": df["value_min"].min(),
        "avg": df["value_avg"].mean(),
        "max": df["value_max"].max()
    }


# Main Script
def main():
    auth_token = authenticate()
    host_input = input("Enter host IDs separated by commas: ").split(",")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    
    # Convert dates to timestamps
    time_from = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    time_till = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    # Define key options for metrics
    keys = {
        "CPU": ["system.cpu.util"],
        "Memory": ["vm.memory.util", "vm.memory.utilization"],
        "Disk": ["perf_counter_en[\"\\PhysicalDisk(0 C:)\\% Idle Time\",60]", "vfs.dev.util[sda]"]
    }

    results = []

    for host in host_input:
        host = host.strip()
        host_details = get_host_details(auth_token, host)
        if not host_details:
            print(f"Host {host} not found.")
            continue

        host_info = host_details[0]
        host_id = host_info["hostid"]
        host_ip = host_info["interfaces"][0]["ip"]
        host_name = host_info["name"]

        row = {"Host ID": host, "Hostname": host_name, "IP Address": host_ip}

        for metric, key_list in keys.items():
            items = get_item_ids(auth_token, host_id, key_list)
            if not items:
                row[f"{metric} Min"] = None
                row[f"{metric} Avg"] = None
                row[f"{metric} Max"] = None
                continue
            
            item_ids = [item["itemid"] for item in items]
            trends = get_trends(auth_token, item_ids, time_from, time_till)
            aggregated_data = process_data(trends)
            
            row[f"{metric} Min"] = aggregated_data["min"]
            row[f"{metric} Avg"] = aggregated_data["avg"]
            row[f"{metric} Max"] = aggregated_data["max"]

        results.append(row)

    # Convert results to a DataFrame
    df = pd.DataFrame(results)

    # Set the columns order to match the original request
    column_order = ['Host ID', 'Hostname', 'IP Address', 'CPU Min', 'CPU Avg', 'CPU Max', 
                    'Memory Min', 'Memory Avg', 'Memory Max', 'Disk Min', 'Disk Avg', 'Disk Max']
    df = df[column_order]

    # Save the final DataFrame to Excel
    print(df)
    df.to_excel("Zabbix_report.xlsx", index=False)
    print("Report saved as 'Zabbix_report.xlsx'.")
    

if __name__ == "__main__":
    main()