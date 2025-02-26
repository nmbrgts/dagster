'''System-provided config objects and constructors.'''
from collections import namedtuple

from dagster import check
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.environment_schema import create_environment_type
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.config import IRunConfig, RunConfig
from dagster.core.types.evaluator import evaluate_config
from dagster.utils import ensure_single_item


def construct_solid_dictionary(solid_dict_value, parent_handle=None, config_map=None):
    config_map = config_map or {}
    for name, value in solid_dict_value.items():
        key = SolidHandle(name, None, parent_handle)
        config_map[str(key)] = SolidConfig.from_dict(value)

        # solids implies a composite solid config
        if value.get('solids'):
            construct_solid_dictionary(value['solids'], key, config_map)

    return config_map


class SolidConfig(namedtuple('_SolidConfig', 'config inputs outputs')):
    def __new__(cls, config, inputs=None, outputs=None):
        return super(SolidConfig, cls).__new__(
            cls,
            config,
            check.opt_dict_param(inputs, 'inputs', key_type=str),
            check.opt_list_param(outputs, 'outputs', of_type=dict),
        )

    @staticmethod
    def from_dict(config):
        check.dict_param(config, 'config', key_type=str)

        return SolidConfig(
            config=config.get('config'),
            inputs=config.get('inputs') or {},
            outputs=config.get('outputs') or [],
        )


class EnvironmentConfig(
    namedtuple(
        '_EnvironmentConfig', 'solids execution storage resources loggers original_config_dict'
    )
):
    def __new__(
        cls,
        solids=None,
        execution=None,
        storage=None,
        resources=None,
        loggers=None,
        original_config_dict=None,
    ):
        check.opt_inst_param(execution, 'execution', ExecutionConfig)
        check.opt_inst_param(storage, 'storage', StorageConfig)
        check.opt_dict_param(original_config_dict, 'original_config_dict')
        check.opt_dict_param(resources, 'resources', key_type=str)

        if execution is None:
            execution = ExecutionConfig(None, None)

        return super(EnvironmentConfig, cls).__new__(
            cls,
            solids=check.opt_dict_param(solids, 'solids', key_type=str, value_type=SolidConfig),
            execution=execution,
            storage=storage,
            resources=resources,
            loggers=check.opt_dict_param(loggers, 'loggers', key_type=str, value_type=dict),
            original_config_dict=original_config_dict,
        )

    @staticmethod
    def from_config_value(config_value, original_config_dict=None):
        check.dict_param(config_value, 'config_value', key_type=str)
        original_config_dict = check.opt_dict_param(
            original_config_dict, 'original_config_dict', key_type=str
        )
        return EnvironmentConfig(
            solids=construct_solid_dictionary(config_value['solids']),
            execution=ExecutionConfig.from_dict(config_value.get('execution')),
            storage=StorageConfig.from_dict(config_value.get('storage')),
            loggers=config_value.get('loggers'),
            original_config_dict=original_config_dict,
            resources=config_value.get('resources'),
        )

    @staticmethod
    def build(pipeline, environment_dict=None, run_config=None):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.opt_dict_param(environment_dict, 'environment')
        run_config = check.opt_inst_param(run_config, 'run_config', IRunConfig, default=RunConfig())

        mode = run_config.mode or pipeline.get_default_mode_name()
        environment_type = create_environment_type(pipeline, mode)

        result = evaluate_config(environment_type, environment_dict, pipeline, run_config)

        if not result.success:
            raise DagsterInvalidConfigError(pipeline, result.errors, environment_dict)

        return EnvironmentConfig.from_config_value(result.value, environment_dict)


class ExecutionConfig(
    namedtuple('_ExecutionConfig', 'execution_engine_name execution_engine_config')
):
    def __new__(cls, execution_engine_name, execution_engine_config):
        return super(ExecutionConfig, cls).__new__(
            cls,
            execution_engine_name=check.opt_str_param(
                execution_engine_name, 'execution_engine_name', 'in_process'
            ),
            execution_engine_config=check.opt_dict_param(
                execution_engine_config, 'execution_engine_config', key_type=str
            ),
        )

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(config, 'config', key_type=str)
        if config:
            execution_engine_name, execution_engine_config = ensure_single_item(config)
            return ExecutionConfig(execution_engine_name, execution_engine_config.get('config'))
        return ExecutionConfig(None, None)


class StorageConfig(namedtuple('_FilesConfig', 'system_storage_name system_storage_config')):
    def __new__(cls, system_storage_name, system_storage_config):
        return super(StorageConfig, cls).__new__(
            cls,
            system_storage_name=check.opt_str_param(
                system_storage_name, 'system_storage_name', 'in_memory'
            ),
            system_storage_config=check.opt_dict_param(
                system_storage_config, 'system_storage_config', key_type=str
            ),
        )

    @staticmethod
    def from_dict(config=None):
        check.opt_dict_param(config, 'config', key_type=str)
        if config:
            system_storage_name, system_storage_config = ensure_single_item(config)
            return StorageConfig(system_storage_name, system_storage_config.get('config'))
        return StorageConfig(None, None)
