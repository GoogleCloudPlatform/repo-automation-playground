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

import pytest

from . import source_parser


class GetMethodChildrenTest(unittest.TestCase):
    def _clear_fake_method(self, id=None, body=None, func=None):
        fake_method = MagicMock(autospec=False)

        del fake_method.expr
        del fake_method.value

        if id:
            fake_method.id = id
        else:
            del fake_method.id

        if body:
            fake_method.body = body
        else:
            del fake_method.body

        if func:
            fake_method.func = func
        else:
            del fake_method.func

        return fake_method

    @pytest.fixture(autouse=True)
    def _dummy_methods(self):
        self.submethod = self._clear_fake_method('submethod')
        self.submethod_1 = self._clear_fake_method('submethod_1')
        self.submethod_2 = self._clear_fake_method('submethod_2')

    def test_handles_id(self):
        fake_method = self._clear_fake_method('abcd')

        results = source_parser._get_method_children(fake_method)

        assert results == ['abcd']

    def test_treats_body_as_list(self):
        fake_method = self._clear_fake_method(body=[
            self.submethod_1, self.submethod_2
        ])

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod_1', 'submethod_2']

    def test_treats_func_as_list(self):
        fake_method = self._clear_fake_method(func=[
            self.submethod_1, self.submethod_2
        ])

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod_1', 'submethod_2']

    def test_treats_func_as_prop(self):
        fake_method = self._clear_fake_method(func=self.submethod)

        results = source_parser._get_method_children(fake_method)

        assert results == ['submethod']

    def test_handles_func_args(self):
        fake_method = self._clear_fake_method(body=[
            self.submethod, self.submethod_1, self.submethod_2
        ])

        results = source_parser._get_method_children(fake_method)

        assert results == [
            'submethod', 'submethod_1', 'submethod_2']

    def test_body_must_be_list(self):
        fake_method = self._clear_fake_method(body='not_a_list')

        results = source_parser._get_method_children(fake_method)

        assert results == []


class GetTopLevelMethodsTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_file(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'test_data/parser/edge_cases/edge_cases.py'
        )
        self.methods = source_parser.get_top_level_methods(path)

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


class GetEndingLineNumberTest(unittest.TestCase):
    def _clear_fake_elem(self, lineno):
        fake_elem = MagicMock(autospec=False)

        del fake_elem.args
        del fake_elem.body
        del fake_elem.elts
        del fake_elem.exc
        del fake_elem.expr
        del fake_elem.generators
        del fake_elem.iter
        del fake_elem.value
        del fake_elem.values
        del fake_elem.orelse

        fake_elem.lineno = lineno

        return fake_elem

    def test_handles_body_as_list(self):
        elem = self._clear_fake_elem(1)
        elem.body = [self._clear_fake_elem(2), self._clear_fake_elem(3)]

        assert source_parser._get_ending_line(elem) == 3

    def test_handles_empty_body_list(self):
        elem = self._clear_fake_elem(2)
        elem.body = []

        assert source_parser._get_ending_line(elem) == 2

    def test_handles_body_as_element(self):
        elem = self._clear_fake_elem(1)
        elem.body = self._clear_fake_elem(2)

        assert source_parser._get_ending_line(elem) == 2

    def test_handles_exc(self):
        elem = self._clear_fake_elem(1)
        elem.exc = self._clear_fake_elem(2)

        assert source_parser._get_ending_line(elem) == 2

    def test_handles_args(self):
        elem = self._clear_fake_elem(1)
        elem.args = [self._clear_fake_elem(2), self._clear_fake_elem(3)]

        assert source_parser._get_ending_line(elem) == 3

    def test_handles_empty_args(self):
        elem = self._clear_fake_elem(1)
        elem.args = []

        assert source_parser._get_ending_line(elem) == 1

    def test_handles_elts(self):
        elem = self._clear_fake_elem(1)
        elem.elts = [self._clear_fake_elem(2), self._clear_fake_elem(3)]

        assert source_parser._get_ending_line(elem) == 3

    def test_handles_empty_elts(self):
        elem = self._clear_fake_elem(1)
        elem.elts = []

        assert source_parser._get_ending_line(elem) == 1

    def test_handles_generators(self):
        elem = self._clear_fake_elem(1)
        elem.generators = [self._clear_fake_elem(2), self._clear_fake_elem(3)]

        assert source_parser._get_ending_line(elem) == 3

    def test_handles_empty_generators(self):
        elem = self._clear_fake_elem(1)
        elem.generators = []

        assert source_parser._get_ending_line(elem) == 1

    def test_handles_iter(self):
        elem = self._clear_fake_elem(1)
        elem.iter = self._clear_fake_elem(2)

        assert source_parser._get_ending_line(elem) == 2

    def test_handles_values(self):
        elem = self._clear_fake_elem(1)
        elem.values = [self._clear_fake_elem(2), self._clear_fake_elem(3)]

        assert source_parser._get_ending_line(elem) == 3

    def test_handles_empty_values(self):
        elem = self._clear_fake_elem(1)
        elem.values = []

        assert source_parser._get_ending_line(elem) == 1

    def test_handles_value(self):
        elem = self._clear_fake_elem(1)
        elem.value = self._clear_fake_elem(2)

        assert source_parser._get_ending_line(elem) == 2

    def test_handles_orelse(self):
        elem = self._clear_fake_elem(1)
        elem.orelse = [self._clear_fake_elem(2)]

        assert source_parser._get_ending_line(elem) == 2


def test_warns_on_invalid_file(capsys):
    # This test cannot be within a class, since it uses the capsys fixture
    invalid_methods = source_parser.get_top_level_methods('foo.bar')

    _, stderr = capsys.readouterr()

    assert 'could not read file: foo.bar' in stderr
    assert invalid_methods == []
