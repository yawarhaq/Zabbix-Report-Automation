import requests
import json
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Zabbix API details
ZABBIX_URL = "http://url/zabbix/api_jsonrpc.php"
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

# Step 2: Get Host
def get_hosts_from_groups(auth_token, group_names_or_ids):
    # Determine whether the input is numeric (host group ID) or name
    filter_field = "groupid" if all(name.isdigit() for name in group_names_or_ids) else "name"

    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": ["groupid"],
            "filter": {filter_field: group_names_or_ids},
            "selectHosts": ["hostid", "host", "name"]
        },
        "auth": auth_token,
        "id": 2
    }
    response = requests.post(ZABBIX_URL, json=payload)
    groups = response.json()["result"]

    # Extract all hosts from the fetched groups
    hosts = []
    for group in groups:
        hosts.extend(group.get("hosts", []))
    return hosts

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



def main():
    auth_token = authenticate()
    group_input = input("Enter host group names or IDs separated by commas: ").split(",")
    group_input = [group.strip() for group in group_input]
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    
    # Calculate the total number of days
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    time_from = int(start_datetime.timestamp())
    time_till = int(end_datetime.timestamp())
    total_days = (end_datetime - start_datetime).days + 1  # Inclusive of start and end dates

    keys = {
        "CPU": ["system.cpu.util"],
        "Memory": ["vm.memory.util", "vm.memory.utilization"]
    }

    # Fetch all hosts from the provided host groups
    hosts = get_hosts_from_groups(auth_token, group_input)
    if not hosts:
        print("No hosts found in the specified host groups.")
        return

    results = []

    for host_info in hosts:
        host_id = host_info["hostid"]
        host_name = host_info["name"]
        host_ip = None

        # Fetch host details to get IP address
        host_details = get_host_details(auth_token, host_id)
        if host_details:
            host_ip = host_details[0]["interfaces"][0]["ip"]

        row = {"Host ID": host_id, "Hostname": host_name, "IP Address": host_ip}

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

    df = pd.DataFrame(results)
    print(df)

    column_order = ['Host ID', 'Hostname', 'IP Address', 'CPU Min', 'CPU Avg', 'CPU Max', 
                    'Memory Min', 'Memory Avg', 'Memory Max']
    df = df[column_order]

    # Create an Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Zabbix Report"

    # Add metadata at the top
    ws.append(["Start Date", start_date])
    ws.append(["End Date", end_date])
    ws.append(["Total Days", total_days])
    ws.append([])  # Blank row to separate metadata from the table

    # Add the DataFrame to the worksheet
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)

    # Save the Excel file
    report_file = "Report-Servers-CPU-MEM-New.xlsx"
    wb.save(report_file)
    print(f"Report saved as '{report_file}'.")
    

if __name__ == "__main__":
    main()