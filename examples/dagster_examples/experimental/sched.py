import os
from datetime import datetime

from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, TimeBasedPartition, schedules
from dagster.core.definitions.schedule import CronSchedule


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    def dash_stats_datetime_partition_config(date):
        date_string = date.strftime("%Y-%m-%d")

        return {
            'resources': {
                'bigquery': None,
                'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},
            },
            'solids': {'bq_solid': {'config': {'date': date_string}}},
        }

    dash_stats_datetime_partition = ScheduleDefinition(
        name='dash_stats_datetime_partition',
        schedule=CronSchedule(cron='* * * * *'),
        pipeline_name='dash_stats',
        environment_dict_fn=dash_stats_datetime_partition_config,
        environment_vars={
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'SLACK_TOKEN': os.getenv('SLACK_TOKEN'),
        },
    )

    def do_something_datetime_partition_config(date):
        date_string = date.strftime("%Y-%m-%d")

        return {
            'resources': {'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}}},
            'solids': {'something': {'config': {'date': date_string}}},
        }

    do_something_datetime_partition = ScheduleDefinition(
        name='do_something_datetime_partition',
        schedule=TimeBasedPartition(start_date=datetime(2019, 10, 24, 16, 7), cron='0 0 * * *'),
        pipeline_name='do_something',
        environment_dict_fn=do_something_datetime_partition_config,
        environment_vars={'SLACK_TOKEN': os.getenv('SLACK_TOKEN')},
    )

    return [dash_stats_datetime_partition, do_something_datetime_partition]
