from enum import Enum
from typing import Optional

import dagster._check as check
from dagster import (
    Array,
    DagsterEventType,
    Enum as DagsterEnum,
    Field,
    String,
)
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.inputs import FromStepOutput, StepInput
from dagster._core.execution.plan.outputs import StepOutputData
from dagster._core.executor.step_delegating import StepHandlerContext
from dagster._core.storage.event_log import EventLogRecord, SqlEventLogStorage
from dagster._utils.merger import merge_dicts

from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import K8sStepHandler
from dagster_k8s.job import (
    USER_DEFINED_K8S_CONFIG_KEY,
    USER_DEFINED_K8S_CONFIG_SCHEMA,
    UserDefinedDagsterK8sConfig,
)


class InputStrategy(Enum):
    none = "none"
    all = "all"
    first = "first"
    select = "select"

    def is_select(self) -> bool:
        return self.value == InputStrategy.select.value


StringList = Array(String)

USER_DEFINED_K8S_OP_CONFIG_SCHEMA = merge_dicts(
    USER_DEFINED_K8S_CONFIG_SCHEMA.fields,
    {
        {
            "input_strategy": Field(
                DagsterEnum.from_python_enum(InputStrategy),
                default_value=InputStrategy.none,
                is_required=False,
            ),
            "from_inputs": Field(StringList, is_required=False),
        }
    },
)


class K8sOpStepHandler(K8sStepHandler):
    """Specialized step handler that configure the next op based on the op metadata of the prior op."""

    _step_to_container_context: dict[str, K8sContainerContext]
    input_strategy: InputStrategy

    def __init__(
        self,
        image: str | None,
        container_context: K8sContainerContext,
        load_incluster_config: bool,
        kubeconfig_file: str | None,
        k8s_client_batch_api=None,
        input_strategy: InputStrategy = InputStrategy.none,
    ):
        check.inst_param(input_strategy, "input_strategy", InputStrategy)
        self.input_strategy = input_strategy
        self._step_to_container_context = {}
        super().__init__(
            image, container_context, load_incluster_config, kubeconfig_file, k8s_client_batch_api
        )

    def _get_corresponding_output_config(
        self, step_input: StepInput, step_context: StepExecutionContext
    ) -> Optional[K8sContainerContext]:
        source = step_input.source
        if not isinstance(source, FromStepOutput):
            return None
        if source.fan_in:
            return None
        event_log = step_context.instance.event_log_storage
        if not isinstance(event_log, SqlEventLogStorage):
            return None

        def valid_record(record: EventLogRecord) -> bool:
            log_entry = record.event_log_entry
            if log_entry.step_key != step_context.step.key:
                return False
            if not log_entry.is_dagster_event:
                return False
            dagster_event = log_entry.get_dagster_event()
            step_output_data = dagster_event.event_specific_data
            if not isinstance(step_output_data, StepOutputData):
                return False
            if step_output_data.mapping_key:
                # we don't accept dynamic outputs
                return False
            return step_output_data.step_output_handle == source.step_output_handle

        run_id = step_context.dagster_run.run_id
        LIMIT = 100
        event_log_conn = event_log.get_records_for_run(
            run_id, of_type=DagsterEventType.STEP_OUTPUT, limit=LIMIT
        )
        records = [r for r in event_log_conn.records if valid_record(r)]
        # we expect to only have 1 record corresponding to a step output
        while not records and event_log_conn.has_more:
            event_log_conn = event_log.get_records_for_run(
                run_id, event_log_conn.cursor, DagsterEventType.STEP_OUTPUT, LIMIT
            )
            records += [r for r in event_log_conn.records if valid_record(r)]
        if not records:
            return None
        assert len(records) == 1, "unexpected amount of records from filter query"
        output_record = records[0]
        log_entry = output_record.event_log_entry
        dagster_step_output_event = log_entry.get_dagster_event()
        step_output_data: StepOutputData = dagster_step_output_event.event_specific_data
        metadata = step_output_data.metadata
        if not metadata or USER_DEFINED_K8S_CONFIG_KEY not in metadata:
            return None
        config_dict = metadata[USER_DEFINED_K8S_CONFIG_KEY].value
        if not isinstance(config_dict, dict):
            step_context.log.warning(
                f"configured input {step_input.name} has metadata of unexpected type {type(config_dict)}"
            )
            return None
        output_config = UserDefinedDagsterK8sConfig.from_dict(config_dict)
        return K8sContainerContext(run_k8s_config=output_config)

    def _get_combined_input_container_context(
        self, step_handler_context: StepHandlerContext
    ) -> K8sContainerContext:
        step_key = self._get_step_key(step_handler_context)
        step_context = step_handler_context.get_step_context(step_key)
        viable_inputs = step_context.step.step_input_dict
        for step_input in viable_inputs.values():
            self._get_corresponding_output_config(step_input)

    def _get_container_context(
        self, step_handler_context: StepHandlerContext
    ) -> K8sContainerContext:
        step_key = self._get_step_key(step_handler_context)
        if step_key in self._step_to_container_context:
            return self._step_to_container_context[step_key]
        container_context = super()._get_container_context(step_handler_context)
        self._step_to_container_context[step_key] = container_context
        if self.input_strategy == InputStrategy.none:
            return container_context
        # iterate over all inputs and fetch their corresponding output metadata as launch configs

        return container_context
