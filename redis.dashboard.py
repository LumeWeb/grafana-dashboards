#!/usr/bin/env python
"""Redis dashboard and alerts."""

from grafanalib.core import (
    Alert, AlertCondition, Dashboard, Graph, GridPos, Target, TimeRange,
    YAxes, YAxis, MILLISECONDS_FORMAT, BYTES_FORMAT, SHORT_FORMAT,
    GreaterThan, EVAL_LT, OP_AND, RTYPE_MAX, single_y_axis,
    Template, Templating
)


def create_redis_alerts():
    """Create Redis alerts."""
    return [
        # Memory alerts
        Alert(
            name="Redis High Memory Usage",
            message="Redis memory usage is high",
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='redis_memory_used_bytes{instance=~"$instance"} / redis_memory_max_bytes{instance=~"$instance"} * 100 > 90',
                        refId='A',
                        datasource="${datasource}",
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=GreaterThan(90),
                    operator=OP_AND,
                    reducerType=RTYPE_MAX,
                ),
            ],
            executionErrorState='alerting',
            frequency='1m',
            handler=1,
        ),
        Alert(
            name="Redis High Memory Fragmentation",
            message="Redis memory fragmentation ratio is high",
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='redis_mem_fragmentation_ratio{instance=~"$instance"} > 2',
                        refId='A',
                        datasource="${datasource}",
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=GreaterThan(2),
                    operator=OP_AND,
                    reducerType=RTYPE_MAX,
                ),
            ],
            executionErrorState='alerting',
            frequency='1m',
            handler=1,
        ),
        # Client alerts
        Alert(
            name="Redis Too Many Clients",
            message="Redis has too many connected clients",
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='redis_connected_clients{instance=~"$instance"} > 5000',
                        refId='A',
                        datasource="${datasource}",
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=GreaterThan(5000),
                    operator=OP_AND,
                    reducerType=RTYPE_MAX,
                ),
            ],
            executionErrorState='alerting',
            frequency='1m',
            handler=1,
        ),
        # Latency alerts
        Alert(
            name="Redis High Command Latency",
            message="Redis command latency is high",
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='rate(redis_commands_duration_seconds_total{instance=~"$instance"}[$rate_interval]) > 0.1',
                        refId='A',
                        datasource="${datasource}",
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=GreaterThan(0.1),
                    operator=OP_AND,
                    reducerType=RTYPE_MAX,
                ),
            ],
            executionErrorState='alerting',
            frequency='1m',
            handler=1,
        ),
        # Error alerts
        Alert(
            name="Redis High Error Rate",
            message="Redis error rate is high",
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='increase(redis_total_error_replies{instance=~"$instance"}[$rate_interval]) > 100',
                        refId='A',
                        datasource="${datasource}",
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=GreaterThan(100),
                    operator=OP_AND,
                    reducerType=RTYPE_MAX,
                ),
            ],
            executionErrorState='alerting',
            frequency='1m',
            handler=1,
        ),
    ]

def create_redis_dashboard():
    """Create a Redis monitoring dashboard."""
    return Dashboard(
        title="Redis Monitoring",
        description="Dashboard for monitoring Redis metrics",
        tags=["redis", "monitoring", "database"],
        timezone="browser",
        templating=Templating(
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
                    name="instance",
                    dataSource="${datasource}",
                    query='label_values(redis_up, instance)',
                    label="Redis Instance",
                    includeAll=True,
                ),
                Template(
                    name="rate_interval",
                    dataSource=None,
                    query='1m,5m,10m,30m,1h',
                    label="Rate Interval",
                    type='interval',
                    default='5m',
                ),
            ]
        ),
        panels=[
            # Memory Usage Panel
            Graph(
                title="Memory Usage",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='redis_memory_used_bytes{instance=~"$instance"}',
                        legendFormat='Used Memory',
                        refId='A',
                    ),
                    Target(
                        expr='redis_memory_max_bytes{instance=~"$instance"}',
                        legendFormat='Max Memory',
                        refId='B',
                    ),
                ],
                yAxes=single_y_axis(format=BYTES_FORMAT),
                gridPos=GridPos(h=8, w=12, x=0, y=0),
            ),
            Graph(
                title="Memory Fragmentation",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='redis_mem_fragmentation_ratio{instance=~"$instance"}',
                        legendFormat='Fragmentation Ratio',
                        refId='A',
                    ),
                ],
                yAxes=single_y_axis(format=SHORT_FORMAT),
                gridPos=GridPos(h=8, w=12, x=12, y=0),
            ),
            # Client Connections Panel
            Graph(
                title="Client Connections",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='redis_connected_clients{instance=~"$instance"}',
                        legendFormat='Connected Clients',
                        refId='A',
                    ),
                    Target(
                        expr='redis_blocked_clients{instance=~"$instance"}',
                        legendFormat='Blocked Clients',
                        refId='B',
                    ),
                ],
                yAxes=single_y_axis(format=SHORT_FORMAT),
                gridPos=GridPos(h=8, w=12, x=0, y=8),
            ),
            # Command Processing Panel
            Graph(
                title="Commands Processed",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(redis_commands_processed_total{instance=~"$instance"}[$rate_interval])',
                        legendFormat='Commands/sec',
                        refId='A',
                    ),
                ],
                yAxes=single_y_axis(format=SHORT_FORMAT),
                gridPos=GridPos(h=8, w=12, x=12, y=8),
            ),
            # Network Traffic Panel
            Graph(
                title="Network Traffic",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(redis_net_input_bytes_total{instance=~"$instance"}[$rate_interval])',
                        legendFormat='Input Bytes/sec',
                        refId='A',
                    ),
                    Target(
                        expr='rate(redis_net_output_bytes_total{instance=~"$instance"}[$rate_interval])',
                        legendFormat='Output Bytes/sec',
                        refId='B',
                    ),
                ],
                yAxes=single_y_axis(format=BYTES_FORMAT),
                gridPos=GridPos(h=8, w=12, x=0, y=16),
            ),
            # Command Latency Panel
            Graph(
                title="Command Latency",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(redis_commands_duration_seconds_total{instance=~"$instance"}[$rate_interval])',
                        legendFormat='Command Duration',
                        refId='A',
                    ),
                ],
                yAxes=single_y_axis(format=MILLISECONDS_FORMAT),
                gridPos=GridPos(h=8, w=12, x=12, y=16),
            ),
            # Error Rate Panel
            Graph(
                title="Error Rate",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(redis_total_error_replies{instance=~"$instance"}[$rate_interval])',
                        legendFormat='Errors/sec',
                        refId='A',
                    ),
                ],
                yAxes=single_y_axis(format=SHORT_FORMAT),
                gridPos=GridPos(h=8, w=12, x=0, y=24),
            ),
        ],
    ).auto_panel_ids()

# The dashboard variable must be defined at module level for grafanalib
dashboard = create_redis_dashboard()
dashboard.alerts = create_redis_alerts()

if __name__ == "__main__":
    # No-op - grafanalib will use the dashboard variable directly
    pass
