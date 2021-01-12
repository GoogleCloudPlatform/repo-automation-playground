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

import pytest

from . import test_parser


TEST_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    'test_data'
)


class GetTestMethodsTests(unittest.TestCase):
    def test_gets_test_methods(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/edge_cases/edge_cases_test.py'
        )

        test_methods = test_parser.get_test_methods(path)

        assert len(test_methods) == 1
        assert test_methods[0].name == 'test_not_main'

    def test_filters_methods_by_prefix(self):
        # test methods should be prefixed with "test_"
        path = os.path.join(
            TEST_DATA_DIR,
            'new_tests/test_parser_sample_test.py'
        )

        test_methods = test_parser.get_test_methods(path)

        assert test_methods == []

    def test_handles_class_wrapped_tests(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/class_wrapped_tests/class_wrapped_test.py'
        )

        test_methods = test_parser.get_test_methods(path)

        assert len(test_methods) == 2
        assert test_methods[0].name == 'test_first'
        assert test_methods[1].name == 'test_second'


def test_warns_on_invalid_file(capsys):
    # This test cannot be within a class, since it uses the capsys fixture
    invalid_methods = test_parser.get_test_methods('foo.bar')

    _, stderr = capsys.readouterr()

    assert 'could not read file: foo.bar' in stderr
    assert invalid_methods == []


class GetTestToMethodMapSmokeTests(unittest.TestCase):
    def test_handles_http_methods(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/http/http_test.py'
        )

        test_methods = test_parser.get_test_methods(path)
        test_map = test_parser.get_test_key_to_snippet_map(test_methods)

        key = ('http_main', 'hello_http')

        assert key in test_map

        entry = test_map[key]
        assert len(entry) == 2
        assert entry[0] == (path, 'test_print_name')
        assert entry[1] == (path, 'test_print_hello_world')

    def test_handles_http_methods(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/flask/flask_parameterized_test.py'
        )

        test_methods = test_parser.get_test_methods(path)
        test_map = test_parser.get_test_key_to_snippet_map(test_methods)

        key = ('get', '/')

        assert key in test_map

    def test_handles_class_and_method_names(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/edge_cases/edge_cases_test.py'
        )

        test_methods = test_parser.get_test_methods(path)
        test_map = test_parser.get_test_key_to_snippet_map(test_methods)

        key = ('edge_cases', 'not_main')

        assert key in test_map

        entry = test_map[key]
        assert len(entry) == 1
        assert entry[0] == (path, 'test_not_main')

    def test_handles_function_wrapped_calls(self):
        path = os.path.join(
            TEST_DATA_DIR,
            'parser/function_wrapped_calls/function_wrapped_test.py'
        )

        test_methods = test_parser.get_test_methods(path)
        test_map = test_parser.get_test_key_to_snippet_map(test_methods)

        key = ('function_wrapped', 'main')

        assert key in test_map

        entry = test_map[key]
        assert len(entry) == 1
        assert entry[0] == (path, 'test_function_wrapped')


class GetTestToMethodMapTryFinallyTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_methods(self):
        self.path = os.path.join(
            TEST_DATA_DIR,
            'parser/try_finally/try_finally_test.py'
        )
        self.test_methods = test_parser.get_test_methods(self.path)
        self.test_map = (
            test_parser.get_test_key_to_snippet_map(self.test_methods))

    def test_finds_tests_in_try_clauses(self):
        key = ('try_finally', 'try_method')
        assert key in self.test_map

        entry = self.test_map[key]
        self.assertEqual(entry, [(self.path, 'test_try_finally')])

    def test_ignores_tests_in_except_clauses(self):
        key = ('try_finally', 'exception_handler')
        assert key not in self.test_map

    def test_finds_tests_in_finally_clauses(self):
        key = ('try_finally', 'final_method')
        assert key in self.test_map

        entry = self.test_map[key]
        self.assertEqual(entry, [(self.path, 'test_try_finally')])
