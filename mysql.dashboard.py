from grafanalib.core import (
    Dashboard, TimeSeries, Target, GridPos,
    SHORT_FORMAT, BYTES_FORMAT,
    OPS_FORMAT, Stat, AlertCondition, Alert,
    Evaluator, TimeRange, OP_AND,
    EVAL_GT, STATE_ALERTING, Template, Templating, STATE_NO_DATA,
    Graph
)

def create_mysql_alerts():
    """Create all alert definitions used in the dashboard"""
    return {
        'mysql_down': Alert(
            name="MySQL Instance Down",
            message="MySQL instance {{ $labels.instance }} is down",
            executionErrorState=STATE_ALERTING,
            noDataState=STATE_NO_DATA,
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='mysql_up{job=~"$job", instance=~"$instance", environment=~"$environment"} == 0',
                        refId='A',
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=Evaluator(EVAL_GT, 0),
                    operator=OP_AND,
                )
            ],
            frequency="1m",
        ),
        'high_connections': Alert(
            name="High Connection Count",
            message="MySQL instance {{ $labels.instance }} has high number of connections",
            executionErrorState=STATE_ALERTING,
            noDataState=STATE_NO_DATA,
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='mysql_global_status_threads_connected{job=~"$job", instance=~"$instance", environment=~"$environment"} / mysql_global_variables_max_connections * 100 > $connection_threshold',
                        refId='A',
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=Evaluator(EVAL_GT, 0),
                    operator=OP_AND,
                )
            ],
            frequency="1m",
        ),
        'connection_errors': Alert(
            name="High Connection Error Rate",
            message="MySQL instance {{ $labels.instance }} has high connection error rate",
            executionErrorState=STATE_ALERTING,
            noDataState=STATE_NO_DATA,
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='rate(mysql_global_status_connection_errors_total{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m]) > 1',
                        refId='A',
                    ),
                    timeRange=TimeRange("5m", "now"),
                    evaluator=Evaluator(EVAL_GT, 0),
                    operator=OP_AND,
                )
            ],
            frequency="1m",
        ),
        'buffer_pool_free': Alert(
            name="InnoDB Buffer Pool Low Free Pages",
            message="MySQL instance {{ $labels.instance }} has low free buffer pool pages",
            executionErrorState=STATE_ALERTING,
            noDataState=STATE_NO_DATA,
            alertConditions=[
                AlertCondition(
                    Target(
                        expr='mysql_global_status_buffer_pool_pages{job=~"$job", instance=~"$instance", environment=~"$environment", state="free"} / mysql_global_status_buffer_pool_pages{state="total"} * 100 < $buffer_pool_threshold',
                        refId='A',
                    ),
                    timeRange=TimeRange("15m", "now"),
                    evaluator=Evaluator(EVAL_GT, 0),
                    operator=OP_AND,
                )
            ],
            frequency="5m",
        ),
    }

def create_mysql_dashboard():
    """Create the MySQL dashboard with all panels and alerts"""

    alerts = create_mysql_alerts()

    dashboard = Dashboard(
        title="MySQL Overview",
        description="MySQL server performance and health metrics",
        tags=["mysql", "database"],
        timezone="browser",
        refresh="1m",
        editable=True,
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
                    name="job",
                    label="Job",
                    dataSource="${datasource}",
                    query='label_values(mysql_up, job)',
                    type="query",
                    refresh=1,
                    includeAll=True,
                    multi=True
                ),
                Template(
                    name="instance",
                    label="Instance",
                    dataSource="${datasource}",
                    query='label_values(mysql_up{job=~"$job"}, instance)',
                    type="query",
                    refresh=2,
                    includeAll=True,
                    multi=True
                ),
                Template(
                    name="environment",
                    label="Environment",
                    dataSource="${datasource}",
                    query='label_values(mysql_up, environment)',
                    type="query",
                    refresh=1,
                    includeAll=True
                ),
                Template(
                    name="connection_threshold",
                    label="Connection Alert Threshold %",
                    dataSource=None,
                    query="",
                    type="constant",
                    default="80"
                ),
                Template(
                    name="slow_query_threshold",
                    label="Slow Query Alert Threshold",
                    dataSource=None,
                    query="",
                    type="constant",
                    default="5"
                ),
                Template(
                    name="buffer_pool_threshold",
                    label="Buffer Pool Free % Threshold",
                    dataSource=None,
                    query="",
                    type="constant",
                    default="10"
                )
            ]
        ),
        panels=[
            # MySQL Up Status
            Graph(
                title="MySQL Status",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='mysql_up{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='A',
                    )
                ],
                gridPos=GridPos(h=3, w=4, x=0, y=0),
                alert=alerts['mysql_down'],
            ),

            # Connections
            Graph(
                title="MySQL Connections",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='mysql_global_status_threads_connected{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='A',
                        legendFormat='Connected Threads',
                    ),
                    Target(
                        expr='mysql_global_variables_max_connections{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='B',
                        legendFormat='Max Used',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=0, y=3),
                alert=alerts['high_connections'],
            ),

            # Connection Errors
            Graph(
                title="Connection Errors", 
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_connection_errors_total{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='{{error}}',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=12, y=3),
                unit=OPS_FORMAT,
                alert=alerts['connection_errors'],
            ),

            # Buffer Pool Size
            Graph(
                title="InnoDB Buffer Pool Size",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='mysql_global_status_buffer_pool_pages{job=~"$job", instance=~"$instance", environment=~"$environment",state="data"} * on(instance) mysql_global_variables_innodb_page_size{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='A',
                        legendFormat='Data',
                    ),
                    Target(
                        expr='mysql_global_status_buffer_pool_pages{job=~"$job", instance=~"$instance", environment=~"$environment",state="free"} * on(instance) mysql_global_variables_innodb_page_size{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='B',
                        legendFormat='Free',
                    ),
                ],
                gridPos=GridPos(h=8, w=12, x=0, y=11),
                unit=BYTES_FORMAT,
                alert=alerts['buffer_pool_free'],
            ),

            # InnoDB Read/Write
            TimeSeries(
                title="InnoDB Read/Write Operations",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_innodb_data_reads{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='Reads',
                    ),
                    Target(
                        expr='rate(mysql_global_status_innodb_data_writes{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='B',
                        legendFormat='Writes',
                    ),
                ],
                gridPos=GridPos(h=8, w=12, x=12, y=11),
                unit=OPS_FORMAT,
                legendDisplayMode="table",
                legendCalcs=["mean", "max"],
            ),

            # Slow Queries
            TimeSeries(
                title="Slow Queries",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_slow_queries{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='Slow Queries',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=0, y=19),
                unit=SHORT_FORMAT,
            ),

            # Command Operations
            TimeSeries(
                title="Command Operations",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_commands_total{command=~"select|insert|update|delete",job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='{{command}}',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=12, y=19),
                unit=OPS_FORMAT,
                legendDisplayMode="table",
                legendCalcs=["mean", "max"],
            ),

            # Thread Activity
            TimeSeries(
                title="Thread Activity",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='mysql_global_status_threads_running{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='A',
                        legendFormat='Running',
                    ),
                    Target(
                        expr='mysql_global_status_threads_connected{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='B',
                        legendFormat='Connected',
                    ),
                    Target(
                        expr='mysql_global_status_threads_cached{job=~"$job", instance=~"$instance", environment=~"$environment"}',
                        refId='C',
                        legendFormat='Cached',
                    ),
                ],
                gridPos=GridPos(h=8, w=12, x=0, y=27),
                unit=SHORT_FORMAT,
            ),

            # Buffer Pool Hit Ratio
            TimeSeries(
                title="Buffer Pool Hit Ratio",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_buffer_pool_read_requests{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='Read Requests',
                    ),
                    Target(
                        expr='rate(mysql_global_status_buffer_pool_reads{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='B',
                        legendFormat='Reads',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=12, y=27),
                unit=OPS_FORMAT,
            ),

            # Connection Aborts
            TimeSeries(
                title="Connection Aborts",
                dataSource="${datasource}",
                targets=[
                    Target(
                        expr='rate(mysql_global_status_aborted_connects{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='A',
                        legendFormat='Connect Aborts',
                    ),
                    Target(
                        expr='rate(mysql_global_status_aborted_clients{job=~"$job", instance=~"$instance", environment=~"$environment"}[5m])',
                        refId='B',
                        legendFormat='Client Aborts',
                    )
                ],
                gridPos=GridPos(h=8, w=12, x=0, y=35),
                unit=OPS_FORMAT,
            ),
        ],
    )
    return dashboard

# Create dashboard instance
dashboard = create_mysql_dashboard()
