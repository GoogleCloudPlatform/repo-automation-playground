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

from . import source_parser, test_parser


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


class StoreTestsOnMethodsTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _direct_invocation_map(self):
        root_path = os.path.join(
            TEST_DATA_DIR,
            'parser/edge_cases'
        )

        source_path = os.path.join(root_path, 'edge_cases.py')
        test_path = os.path.join(root_path, 'edge_cases_test.py')

        test_map = test_parser.get_test_key_to_snippet_map(
            test_parser.get_test_methods(test_path)
        )

        self.direct_invocation_test_path = test_path
        self.direct_invocation_methods = \
            source_parser.get_top_level_methods(source_path)

        test_parser.store_tests_on_methods(
            self.direct_invocation_methods, test_map)

    @pytest.fixture(autouse=True)
    def _webapp2_map(self):
        root_path = os.path.join(
            TEST_DATA_DIR,
            'parser/webapp2'
        )

        source_path = os.path.join(root_path, 'webapp2_main.py')
        test_path = os.path.join(root_path, 'webapp2_test.py')

        test_map = test_parser.get_test_key_to_snippet_map(
            test_parser.get_test_methods(test_path)
        )

        self.webapp2_test_path = test_path
        self.webapp2_methods = \
            source_parser.get_top_level_methods(source_path)

        test_parser.store_tests_on_methods(self.webapp2_methods, test_map)

    @pytest.fixture(autouse=True)
    def _flask_map(self):
        root_path = os.path.join(
            TEST_DATA_DIR,
            'parser/flask'
        )

        source_path = os.path.join(root_path, 'flask_main.py')
        test_path = os.path.join(root_path, 'flask_test.py')

        test_map = test_parser.get_test_key_to_snippet_map(
            test_parser.get_test_methods(test_path)
        )

        self.flask_test_path = test_path
        self.flask_methods = source_parser.get_top_level_methods(source_path)

        test_parser.store_tests_on_methods(self.flask_methods, test_map)

    def test_handles_direct_invocations(self):
        test_data = self.direct_invocation_methods[0].drift.test_methods

        assert len(test_data) == 1
        assert test_data[0] == (
            self.direct_invocation_test_path,
            'test_not_main'
        )

    def test_handles_webapp2_routes(self):
        test_data = self.webapp2_methods[0].drift.test_methods

        assert len(test_data) == 2
        assert test_data[0] == (
            self.webapp2_test_path,
            'test_get'
        )
        assert test_data[1] == (
            self.webapp2_test_path,
            'test_post_and_get'
        )

    def test_handles_flask_routes(self):
        test_data = self.flask_methods[0].drift.test_methods

        assert len(test_data) == 1
        assert test_data[0] == (
            self.flask_test_path,
            'test_index'
        )
