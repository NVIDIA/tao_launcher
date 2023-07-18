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

"""TAO Toolkit instance handler for launching jobs locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import logging
import os
import sys
import textwrap

from tabulate import tabulate
from nvidia_tao_cli.components.docker_handler.docker_handler import (
    DOCKER_MOUNT_FILE,
    DockerHandler
)
from nvidia_tao_cli.components.instance_handler.base_instance import TAOInstance
from nvidia_tao_cli.components.instance_handler.utils import (
    docker_logged_in,
    load_config_file,
)
from nvidia_tao_cli.components.types.task import Task

logger = logging.getLogger(__name__)

TAB_SPACE = 4
TABS = " " * TAB_SPACE


class LocalInstance(TAOInstance):
    """Instance handler class to define a TAO Toolkit instance."""

    def __init__(self, task_map, docker_images, config_path):
        """Initialize a local TAO Toolkit instance.

        Args:
            task_map(dict): Dictionary of task name to Task data structure.
            docker_images(list): List of docker image names.
        """
        super(LocalInstance, self).__init__(
            task_map=task_map,
            docker_images=docker_images
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
                    logger.debug(json.dumps(image_data, indent=4))
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
            Initialized LocalInstance object.
        """
        config_data = cls.load_config(config_path)
        task_map, docker_images = cls.parse_launcher_config(config_data)
        debug_string = ""
        for task_name, task in task_map.items():
            if config_data["format_version"] == 3.0:
                task_list = ""
                for name, task_data in task.items():
                    task_list += f"{name}: {str(task_data)}\n"
                debug_string = f"{task_name}: {task_list}"
            else:
                debug_string += f"\n {task_name}: {str(task)}\n"
        logger.debug(debug_string)
        return LocalInstance(
            task_map,
            docker_images,
            config_path
        )

    @property
    def handler_map(self):
        """Get image to handler map."""
        handler_map = {}
        # Build a handler map for the local instance.
        assert bool(self.task_map), (
            "A valid task map wasn't provided."
        )
        logger.debug("Acquiring handler map for dockers.")
        for _, tasks_dict in self.task_map.items():
            for _, map_val in tasks_dict.items():
                handler_key = f"{map_val.docker_image}:{map_val.docker_tag}"
                if handler_key not in handler_map.keys():
                    handler_map[handler_key] = DockerHandler(
                        docker_registry=map_val.docker_registry,
                        image_name=map_val.docker_image,
                        docker_tag=map_val.docker_tag,
                        docker_digest=map_val.docker_digest,
                        docker_mount_file=os.getenv("LAUNCHER_MOUNTS", DOCKER_MOUNT_FILE)
                    )
        return handler_map

    @property
    def _docker_client(self):
        """Get a docker handler to interact with the docker client."""
        docker_handler = list(self.handler_map.values())[0]
        return docker_handler._docker_client

    def _get_running_containers(self):
        """Return a list of running TAO Toolkit containers."""
        assert len(list(self.handler_map.keys())) > 0, (
            "A valid handler map was not defined."
        )
        return [container for container in self._docker_client.containers.list()
                for image in self.handler_map.keys()
                if image in container.attrs["Config"]["Image"]]

    def kill_containers(self, container_ids, kill_all=False):
        """Kill containers by a list of container ids."""
        if kill_all:
            for container in self._get_running_containers():
                container.stop()
        else:
            # Containers don't exist.
            if isinstance(container_ids, list):
                for idx in container_ids:
                    container = self._docker_client.containers.get(idx)
                    container.stop()
            else:
                print("No containers provided in the list to stop. "
                      "Please run tao stop --help for more information.")

    def list_running_jobs(self):
        """Simple function to list all existing jobs in a container."""
        container_list = self._get_running_containers()
        command_per_container = {}
        # Map the commands to the containers.
        for task_group in self.task_map.keys():
            tasks_per_group = self.task_map[task_group].keys()
            for container in container_list:
                procs_list = container.top()
                command_per_container[container] = ""
                for item in procs_list["Processes"]:
                    # Getting the command from the row returned by container top.
                    command = item[-1:][0]
                    # Extracting entrypoint from the running command.
                    task_point = command.split(" ")
                    if len(task_point) < 2:
                        continue
                    task_point = task_point[1]
                    # Since only 1 entrypoint will be launched per container, we only care
                    # about finding the process for that entrypoint.
                    if task_point.split("/")[-1] in tasks_per_group:
                        command_per_container[container] = "{} {}".format(
                            task_point.split("/")[-1],
                            " ".join(command.split(" ")[2:])
                        )
                        # We break from here because the launcher is currently designed to
                        # handle one command per container. And since we only expose the entrypoints
                        # we only need to look for the entrypoints running in the container.
                        # TODO @vpraveen: We may need to change this in the future.
                        break

        # Tabulate and print out the processes.
        self.pretty_print(command_per_container)

    def print_information(self, verbose=False):
        """Print the information of the current TAO Toolkit."""
        print("Configuration of the TAO Toolkit Instance")
        try:
            config = self.load_config(self.current_config_path)
        except AssertionError:
            print("Config file doesn't exist. Aborting information printing")
            sys.exit(-1)
        if verbose:
            print(self.dict_print(config))
        else:
            for key, value in config.items():
                print_value = value
                if isinstance(value, dict):
                    print_value = list(value.keys())
                print("{}: {}".format(key, print_value))
        return False

    def dict_print(self, dictionary, nlevels=0):
        """Print the dictionary element.

        Args:
            dictionary (dict): Dictionary to recursive print
            nlevels (int): Tab indentation level.

        Returns:
            output_string (str): Formatted print string.
        """
        assert isinstance(dictionary, dict), ""
        output_string = "{}".format(f"{TABS}" * nlevels)
        for key, value in dictionary.items():
            output_string += "\n{}{}: ".format(f"{TABS}" * nlevels, key)
            if isinstance(value, dict):
                output_string += "{}{}".format(
                    TABS, self.dict_print(value, nlevels + 1)
                )
            elif isinstance(value, list):
                for idx, item in enumerate(value, start=1):
                    output_string += "\n{}{}. {}".format(f"{TABS}" * (nlevels + 1),
                                                         idx,
                                                         item)
            else:
                output_string += "{}".format(value)
        return output_string

    @staticmethod
    def pretty_print(container_dict):
        """Tabulate and print out the container status."""
        headers = ["container_id", "container_status", "command"]
        data = []
        for container in list(container_dict.keys()):
            container_string = "Not in support DNN tasks."
            if container_dict[container] != "":
                container_string = container_dict[container]
            data.append([
                container.short_id,
                container.status,
                textwrap.fill(container_string, width=100)]
            )
        print(tabulate(data, headers=headers, tablefmt="rst"))

    def launch_command(self, task_group, task, args):
        """Launch command in the respective docker.

        Args:
            task(str): Name of the task from the entrypoint.
            args(list): List of args to the task in the docker.

        Returns:
            No explicit returns.
        """
        if task_group in self.task_map.keys():
            task_map = self.task_map[task_group]
            if task in list(task_map.keys()):
                assert isinstance(args, list), (
                    "The arguments must be given as a list to be passed "
                    "to the docker. Got a {} instead".format(
                        type(args)
                    )
                )
                docker_logged_in(required_registry=task_map[task].docker_registry)
                docker_handler = self.handler_map[
                    f"{task_map[task].docker_image}:{task_map[task].docker_tag}"
                ]
                logger.info(
                    "Running command in container: {}".format(docker_handler.docker_image)
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
                        "Kicking off an interactive docker session.\n"
                        "NOTE: This container instance will be terminated "
                        "when you exit."
                    )
                    command = "/bin/bash"
                # Running command in the container.
                if os.getenv("CI_PROJECT_DIR", None) is not None:
                    docker_handler.run_container_on_ci(command)
                else:
                    docker_handler.run_container(command)
        else:
            assert task_group in self.instance_handler_tasks, (
                "The tasks provided must be in instance handlers tasks or supported DL tasks."
            )
            assert isinstance(args, argparse.Namespace), {
                "The arguments passed to the instance tasks must be argpase.Namespace to a dictionary."
                "Type got here is: {}".format(type(args))
            }
            if task_group == "list":
                self.list_running_jobs()
            elif task_group == "stop":
                self.kill_containers(args.container_id, args.all)
            elif task_group == "info":
                self.print_information(verbose=args.verbose)
            else:
                raise NotImplementedError(
                    "Task asked for wasn't implemented. {}".format(task))
