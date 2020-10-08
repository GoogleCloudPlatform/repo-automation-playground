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

import os
import re


IGNORED_METHOD_NAMES = (
    'run_command',
    'parse_command_line_args',
    'main'
)


_APPENGINE_LIB_REGEX = re.compile(r'appengine/(.+/)*lib')


START_VERB_REGEX = re.compile(r'\[START\s(\w+)\]')


def region_tag_predicate(path: str) -> bool:
    """Determines whether a given file (or folder) path
       should be searched for region tags.

    Args:
        path: the path to search

    Returns:
        True if the path's files and subfolders
        should be searched, False otherwise.

    Note:
        If this function is called for a given folder path, it should
        also be called (recursively) for both subfolders and files!
    """
    filename = os.path.basename(path)
    extension = os.path.splitext(path)[1]

    # Language-specific arguments
    if '/node_modules/' in f'/{path}/':
        return False

    if _APPENGINE_LIB_REGEX.search(path):
        return False

    # Dockerfiles
    if 'dockerfile' in path.lower():
        return True

    # Webapps
    if 'appengine' in path and extension in ['.html', '.css']:
        return True

    # Source code
    if extension in ['.js', '.py']:
        return True

    # Metadata files
    if extension in ['.yml', '.yaml']:
        return True
    if filename in [
      'requirements.txt',
      'requirements-dev.txt',
      'package.json',
      'config.json']:
        return True

    # Folders
    if os.path.isdir(path):
        return True

    # Non-matching file
    return False
