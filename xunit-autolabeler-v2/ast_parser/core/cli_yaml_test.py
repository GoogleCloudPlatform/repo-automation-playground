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

import re
import unittest
from os import path

from ast_parser.core import cli, cli_yaml_errors

import pytest


TEST_DATA_PATH = path.join(
    path.abspath(path.dirname(__file__)), 'test_data/yaml')


class YamlSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys
        self.smoke_path = path.join(TEST_DATA_PATH, 'smoke_tests')

    def test_validates_yaml_recursively(self):
        cli.validate_yaml(
            path.join(TEST_DATA_PATH, 'polyglot_snippet_data.json'),
            TEST_DATA_PATH
        )
        out, _ = self.capsys.readouterr()
        assert 'Invalid file(s) found!' in out


class YamlEdgeCaseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_requires_parent_tags_to_be_in_grep_region_tags(self):
        data_path = path.join(TEST_DATA_PATH, 'invalid')

        json_path = path.join(data_path, 'polyglot_snippet_data.json')
        yaml_path = path.join(data_path, '.drift-data.yml')

        cli.validate_yaml(json_path, data_path)

        out, _ = self.capsys.readouterr()

        error = cli_yaml_errors.UnusedRegionTagViolation(
            'nonexistent_test_file', yaml_path)
        assert str(error) in out


class RequiredValueClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.invalid_path = path.join(TEST_DATA_PATH, 'invalid')
        self.yaml_path = path.join(self.invalid_path, '.drift-data.yml')

        cli.validate_yaml(
            path.join(self.invalid_path, 'polyglot_snippet_data.json'),
            self.invalid_path
        )
        out, _ = capsys.readouterr()

        self.out = out

    def test_tested_strictequal_false(self):
        assert re.search('Invalid tested value.+expected False', self.out)

    def test_tested_not_confused_for_filepath(self):
        assert 'invalid/tested used in' not in self.out

    def test_tested_tags_cannot_be_parsed(self):
        error = cli_yaml_errors.DetectedTagMarkedUndetectedViolation(
            'detectable_tag', self.yaml_path)

        assert str(error) in self.out

    def test_overwritten_tags_exist_in_source(self):
        error = cli_yaml_errors.UnusedRegionTagViolation(
            'unparsed_overwritten_tag', self.yaml_path)
        assert str(error) in self.out


class ManuallySpecifiedClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        invalid_path = path.join(TEST_DATA_PATH, 'invalid')
        explicit_path = path.join(TEST_DATA_PATH, 'explicit_tests')

        data_path = path.join(invalid_path, 'polyglot_snippet_data.json')

        self.test_path = path.join(invalid_path, 'fake_test.py')
        self.yaml_path = path.join(invalid_path, '.drift-data.yml')

        cli.validate_yaml(
            data_path,
            explicit_path,
        )
        out, _ = capsys.readouterr()
        self.explicit_out = out

        cli.validate_yaml(
            data_path,
            invalid_path
        )
        out, _ = capsys.readouterr()

        self.invalid_out = out

    def test_requires_test_tag_file_to_exist(self):
        error = cli_yaml_errors.MissingTestFileViolation(
            self.test_path, self.yaml_path)
        assert str(error) in self.invalid_out


class RelationshipClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        invalid_path = path.join(TEST_DATA_PATH, 'invalid')
        self.yaml_path = path.join(invalid_path, '.drift-data.yml')

        cli.validate_yaml(
            path.join(invalid_path, 'polyglot_snippet_data.json'),
            invalid_path
        )
        out, _ = capsys.readouterr()

        self.out = out

    def test_requires_additions_tag_to_be_an_array(self):
        error = cli_yaml_errors.AdditionsKeyNotAListViolation(
            'additions_tag', self.yaml_path)

        assert str(error) in self.out
