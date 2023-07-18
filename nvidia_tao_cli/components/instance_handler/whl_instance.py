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

"""TAO Toolkit instance handler for launching jobs on Whl based non-docker instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys
import subprocess

from nvidia_tao_cli.components.instance_handler.base_instance import TAOInstance
from nvidia_tao_cli.components.instance_handler.utils import (
    load_config_file,
)
from nvidia_tao_cli.components.types.task import Task

logger = logging.getLogger(__name__)


class WHLInstance(TAOInstance):
    """Instance handler class to define a TAO Toolkit instance."""

    def __init__(self, task_map, config_path):
        """Initialize a Wheel based TAO Toolkit instance.

        Args:
            task_map(dict): Dictionary of task name to Task data structure.
        """
        super(WHLInstance, self).__init__(
            task_map=task_map,
        )
        self.current_config_path = config_path
        logger.debug("Current config file imported from: {}".format(
            self.current_config_path
        ))

    @staticmethod
    def load_config(config_path):
        """Function to load the json config file.

        Args:
            config_path(str): Unix style path to the config file.

        Returns:
            config_data(dict): Parsed config data.
        """
        data = load_config_file(config_path)
        return data

    @staticmethod
    def parse_launcher_config(config_data):
        """Parse launcher configuration data based on format version.

        Args:
            data(dict): Data containing configuration parameters for the launcher instance

        Returns:
            task_map(dict): Dictionary of tasks mapped to the respective dockers.
        """
        if "format_version" not in config_data.keys():
            raise KeyError("format is a required key in the launcher config.")

        task_map = {}
        docker_images = set()
        if config_data["format_version"] == 1.0:
            local_map = {}
            for image in list(config_data["dockers"].keys()):
                logger.debug("Processing {}".format(image))
                docker_data = config_data["dockers"][image]
                if "tasks" not in list(docker_data.keys()):
                    raise NotImplementedError(
                        "The config data must contain tasks associated with the "
                        "respective docker."
                    )
                local_map.update({
                    task: Task(
                        name=task,
                        docker_image=image,
                        docker_tag=docker_data["docker_tag"],
                        docker_registry=docker_data["docker_registry"],
                        docker_digest=docker_data["docker_digest"] if "docker_digest" in docker_data.keys() else None
                    ) for task in docker_data["tasks"]
                })
                docker_images.add(image)
            task_map["container_actions"] = local_map
        elif config_data["format_version"] == 2.0:
            local_map = {}
            for image in list(config_data["dockers"].keys()):
                logger.debug("Processing {}".format(image))
                docker_data = config_data["dockers"][image]
                if not isinstance(docker_data, dict):
                    raise ValueError("Invalid format.")
                local_map.update({
                    task: Task(
                        name=task,
                        docker_image=image,
                        docker_tag=tag,
                        docker_registry=docker_data[tag]["docker_registry"],
                        docker_digest=docker_data[tag]["docker_digest"] if "docker_digest" in docker_data[tag].keys() else None
                    ) for tag in docker_data.keys() for task in docker_data[tag]["tasks"]
                })
                docker_images.add(image)
            task_map["container_actions"] = local_map
        elif config_data["format_version"] == 3.0:
            for task_group, group_data in config_data["task_group"].items():
                logger.debug("Configuring task group {task_group}".format(
                    task_group=task_group
                ))
                local_map = {}
                for image, image_data in group_data["dockers"].items():
                    logger.debug(
                        "Extracting tasks from docker {image}".format(
                            image=image
                        )
                    )
                    if not isinstance(image_data, dict):
                        raise ValueError(f"Invalid data format for images {type(image_data)} encountered.")
                    local_map.update({
                        task: Task(
                            name=task,
                            docker_image=image,
                            docker_tag=tag,
                            docker_registry=image_data[tag]["docker_registry"],
                            docker_digest=image_data[tag].get("docker_digest", None)
                        ) for tag in image_data.keys() for task in image_data[tag]["tasks"]
                    })
                    docker_images.add(image)
                task_map[task_group] = local_map
        else:
            raise NotImplementedError("Invalid format type: {}".format(config_data["format_version"]))
        return task_map, docker_images

    @classmethod
    def from_config(cls, config_path):
        """Instantiate a TAO Toolkit instance from a config file.

        Args:
            config_path(str): Path to the launcher config file.

        Returns:
            Initialized WHLInstance object.
        """
        config_data = cls.load_config(config_path)
        task_map, _ = cls.parse_launcher_config(config_data)
        debug_string = ""
        for task_name, task in task_map.items():
            debug_string += f"{task_name}: {str(task)}\n"
        logger.debug(debug_string)
        return WHLInstance(
            task_map,
            config_path
        )

    def launch_command(self, task_group, task, args):
        """Launch command for tasks.

        Args:
            task(str): Name of the task from the entrypoint.
            args(list): List of args to the task.

        Returns:
            No explicit returns.
        """
        if task_group in self.task_map.keys():
            task_map = self.task_map[task_group]
            if task in list(task_map.keys()):
                assert isinstance(args, list), (
                    "The arguments must be given as a list to be passed. "
                    "Got a {} instead".format(
                        type(args)
                    )
                )
                if args:
                    command = ""
                    if args[0] == "run":
                        args.pop(0)
                    else:
                        command = "{} ".format(task)
                    command += " ".join(args)
                else:
                    logger.info(
                        "No commands provided to the launcher\n"
                        "Listing the help options "
                        "when you exit."
                    )
                    command += " -h"
                try:
                    subprocess.check_call(
                        command,
                        shell=True,
                        stdout=sys.stdout
                    )
                except subprocess.CalledProcessError as e:
                    if e.output is not None:
                        print("TAO Toolkit command run failed with error: {}".format(e.output))
                        sys.exit(-1)
            else:
                raise NotImplementedError(
                    "Task asked for wasn't implemented to run on WHL instance. {}".format(task))
        else:
            raise NotImplementedError(
                f"Task group asked for wasn't implemented to run on WHL instance: {task_group}"
            )
