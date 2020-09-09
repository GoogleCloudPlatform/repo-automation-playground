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

import re
import os

from . import constants


def _get_file_paths(
    root_dir: str,
    predicate: Callable[[str], bool]
) -> List[str]:
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

    paths = [os.path.join(root_dir, path) for path in os.listdir(root_dir)]

    folders = [path for path in paths if not os.path.isfile(path)]

    files = [path for path in paths if os.path.isfile(path)
             and predicate(path)]

    for file in folders:
        files += _get_file_paths(file, predicate)

    return files


def get_python_files(root_dir: str) -> List[str]:
    """Recursively lists the Python files in a directory

    Args:
        root_dir: the root directory to search from

    Returns:
        A list of Python filepaths relative to root_dir
    """

    # Not language-agnostic, so keep it in this method
    gae_lib_regex = re.compile(r'/appengine/(.+/)*lib/')

    return _get_file_paths(
        root_dir,
        lambda path: (
            path.endswith('.py') and not gae_lib_regex.search(path)
        )
    )


def get_drift_yaml_files(root_dir: str) -> List[str]:
    """Recursively lists the DRIFT yaml metadata files in a directory

    Args:
        root_dir: the root directory to search from

    Returns:
        A list of DRIFT yaml metadata filepaths relative to root_dir
    """
    return _get_file_paths(
        root_dir,
        lambda path: (
            os.path.basename(path) == '.drift-data.yml'
            or os.path.basename(path) == '.drift-data.yaml'
        )
    )


def get_region_tags(root_dir: str) -> List[str]:
    """Recursively find the region tags in a directory

    Args:
        root_dir: the root directory to search from

    Returns:
        The list of region tags found in root_dir
    """
    file_paths = _get_file_paths(root_dir, constants.region_tag_predicate)
    region_tags = set()
    for path in file_paths:
        with open(path, 'r') as file:
            file_contents = file.read()

            file_region_tags = \
                constants.START_VERB_REGEX.findall(file_contents)

            if file_region_tags:
                region_tags = region_tags.union(set(file_region_tags))

    return list(region_tags)
