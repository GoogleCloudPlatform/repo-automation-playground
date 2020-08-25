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


class CliSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_recursively_lists_source_files(self):
        cli.list_source_files('test_data/parser/', '*')
        out, _ = self.capsys.readouterr()

        assert 'main.py' in out
        assert 'main_test.py' not in out

        assert 'http' in out
        assert 'nested_tags' in out


class ListRegionTagsTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_recursively_lists_detected_region_tags(self):
        cli.list_region_tags(
            'test_data/parser/',
            True,
            False,
            False,
            False
        )
        out, _ = self.capsys.readouterr()

        assert 'root_tag' in out
        assert 'sample_route' in out

    def test_recursively_lists_undetected_region_tags(self):
        cli.list_region_tags(
            'test_data/parser/',
            False,
            True,
            False,
            False
        )
        out, _ = self.capsys.readouterr()

        assert 'functions_http_unit_test' in out

        # Ignored tags shouldn't be listed
        assert re.search('Ignored.+app', out, re.DOTALL)

    def test_shows_test_counts(self):
        cli.list_region_tags(
            'test_data/parser/flask',
            True,
            False,
            True,
            False
        )
        out, _ = self.capsys.readouterr()

        assert '1 test(s)' in out

    def test_test_counts_warns_if_detected_is_false(self):
        cli.list_region_tags(
            'test_data/parser/',
            False,
            True,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'Undetected/ignored region tags do not have test counts' in out

    def test_shows_file_names(self):
        cli.list_region_tags(
            'test_data/parser/',
            True,
            False,
            True,
            True
        )

        out, _ = self.capsys.readouterr()
        assert re.search(
            'sign_handler.+webapp2/webapp2_main.py', out, re.DOTALL)


class CliEdgeCaseTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_warn_on_improper_region_tag_usage(self):
        with self.assertRaises(ValueError) as err:
            cli.list_region_tags(
                'test_data/cli/bad_region_tag',
                True,
                False,
                True,
                True
            )

        assert 'Mismatched region tags' in str(err.exception)

    def test_injects_xunit_into_stdin(self):
        with open('test_data/parser/edge_cases/xunit_example.xml', 'r') as f:
            xunit_lines = f.readlines()

            cli.inject_snippet_mapping(
                'test_data/parser/edge_cases', xunit_lines)

            out, _ = self.capsys.readouterr()
            assert 'region_tags' in out

    def test_sums_test_counts_from_constituents_and_detected_methods(self):
        cli.list_region_tags(
            'test_data/cli/additions/',
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'untested_method (2 test(s))' in out

    def test_detects_tests_wrapped_in_classes(self):
        cli.list_region_tags(
            'test_data/parser/class_wrapped_tests',
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()
        print(out)
        assert '2 test(s)' in out


class ListSourceFilesTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_respects_tested_arg_all(self):
        cli.list_source_files('test_data/parser/', 'all')
        out, _ = self.capsys.readouterr()

        tests_all_methods = 'flask/flask_main.py'
        tests_some_methods = 'http/http_main.py'
        assert tests_all_methods in out
        assert tests_some_methods not in out

    def test_respects_tested_arg_some(self):
        cli.list_source_files('test_data/parser/', 'some')
        out, _ = self.capsys.readouterr()

        tests_all_methods = 'flask/flask_main.py'
        tests_some_methods = 'http/http_main.py'
        assert tests_all_methods in out
        assert tests_some_methods in out

    def test_respects_tested_arg_none(self):
        cli.list_source_files('test_data/cli/additions', 'none')
        out, _ = self.capsys.readouterr()

        tests_some_methods = 'additions/additions_main.py'
        tests_no_methods = 'additions/untested_file.py'

        assert tests_no_methods in out
        assert tests_some_methods not in out
