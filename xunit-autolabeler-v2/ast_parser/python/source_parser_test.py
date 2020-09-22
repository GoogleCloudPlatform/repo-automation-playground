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
import unittest
from unittest.mock import MagicMock


from . import source_parser

import pytest


class GetMethodChildrenTest(unittest.TestCase):
    def _clear_fake_method(self):
        fake_method = MagicMock(autospec=False)

        del fake_method.id
        del fake_method.body
        del fake_method.expr
        del fake_method.value
        del fake_method.func

        return fake_method

    def test_handles_id(self):
        fake_method = self._clear_fake_method()
        fake_method.id = "abcd"

        results = source_parser._get_method_children(fake_method)

        assert results == ['abcd']

    def test_treats_body_as_list(self):
        submethod_1 = self._clear_fake_method()
        submethod_1.id = "submethod_1"

        submethod_2 = self._clear_fake_method()
        submethod_2.id = "submethod_2"

        fake_method = self._clear_fake_method()
        fake_method.body = [submethod_1, submethod_2]

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod_1', 'submethod_2']

    def test_treats_func_as_list(self):
        submethod_1 = self._clear_fake_method()
        submethod_1.id = "submethod_1"

        submethod_2 = self._clear_fake_method()
        submethod_2.id = "submethod_2"

        fake_method = self._clear_fake_method()
        fake_method.func = [submethod_1, submethod_2]

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod_1', 'submethod_2']

    def test_treats_func_as_prop(self):
        submethod = self._clear_fake_method()
        submethod.id = "submethod"

        fake_method = self._clear_fake_method()
        fake_method.func = submethod

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod']

    def test_handles_func_args(self):
        func_submethod = self._clear_fake_method()
        func_submethod.id = "submethod_func"

        args_submethod_1 = self._clear_fake_method()
        args_submethod_1.id = "submethod_args_1"

        args_submethod_2 = self._clear_fake_method()
        args_submethod_2.id = "submethod_args_2"

        fake_method = self._clear_fake_method()
        fake_method.body = [
            func_submethod, args_submethod_1, args_submethod_2]

        results = source_parser._get_method_children(fake_method)

        assert results == [
            'submethod_func', 'submethod_args_1', 'submethod_args_2']

    def test_body_must_be_list(self):
        fake_method = self._clear_fake_method()
        fake_method.body = "not_a_list"

        results = source_parser._get_method_children(fake_method)

        assert results == []


class GetEndingLineTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_file(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'test_data/new_tests/ending_lines.py'
        )
        self.methods = source_parser.get_top_level_methods(path)

    def test_supports_one_level_function(self):
        method = self.methods[0]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 16
        assert drift.end_line == 20

    def test_supports_multiline_args_tuple(self):
        method = self.methods[1]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 23
        assert drift.end_line == 31

    def test_supports_nested_if_statement(self):
        method = self.methods[2]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 34
        assert drift.end_line == 40

    def test_supports_nested_for_statement(self):
        method = self.methods[3]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 43
        assert drift.end_line == 49

    def test_supports_nested_with_statement(self):
        method = self.methods[4]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 52
        assert drift.end_line == 55

    def test_supports_returning_multiline_tuple(self):
        method = self.methods[5]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 59
        assert drift.end_line == 66

    def test_supports_returning_multiline_dict(self):
        method = self.methods[6]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 70
        assert drift.end_line == 77

    def test_supports_returning_multiline_array(self):
        method = self.methods[7]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 81
        assert drift.end_line == 88

    def test_supports_returning_multiline_list_comp(self):
        method = self.methods[8]

        assert hasattr(method, 'drift')
        drift = method.drift

        assert drift.start_line == 92
        assert drift.end_line == 97


class GetTopLevelMethodsTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_file(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'test_data/parser/edge_cases/edge_cases.py'
        )
        self.methods = source_parser.get_top_level_methods(path)

    def test_initializes_values(self):
        first_method = self.methods[0]

        assert hasattr(first_method, 'drift')
        assert hasattr(first_method.drift, 'test_methods')

    def test_uses_absolute_source_path(self):
        first_method = self.methods[0]

        assert hasattr(first_method, 'drift')

        drift = first_method.drift
        assert hasattr(drift, 'source_path')
        assert os.path.isabs(drift.source_path)

    def test_has_line_numbers(self):
        first_method = self.methods[0]

        assert hasattr(first_method, 'drift')
        drift = first_method.drift

        assert hasattr(drift, 'start_line')
        assert hasattr(drift, 'end_line')
        assert drift.end_line > drift.start_line
