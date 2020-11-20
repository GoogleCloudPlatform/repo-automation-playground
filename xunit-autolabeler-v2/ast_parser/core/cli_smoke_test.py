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
import re
import unittest
from unittest.mock import MagicMock, mock_open, patch

from ast_parser.core import cli

import pytest


TEST_DATA_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'test_data')


class CliSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys
        self.parser_path = os.path.join(TEST_DATA_PATH, 'parser')
        self.smoke_path = os.path.join(TEST_DATA_PATH, 'yaml/smoke_tests')

    def test_recursively_lists_source_files(self):
        cli.list_source_files(
            os.path.join(self.parser_path, 'polyglot_snippet_data.json'),
            self.parser_path,
            '*'
        )
        out, _ = self.capsys.readouterr()

        assert 'main.py' in out
        assert 'main_test.py' not in out

        assert 'http' in out
        assert 'nested_tags' in out

    def test_outputs_to_file(self):
        open_mock = mock_open()
        with patch('ast_parser.core.cli.open', open_mock, create=True):
            cli.list_source_files(
                os.path.join(self.parser_path, 'polyglot_snippet_data.json'),
                self.parser_path,
                '*',
                'test-file.txt'
            )

        out = open_mock.return_value.write.call_args[0][0]

        assert 'main.py' in out
        assert 'main_test.py' not in out

        assert 'http' in out
        assert 'nested_tags' in out

    def test_handle_untested_marker(self):
        cli.list_region_tags(
            os.path.join(self.smoke_path, 'polyglot_snippet_data.json'),
            self.smoke_path,
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
            os.path.join(self.smoke_path, 'polyglot_snippet_data.json'),
            self.smoke_path,
            True,
            False,
            True,
            False
        )
        out, _ = self.capsys.readouterr()

        assert 'no_explicit_tests (1 test(s))' in out

    def test_handles_additions_tag(self):
        cli.list_region_tags(
            os.path.join(self.smoke_path, 'polyglot_snippet_data.json'),
            self.smoke_path,
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()
        assert 'additions_tests (1 test(s))' in out

    def test_overwrite_should_replace_detected_region_tags(self):
        data_path = os.path.join(TEST_DATA_PATH, 'yaml/overwrite_tests')

        cli.list_region_tags(
            os.path.join(data_path, 'polyglot_snippet_data.json'),
            data_path,
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'method_1 (2 test(s))' in out
        assert 'method_2 (1 test(s))' in out


class ListRegionTagsTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys
        self.path = os.path.join(TEST_DATA_PATH, 'parser')

    def test_recursively_lists_detected_region_tags(self):
        cli.list_region_tags(
            os.path.join(self.path, 'polyglot_snippet_data.json'),
            self.path,
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
            os.path.join(self.path, 'polyglot_snippet_data.json'),
            self.path,
            False,
            True,
            True,
            False
        )
        out, _ = self.capsys.readouterr()

        assert 'empty_tag' in out

        # Ignored tags should be listed separately
        assert re.search('Ignored.+app', out, re.DOTALL)

    def test_shows_test_counts(self):
        cli.list_region_tags(
            os.path.join(self.path, 'polyglot_snippet_data.json'),
            os.path.join(self.path, 'flask'),
            True,
            False,
            True,
            False
        )
        out, _ = self.capsys.readouterr()

        assert '1 test(s)' in out

    def test_test_counts_warns_if_detected_is_false(self):
        cli.list_region_tags(
            os.path.join(self.path, 'polyglot_snippet_data.json'),
            self.path,
            False,
            True,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'Undetected/ignored region tags do not have test counts' in out

    def test_shows_file_names(self):
        cli.list_region_tags(
            os.path.join(self.path, 'polyglot_snippet_data.json'),
            self.path,
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
        self.cli_path = os.path.join(TEST_DATA_PATH, 'cli')
        self.parser_path = os.path.join(TEST_DATA_PATH, 'parser')

    def test_warn_on_improper_region_tag_usage(self):
        bad_tag_path = os.path.join(self.cli_path, 'bad_region_tag/')
        with self.assertRaises(ValueError) as err:
            cli.list_region_tags(
                os.path.join(bad_tag_path, 'polyglot_snippet_data.json'),
                bad_tag_path,
                True,
                False,
                True,
                True
            )

        assert 'Mismatched region tags' in str(err.exception)

    def test_injects_xunit_into_stdin(self):
        edge_cases_path = os.path.join(self.parser_path, 'edge_cases')
        xunit_path = os.path.join(
            self.parser_path, 'edge_cases/xunit_example.xml')
        with open(xunit_path, 'r') as f:
            xunit_lines = f.readlines()

            cli.inject_snippet_mapping(
                os.path.join(edge_cases_path, 'polyglot_snippet_data.json'),
                edge_cases_path,
                xunit_lines
            )

            out, _ = self.capsys.readouterr()
            assert 'region_tags' in out

    def test_sums_test_counts_from_constituents_and_detected_methods(self):
        additions_path = os.path.join(self.cli_path, 'additions')
        cli.list_region_tags(
            os.path.join(additions_path, 'polyglot_snippet_data.json'),
            additions_path,
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'untested_method (2 test(s))' in out

    def test_detects_tests_wrapped_in_classes(self):
        cli.list_region_tags(
            os.path.join(self.parser_path, 'polyglot_snippet_data.json'),
            os.path.join(self.parser_path, 'class_wrapped_tests'),
            True,
            False,
            True,
            False
        )

        out, _ = self.capsys.readouterr()

        assert '2 test(s)' in out

    def test_errors_on_corrupt_repo_json(self):
        path_mock = MagicMock(wraps=os.path)
        path_mock.isfile = MagicMock(return_value=False)

        with patch('ast_parser.core.analyze.path', path_mock, create=True):
            with self.assertRaises(ValueError) as err:
                cli.list_region_tags(
                    os.path.join(
                        self.parser_path, 'polyglot_snippet_data.json'
                    ),
                    self.parser_path,
                    True,
                    False,
                    True,
                    False
                )

        expected = 'Try regenerating polyglot_snippet_data.json'
        assert expected in str(err.exception)


class DotfileIgnoreTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

        self.cli_path = os.path.join(TEST_DATA_PATH, 'cli/dotfile_test')
        self.dotfile_path = os.path.join(self.cli_path, '.dotfile')

    def test_ignores_dotfile_directories(self):
        cli.list_region_tags(
            os.path.join(self.cli_path, 'polyglot_snippet_data.json'),
            self.cli_path,
            True,
            True,
            False,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'dotfile' not in out

    def test_ignores_dotfile_subdirectories(self):
        cli.list_region_tags(
            os.path.join(self.dotfile_path, 'polyglot_snippet_data.json'),
            self.dotfile_path,
            True,
            True,
            False,
            False
        )

        out, _ = self.capsys.readouterr()

        assert 'dotfile' not in out


class ListSourceFilesTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys
        self.cli_path = os.path.join(TEST_DATA_PATH, 'cli')
        self.parser_path = os.path.join(TEST_DATA_PATH, 'parser')

    def test_respects_tested_arg_all(self):
        cli.list_source_files(
            os.path.join(self.parser_path, 'polyglot_snippet_data.json'),
            self.parser_path,
            'all'
        )
        out, _ = self.capsys.readouterr()

        tests_all_methods = 'flask/flask_main.py'
        tests_some_methods = 'http/http_main.py'

        assert tests_all_methods in out
        assert tests_some_methods not in out

    def test_respects_tested_arg_some(self):
        cli.list_source_files(
            os.path.join(self.parser_path, 'polyglot_snippet_data.json'),
            self.parser_path,
            'some')
        out, _ = self.capsys.readouterr()

        tests_all_methods = 'flask/flask_main.py'
        tests_some_methods = 'http/http_main.py'
        assert tests_all_methods in out
        assert tests_some_methods in out

    def test_respects_tested_arg_none(self):
        additions_path = os.path.join(self.cli_path, 'additions')
        cli.list_source_files(
            os.path.join(additions_path, 'polyglot_snippet_data.json'),
            additions_path,
            'none')
        out, _ = self.capsys.readouterr()

        tests_some_methods = 'additions/additions_main.py'
        tests_no_methods = 'additions/untested_file.py'

        assert tests_no_methods in out
        assert tests_some_methods not in out
