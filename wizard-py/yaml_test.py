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


import unittest
import cli
import pytest
import re


class YamlSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_validates_yaml_recursively(self):
        cli.validate_yaml('test_data/yaml/')
        out, _ = self.capsys.readouterr()
        assert 'Invalid file(s) found!' in out

    def test_handle_untested_marker(self):
        cli.list_region_tags(
            'test_data/yaml/smoke_tests/',
            False,
            False,
            False,
            False
        )
        out, _ = self.capsys.readouterr()
        assert re.search(
            'Ignored region tags.+undetectable_tag', out, re.DOTALL)

    def test_handles_tests_tag(self):
        cli.list_region_tags(
            'test_data/yaml/smoke_tests/',
            True,
            False,
            True,
            False
        )
        out, _ = self.capsys.readouterr()

        assert 'no_explicit_tests (1 test(s))' in out

    def test_handles_additions_tag(self):
        cli.list_region_tags(
            'test_data/yaml/smoke_tests/',
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()
        assert 'additions_tests (1 test(s))' in out


class TestedFalseClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        cli.validate_yaml('test_data/yaml/invalid/')
        out, _ = capsys.readouterr()

        self.out = out

    def test_requires_tested_to_strictequal_false(self):
        print(self.out)
        assert re.search('Invalid tested value.+expected False', self.out)

    def test_tested_tag_not_confused_for_filepath(self):
        assert 'invalid/tested used in' not in self.out

    def test_requires_tested_to_not_be_parsed(self):
        print(self.out)
        assert re.search(
            'Parsed tag detectable_tag.+ marked untested!', self.out)


class ExplicitlySpecifiedClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        cli.validate_yaml('test_data/yaml/explicit_tests/')
        out, _ = capsys.readouterr()
        self.explicit_out = out

        cli.validate_yaml('test_data/yaml/invalid/')
        out, _ = capsys.readouterr()

        self.invalid_out = out

    def test_requires_test_tag_file_to_exist(self):
        assert re.search(
            'Test file .+fake_test.py used in .+drift-data.yml not found!',
            self.invalid_out)


class RelationshipClauseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        cli.validate_yaml('test_data/yaml/invalid/')
        out, _ = capsys.readouterr()

        self.out = out

    def test_requires_additions_tag_to_be_an_array(self):
        assert re.search('Additions key .+ is not a list', self.out)


class OverwriteAttributeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_overwrite_should_replace_detected_region_tags(self):
        cli.list_region_tags(
            'test_data/yaml/overwrite_tests/',
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'method_1 (2 test(s))' in out
        assert 'method_2 (1 test(s))' in out

    def test_overwritten_tags_should_exist_in_source(self):
        cli.validate_yaml('test_data/yaml/invalid/')

        out, _ = self.capsys.readouterr()

        assert 'tag not used in source files: unparsed_overwritten_tag' in out


class YamlEdgeCaseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_requires_parent_tags_to_be_in_grep_region_tags(self):
        cli.validate_yaml('test_data/yaml/invalid/')
        out, _ = self.capsys.readouterr()

        assert 'tag not used in source files: nonexistent_test_file' in out
