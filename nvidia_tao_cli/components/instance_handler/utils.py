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

"""Utilities for the TAO Toolkit instance handler."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
import shutil

logger = logging.getLogger(__name__)

# Setup default paths.
DOCKER_CONFIG = os.path.expanduser("~/.docker/config.json")

# Launcher config and drive maps.
OVERRIDE_CONFIG = os.path.expanduser("~/.tao/config.json")
DEPLOY_OVERRIDE_CONFIG = os.path.expanduser("~/.tao/config_deploy.json")

# Docker registries supported.
INTERNAL = os.getenv("LAUNCHER_MODE_INTERNAL", "0") == "1"
REQUIRED_REGISTRIES = ["nvcr.io"]
if INTERNAL:
    REQUIRED_REGISTRIES.append("stg.nvcr.io")


def up_directories(path, n):
    """Recursively travel up the directory tree."""
    if n == 0:
        return os.path.dirname(path)
    return up_directories(os.path.dirname(path), n - 1)


def get_config_file(entrypoint_type='tao'):
    """Download a config file to the config_dir.

    Args:
        entrypoint_type (str): Which type of entrypoint to use. (Choices: [tao, tao-deploy]).

    Returns:
        config_file (str): Path to the config file.
    """
    assert entrypoint_type in ['tao', 'tao-deploy'], f"Incorrect entrypoint type named {entrypoint_type}"
    if entrypoint_type == "tao-deploy":
        if os.path.exists(DEPLOY_OVERRIDE_CONFIG) and os.path.isfile(DEPLOY_OVERRIDE_CONFIG):
            logger.info("Initializing configuration from: {}".format(DEPLOY_OVERRIDE_CONFIG))
            return DEPLOY_OVERRIDE_CONFIG
        config_dir = os.path.join(up_directories(__file__, 2), "config")
        config_file = os.path.join(config_dir, "config_deploy.json")
    else:
        if os.path.exists(OVERRIDE_CONFIG) and os.path.isfile(OVERRIDE_CONFIG):
            logger.info("Initializing configuration from: {}".format(OVERRIDE_CONFIG))
            return OVERRIDE_CONFIG
        config_dir = os.path.join(up_directories(__file__, 2), "config")
        config_file = os.path.join(config_dir, "config.json")
    logger.debug("Loading default config file from: {}".format(config_file))
    return config_file


def load_config_file(config_path):
    """Load a config file and return it's data.

    Args:
        config_path(str): Unix style path to the config file.

    Returns:
        data(dict): Parsed config file.
    """
    assert os.path.exists(config_path), (
        "Config path must be a valid unix path. "
        "No file found at: {}. Did you run docker login?".format(config_path)
    )

    # Read the config file and load the data.
    with open(config_path, 'r') as cfile:
        data = json.load(cfile)
    return data


def validate_config_file(config_path):
    """Validate a TAO Toolkit config file.

    Args:
        config_file(str): Unix style path to store the config file.

    Returns:
        True/False: Boolean of whether the downloaded file was valid.
    """
    data = load_config_file(config_path)
    # TODO @vpraveen: This needs to change to the mdf5 based validation
    # once the config file has been formatted.
    return isinstance(data, dict)


def update_config_file(tmpdir_path, config_file_path):
    """Update the current config file and move the previous ones to a new location.

    This function downloads the latest config file, validates the downloaded file,
    hosted in the TAO Toolkit link, backs up the previous config files and places the
    new config at the DEFAULT_CONFIG_FILE path where the local instance expects
    a valid config file.

    **This function has been deprecated**

    Args:
        tmp_dir_path(str): Unix style path to the tmpdir where the instance
            config is downloaded.
        config_file_path(str): Unix style path to where the config file new
            file should be placed.

    Returns:
        True/False: Status of a successful or failed update.
    """
    target_config_dir = os.path.dirname(config_file_path)

    # version the previous config files.
    logger.info("Backing up older configs.")

    # Move current config to config_1.json
    toolkit_version = load_config_file(config_file_path)["toolkit_version"]
    shutil.move(config_file_path, os.path.join(
        target_config_dir, "config_{}.json".format(toolkit_version))
    )
    # Move downloaded directory to config.json
    shutil.move(
        os.path.join(tmpdir_path, "config.json"),
        config_file_path
    )
    return True


def docker_logged_in(docker_config=DOCKER_CONFIG, required_registry=REQUIRED_REGISTRIES):
    """Simple function to warn the user the docker registry required hasn't been logged in."""
    override_registry = os.getenv("OVERRIDE_REGISTRY", None)
    if override_registry is None:
        data = load_config_file(docker_config)

        if "auths" not in list(data.keys()):
            raise ValueError(
                "Docker CLI hasn't been logged in to a registry."
                "Please run `docker login nvcr.io`"
            )
        if not isinstance(required_registry, list):
            required_registry = [required_registry]
        logging.info("Registry: {}".format(required_registry))
        registry_status = [registry in list(data["auths"].keys()) for registry in required_registry]

        def error_msg(registry_status):
            emsg = ""
            for idx, status in enumerate(registry_status):
                if not status:
                    emsg += "\nDocker not logged in to {}. Please run docker login {}".format(
                        required_registry[idx], required_registry[idx]
                    )
            return emsg
        assert all(
            [registry in list(data["auths"].keys()) for registry in required_registry]
        ), error_msg(registry_status)
    else:
        logger.info("Skipping docker login check.")
