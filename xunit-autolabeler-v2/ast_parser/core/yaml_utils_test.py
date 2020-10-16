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

from ast_parser.core import polyglot_drift_data, yaml_utils

import pytest


def _create_source_methods_json(region_tag, test_methods):
    return [polyglot_drift_data.PolyglotDriftData(
        # Unused (but non-optional) properties
        # These properties are required outside of tests
        name=None,
        class_name=None,
        method_name=None,
        source_path=None,
        start_line=None,
        end_line=None,
        parser=None,

        # Useful properties
        region_tags=[region_tag],
        test_methods=test_methods
    )]


class HandleOverwritesTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_dir(self):
        self.TEST_DIR = os.path.join(
            os.path.dirname(__file__),
            'test_data/yaml/overwrite_tests/'
        )

    def test_noop_if_region_tag_not_modified(self):
        source_methods_json = \
            _create_source_methods_json(
                'method_0', [('some_test_file.py', 'test_something')])
        yaml_utils._handle_overwrites(source_methods_json, self.TEST_DIR)

        assert len(source_methods_json[0].test_methods) == 1

    def test_noop_if_overwrite_omitted(self):
        source_methods_json = \
            _create_source_methods_json(
                'method_1', [('some_test_file.py', 'test_something')])
        yaml_utils._handle_overwrites(source_methods_json, self.TEST_DIR)
        assert len(source_methods_json[0].test_methods) == 1

    def test_handles_overwrite_if_true(self):
        source_methods_json = \
            _create_source_methods_json(
                'method_2', [('some_test_file.py', 'test_something')])
        yaml_utils._handle_overwrites(source_methods_json, self.TEST_DIR)
        assert source_methods_json[0].test_methods == []


class HandleAdditionsClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_dir(self):
        self.TEST_DIR = os.path.join(
            os.path.dirname(__file__),
            'test_data/yaml/smoke_tests/'
        )

    def test_handles_additions_tag(self):
        source_methods_json = \
            _create_source_methods_json('additions_tests', [])
        yaml_utils._handle_additions_clause(
            source_methods_json, self.TEST_DIR)

        actual_tags = set(source_methods_json[0].region_tags)
        expected_tags = set(['additions_tests', 'detectable_tag'])

        assert actual_tags == expected_tags

    def test_is_bidirectional(self):
        source_methods_json = \
            _create_source_methods_json('detectable_tag', [])
        yaml_utils._handle_additions_clause(
            source_methods_json, self.TEST_DIR)

        actual_tags = set(source_methods_json[0].region_tags)
        expected_tags = set(['additions_tests', 'detectable_tag'])

        assert actual_tags == expected_tags

    def test_ignores_omitted_region_tags(self):
        source_methods_json = \
            _create_source_methods_json('not_mentioned', [])
        yaml_utils._handle_additions_clause(
            source_methods_json, self.TEST_DIR)

        assert source_methods_json[0].region_tags == ['not_mentioned']


class HandleManuallySpecifiedTests(unittest.TestCase):
    def test_ignores_reserved_keys(self):
        TEST_METHODS = [('some_test_file.py', 'test_something')]
        ROOT_DIR = os.path.join(
            os.path.dirname(__file__),
            'test_data/yaml/smoke_tests/'
        )

        source_methods_json = _create_source_methods_json(
            'additions_tests', TEST_METHODS,
        )

        yaml_utils._handle_manually_specified_tests(
            source_methods_json, ROOT_DIR)

        actual_test_methods = source_methods_json[0].test_methods

        assert actual_test_methods == TEST_METHODS

    def test_does_not_ignore_overwrite(self):
        # (overwrite *is* a reserved key, but *can* be
        #  in a manually-specified test's YAML entry)
        TEST_METHODS = []
        ROOT_DIR = os.path.join(
            os.path.dirname(__file__),
            'test_data/yaml/overwrite_tests/'
        )

        source_methods_json = _create_source_methods_json(
            'method_2',
            TEST_METHODS,
        )

        yaml_utils._handle_manually_specified_tests(
            source_methods_json, ROOT_DIR)

        expected_test = [(
            os.path.join(ROOT_DIR, 'overwrite_test.py'),
            'nonexistent_test_method'
        )]

        assert source_methods_json[0].test_methods == [expected_test]


class GetUntestedRegionTagTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _test_dir(self):
        self.TEST_DIR = os.path.join(
            os.path.dirname(__file__),
            'test_data/yaml/invalid/'
        )

    def test_handles_tested_equal_false(self):
        tags = yaml_utils.get_untested_region_tags(self.TEST_DIR)
        assert 'detectable_tag' in tags

    def test_ignores_tested_equal_true(self):
        tags = yaml_utils.get_untested_region_tags(self.TEST_DIR)
        assert 'undetectable_tag' not in tags

    def test_ignores_tested_not_set(self):
        tags = yaml_utils.get_untested_region_tags(self.TEST_DIR)
        assert 'overwritten_tag' not in tags
