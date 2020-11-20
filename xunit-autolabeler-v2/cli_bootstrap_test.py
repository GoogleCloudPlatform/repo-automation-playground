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


import io
import os
import unittest
import xml.etree.ElementTree as etree

import cli_bootstrap

import pytest


class CliSmokeTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    @pytest.fixture(autouse=True)
    def monkeypatch(self, monkeypatch):
        self.monkeypatch = monkeypatch

    @pytest.fixture(autouse=True)
    def init_values(self):
        self.test_dir = os.path.abspath('ast_parser/core/test_data/parser')

        self.xml_path = os.path.join(
            self.test_dir, 'edge_cases/xunit_example.xml')

        with open(self.xml_path, 'r+') as xml_file:
            self.xml_contents = xml_file.read()

    def test_list_region_tags(self):
        cli_bootstrap.parse_args([
            'list-region-tags', self.test_dir])

        out, _ = self.capsys.readouterr()

        assert 'root_tag' in out

    def test_list_source_files(self):
        cli_bootstrap.parse_args([
            'list-source-files', self.test_dir])

        out, _ = self.capsys.readouterr()
        assert 'nested_tags.py' in out

    def test_inject_xunit(self):
        self.monkeypatch.setattr(
            'sys.stdin',
            io.StringIO(self.xml_contents)
        )

        cli_bootstrap.parse_args([
            'inject-snippet-mapping', self.test_dir
        ])

        out, _ = self.capsys.readouterr()

        # assert out is valid XML
        try:
            etree.fromstring(out)
        except Exception:
            self.fail('XML parsing failed')

        expected = 'name="test_not_main" region_tags="not_main"'
        assert expected in out

    def test_validate_yaml(self):
        cli_bootstrap.parse_args([
            'validate-yaml', self.test_dir])

        out, _ = self.capsys.readouterr()
        assert 'All files are valid' in out
