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
"""A docker handler to interface with the docker.

This component is responsible for:
1. Interacting with the docker registry
2. Pulling the docker from the registry
3. Instantiating a docker locally.
4. Executing the command locally.
"""

import json
import logging
import os
import sys
import subprocess

import docker
from rich.progress import Progress
from tabulate import tabulate

DOCKER_COMMAND = "docker"
DEFAULT_DOCKER_PATH = "unix://var/run/docker.sock"
VALID_PORT_PROTOCOLS = ["tcp", "udp", "sctp"]
VALID_DOCKER_ARGS = ["user", "ports", "shm_size", "ulimits", "privileged", "network", "tty"]

logger = logging.getLogger(__name__)

TASKS = {}


def get_default_mountsfile():
    """Get the default mounts file."""
    default_mounts = "~/.tao_mounts.json"
    if not os.path.exists(os.path.expanduser(default_mounts)):
        print(
            "~/.tao_mounts.json wasn't found. Falling back to obtain "
            "mount points and docker configs from ~/.tao_mounts.json.\n"
            "Please note that this will be deprecated going forward."
        )
        default_mounts = "~/.tao_mounts.json"
    return default_mounts


def docker_pull_progress(line, progress):
    """Simple function to visualize a docker pull."""
    if line['status'] == 'Downloading':
        idx = f'[red][Download {line["id"]}]'
    elif line['status'] == 'Extracting':
        idx = f'[green][Extract  {line["id"]}]'
    else:
        # skip other statuses
        return
    if idx not in TASKS.keys():
        TASKS[idx] = progress.add_task(f"{idx}", total=line['progressDetail']['total'])
    else:
        progress.update(TASKS[idx], completed=line['progressDetail']['current'])


DOCKER_MOUNT_FILE = get_default_mountsfile()


class DockerHandler(object):
    """Handler to control docker interactions.

    This is an object to encapsulate the interactions of a docker container. It contains routines to
    1. Start a container.
    2. Launch a command
    3. Inspect a container's processes
    4. Stop a container.
    """

    def __init__(self,
                 docker_registry=None,
                 image_name=None,
                 docker_tag=None,
                 docker_digest=None,
                 docker_mount_file=DOCKER_MOUNT_FILE,
                 docker_env_path=DEFAULT_DOCKER_PATH):
        """Initialize the docker handler object."""
        self._docker_client = docker.from_env()
        self._api_client = docker.APIClient(base_url=docker_env_path)
        self._docker_registry = docker_registry
        self._image_name = image_name
        self._docker_mount_file = os.path.expanduser(docker_mount_file)
        self._docker_tag = docker_tag
        self._docker_digest = docker_digest
        self.docker_exec_command = "docker exec"
        self.initialized = True
        self._container = None

    @staticmethod
    def _load_mounts_file(docker_mount_file):
        """Simple function to load the mount file."""
        with open(docker_mount_file, "r") as mfile:
            data = json.load(mfile)
        return data

    def _get_mount_env_data(self):
        """Get the mounts from the tao_mount.json file."""
        mount_points = []
        env_vars = []
        docker_options = dict()
        if not os.path.exists(self._docker_mount_file):
            logging.info(
                "No mount points were found in the {} file.".format(self._docker_mount_file)
            )
            return mount_points, env_vars, docker_options

        # Load mounts file.
        data = self._load_mounts_file(self._docker_mount_file)

        # Extract mounts and environment variables.
        assert "Mounts" in list(data.keys()), (
            "Invalid json file. Requires Mounts key."
        )
        for key, value in data.items():
            if key == "Mounts":
                for mount in value:
                    assert 'source' in list(mount.keys()) and 'destination' in list(mount.keys()), (
                        "Mounts are not formatted correctly."
                    )
                    mount["source"] = os.path.realpath(
                        os.path.expanduser(mount["source"])
                    )
                    mount["destination"] = os.path.realpath(
                        os.path.expanduser(mount["destination"])
                    )
                    logger.debug("Source path: {}, Destination path: {}".format(mount["source"], mount["destination"]))
                    if not os.path.exists(mount['source']):
                        raise ValueError("Mount point source path doesn't exist. {}".format(mount['source']))
                    mount_points.append(mount)
            elif key == "Envs":
                for env_var in value:
                    assert "variable" in list(env_var.keys()) and "value" in list(env_var.keys()), (
                        "Env variables aren't formatter correctly."
                    )
                    env_vars.append(env_var)
            elif key == "DockerOptions":
                docker_options = value
            else:
                raise KeyError("Invalid field {} found in {} file.".format(key, self._docker_mount_file))

        # Extract env variables.
        return mount_points, env_vars, docker_options

    def _check_image_exists(self):
        """Check if the image exists locally."""
        image_list = self._docker_client.images.list()
        assert isinstance(image_list, list), (
            "image_list should be a list."
        )
        for image in image_list:
            image_inspection_content = self._api_client.inspect_image(image.attrs["Id"])
            if image_inspection_content["RepoTags"]:
                if self.docker_image in image_inspection_content["RepoTags"]:
                    return True
        return False

    def pull(self):
        """Pull the base docker."""
        logger.info(
            "Pulling the required container. This may take several minutes if you're doing this for the first time. "
            "Please wait here.\n...")
        try:
            repository = "{}/{}".format(self._docker_registry, self._image_name)
            print("Pulling from repository: {}".format(repository))
            with Progress() as progress:
                response = self._api_client.pull(
                    repository=repository,
                    tag=self._docker_tag,
                    stream=True,
                    decode=True
                )
                for line in response:
                    docker_pull_progress(line, progress)
        except docker.errors.APIError as e:
            print("Docker pull failed. {}".format(e))
            sys.exit(1)
        logger.info("Container pull complete.")

    @property
    def docker_image(self):
        """Get the docker image name."""
        if not self.initialized:
            raise ValueError("Docker instance wasn't initialized")
        return "{}/{}:{}".format(self._docker_registry,
                                 self._image_name,
                                 self._docker_tag)

    @staticmethod
    def formatted_mounts(mountpoints_list):
        """Get formatted mounts for the docker command."""
        assert isinstance(mountpoints_list, list), (
            "Mount points provided to format must be a list"
        )
        volumes = {}
        for mount in mountpoints_list:
            logger.debug("formatting the mounts")
            source_path = os.path.realpath(mount["source"])
            destination_path = os.path.realpath(mount["destination"])
            volumes[source_path] = {
                "bind": destination_path,
                "mode": "rw"
            }

        return volumes

    @staticmethod
    def formatted_envs(env_var_list):
        """Get a formatted list of env vars for the docker."""
        assert isinstance(env_var_list, list), (
            "Env variables provided must be a list"
        )
        env_vars = [
            "{}={}".format(
                item["variable"],
                item["value"]) for item in env_var_list
        ]
        return env_vars

    @staticmethod
    def get_device_requests():
        """Create device requests for the docker."""
        device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])]
        return device_requests

    @staticmethod
    def get_docker_ulimits(name, value):
        """Get ulimits for the host config.

        Args:
            name (str): Name of the ulimit property.
            value (str): Value of the property. This is the same value
                set as soft and hard limit.

        Return:
            docker_limits (list): Listof docker.types.Ulimit objects
                to be used with docker start.
        """
        return docker.types.Ulimit(name=name, soft=value, hard=value)

    def get_docker_option_args(self, docker_options):
        """Setting options for docker args.

        Args:
            docker_options (dict): Dictionary of docker config params.

        Returns:
            docker_args (dict): Keyword args for docker options to be
                defined for docker start.
        """
        docker_args = {}
        if docker_options is not None:
            for key, value in docker_options.items():
                assert key in VALID_DOCKER_ARGS, (
                    "The parameter \"{}\" mentioned in the config file isn't a valid option."
                    "\nPlease choose one of the following: {}".format(key, VALID_DOCKER_ARGS)
                )
                if key == "ulimits":
                    assert isinstance(value, dict), (
                        "Ulimits should be a dictionary of params"
                    )
                    docker_args[key] = [
                        self.get_docker_ulimits(p_name, p_value)
                        for p_name, p_value in value.items()
                    ]
                else:
                    docker_args[key] = value
        return docker_args

    def start_container(self, volumes, env_vars, docker_options=None):
        """This will create a docker container."""
        # Getting user limits for the docker.
        docker_args = self.get_docker_option_args(docker_options)
        if "user" not in list(docker_args.keys()):
            logger.warning(
                "\nDocker will run the commands as root. If you would like to retain your"
                "\nlocal host permissions, please add the \"user\":\"UID:GID\" in the"
                "\nDockerOptions portion of the \"{}\" file. You can obtain your"
                "\nusers UID and GID by using the \"id -u\" and \"id -g\" commands on the"
                "\nterminal.".format(self._docker_mount_file)
            )
        # Try instantiating a container and return error.
        try:
            logger.debug("Starting the TAO Toolkit Container: {}".format(self.docker_image))
            tty = docker_args.get("tty", True)
            if "tty" in docker_args.keys():
                docker_args.pop("tty")
            logger.info("Printing tty value {tty}".format(tty=tty))
            self._container = self._docker_client.containers.run(
                "{}".format(self.docker_image),
                command=None,
                device_requests=self.get_device_requests(),
                tty=tty,
                stderr=True,
                stdout=True,
                detach=True,
                volumes=volumes,
                environment=env_vars,
                remove=True,
                **docker_args
            )
        except docker.errors.APIError as e:
            print("Docker instantiation failed with error: {}".format(e))
            sys.exit(1)

    def run_container(self, task_command):
        """Instantiating an instance of the TAO Toolkit docker."""
        if not self._check_image_exists():
            logger.info(
                "The required docker doesn't exist locally/the manifest has changed. "
                "Pulling a new docker.")
            self.pull()
        mount_data, env_vars, docker_options = self._get_mount_env_data()
        volumes = self.formatted_mounts(mount_data)
        env_variables = self.formatted_envs(env_vars)

        # Start the container if the it isn't already.
        tty = True
        if "tty" in docker_options.keys():
            tty = docker_options["tty"]

        self.start_container(volumes, env_variables, docker_options)
        interactive_option = "-i"
        if tty:
            interactive_option = "-it"

        formatted_command = "bash -c \'{} {} {} {}\'".format(
            self.docker_exec_command,
            interactive_option,
            self._container.id,
            task_command
        )
        logger.debug("volumes: {}".format(volumes))
        logger.debug("formatted_command: {}\nExecuting the command.".format(formatted_command))
        try:
            subprocess.check_call(
                formatted_command,
                shell=True,
                stdout=sys.stdout
            )
        except subprocess.CalledProcessError as e:
            if e.output is not None:
                print("TAO command run failed with error: {}".format(e.output))
                if self._container:
                    logger.info("Stopping container post instantiation")
                    self.stop_container()
                sys.exit(-1)
        finally:
            if self._container:
                logger.info("Stopping container.")
                self.stop_container()

    def run_container_on_ci(self, task_command):
        """Simple function to run command on gitlab-ci."""
        # TODO: @vpraveen: This is a temporary WAR to make sure that the
        # gitlab tty issue doesn't block CI automation of notebooks.
        # will need to revisit this asap before the code freeze.
        if not self._check_image_exists():
            logger.info(
                "The required docker doesn't exist locally/the manifest has changed. "
                "Pulling a new docker.")
            self.pull()
        mount_data, env_vars, docker_options = self._get_mount_env_data()
        volumes = self.formatted_mounts(mount_data)
        env_variables = self.formatted_envs(env_vars)

        volume_args = " ".join(
            [f"-v {source}:{value['bind']}:{value['mode']}" for source, value in volumes.items()]
        )
        env_args = " ".join(
            [f"-e {env_var}" for env_var in env_variables]
        )

        # Start the container if the it isn't already.
        interactive_option = "-i"
        if docker_options.get("tty", True):
            interactive_option += "t"

        docker_command = [
            "docker run",
            f"{interactive_option}",
            "--rm",
            "--gpus all",
            f"{volume_args}",
            f"{env_args}",
        ]
        options = []
        for option, value in docker_options.items():
            if option == "privileged" and value:
                options.append("--privileged")
            if option == "shm_size":
                options.append(f"--shm-size {value}")
        docker_command.extend(options)

        formatted_command = "{} {} {}".format(
            " ".join(docker_command),
            self.docker_image,
            task_command
        )

        logger.debug("volumes: {}".format(volumes))
        logger.debug("formatted_command: {}\nExecuting the command.".format(formatted_command))
        try:
            subprocess.check_call(
                formatted_command,
                shell=True,
                stdout=sys.stdout
            )
        except subprocess.CalledProcessError as e:
            if e.output is not None:
                print("TAO command run failed with error: {}".format(e.output))
                if self._container:
                    logger.info("Stopping container post instantiation")
                    self.stop_container()
                sys.exit(-1)

    def stop_container(self):
        """Stop an instantiated container."""
        logger.debug("Stopping the container: {}".format(
            self.container_id
        ))
        self._container.stop()

    @property
    def container_id(self):
        """Get container id of the current handler."""
        assert isinstance(self._container, docker.models.containers.Container), (
            "The container object should be a docker.models.container.Container instance"
        )
        return self._container.short_id

    def get_processes(self):
        """Get the list of processes running in the container."""
        procs_list = self._container.top()
        processes = procs_list["Processes"]
        title = procs_list["Titles"]
        logger.info(tabulate(processes, headers=title))
        return processes, title
