Overview:

- Authenticate and fetch details of specified hosts.
- Retrieve performance metrics such as CPU utilization, memory usage, and disk activity.
- Process trend data to calculate minimum, average, and maximum values.
- Export the aggregated data to an Excel report for easy visualization and sharing.

This tool is ideal for system administrators and DevOps engineers who need a quick and efficient way to analyze Zabbix trends over a given time frame.

Features:

- Authentication: Securely connects to the Zabbix API using user credentials.
- Host Details Fetching: Supports querying by both host IDs and hostnames.
- Metric Retrieval: Gathers key metrics for CPU, memory, and disk usage.
- Data Aggregation: Processes trend data to calculate min, avg, and max values.
- Excel Reporting: Exports results in a well-structured Excel file for reporting.
- Error Handling: Gracefully handles missing hosts or metrics.

Technologies Used:

- Python: The core programming language.
- Zabbix API: JSON-RPC API for interacting with the Zabbix monitoring system.
- requests Library: For making HTTP POST requests to the Zabbix API.
- pandas Library: For data manipulation and aggregation.
- openpyxl: Implicitly used via Pandas for Excel file generation.
- datetime Module: For handling date and time conversions.

Contributing:
Contributions are welcome! Feel free to open issues or submit pull requests with improvements.

Future Enhancements:

- Add support for additional metrics.
- Provide real-time data visualization.
- Extend compatibility with Zabbix API versions.
