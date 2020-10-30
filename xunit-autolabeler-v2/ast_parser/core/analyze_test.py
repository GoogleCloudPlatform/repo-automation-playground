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
        self.method = analyze._get_methods(json_path)[0]

    def test_retrieves_test_methods(self):
        assert len(self.method.test_methods) == 1

    def test_source_paths_are_absolute(self):
        assert os.path.isabs(self.method.source_path)

    def test_test_paths_are_relative(self):
        test_data = self.method.test_methods[0]
        test_path = test_data[0]

        assert not os.path.isabs(test_path)


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
        tuple_methods = analyze._get_methods(json_path)

        _, ignored_tags = analyze._process_file_region_tags(
            os.path.join(_TEST_DIR, 'flask/flask_main.py'),
            json_path,
            tuple_methods
        )

        assert 'app' in ignored_tags


class DedupeSourceMethodsTest(unittest.TestCase):
    def _create_drift_data(self, region_tags):
        return pdd.PolyglotDriftData(
            name=None,
            class_name=None,
            method_name=None,
            source_path=None,
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
