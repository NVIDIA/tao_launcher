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

"""Define a data structure containing information about a task class."""

import json
import os

OVERRIDE_REGISTRY = os.getenv("OVERRIDE_REGISTRY", None)


class Task(object):
    """Define the task data structure."""

    def __init__(self, name, docker_image=None, docker_tag=None,
                 docker_registry=None, docker_digest=None):
        """Initialize the task data structure.

        Args:
            name(str): Name of the task.
            docker_image(str): Name of the docker image to be mapped to.
            docker_tag(str) (optional): Tag of the docker.
            docker_registry (str): Registry from where the docker should be
                pulled.
            docker_digest(str): Digest value of the docker in the registry.

        """
        self.name = name
        self.docker_image = docker_image
        self.docker_tag = docker_tag
        self.docker_registry = docker_registry
        if OVERRIDE_REGISTRY is not None:
            self.docker_registry = OVERRIDE_REGISTRY
        self.docker_digest = docker_digest

    def get_config(self):
        """Return the Task configuration as a dict."""
        config = {
            "name": self.name,
            "docker_image": self.docker_image,
            "docker_registry": self.docker_registry,
            "docker_tag": self.docker_tag,
            "docker_digest": self.docker_digest
        }
        return config

    @classmethod
    def from_config(cls, config_data):
        """Return a task data structure from config."""
        assert isinstance(config_data, dict), (
            "The config data should be a dictionary."
        )
        mandatory_args = ["name", "docker_image", "docker_tag", "docker_registry"]
        optional_args = ["docker_digest"]
        assert all([key in mandatory_args for key in list(config_data.keys())])
        args = [
            config_data["name"],
            config_data["docker_image"],
            config_data["docker_tag"],
            config_data["docker_registry"]
        ]
        kwargs = {}
        for arg in optional_args:
            if arg in config_data.keys():
                kwargs[arg] = config_data[arg]
        return Task(*args, **kwargs)

    def __str__(self):
        """String representation of this task."""
        config = self.get_config()
        return json.dumps(
            config, indent=4
        )
