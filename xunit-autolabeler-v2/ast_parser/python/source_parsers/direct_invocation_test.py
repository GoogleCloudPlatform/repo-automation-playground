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


import ast
import os
from unittest.mock import MagicMock

from . import direct_invocation


def test_ignores_methods_with_existing_drift_attr():
    fake_method = MagicMock()
    fake_method.drift = '1234'

    methods = direct_invocation.parse([fake_method], 'my_class')

    assert fake_method.drift == '1234'
    assert methods == []  # there shouldn't be any processed methods


def test_sets_drift_attr_for_methods_without_it():
    path = os.path.join(
        os.path.dirname(__file__),
        'test_data/direct_invocation_example.py'
    )

    methods = []
    with open(path, 'r') as file:
        content = file.read()
        nodes = ast.iter_child_nodes(ast.parse(content))
        methods = direct_invocation.parse(nodes, 'direct_invocation_example')

    assert len(methods) == 1
    first_method = methods[0]

    assert hasattr(first_method, 'drift')

    drift = first_method.drift

    assert drift.name == 'some_method'
    assert drift.method_name == 'some_method'
    assert drift.class_name == 'direct_invocation_example'
    assert drift.parser == 'direct_invocation'
    assert drift.start_line == 16
