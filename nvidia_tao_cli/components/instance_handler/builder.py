# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Returns Docker or WHL instance with their supported tasks."""

import os

from nvidia_tao_cli.components.instance_handler.base_instance import INSTANCE_HANDLER_TASKS as CLI_TASKS

if os.environ.get('TAO_DOCKER_DISABLE', '0') != '0':
    from nvidia_tao_cli.components.instance_handler.whl_instance import WHLInstance
else:
    from nvidia_tao_cli.components.instance_handler.local_instance import LocalInstance


def get_launcher(launcher_config_file):
    """Choose between WHL and Docker based instance.

    Args: launcher_config_file.
    Returns: Instance along with the supported tasks.
    """
    assert os.environ.get('TAO_DOCKER_DISABLE', '0') in ['0', '1'], 'Invalid value for TAO_DOCKER_DISABLE'
    if os.environ.get('TAO_DOCKER_DISABLE', '0') == '1':
        instance = WHLInstance.from_config(launcher_config_file)
        supported_tasks = [*instance.dl_tasks]
    else:
        instance = LocalInstance.from_config(launcher_config_file)
        supported_tasks = [*CLI_TASKS, *instance.dl_tasks]
    return instance, supported_tasks
