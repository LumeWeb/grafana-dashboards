import grafanalib.core as G
from grafanalib.core import (
    Dashboard, Graph, Row, Target, GridPos,
    YAxes, YAxis, Stat, Time, DEFAULT_TIME_PICKER,
    PERCENT_FORMAT, BYTES_FORMAT, SHORT_FORMAT,
    Template, Templating, REFRESH_ON_TIME_RANGE_CHANGE,
    Alert, AlertCondition, Notification, 
    GreaterThan, TimeRange, OP_AND
)

# Alert Conditions
def create_system_alerts():
    # System alerts
    disk_space_alert = Alert(
        name="Low Disk Space",
        message="Disk space usage is above 85% for 5 minutes",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(85),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    load_avg_alert = Alert(
        name="High System Load",
        message="System load average (1m) is high for 5 minutes",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='node_load1',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(4),  # Adjust based on CPU cores
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    # Network alerts
    network_saturation_alert = Alert(
        name="Network Interface Saturation",
        message="Network interface bandwidth usage > 80% for 5 minutes",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='(rate(system_network_tx_bytes_per_second{interface="$interface"}[$rate_interval]) + rate(system_network_rx_bytes_per_second{interface="$interface"}[$rate_interval])) / 1000000000 * 8 > 0.8',  # Assumes 1Gbps link
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(0.8),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    # I/O alerts
    io_latency_alert = Alert(
        name="High I/O Latency",
        message="I/O operations are taking too long",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='rate(node_disk_read_time_seconds_total[$rate_interval]) / rate(node_disk_reads_completed_total[$rate_interval]) > 0.1',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(0.1),  # 100ms average latency
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )
    cpu_alert = Alert(
        name="High CPU Usage",
        message="CPU usage is above 80% for 5 minutes",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='system_cpu_usage_percent / 1000000',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(80),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    memory_alert = Alert(
        name="High Memory Usage",
        message="Memory usage is above 80% for 5 minutes",
        noDataState="no_data", 
        alertConditions=[
            AlertCondition(
                Target(
                    expr='system_memory_usage_bytes / system_memory_total_bytes * 100',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(80),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    goroutine_alert = Alert(
        name="High Goroutine Count",
        message="Number of goroutines has increased significantly",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='go_goroutines > 10000',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(10000),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    gc_duration_alert = Alert(
        name="Long GC Duration",
        message="Garbage collection is taking too long",
        noDataState="no_data",
        alertConditions=[
            AlertCondition(
                Target(
                    expr='rate(go_gc_duration_seconds_sum[$rate_interval])',
                    refId='A',
                    datasource="${datasource}",
                ),
                timeRange=TimeRange("5m", "now"),
                evaluator=GreaterThan(0.1),
                operator=OP_AND,
            )
        ],
        gracePeriod="5m",
        frequency="1m",
    )

    return (cpu_alert, memory_alert, goroutine_alert, gc_duration_alert,
            disk_space_alert, load_avg_alert, network_saturation_alert, io_latency_alert)

# Template Variables
templating = Templating(
    list=[
        Template(
            name="datasource",
            label="Data Source",
            dataSource=None,
            query="prometheus",
            type="datasource",
            regex="/.*/"
        ),
        Template(
            name="job",
            label="Job",
            dataSource="${datasource}",
            query="label_values(system_cpu_usage_percent, job)",
            refresh=REFRESH_ON_TIME_RANGE_CHANGE,
        ),
        Template(
            name="instance",
            label="Instance", 
            dataSource="${datasource}",
            query="label_values(system_cpu_usage_percent{job=~\"$job\"}, instance)",
            refresh=REFRESH_ON_TIME_RANGE_CHANGE,
        ),
        Template(
            name="interface",
            label="Network Interface",
            dataSource="${datasource}",
            query='label_values(system_network_rx_bytes_per_second, interface)',
            refresh=REFRESH_ON_TIME_RANGE_CHANGE,
        ),
        Template(
            name="rate_interval",
            label="Rate Interval",
            dataSource=None,
            query="1m,5m,10m,30m,1h",
            type="custom",
            default="5m"
        ),
    ]
)

# Quick Stats Row
cpu_stat = Stat(
    title="CPU Usage",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='avg_over_time(system_cpu_usage_percent{job=~"$job", instance=~"$instance"}[$rate_interval]) / 1000000',
            refId='A',
        ),
    ],
    gridPos=GridPos(h=3, w=6, x=0, y=0),
    format=PERCENT_FORMAT,
)

memory_stat = Stat(
    title="Memory Usage",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='avg_over_time(system_memory_usage_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            refId='A',
        ),
    ],
    gridPos=GridPos(h=3, w=6, x=6, y=0),
    format=BYTES_FORMAT,
)

goroutines_stat = Stat(
    title="Goroutines",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='avg_over_time(go_goroutines[$rate_interval])',
            refId='A',
        ),
    ],
    gridPos=GridPos(h=3, w=6, x=12, y=0),
)

threads_stat = Stat(
    title="OS Threads",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='avg_over_time(go_threads[$rate_interval])',
            refId='A',
        ),
    ],
    gridPos=GridPos(h=3, w=6, x=18, y=0),
)

# System Resources Section
# Get alert definitions
(cpu_alert, memory_alert, goroutine_alert, gc_duration_alert,
 disk_space_alert, load_avg_alert, network_saturation_alert, io_latency_alert) = create_system_alerts()

cpu_panel = Graph(
    title="CPU Usage Over Time",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='system_cpu_usage_percent{job=~"$job", instance=~"$instance"} / 1000000',
            legendFormat='CPU {{instance}}',
            refId='A',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=0, y=3),
    yAxes=YAxes(
        YAxis(format=PERCENT_FORMAT, min=0),
        YAxis(format=SHORT_FORMAT)
    ),
    alert=cpu_alert,
)

memory_panel = Graph(
    title="Memory Usage Over Time",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='system_memory_usage_bytes{job=~"$job", instance=~"$instance"}',
            legendFormat='System Memory Usage {{instance}}',
            refId='A',
        ),
        Target(
            expr='rate(process_resident_memory_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Process Resident Memory {{instance}}',
            refId='B',
        ),
        Target(
            expr='rate(process_virtual_memory_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Process Virtual Memory {{instance}}',
            refId='C',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=12, y=3),
    yAxes=YAxes(
        YAxis(format=BYTES_FORMAT, min=0),
        YAxis(format=SHORT_FORMAT)
    ),
    alert=memory_alert,
)

# Network Section
network_traffic = Graph(
    title="Network Traffic (bytes/sec)", 
    dataSource="${datasource}",
    targets=[
        Target(
            expr='system_network_rx_bytes_per_second{job=~"$job", instance=~"$instance", interface="$interface"}',
            legendFormat='Receive {{instance}}',
            refId='A',
        ),
        Target(
            expr='system_network_tx_bytes_per_second{job=~"$job", instance=~"$instance", interface="$interface"}',
            legendFormat='Transmit {{instance}}',
            refId='B',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=0, y=11),
    alert=network_saturation_alert,
    yAxes=YAxes(
        YAxis(format=BYTES_FORMAT, min=0),
        YAxis(format=SHORT_FORMAT)
    ),
)

network_packets = Graph(
    title="Network Packets (packets/sec)",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='system_network_rx_packets_per_second{job=~"$job", instance=~"$instance", interface="$interface"}',
            legendFormat='Receive Packets {{instance}}',
            refId='A',
        ),
        Target(
            expr='system_network_tx_packets_per_second{job=~"$job", instance=~"$instance", interface="$interface"}',
            legendFormat='Transmit Packets {{instance}}',
            refId='B',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=12, y=11),
)

# IO Section
io_operations = Graph(
    title="IO Operations",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='rate(system_io_read_operations{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Read Ops/sec {{instance}}',
            refId='A',
        ),
        Target(
            expr='rate(system_io_write_operations{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Write Ops/sec {{instance}}',
            refId='B',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=0, y=19),
    alert=io_latency_alert,
)

io_bytes = Graph(
    title="IO Bytes",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='rate(system_io_read_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Read Bytes/sec {{instance}}',
            refId='A',
        ),
        Target(
            expr='rate(system_io_write_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Write Bytes/sec {{instance}}',
            refId='B',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=12, y=19),
    yAxes=YAxes(
        YAxis(format=BYTES_FORMAT, min=0),
        YAxis(format=SHORT_FORMAT)
    ),
)

# Go Runtime Section
gc_metrics = Graph(
    title="Garbage Collection",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='rate(go_gc_duration_seconds_sum{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='GC Duration {{instance}}',
            refId='A',
        ),
        Target(
            expr='go_gc_duration_seconds{job=~"$job", instance=~"$instance", quantile="0.75"}',
            legendFormat='GC 75th %ile {{instance}}',
            refId='B',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=0, y=27),
    alert=gc_duration_alert,
)

heap_metrics = Graph(
    title="Go Heap Usage",
    dataSource="${datasource}",
    targets=[
        Target(
            expr='rate(go_memstats_heap_alloc_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Heap Allocated {{instance}}',
            refId='A',
        ),
        Target(
            expr='rate(go_memstats_heap_inuse_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Heap In Use {{instance}}',
            refId='B',
        ),
        Target(
            expr='rate(go_memstats_heap_idle_bytes{job=~"$job", instance=~"$instance"}[$rate_interval])',
            legendFormat='Heap Idle {{instance}}',
            refId='C',
        ),
    ],
    gridPos=GridPos(h=8, w=12, x=12, y=27),
    yAxes=YAxes(
        YAxis(format=BYTES_FORMAT, min=0),
        YAxis(format=SHORT_FORMAT)
    ),
)

dashboard = Dashboard(
    title="System Metrics Dashboard",
    description="Comprehensive system metrics from Prometheus",
    tags=['system', 'golang'],
    timezone="browser",
    templating=templating,
    panels=[
        # Stats Row
        cpu_stat, memory_stat, goroutines_stat, threads_stat,
        # System Resources
        cpu_panel, memory_panel,
        # Network
        network_traffic, network_packets,
        # IO
        io_operations, io_bytes,
        # Go Runtime
        gc_metrics, heap_metrics
    ],
    time=Time("now-3h", "now"),
    timePicker=DEFAULT_TIME_PICKER,
    refresh="10s",
).auto_panel_ids()
