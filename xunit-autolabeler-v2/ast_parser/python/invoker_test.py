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

from . import invoker


TEST_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    'test_data/parser/edge_cases'
)

source_path = os.path.join(TEST_DATA_PATH, 'edge_cases.py')
test_path = os.path.join(TEST_DATA_PATH, 'edge_cases_test.py')


def test_recognizes_source_files():
    methods = invoker._parse_source(source_path)

    assert len(methods) == 1


def test_recognizes_test_files():
    methods = invoker._parse_source(source_path)

    invoker._parse_test(test_path, methods)

    assert len(methods) == 1
    assert len(methods[0].drift.test_methods) == 1


def test_get_json_for_dir():
    repo_obj = invoker.get_json_for_dir(TEST_DATA_PATH)
    assert len(repo_obj) == 1

    first_repo_obj = repo_obj[0]

    assert 'name' in first_repo_obj
    assert 'class_name' in first_repo_obj
    assert 'parser' in first_repo_obj
    assert 'start_line' in first_repo_obj
    assert 'end_line' in first_repo_obj
    assert 'method_name' in first_repo_obj
    assert 'test_methods' in first_repo_obj
