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


import dataclasses
import os
from typing import Any, Dict, List

from ast_parser.lib import constants as lib_constants, file_utils

from . import constants, source_parser, test_parser


def _parse_source(source_path: str) -> List[Any]:
    source_methods = source_parser.get_top_level_methods(source_path)
    return [method for method in source_methods]


def _parse_test(test_path: str, source_methods: List[Any]) -> None:
    test_methods = test_parser.get_test_methods(test_path)
    test_method_map = test_parser.get_test_key_to_snippet_map(test_methods)

    return test_method_map


def get_json_for_dir(root_dir: str) -> List[Dict]:
    python_files = file_utils.get_python_files(root_dir)

    source_methods = []
    source_files = [file for file in python_files
                    if constants.TEST_FILE_MARKER not in file]

    for file in source_files:
        source_methods += _parse_source(file)

    test_files = [file for file in python_files
                  if constants.TEST_FILE_MARKER in file]

    test_method_map = dict()
    for file in test_files:
        tests = _parse_test(file, source_methods)
        for test_keys, test_value in tests.items():
            key_str = (
                test_keys[0] + lib_constants.KEY_SEPARATOR + test_keys[1])

            if key_str not in test_method_map:
                test_method_map[key_str] = []

            test_method_map[key_str] += test_value

    for method in source_methods:
        new_source_path = os.path.abspath(
            method.drift.source_path)
        method.drift.source_path = new_source_path

    output = {
        'snippets': [
            dataclasses.asdict(method.drift) for method in source_methods
        ],
        'test_method_map': test_method_map
    }

    return output
