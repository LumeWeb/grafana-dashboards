# Grafana Dashboard Generator

This repository contains Python scripts to generate Grafana dashboards for monitoring various systems and services using grafanalib.

## Prerequisites

- Python 3.6+
- grafanalib
- Prometheus configured with appropriate exporters for your metrics
- Grafana server

## Installation

1. Install the required Python package:

```bash
pip install grafanalib
```

## Available Dashboards

- `system_metrics.dashboard.py`: System metrics dashboard including CPU, memory, network, and IO metrics
- `mysql.dashboard.py`: MySQL database monitoring dashboard
- `redis.dashboard.py`: Redis monitoring dashboard

## Generating Dashboards

To generate a dashboard JSON file, use the `generate-dashboard` command provided by grafanalib:

```bash
# Generate system metrics dashboard
generate-dashboard system_metrics.dashboard.py > system_metrics.json

# Generate MySQL dashboard
generate-dashboard mysql.dashboard.py > mysql.json

# Generate Redis dashboard
generate-dashboard redis.dashboard.py > redis.json
```

## Importing into Grafana

1. Open your Grafana instance in a web browser
2. Navigate to Dashboards > Import
3. Either:
   - Click "Upload JSON file" and select the generated .json file
   - Or paste the contents of the generated JSON file into the "Import via panel json" text area
4. Click "Load"
5. Select your Prometheus data source in the "Prometheus" dropdown
6. Click "Import"

## Customization

Each dashboard can be customized by modifying the corresponding Python file:

- Adjust alert thresholds
- Modify panel layouts
- Add/remove metrics
- Change visualization types
- Update refresh intervals

After making changes, regenerate the JSON file using the `generate-dashboard` command.

## Metrics Requirements

### System Metrics Dashboard
Requires node_exporter or similar exporter providing:
- system_cpu_usage_percent
- system_memory_usage_bytes
- system_network_*_bytes_per_second
- system_io_*_bytes
- go_* metrics (for Go runtime stats)

### MySQL Dashboard
Requires mysqld_exporter providing:
- mysql_up
- mysql_global_status_*
- mysql_global_variables_*

### Redis Dashboard
Requires redis_exporter providing:
- redis_memory_used_bytes
- redis_memory_max_bytes
- redis_connected_clients
- redis_commands_*
- redis_net_*

## Contributing

Feel free to submit issues and pull requests for:
- New dashboards
- Dashboard improvements
- Bug fixes
- Documentation updates
