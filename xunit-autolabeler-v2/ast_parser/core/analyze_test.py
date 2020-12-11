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

from ast_parser.core import analyze, polyglot_drift_data as pdd

import mock

import pytest


_TEST_DIR = os.path.join(
    os.path.dirname(__file__),
    'test_data/parser'
)


class GetMethodsTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _methods(self):
        json_path = os.path.join(
            _TEST_DIR,
            'edge_cases/polyglot_snippet_data.json'
        )
        methods, test_method_map = analyze._get_data(json_path)
        analyze._store_tests_on_methods(methods, test_method_map)

        self.method = methods[0]

    def test_retrieves_test_methods(self):
        assert len(self.method.test_methods) == 1

    def test_source_paths_are_absolute(self):
        assert os.path.isabs(self.method.source_path)

    def test_test_paths_are_absolute(self):
        test_data = self.method.test_methods[0]
        test_path = test_data[0]

        assert os.path.isabs(test_path)


class ProcessRegionTagsTest(unittest.TestCase):
    def test_raises_error_on_missing_source_file(self):
        with self.assertRaisesRegex(ValueError, 'not found!'):
            analyze._process_file_region_tags(
                'bad_path',
                os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
                _TEST_DIR
            )

    def test_adds_child_drift_data(self):
        with mock.patch('ast_parser.core.analyze.polyglot_parser') \
          as parser_mock:
            parser_mock.get_region_tag_regions.return_value = ([], [])

            analyze.analyze_json(
                os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
                _TEST_DIR
            )

            source_path = os.path.abspath(
                os.path.join(_TEST_DIR, 'http/http_main.py'))
            parser_mock.get_region_tag_regions.assert_any_call(source_path)

    def test_labels_ignored_tags(self):
        json_path = os.path.join(
            _TEST_DIR,
            'edge_cases/polyglot_snippet_data.json'
        )
        tuple_methods, _ = analyze._get_data(json_path)

        _, ignored_tags = analyze._process_file_region_tags(
            os.path.join(_TEST_DIR, 'flask/flask_main.py'),
            json_path,
            tuple_methods
        )

        assert 'app' in ignored_tags


class DedupeSourceMethodsTest(unittest.TestCase):
    def _create_drift_data(self, region_tags, name=None):
        return pdd.PolyglotDriftData(
            name=name,
            class_name=None,
            method_name=None,
            source_path='',
            start_line=None,
            end_line=None,
            parser=None,
            region_tags=region_tags
        )

    def test_dedupes_methods(self):
        methods = [
            self._create_drift_data(['a', 'b']),
            self._create_drift_data(['a', 'b'])
        ]

        assert len(analyze._dedupe_source_methods(methods)) == 1

    def test_ignores_region_tag_order(self):
        methods = [
            self._create_drift_data(['a', 'b']),
            self._create_drift_data(['b', 'a'])
        ]

        assert len(analyze._dedupe_source_methods(methods)) == 1

    def test_keeps_snippet_invocation_methods_without_tags(self):
        method_name = 'run_sample'
        methods = [
            self._create_drift_data(['a', 'b']),
            self._create_drift_data(['b', 'a']),

            # this method is considered a 'snippet invocation method'
            # these methods aren't required to have region tags
            self._create_drift_data([], method_name),
        ]

        results = analyze._dedupe_source_methods(methods)

        assert len(results) == 2
        assert results[1].name == method_name


class StoreTestsOnMethodsTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _direct_invocation_map(self):
        root_path = os.path.join(_TEST_DIR, 'edge_cases')
        json_path = os.path.join(
            _TEST_DIR,
            'edge_cases/polyglot_snippet_data.json'
        )

        self.direct_invocation_test_path = (
            os.path.join(root_path, 'edge_cases_test.py'))

        self.direct_invocation_methods, test_map = (
            analyze._get_data(json_path))

        analyze._store_tests_on_methods(
            self.direct_invocation_methods, test_map)

    @pytest.fixture(autouse=True)
    def _webapp2_map(self):
        root_path = os.path.join(_TEST_DIR, 'webapp2')
        json_path = os.path.join(
            _TEST_DIR,
            'webapp2/polyglot_snippet_data.json'
        )

        self.webapp2_test_path = os.path.join(root_path, 'webapp2_test.py')
        self.webapp2_methods, test_map = analyze._get_data(json_path)

        analyze._store_tests_on_methods(self.webapp2_methods, test_map)

    @pytest.fixture(autouse=True)
    def _flask_map(self):
        root_path = os.path.join(_TEST_DIR, 'flask')
        json_path = os.path.join(
            _TEST_DIR,
            'flask/polyglot_snippet_data.json'
        )

        self.flask_test_path = os.path.join(root_path, 'flask_test.py')
        self.flask_methods, test_map = analyze._get_data(json_path)

        analyze._store_tests_on_methods(self.flask_methods, test_map)

    def test_handles_direct_invocations(self):
        test_data = self.direct_invocation_methods[0].test_methods

        assert len(test_data) == 1
        assert test_data[0] == (
            self.direct_invocation_test_path,
            'test_not_main'
        )

    def test_handles_webapp2_routes(self):
        test_data = self.webapp2_methods[0].test_methods

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
        test_data = self.flask_methods[0].test_methods

        assert len(test_data) == 1
        assert test_data[0] == (
            self.flask_test_path,
            'test_index'
        )
