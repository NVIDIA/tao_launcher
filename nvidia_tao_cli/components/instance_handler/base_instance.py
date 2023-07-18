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

"""Base class for the TAO Toolkit instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from abc import abstractmethod

INSTANCE_HANDLER_TASKS = ["list", "stop", "info"]


class TAOInstance(object):
    """Simple class definition for a TAO instance."""

    def __init__(self, task_map, docker_images=None):
        """Intialize a base instance of the tao instance handler."""
        self.task_map = task_map
        self.dl_tasks = sorted(list(task_map.keys()))
        self.docker_images = docker_images
        self.instance_handler_tasks = INSTANCE_HANDLER_TASKS

    @staticmethod
    @abstractmethod
    def load_config(config_path):
        """Load TAO Toolkit instance config file."""
        raise NotImplementedError("Base class doesn't have this method implemented.")

    @classmethod
    def from_config(cls, config_path):
        """Initialize an instance from config."""
        raise NotImplementedError("Base class doesn't have this method implemented.")

    @abstractmethod
    def launch_command(self, command, args):
        """Launch the TAO Toolkit command."""
        raise NotImplementedError("Base class doesn't have this method implemented.")
