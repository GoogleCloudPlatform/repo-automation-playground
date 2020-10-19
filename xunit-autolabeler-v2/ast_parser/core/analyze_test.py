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

from ast_parser.core import analyze

import mock

import pytest


_TEST_DIR = os.path.join(
    os.path.dirname(__file__),
    'test_data/parser'
)


class AnalyzeBasicTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _get_analyze_result(self):
        basic_test_dir = os.path.join(_TEST_DIR, 'edge_cases')
        analyze_result = analyze.analyze_json(
            os.path.join(basic_test_dir, 'polyglot_snippet_data.json'),
            basic_test_dir
        )

        (self.grep_tags,
         self.source_tags,
         self.ignored_tags,
         self.source_methods) = analyze_result

    def test_normalizes_source_paths(self):
        assert self.source_methods != []

        source_path = self.source_methods[0].source_path
        assert source_path is not None
        assert os.path.isabs(source_path)

    def test_converts_test_methods_to_tuples(self):
        assert self.source_methods != []

        test_methods = self.source_methods[0].test_methods
        assert test_methods != []

        test = test_methods[0]
        assert type(test) == tuple


class AnalyzeMiscTests(unittest.TestCase):
    def test_raises_error_on_missing_source_file(self):
        with mock.patch('ast_parser.core.analyze.path') as path_mock:
            path_mock.isfile.return_value = False

            with self.assertRaisesRegex(ValueError, 'not found!'):
                analyze.analyze_json(
                    os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
                    _TEST_DIR
                )

    def test_dedupes_region_tags(self):
        analyze_result = analyze.analyze_json(
            os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
            _TEST_DIR
        )

        _, _, _, source_methods = analyze_result
        tag_sets = [method.region_tags for method in source_methods]

        assert sum(tag_set == ['not_main'] for tag_set in tag_sets) == 1


class AnalyzeMockCallTests(unittest.TestCase):
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

    def test_adds_yaml_data(self):
        with mock.patch('ast_parser.core.analyze.yaml_utils') \
          as yaml_mock:
            analyze.analyze_json(
                os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
                _TEST_DIR
            )

            yaml_mock.add_yaml_data_to_source_methods.assert_called()


class AnalyzeSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _get_analyze_result(self):
        analyze_result = analyze.analyze_json(
            os.path.join(_TEST_DIR, 'polyglot_snippet_data.json'),
            _TEST_DIR
        )

        (self.grep_tags,
         self.source_tags,
         self.ignored_tags,
         self.source_methods) = analyze_result

    def test_grep_tags_includes_undetected_tags(self):
        assert 'main_method' not in self.source_tags
        assert 'main_method' in self.grep_tags

    def test_source_tags_only_includes_detected_tags(self):
        assert 'not_main' in self.source_tags
        assert 'main_method' not in self.source_tags

    def test_omits_ignored_tags(self):
        assert 'app' not in self.source_tags
        assert 'app' in self.ignored_tags
