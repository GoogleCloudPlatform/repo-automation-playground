# Copyright 2020 Google LLC. All Rights Reserved.
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

from dataclasses import dataclass
from enum import Enum
from typing import List


"""
These structs loosely follow the Protocol Buffers pattern of separate request
and response objects for each method. Unlike Protocol Buffers however, the
objects in this file are designed to be used by CLI-invoked methods - not
HTTP/gRPC-based ones.
"""


class ShowTestedFilesOption(Enum):
    # List all files (default)
    UNSPECIFIED = 1

    # Only list files where all snippets are tested
    ALL_TESTED = 2

    # Only list files where some (and possibly all) snippets are tested
    ANY_TESTED = 3

    # Only list files where no snippets are tested
    NOT_TESTED = 4


@dataclass
class ListSourceFilesInvocation:
    """Struct for storing command-line invocation data for list_source_files()
    calls

    This object stores a user-provided CLI invocation request to
    list_source_files.
    """

    # A path to a polyglot_drift_data.json
    # file for the specified root directory.
    data_json: str

    # A path to the target root directory.
    root_dir: str

    # Whether to show files that various levels of test coverage.
    show_tested_files: ShowTestedFilesOption


@dataclass
class ListSourceFilesResult:
    """Struct for storing output data for list_source_files() calls

    This object stores the processed results of a list_source_files() call.
    """

    # A list of *all* filepaths regardless of snippet test status
    all_files: List[str]

    # A list of filepaths for which *all* snippets are tested.
    all_tested_files: List[str]

    # A list of filepaths for which *some*
    # (and *possibly* all) snippets are tested.
    any_tested_files: List[str]

    # A list of filepaths for which *no* snippets are tested.
    not_tested_files: List[str]
