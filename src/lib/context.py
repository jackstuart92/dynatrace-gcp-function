#     Copyright 2020 Dynatrace LLC
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import enum
import os
from datetime import datetime, timedelta
from typing import Optional

import aiohttp


class LoggingContext:
    def __init__(self, scheduled_execution_id: Optional[str]):
        self.scheduled_execution_id: str = scheduled_execution_id[0:8] if scheduled_execution_id else None

    def log(self, message: str):
        timestamp_utc = datetime.utcnow()
        timestamp_utc_iso = timestamp_utc.isoformat(sep=" ")
        if self.scheduled_execution_id:
            print(f"{timestamp_utc_iso} [{self.scheduled_execution_id}] : {message}")
        else:
            print(f"{timestamp_utc_iso} : {message}")


class Context(LoggingContext):
    def __init__(
            self,
            session: aiohttp.ClientSession,
            project_id_owner: str,
            token: str,
            execution_time: datetime,
            execution_interval_seconds: int,
            dynatrace_api_key: str,
            dynatrace_url: str,
            print_metric_ingest_input: bool,
            scheduled_execution_id: Optional[str]
    ):
        super().__init__(scheduled_execution_id)

        self.session = session
        self.project_id_owner = project_id_owner
        self.token = token
        self.execution_time = execution_time.replace(microsecond=0)
        self.execution_interval = timedelta(seconds=execution_interval_seconds)
        self.dynatrace_api_key = dynatrace_api_key
        self.dynatrace_url = dynatrace_url
        self.print_metric_ingest_input = print_metric_ingest_input
        self.function_name = os.environ.get("FUNCTION_NAME", "Local")
        self.location = os.environ.get("FUNCTION_REGION", "us-east1")
        self.maximum_metric_data_points_per_minute = int(os.environ.get("MAXIMUM_METRIC_DATA_POINTS_PER_MINUTE", "100000"))
        self.metric_ingest_batch_size = int(os.environ.get("METRIC_INGEST_BATCH_SIZE", "1000"))
        self.require_valid_certificate = os.environ.get("REQUIRE_VALID_CERTIFICATE", "True") in ["True", "T", "true"]

        # self monitoring data
        self.dynatrace_request_count = {}
        self.dynatrace_connectivity = DynatraceConnectivity.Ok

        self.dynatrace_ingest_lines_ok_count = 0
        self.dynatrace_ingest_lines_invalid_count = 0
        self.dynatrace_ingest_lines_dropped_count = 0

        self.setup_execution_time = 0
        self.fetch_gcp_data_execution_time = 0
        self.push_to_dynatrace_execution_time = 0


class DynatraceConnectivity(enum.Enum):
    Ok = 0,
    ExpiredToken = 1,
    WrongToken = 2,
    WrongURL = 3,
    Other = 4
