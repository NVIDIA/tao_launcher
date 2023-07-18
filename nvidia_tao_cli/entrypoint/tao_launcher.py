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

"""Simple script to launch TAO Toolkit commands."""

import argparse
import logging
import os
import sys

from nvidia_tao_cli.components.instance_handler.base_instance import INSTANCE_HANDLER_TASKS as CLI_TASKS
from nvidia_tao_cli.components.instance_handler.builder import get_launcher
from nvidia_tao_cli.components.instance_handler.utils import (
    get_config_file
)


logger = logging.getLogger(__name__)

PYTHON_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def build_command_line_parser(parser=None, supported_tasks=None, launcher_instance=None):
    """Build command line parser for the TAO Toolkit launcher."""
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="tao", description="Launcher for TAO Toolkit.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            add_help=True
        )
    module_subparser = parser.add_subparsers(title="task_groups")

    # Parser for tao subtasks.
    for task_group in supported_tasks:
        taskgroup_subparser = module_subparser.add_parser(
            task_group,
            parents=[parser],
            add_help=False,
        )
        task_subparsers = taskgroup_subparser.add_subparsers(title="task")
        if task_group not in CLI_TASKS:
            for task in launcher_instance.task_map[task_group].keys():
                logger.debug(
                    "Task group: {task_group} task {task}".format(
                        task_group=task_group,
                        task=task
                    )
                )
                task_parser = task_subparsers.add_parser(
                    task,
                    parents=[taskgroup_subparser],
                    add_help=False
                )
                task_parser.add_argument(
                    "script_args",
                    nargs=argparse.REMAINDER,
                    type=str,
                    default=None,
                )
        else:
            if task_group == "stop":
                # List of container id's to be closed.
                taskgroup_subparser.add_argument(
                    "--container_id",
                    type=str,
                    nargs="+",
                    required=False,
                    default=None,
                    help="Ids of the containers to be stopped."
                )
                # Force shutdown all containers.
                taskgroup_subparser.add_argument(
                    "--all",
                    action="store_true",
                    default=False,
                    help="Kill all running TAO Toolkit containers.",
                    required=False
                )
            elif task_group == "info":
                taskgroup_subparser.add_argument(
                    "--verbose",
                    action="store_true",
                    default=False,
                    help="Print information about the TAO Toolkit instance."
                )
            else:
                pass
    return parser


def main(args=sys.argv[1:]):
    """TLT entrypoint script to the TAO Toolkit Launcher."""
    verbosity = logging.INFO
    if os.getenv("TAO_LAUNCHER_DEBUG", "0") == "1":
        verbosity = logging.DEBUG

    # Configuring the logger.
    logging.basicConfig(
        format='%(asctime)s [TAO Toolkit] [%(levelname)s] %(name)s %(lineno)d: %(message)s',
        level=verbosity
    )

    # Get the default list of tasks to be supported.
    launcher_config_file = get_config_file()

    instance, supported_tasks = get_launcher(launcher_config_file)
    # Build cascaded command line parser.
    parser = build_command_line_parser(parser=None, supported_tasks=supported_tasks, launcher_instance=instance)

    if not args:
        args = ["--help"]
    task_group = args[0]
    task = None
    if len(args) < 2:
        if task_group not in instance.instance_handler_tasks:
            args += ["--help"]
    else:
        if args[1] != "--help":
            task = args[1]

    # Run tasks in container only if the task group and tasks are supported.
    if task_group in instance.task_map.keys() and task in instance.task_map[task_group].keys():
        instance.launch_command(
            task_group,
            task,
            args[2:]
        )
    else:
        logger.debug("Running command.")
        parsed_args, unknown_args = parser.parse_known_args(args)  # noqa pylint: disable=W0612
        # TODO: CLI related actions to be implemented
        # --> init  (to download the config, validate and place it at ~/.tao/config.json)
        # --> update (to download the latest config and update the config in the default path.)
        # --> list (to list active TAO Toolkit container instances.)
        # run_cli_instruction(task, parsed_args)
        logger.debug(parsed_args)
        instance.launch_command(
            task_group,
            task,
            parsed_args
        )


if __name__ == "__main__":
    main(sys.argv[1:])
