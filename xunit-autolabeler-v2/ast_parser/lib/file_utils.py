# Copyright 2020 Google LLC.
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


from typing import List, Callable

import os
import subprocess

import constants


def _getFiles(root_dir: str, predicate: Callable[[str], bool]) -> List[str]:
    """Recursively list the files in a given directory
       whose names match the provided predicate function

    Args:
        root_dir: the root directory to search from
        predicate: the predicate function
                                       to filter filenames with

    Returns:
        A list of filepaths relative to root_dir that match the predicate
    """
    if os.path.basename(os.path.normpath(root_dir)).startswith('.'):
        # Ignore dot-directories
        return []

    paths = [os.path.join(root_dir, path) for path in os.listdir(root_dir)
             if path != 'lib']

    folders = [path for path in paths if not os.path.isfile(path)]

    files = [path for path in paths if os.path.isfile(path)
             and predicate(os.path.basename(path))]

    for file in folders:
        files += _getFiles(file, predicate)

    return files


def get_python_files(root_dir: str) -> List[str]:
    """Recursively lists the Python files in a directory

    Args:
        root_dir: the root directory to search from

    Returns:
        A list of Python filepaths relative to root_dir
    """
    return _getFiles(root_dir, lambda path: path.endswith('.py'))


def get_yaml_files(root_dir: str) -> List[str]:
    """Recursively lists the DRIFT yaml metadata files in a directory

    Args:
        root_dir: the root directory to search from

    Returns:
        A list of DRIFT yaml metadata filepaths relative to root_dir
    """
    return _getFiles(root_dir, lambda path: path == '.drift-data.yml')


def get_region_tags(root_dir: str) -> List[str]:
    """Recursively find the region tags in a directory using `grep`

    Args:
        root_dir: the root directory to search from

    Returns:
        The list of region tags found in root_dir
    """
    proc = subprocess.Popen(
        constants.REGION_TAG_GREP_ARGS,
        stdout=subprocess.PIPE,
        cwd=root_dir)
    region_tags = proc.stdout.read().decode().split('\n')
    region_tags = [tag.lstrip('/#').strip() for tag in region_tags]
    region_tags = [tag[7:-1] for tag in region_tags]  # Strip START + brackets
    region_tags = [tag for tag in region_tags if len(tag) > 1]

    return list(set(region_tags))
