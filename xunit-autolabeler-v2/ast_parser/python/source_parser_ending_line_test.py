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

import os

import pytest

from . import source_parser


##############################################################
# Pytest doesn't support parametrizing tests within classes, #
# so this test uses its own file for codebase cleanliness.   #
##############################################################


@pytest.fixture(autouse=True)
def _methods():
    path = os.path.join(
        os.path.dirname(__file__),
        'test_data/new_tests/ending_lines.py'
    )
    return source_parser.get_top_level_methods(path)


@pytest.mark.parametrize(
    'method_idx,start,end',
    [
        (0, 16, 20),
        (1, 23, 31),
        (2, 34, 40),
        (3, 43, 49),
        (4, 52, 55),
        (5, 58, 66),
        (6, 69, 77),
        (7, 80, 88),
        (8, 91, 97),
        (9, 99, 106),
        (10, 109, 116),
        (11, 119, 120)
    ],
    ids=[
        'one_level_function',
        'multiline_args_tuple',
        'nested_if_statement',
        'nested_for_statement',
        'nested_with_statement',
        'returning_multiline_tuple',
        'returning_multiline_dict',
        'returning_multiline_array',
        'returning_multiline_list_comp',
        'if_else',
        'if_elseif',
        'one_line_if'
    ]
)
def test_ending_line(method_idx, start, end, _methods):
    method = _methods[method_idx]

    assert hasattr(method, 'drift')
    drift = method.drift

    assert drift.start_line == start

    # This differs between py3.8 and py3.9
    # The difference doesn't affect parser logic,
    # so we allow both possible results.
    #
    # Likely caused by
    # https://bugs.python.org/issue34822
    assert drift.end_line in [end - 1, end]
