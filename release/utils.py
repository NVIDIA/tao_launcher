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
"""Helper utils for packaging."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import os


def get_long_description(root):
    """Get the long description for the launcher wheel."""
    long_desc_file = os.path.join(root, "tlt_pypi_description.md")
    with open(long_desc_file, "r") as lfile:
        data = lfile.read()
    return data


def up_directory(dir_path, n=1):
    """Go up n directories from dir_path."""
    dir_up = dir_path
    for _ in range(n):
        dir_up = os.path.split(dir_up)[0]
    return dir_up


def remove_prefix(dir_path):
    """Remove a certain prefix from path."""
    max_path = 8
    prefix = dir_path
    while max_path > 0:
        prefix = os.path.split(prefix)[0]
        if prefix.endswith('ai_infra'):
            return dir_path[len(prefix) + 1:]
        max_path -= 1
    return dir_path


def get_subdirs(path):
    """Get all subdirs of given path."""
    dirs = os.walk(path)
    return [remove_prefix(x[0]) for x in dirs]


def rename_py_files(path, ext, new_ext, ignore_files):
    """Rename all .ext files in a path to .new_ext except __init__ files."""
    files = glob.glob(path + '/*' + ext)
    for ignore_file in ignore_files:
        files = [f for f in files if ignore_file not in f]

    for filename in files:
        os.rename(filename, filename.replace(ext, new_ext))
