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

# Step 2: Get Hosts from Groups
def get_hosts_from_groups(auth_token, group_names_or_ids):
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

# Step 5: Process Data
def process_data(trend_data):
    if not trend_data:
        return {"min": None, "avg": None, "max": None}
    df = pd.DataFrame(trend_data)
    df["clock"] = pd.to_datetime(pd.to_numeric(df["clock"]), unit="s")
    # Convert values from bytes to GB
    df[["value_min", "value_avg", "value_max"]] = df[["value_min", "value_avg", "value_max"]].apply(pd.to_numeric) / (1024 ** 3)
    return {
        "min": df["value_min"].min(),
        "avg": df["value_avg"].mean(),
        "max": df["value_max"].max()
    }

# Main Function
def main():
    auth_token = authenticate()
    group_input = input("Enter host group names or IDs separated by commas: ").split(",")
    group_input = [group.strip() for group in group_input]
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    time_from = int(start_datetime.timestamp())
    time_till = int(end_datetime.timestamp())
    total_days = (end_datetime - start_datetime).days + 1  # Inclusive of start and end dates

    keys = {
        "C: Total(GB)": ["vfs.fs.dependent.size[C:,total]"],
        "C: Used(GB)": ["vfs.fs.dependent.size[C:,used]"],
        "C: Available(GB)": ["vfs.fs.dependent.size[C:,free]"],
        "D: Total(GB)": ["vfs.fs.dependent.size[D:,total]"],
        "D: Used(GB)": ["vfs.fs.dependent.size[D:,used]"],
        "D: Available(GB)": ["vfs.fs.dependent.size[D:,free]"],
        "E: Total(GB)": ["vfs.fs.dependent.size[E:,total]"],
        "E: Used(GB)": ["vfs.fs.dependent.size[E:,used]"],
        "E: Available(GB)": ["vfs.fs.dependent.size[E:,free]"],
        "F: Total(GB)": ["vfs.fs.dependent.size[F:,total]"],
        "F: Used(GB)": ["vfs.fs.dependent.size[F:,used]"],
        "F: Available(GB)": ["vfs.fs.dependent.size[F:,free]"],
    }

    # Fetch all hosts
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
                row[f"{metric}"] = None
                continue

            item_ids = [item["itemid"] for item in items]
            trends = get_trends(auth_token, item_ids, time_from, time_till)
            aggregated_data = process_data(trends)

            # Only store the Avg value for each drive's Total, Used, Available
            if "Total" in metric or "Used" in metric or "Available" in metric:
                row[f"{metric}"] = aggregated_data["avg"]

        # Add only the required columns for Avg values to the results
        results.append(row)

    # Create a DataFrame containing only the necessary columns
    df = pd.DataFrame(results)

    # Keep only the necessary columns: Host ID, Hostname, IP Address, and Avg values
    # Reorder columns to have Used, Available, then Total for each drive
    column_order = [
        "Host ID", "Hostname", "IP Address", 
        "C: Used(GB)", "C: Available(GB)", "C: Total(GB)",
        "D: Used(GB)", "D: Available(GB)", "D: Total(GB)",
        "E: Used(GB)", "E: Available(GB)", "E: Total(GB)",
        "F: Used(GB)", "F: Available(GB)", "F: Total(GB)"
    ]
    
    # Reorder the DataFrame columns
    df = df[column_order]
    print(df)

    # Create an Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Drive Report"

    # Add metadata
    ws.append(["Start Date", start_date])
    ws.append(["End Date", end_date])
    ws.append(["Total Days", total_days])
    ws.append([])

    # Add DataFrame to worksheet
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)

    # Save report
    report_file = "Report-Servers-W-Disk-New.xlsx"
    wb.save(report_file)
    print(f"Report saved as '{report_file}'.")


if __name__ == "__main__":
    main()