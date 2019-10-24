import abc
from collections import namedtuple
from datetime import datetime

import six
from croniter import croniter

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.serdes import whitelist_for_serdes


class Partition(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def partitions(self):
        pass


class CronSchedule(Partition):
    def __init__(self, cron):
        check.str_param(cron, 'cron')

        self._cron = cron

    def partitions(self):
        current_time = datetime.today()
        return [current_time]

    @property
    def cron_schedule(self):
        return self._cron

    def partition_to_string(self, partition):
        return str(partition)


class TimeBasedPartition(Partition):
    def __init__(self, start_date, cron):
        check.inst_param(start_date, 'start_date', datetime)
        check.str_param(cron, 'cron')

        self._start_date = start_date
        self._cron = cron

    def partitions(self):
        current_time = datetime.today()

        arr = []
        itr = croniter(self._cron, start_time=self._start_date)

        curr = itr.get_next(datetime)
        while curr < current_time:
            arr.append(curr)
            curr = itr.get_next(datetime)

        return arr

    @property
    def cron_schedule(self):
        return self._cron

    def partition_to_string(self, partition):
        return str(partition)


@whitelist_for_serdes
class ScheduleDefinitionData(
    namedtuple('ScheduleDefinitionData', 'name cron_schedule environment_vars')
):
    def __new__(cls, name, cron_schedule, environment_vars=None):
        return super(ScheduleDefinitionData, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.opt_dict_param(environment_vars, 'environment_vars'),
        )


class ScheduleDefinition(object):
    '''Define a schedule that targets a pipeline

    Args:
        name (str): The name of the schedule.
        cron_schedule (str): A valid cron string for the schedule
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this
            execution, as a dict.
        should_execute (Optional[function]): Function that runs at schedule execution time that
            determines whether a schedule should execute. Defaults to a function that always returns
            ``True``.
        environment_vars (Optional[dict]): The environment variables to set for the schedule
    '''

    __slots__ = [
        '_schedule_definition_data',
        '_execution_params',
        '_environment_dict_fn',
        '_should_execute',
        '_schedule',
    ]

    def __init__(
        self,
        name,
        pipeline_name,
        schedule=None,
        cron_schedule=None,
        environment_dict=None,
        environment_dict_fn=None,
        tags=None,
        mode="default",
        should_execute=lambda: True,
        environment_vars=None,
    ):

        if cron_schedule:
            schedule = CronSchedule(cron_schedule)

        self._schedule_definition_data = ScheduleDefinitionData(
            name=check.str_param(name, 'name'),
            cron_schedule=check.str_param(schedule.cron_schedule, 'cron_schedule'),
            environment_vars=check.opt_dict_param(environment_vars, 'environment_vars'),
        )

        check.str_param(pipeline_name, 'pipeline_name')
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
        tags = check.opt_list_param(tags, 'tags')
        check.str_param(mode, 'mode')

        self._environment_dict_fn = check.opt_callable_param(
            environment_dict_fn, 'environment_dict_fn'
        )
        self._should_execute = check.callable_param(should_execute, 'should_execute')

        if self._environment_dict_fn and environment_dict:
            raise DagsterInvalidDefinitionError(
                'Attempted to provide both environment_dict_fn and environment_dict as arguments'
                ' to ScheduleDefinition. Must provide only one of the two.'
            )

        self._execution_params = {
            'environmentConfigData': environment_dict,
            'selector': {'name': pipeline_name},
            'executionMetadata': {"tags": tags},
            'mode': mode,
        }

        self._schedule = check.inst_param(schedule, 'schedule', Partition)
        self._environment_dict_fn = check.opt_callable_param(
            environment_dict_fn, 'environment_dict_fn'
        )
        self._should_execute = check.callable_param(should_execute, 'should_execute')

    @property
    def schedule_definition_data(self):
        return self._schedule_definition_data

    @property
    def name(self):
        return self._schedule_definition_data.name

    @property
    def cron_schedule(self):
        return self._schedule_definition_data.cron_schedule

    @property
    def schedule(self):
        return self._schedule

    @property
    def environment_vars(self):
        return self._schedule_definition_data.environment_vars

    @property
    def execution_params(self):
        return self._execution_params

    @property
    def environment_dict_fn(self):
        return self._environment_dict_fn

    @property
    def should_execute(self):
        return self._should_execute
